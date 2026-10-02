"""
AI Technical Verification Engine
---------------------------------
Bypasses resumes entirely. Pulls real code from GitHub pull requests,
runs objective static-analysis metrics (cyclomatic complexity, maintainability
index via `radon`), then asks a locally-hosted Ollama LLM (DeepSeek-Coder 6.7B
or Llama 3.1 8B) to reason over architecture/clean-coding quality and produce
a structured, objective talent grade (0-100).

100% local inference on Apple Silicon (M5) — zero cloud inference cost,
zero per-token billing.
"""
import json
import statistics
from dataclasses import dataclass, field

import httpx
from github import Github
from radon.complexity import cc_visit
from radon.metrics import mi_visit

from app.core.config import settings

ASSESSMENT_PROMPT_TEMPLATE = """You are a senior staff software engineer performing an objective,
unbiased technical code review for a B2B hiring platform. You will NOT see any resume, name,
gender, age or demographic signal — only the code diff below.

Evaluate the following pull request diff from repository `{repo}` (PR #{pr_number}).

Static metrics already computed:
- Average Cyclomatic Complexity: {cyclomatic_complexity}
- Maintainability Index (0-100, higher is better): {maintainability_index}
- Approx. test coverage signal (lines touching test files / total): {test_coverage_pct}%

Diff (truncated to relevant hunks):
---
{diff}
---

Respond ONLY with strict JSON matching this schema:
{{
  "architecture_score": <0-100 float, clean separation of concerns / SOLID adherence>,
  "code_smell_count": <int, count of anti-patterns found>,
  "delivery_velocity_score": <0-100 float, inferred engineering efficiency/cadence>,
  "summary": "<2-3 sentence objective rationale>"
}}
"""


@dataclass
class AssessmentResult:
    repo_full_name: str
    pull_request_number: int
    commit_sha: str
    llm_model_used: str
    cyclomatic_complexity: float
    maintainability_index: float
    test_coverage_pct: float
    code_smell_count: int
    delivery_velocity_score: float
    architecture_score: float
    overall_talent_grade: float
    raw_llm_output: dict = field(default_factory=dict)


class CodeVerificationEngine:
    """Orchestrates GitHub retrieval -> static analysis -> local LLM reasoning."""

    def __init__(self, github_token: str | None = None, ollama_host: str | None = None,
                 model: str | None = None):
        self.github = Github(github_token or settings.GITHUB_APP_TOKEN or None)
        self.ollama_host = ollama_host or settings.OLLAMA_HOST
        self.model = model or settings.OLLAMA_MODEL

    # -- Step 1: Pull real code from GitHub -----------------------------------
    def fetch_pull_request_diff(self, repo_full_name: str, pr_number: int) -> tuple[str, str]:
        repo = self.github.get_repo(repo_full_name)
        pr = repo.get_pull(pr_number)
        files = pr.get_files()
        diff_chunks = []
        test_touching = 0
        total_files = 0
        for f in files:
            total_files += 1
            if "test" in f.filename.lower() or "spec" in f.filename.lower():
                test_touching += 1
            if f.patch:
                diff_chunks.append(f"--- {f.filename} ---\n{f.patch}")
        diff_text = "\n".join(diff_chunks)[:12000]  # keep prompt bounded for local LLM context window
        coverage_signal = round((test_touching / total_files) * 100, 2) if total_files else 0.0
        return diff_text, str(coverage_signal), pr.merge_commit_sha or pr.head.sha

    # -- Step 2: Objective static metrics (radon) -----------------------------
    @staticmethod
    def compute_static_metrics(source_code: str) -> dict:
        try:
            blocks = cc_visit(source_code)
            complexities = [b.complexity for b in blocks] or [1]
            avg_complexity = round(statistics.mean(complexities), 2)
        except Exception:
            avg_complexity = 1.0
        try:
            maintainability = round(mi_visit(source_code, multi=True), 2)
        except Exception:
            maintainability = 70.0
        return {"cyclomatic_complexity": avg_complexity, "maintainability_index": maintainability}

    # -- Step 3: Local LLM reasoning via Ollama -------------------------------
    def query_local_llm(self, prompt: str) -> dict:
        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(
                    f"{self.ollama_host}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False, "format": "json"},
                )
                resp.raise_for_status()
                raw = resp.json().get("response", "{}")
                return json.loads(raw)
        except Exception as exc:  # pragma: no cover - degrade gracefully if Ollama unavailable
            return {
                "architecture_score": 60.0,
                "code_smell_count": 0,
                "delivery_velocity_score": 60.0,
                "summary": f"LLM unavailable, fallback heuristic score used ({exc})",
            }

    # -- Step 4: Composite objective talent grade -----------------------------
    @staticmethod
    def compute_overall_grade(maintainability_index: float, architecture_score: float,
                               delivery_velocity_score: float, cyclomatic_complexity: float,
                               test_coverage_pct: float) -> float:
        complexity_penalty = max(0.0, min(20.0, cyclomatic_complexity - 5) * 2)
        weighted = (
            maintainability_index * 0.30
            + architecture_score * 0.30
            + delivery_velocity_score * 0.20
            + test_coverage_pct * 0.20
        )
        return round(max(0.0, min(100.0, weighted - complexity_penalty)), 2)

    def assess_pull_request(self, repo_full_name: str, pr_number: int) -> AssessmentResult:
        diff_text, test_coverage_pct, commit_sha = self.fetch_pull_request_diff(repo_full_name, pr_number)
        static_metrics = self.compute_static_metrics(diff_text)

        prompt = ASSESSMENT_PROMPT_TEMPLATE.format(
            repo=repo_full_name,
            pr_number=pr_number,
            cyclomatic_complexity=static_metrics["cyclomatic_complexity"],
            maintainability_index=static_metrics["maintainability_index"],
            test_coverage_pct=test_coverage_pct,
            diff=diff_text or "(no textual diff available)",
        )
        llm_output = self.query_local_llm(prompt)

        overall_grade = self.compute_overall_grade(
            maintainability_index=static_metrics["maintainability_index"],
            architecture_score=float(llm_output.get("architecture_score", 60.0)),
            delivery_velocity_score=float(llm_output.get("delivery_velocity_score", 60.0)),
            cyclomatic_complexity=static_metrics["cyclomatic_complexity"],
            test_coverage_pct=float(test_coverage_pct),
        )

        return AssessmentResult(
            repo_full_name=repo_full_name,
            pull_request_number=pr_number,
            commit_sha=commit_sha,
            llm_model_used=self.model,
            cyclomatic_complexity=static_metrics["cyclomatic_complexity"],
            maintainability_index=static_metrics["maintainability_index"],
            test_coverage_pct=float(test_coverage_pct),
            code_smell_count=int(llm_output.get("code_smell_count", 0)),
            delivery_velocity_score=float(llm_output.get("delivery_velocity_score", 60.0)),
            architecture_score=float(llm_output.get("architecture_score", 60.0)),
            overall_talent_grade=overall_grade,
            raw_llm_output=llm_output,
        )
