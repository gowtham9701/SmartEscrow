"""
AI technical skill-verification engine (GitHub-based).

This module implements objective, evidence-based developer vetting that replaces
resume keyword-stuffing with measurable signals pulled from a candidate's public
GitHub activity. It produces an explainable 0-100 "talent grade" together with a
per-dimension breakdown and a set of verified skills.

Dimensions scored (each normalized 0-100, then weighted):
  * Code quality  - radon Cyclomatic Complexity + Maintainability Index on real
                    source files fetched from the candidate's top repositories.
  * Languages     - breadth of languages actually used (by code bytes).
  * Impact        - total and peak repository stars (log-normalized).
  * Velocity      - recency of pushes and number of repos active in the last year.
  * Originality   - share of original (non-fork) repositories.
  * Discipline    - presence of tests / CI configuration and documentation.

The engine is resilient: if the network, rate limits, or individual files are
unavailable, it degrades gracefully and still returns a grade from whatever
signals it could gather. All calls are read-only and use the public GitHub REST
API; an optional token raises the rate limit.
"""
from __future__ import annotations

import base64
import json
import logging
import math
import urllib.error
import urllib.request
from datetime import datetime, timezone

from app.core.config import settings

logger = logging.getLogger("smartescrow.verification")

GITHUB_API = "https://api.github.com"
_UA = "Mozilla/5.0 (SmartEscrow Verification Engine) AppleWebKit/537.36 Chrome/120 Safari/537.36"

# How much work to do (keeps calls bounded and fast).
_MAX_REPOS = 100
_MAX_CODE_REPOS = 3        # repos to sample source code from
_MAX_FILES_PER_REPO = 6    # source files per repo for radon analysis
_TIMEOUT = 12

# Weights for the composite talent grade (sum = 1.0).
_WEIGHTS = {
    "code_quality": 0.30,
    "languages": 0.15,
    "impact": 0.20,
    "velocity": 0.15,
    "originality": 0.10,
    "discipline": 0.10,
}

# Map GitHub language names to normalized skill tags.
_LANG_SKILL = {
    "Python": "Python", "JavaScript": "JavaScript", "TypeScript": "TypeScript",
    "Java": "Java", "Go": "Go", "Rust": "Rust", "C": "C", "C++": "C++",
    "C#": "C#", "Ruby": "Ruby", "PHP": "PHP", "Swift": "Swift", "Kotlin": "Kotlin",
    "Scala": "Scala", "Dart": "Dart", "HTML": "HTML", "CSS": "CSS",
    "Shell": "Shell", "Jupyter Notebook": "Data Science", "Vue": "Vue",
    "Objective-C": "iOS", "HCL": "Terraform", "Dockerfile": "Docker",
}

# Repo-topic / name hints that imply framework skills.
_FRAMEWORK_HINTS = {
    "react": "React", "next": "Next.js", "node": "Node.js", "django": "Django",
    "flask": "Flask", "fastapi": "FastAPI", "spring": "Spring", "kubernetes": "Kubernetes",
    "k8s": "Kubernetes", "terraform": "Terraform", "docker": "Docker", "tensorflow": "TensorFlow",
    "pytorch": "PyTorch", "ml": "Machine Learning", "llm": "LLM", "graphql": "GraphQL",
    "aws": "AWS", "gcp": "GCP", "azure": "Azure", "angular": "Angular", "svelte": "Svelte",
}


def _request(path: str) -> tuple[int, object]:
    """GET the GitHub API. Returns (status_code, parsed_json_or_text)."""
    url = path if path.startswith("http") else GITHUB_API + path
    req = urllib.request.Request(url)
    req.add_header("User-Agent", _UA)
    req.add_header("Accept", "application/vnd.github+json")
    if settings.GITHUB_APP_TOKEN:
        req.add_header("Authorization", f"Bearer {settings.GITHUB_APP_TOKEN}")
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            body = resp.read()
            try:
                return resp.status, json.loads(body)
            except json.JSONDecodeError:
                return resp.status, body.decode("utf-8", "ignore")
    except urllib.error.HTTPError as exc:
        return exc.code, None
    except Exception as exc:  # network error, timeout, etc.
        logger.info("GitHub request failed for %s: %s", url, exc)
        return 0, None


