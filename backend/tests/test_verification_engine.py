"""
Unit tests for the AI verification engine's deterministic components
(static metrics + grade composition) — no network calls required.
"""
from app.ai_engine.verification_engine import CodeVerificationEngine


def test_compute_static_metrics_simple_function():
    source = """
def add(a, b):
    return a + b
"""
    metrics = CodeVerificationEngine.compute_static_metrics(source)
    assert metrics["cyclomatic_complexity"] >= 1
    assert 0 <= metrics["maintainability_index"] <= 100


def test_compute_overall_grade_rewards_clean_code():
    high_quality = CodeVerificationEngine.compute_overall_grade(
        maintainability_index=90, architecture_score=90,
        delivery_velocity_score=85, cyclomatic_complexity=3, test_coverage_pct=80,
    )
    low_quality = CodeVerificationEngine.compute_overall_grade(
        maintainability_index=40, architecture_score=30,
        delivery_velocity_score=20, cyclomatic_complexity=25, test_coverage_pct=5,
    )
    assert high_quality > low_quality
    assert 0 <= high_quality <= 100
    assert 0 <= low_quality <= 100


def test_compute_overall_grade_penalizes_high_complexity():
    base = CodeVerificationEngine.compute_overall_grade(
        maintainability_index=80, architecture_score=80,
        delivery_velocity_score=80, cyclomatic_complexity=5, test_coverage_pct=80,
    )
    complex_ = CodeVerificationEngine.compute_overall_grade(
        maintainability_index=80, architecture_score=80,
        delivery_velocity_score=80, cyclomatic_complexity=20, test_coverage_pct=80,
    )
    assert complex_ < base
