"""
Code Assessment API: triggers the local AI Technical Verification Engine.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_engine.verification_engine import CodeVerificationEngine
from app.core.database import get_db
from app.models.entities import CodeAssessment

router = APIRouter(prefix="/assessments", tags=["ai-verification"])


class AssessmentRequest(BaseModel):
    user_id: str
    repo_full_name: str
    pull_request_number: int


class AssessmentResponse(BaseModel):
    overall_talent_grade: float
    cyclomatic_complexity: float
    maintainability_index: float
    test_coverage_pct: float
    architecture_score: float
    delivery_velocity_score: float
    code_smell_count: int
    summary: str | None = None


@router.post("", response_model=AssessmentResponse)
async def run_assessment(req: AssessmentRequest, db: AsyncSession = Depends(get_db)):
    engine = CodeVerificationEngine()
    try:
        result = engine.assess_pull_request(req.repo_full_name, req.pull_request_number)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Assessment failed: {exc}") from exc

    record = CodeAssessment(
        user_id=req.user_id,
        repo_full_name=result.repo_full_name,
        pull_request_number=result.pull_request_number,
        commit_sha=result.commit_sha,
        llm_model_used=result.llm_model_used,
        cyclomatic_complexity=result.cyclomatic_complexity,
        maintainability_index=result.maintainability_index,
        test_coverage_pct=result.test_coverage_pct,
        code_smell_count=result.code_smell_count,
        delivery_velocity_score=result.delivery_velocity_score,
        architecture_score=result.architecture_score,
        overall_talent_grade=result.overall_talent_grade,
        raw_llm_output=result.raw_llm_output,
    )
    db.add(record)
    await db.commit()

    return AssessmentResponse(
        overall_talent_grade=result.overall_talent_grade,
        cyclomatic_complexity=result.cyclomatic_complexity,
        maintainability_index=result.maintainability_index,
        test_coverage_pct=result.test_coverage_pct,
        architecture_score=result.architecture_score,
        delivery_velocity_score=result.delivery_velocity_score,
        code_smell_count=result.code_smell_count,
        summary=result.raw_llm_output.get("summary") if result.raw_llm_output else None,
    )
