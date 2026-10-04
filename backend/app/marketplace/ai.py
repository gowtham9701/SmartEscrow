"""
Lightweight, dependency-free AI helper for SmartEscrow.

Runs 100% locally with zero external API calls or paid services. When a local
Ollama model is available it can be used (optional); otherwise an extractive /
heuristic engine produces clean summaries, key points, skill extraction, and
match recommendations. This keeps the platform free to run on a Mac M5 Air and
reliable on free-tier hosting.
"""
from __future__ import annotations

import re
from collections import Counter

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "to", "of", "in", "on", "for", "with",
    "at", "by", "from", "as", "is", "are", "was", "were", "be", "been", "being",
    "this", "that", "these", "those", "it", "its", "we", "you", "they", "our",
    "your", "their", "will", "can", "should", "must", "have", "has", "had", "do",
    "does", "not", "who", "which", "what", "when", "where", "how", "all", "any",
    "into", "about", "over", "than", "then", "them", "us", "if", "so", "up",
    "out", "per", "via", "across", "within", "also", "more", "most", "such",
}

_KNOWN_SKILLS = {
    "python", "fastapi", "django", "flask", "typescript", "javascript", "react",
    "next.js", "nextjs", "node", "nodejs", "node.js", "nestjs", "go", "golang",
    "rust", "java", "spring", "kotlin", "swift", "sql", "postgresql", "postgres",
    "mysql", "mongodb", "redis", "graphql", "grpc", "rest", "kubernetes", "docker",
    "aws", "gcp", "azure", "terraform", "ci/cd", "devops", "sre", "machine learning",
    "ml", "ai", "llm", "nlp", "pytorch", "tensorflow", "data", "analytics", "etl",
    "spark", "airflow", "tailwind", "css", "html", "figma", "ui", "ux", "design",
    "security", "pentest", "cryptography", "solidity", "web3", "mobile", "ios",
    "android", "flutter", "react native", "qa", "testing", "selenium", "playwright",
    "microservices", "api", "architecture", "scalability", "performance",
}


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [p.strip() for p in parts if len(p.strip()) > 0]


def _word_freq(text: str) -> Counter:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9+./#-]{1,}", text.lower())
    return Counter(w for w in words if w not in _STOPWORDS and len(w) > 2)


def summarize(text: str, max_sentences: int = 3) -> str:
    """Extractive summary: rank sentences by keyword salience."""
    text = (text or "").strip()
    if not text:
        return "No description provided."
    sentences = _sentences(text)
    if len(sentences) <= max_sentences:
        return " ".join(sentences)

    freq = _word_freq(text)
    if not freq:
        return " ".join(sentences[:max_sentences])

    peak = max(freq.values())
    scored = []
    for idx, sent in enumerate(sentences):
        words = _word_freq(sent)
        score = sum(freq.get(w, 0) for w in words) / (len(words) + 1)
        # Reward earlier sentences slightly (lede bias).
        score *= 1.0 + (len(sentences) - idx) / (len(sentences) * 4)
        scored.append((score / peak, idx, sent))

    top = sorted(scored, key=lambda x: x[0], reverse=True)[:max_sentences]
    top_in_order = [s for _, _, s in sorted(top, key=lambda x: x[1])]
    return " ".join(top_in_order)


def key_points(text: str, limit: int = 4) -> list[str]:
    """Pull out the most salient short phrases / requirement lines."""
    points: list[str] = []
    for line in re.split(r"\n+|(?<=[.!?])\s+", (text or "").strip()):
        line = line.strip(" -•\t")
        if 12 <= len(line) <= 140:
            points.append(line[0].upper() + line[1:] if line else line)
        if len(points) >= limit:
            break
    if not points:
        s = _sentences(text or "")
        points = s[:limit]
    return points


def extract_skills(text: str, limit: int = 8) -> list[str]:
    low = f" {(text or '').lower()} "
    found: list[str] = []
    for skill in sorted(_KNOWN_SKILLS, key=len, reverse=True):
        if f" {skill} " in low or f" {skill}," in low or f" {skill}." in low:
            canonical = skill.title() if skill.islower() and " " in skill else skill
            if canonical not in found:
                found.append(canonical)
        if len(found) >= limit:
            break
    return found