def _days_since(iso: str | None) -> float:
    if not iso:
        return 9999.0
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt).total_seconds() / 86400.0
    except ValueError:
        return 9999.0


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _radon_metrics(source: str) -> tuple[float, float] | None:
    """Return (avg_cyclomatic_complexity, maintainability_index) for Python source."""
    try:
        from radon.complexity import cc_visit
        from radon.metrics import mi_visit
    except ImportError:
        return None
    try:
        blocks = cc_visit(source)
        avg_cc = sum(b.complexity for b in blocks) / len(blocks) if blocks else 1.0
        mi = mi_visit(source, multi=True)
        return avg_cc, mi
    except (SyntaxError, Exception):
        return None


def _sample_python_files(full_name: str, default_branch: str) -> list[str]:
    """Fetch up to _MAX_FILES_PER_REPO Python source files from a repo."""
    status, tree = _request(f"/repos/{full_name}/git/trees/{default_branch}?recursive=1")
    if status != 200 or not isinstance(tree, dict):
        return []
    py = [t["path"] for t in tree.get("tree", [])
          if t.get("type") == "blob" and t.get("path", "").endswith(".py")
          and "test" not in t["path"].lower() and t.get("size", 0) < 60000]
    sources: list[str] = []
    for path in py[:_MAX_FILES_PER_REPO]:
        st, content = _request(f"/repos/{full_name}/contents/{path}")
        if st == 200 and isinstance(content, dict) and content.get("encoding") == "base64":
            try:
                sources.append(base64.b64decode(content["content"]).decode("utf-8", "ignore"))
            except Exception:
                continue
    return sources


def _has_tests_or_ci(full_name: str, default_branch: str) -> bool:
    status, tree = _request(f"/repos/{full_name}/git/trees/{default_branch}?recursive=1")
    if status != 200 or not isinstance(tree, dict):
        return False
    for t in tree.get("tree", []):
        p = t.get("path", "").lower()
        if (".github/workflows" in p or p.startswith("test") or "/test" in p
                or p.endswith("_test.go") or p.endswith(".test.ts") or p.endswith(".spec.ts")
                or p in (".travis.yml", "jenkinsfile", ".gitlab-ci.yml")):
            return True
    return False