def analyze_job(title: str, description: str, skills: list[str] | None = None) -> dict:
    """Full AI brief for a job post used on invites / detail pages."""
    body = f"{title}. {description}"
    detected = skills or extract_skills(body)
    seniority = "Senior"
    low = body.lower()
    if any(w in low for w in ("junior", "entry", "graduate", "intern")):
        seniority = "Junior"
    elif any(w in low for w in ("mid", "intermediate")):
        seniority = "Mid-level"
    elif any(w in low for w in ("lead", "principal", "staff", "architect")):
        seniority = "Lead / Principal"

    return {
        "summary": summarize(description, 3),
        "key_points": key_points(description, 4),
        "recommended_skills": detected[:8],
        "suggested_seniority": seniority,
        "reading_time_sec": max(20, len(description.split()) // 3),
        "recommendation": _job_recommendation(title, detected),
    }


def _job_recommendation(title: str, skills: list[str]) -> str:
    skill_str = ", ".join(skills[:3]) if skills else "the listed stack"
    return (
        f"Strong fit for engineers with proven {skill_str} experience. "
        f"Prioritize applicants whose portfolio shows shipped production work "
        f"and clear delivery velocity on similar '{title.lower()}' scopes."
    )


def _tokens_for_match(*texts: str) -> set[str]:
    joined = " ".join(t.lower() for t in texts if t)
    return {w for w in re.findall(r"[a-zA-Z][a-zA-Z0-9+.#-]{1,}", joined) if w not in _STOPWORDS}


def match_score(contributor_skills: list[str], job_skills: list[str], job_text: str = "") -> int:
    """0-100 compatibility score between a contributor and a job."""
    cset = {s.lower() for s in contributor_skills}
    jset = {s.lower() for s in job_skills}
    if not jset:
        jset = _tokens_for_match(job_text) & _KNOWN_SKILLS
    if not jset:
        return 50
    overlap = len(cset & jset)
    base = int(round(100 * overlap / max(len(jset), 1)))
    # Bonus for breadth of relevant skills.
    bonus = min(15, len(cset & jset) * 3)
    return max(8, min(100, base + bonus))


def _estimate_years(text: str) -> int | None:
    """Pull a years-of-experience signal from resume text."""
    matches = re.findall(r"(\d{1,2})\+?\s*(?:years|yrs)", (text or "").lower())
    nums = [int(m) for m in matches if int(m) <= 50]
    return max(nums) if nums else None


def _estimate_seniority(text: str, years: int | None) -> str:
    low = (text or "").lower()
    if any(w in low for w in ("principal", "staff", "lead", "head of", "architect")):
        return "Lead / Principal"
    if years is not None:
        if years >= 8:
            return "Senior"
        if years >= 4:
            return "Mid-level"
        if years >= 1:
            return "Junior"
    if any(w in low for w in ("senior", "sr.")):
        return "Senior"
    if any(w in low for w in ("junior", "intern", "graduate", "entry")):
        return "Junior"
    return "Mid-level"


def analyze_resume(text: str) -> dict:
    """
    Document-level keyword/skill extraction from a resume.

    Returns extracted skills, an estimated seniority + years signal, a short
    summary, and the most salient keywords — used to power job matching and
    recommendations.
    """
    text = (text or "").strip()
    if not text:
        return {
            "skills": [], "summary": "No resume content provided.",
            "seniority": "Unknown", "years_experience": None, "keywords": [],
        }
    skills = extract_skills(text, limit=20)
    years = _estimate_years(text)
    freq = _word_freq(text)
    keywords = [w for w, _ in freq.most_common(12)]
    return {
        "skills": skills,
        "summary": summarize(text, 3),
        "seniority": _estimate_seniority(text, years),
        "years_experience": years,
        "keywords": keywords,
    }


def recommend_skills(user_skills: list[str], job_skill_pool: list[str], limit: int = 6) -> list[str]:
    """
    Suggest in-demand skills the user is missing, ranked by how often they
    appear across the open-job skill pool.
    """
    have = {s.lower() for s in user_skills}
    counts = Counter(s for s in job_skill_pool if s.lower() not in have)
    return [s for s, _ in counts.most_common(limit)]