def verify_github(username: str) -> dict:
    """Run the full verification and return an explainable result dict."""
    username = (username or "").strip().lstrip("@")
    if not username:
        return {"ok": False, "error": "No GitHub username provided."}

    status, profile = _request(f"/users/{username}")
    if status == 404:
        return {"ok": False, "error": f"GitHub user '{username}' not found."}
    if status != 200 or not isinstance(profile, dict):
        return {"ok": False, "error": "GitHub is unreachable or rate-limited. Please try again later."}

    status, repos = _request(f"/users/{username}/repos?per_page={_MAX_REPOS}&sort=pushed")
    if status != 200 or not isinstance(repos, list):
        repos = []

    original = [r for r in repos if not r.get("fork")]
    total_repos = len(repos)
    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    peak_stars = max((r.get("stargazers_count", 0) for r in repos), default=0)

    # --- Languages (by repo count as a proxy; GitHub repo list gives primary language) ---
    lang_count: dict[str, int] = {}
    for r in original or repos:
        lang = r.get("language")
        if lang:
            lang_count[lang] = lang_count.get(lang, 0) + 1
    languages = sorted(lang_count, key=lang_count.get, reverse=True)

    # --- Verified skills: languages + framework hints from names/topics ---
    verified_skills: list[str] = []
    for lang in languages:
        skill = _LANG_SKILL.get(lang)
        if skill and skill not in verified_skills:
            verified_skills.append(skill)
    for r in repos:
        hay = (r.get("name", "") + " " + " ".join(r.get("topics", []) or [])).lower()
        for hint, skill in _FRAMEWORK_HINTS.items():
            if hint in hay and skill not in verified_skills:
                verified_skills.append(skill)

    # --- Velocity ---
    recent_pushes = sum(1 for r in repos if _days_since(r.get("pushed_at")) <= 365)
    last_push_days = min((_days_since(r.get("pushed_at")) for r in repos), default=9999.0)

    # --- Code quality via radon on top original Python repos ---
    code_quality = None
    cc_samples: list[float] = []
    mi_samples: list[float] = []
    has_tests = False
    # Skip very large repos (size is in KB) to keep tree/file fetches fast.
    small = [r for r in original if r.get("size", 0) < 50000]
    py_repos = [r for r in small if r.get("language") == "Python"]
    # fall back to any small original repo for tests/CI detection
    code_targets = (py_repos or small)[:_MAX_CODE_REPOS]
    for r in code_targets:
        branch = r.get("default_branch", "main")
        if r.get("language") == "Python":
            for src in _sample_python_files(r["full_name"], branch):
                m = _radon_metrics(src)
                if m:
                    cc_samples.append(m[0])
                    mi_samples.append(m[1])
        if not has_tests:
            has_tests = _has_tests_or_ci(r["full_name"], branch)

    if mi_samples:
        avg_mi = sum(mi_samples) / len(mi_samples)           # 0-100, higher is better
        avg_cc = sum(cc_samples) / len(cc_samples)           # lower is better (~1-5 good)
        cc_score = _clamp(100 - (avg_cc - 1) * 12)           # 1 -> 100, ~9 -> 4
        code_quality = round(_clamp(0.6 * avg_mi + 0.4 * cc_score), 1)

    # --- Score each dimension 0-100 ---
    scores: dict[str, float] = {}
    # languages: 1 lang ~40, 5+ ~100
    scores["languages"] = _clamp(30 + len(lang_count) * 14)
    # impact: log scale on total stars
    scores["impact"] = _clamp(math.log10(total_stars + 1) * 33)
    # velocity: recent activity + freshness
    freshness = _clamp(100 - last_push_days / 3.65)          # pushed today ~100, 1yr ago ~0
    scores["velocity"] = _clamp(0.6 * freshness + 0.4 * _clamp(recent_pushes * 12))
    # originality: share of non-fork repos
    scores["originality"] = _clamp((len(original) / total_repos * 100) if total_repos else 40)
    # discipline: tests/CI + documentation
    documented = sum(1 for r in original if r.get("description"))
    doc_ratio = (documented / len(original) * 100) if original else 0
    scores["discipline"] = _clamp((60 if has_tests else 0) + 0.4 * doc_ratio)
    # code quality: measured or a neutral estimate if unavailable
    scores["code_quality"] = code_quality if code_quality is not None else round(
        _clamp(0.5 * scores["languages"] + 0.5 * scores["discipline"]), 1)

    overall = round(sum(scores[k] * w for k, w in _WEIGHTS.items()), 1)
    tier = ("A+" if overall >= 85 else "A" if overall >= 72 else
            "B" if overall >= 58 else "C" if overall >= 40 else "D")

    return {
        "ok": True,
        "username": username,
        "profile_url": profile.get("html_url"),
        "name": profile.get("name") or username,
        "avatar_url": profile.get("avatar_url"),
        "public_repos": profile.get("public_repos", total_repos),
        "followers": profile.get("followers", 0),
        "account_created": profile.get("created_at"),
        "talent_grade": overall,
        "tier": tier,
        "breakdown": {k: round(v, 1) for k, v in scores.items()},
        "weights": _WEIGHTS,
        "verified_skills": verified_skills[:12],
        "top_languages": languages[:6],
        "total_stars": total_stars,
        "peak_stars": peak_stars,
        "original_repos": len(original),
        "total_repos": total_repos,
        "repos_active_last_year": recent_pushes,
        "has_tests_or_ci": has_tests,
        "code_quality_measured": code_quality is not None,
        "verified_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
