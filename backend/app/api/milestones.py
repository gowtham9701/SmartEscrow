"""
Milestone escrow lifecycle endpoints (deposit, submit, dispute).
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.entities import (
    EscrowTransaction, EscrowTxStatus, EscrowTxType, Milestone, MilestoneStatus, VoteDecision,
)
from app.services.arbitration_service import ArbitrationService
from app.services.escrow_service import EscrowService

router = APIRouter(prefix="/milestones", tags=["milestones"])


class FundMilestoneRequest(BaseModel):
    payment_method_id: str


@router.post("/{milestone_id}/fund")
async def fund_milestone(milestone_id: uuid.UUID, req: FundMilestoneRequest, db: AsyncSession = Depends(get_db)):
    milestone = await db.get(Milestone, milestone_id)
    if milestone is None:
        raise HTTPException(status_code=404, detail="Milestone not found")
    if milestone.status != MilestoneStatus.draft:
        raise HTTPException(status_code=409, detail="Milestone already funded or in progress")

    intent = EscrowService.deposit_to_vault(
        amount_usd_cents=milestone.amount_usd_cents,
        client_payment_method_id=req.payment_method_id,
        idempotency_key=f"deposit-{milestone.id}",
    )
    tx = EscrowTransaction(
        milestone_id=milestone.id,
        tx_type=EscrowTxType.deposit,
        status=EscrowTxStatus.succeeded if intent.status == "requires_capture" else EscrowTxStatus.processing,
        amount_usd_cents=milestone.amount_usd_cents,
        stripe_payment_intent_id=intent.id,
        idempotency_key=f"deposit-{milestone.id}",
    )
    milestone.status = MilestoneStatus.funded
    db.add(tx)
    await db.commit()
    return {"status": "funded", "payment_intent_id": intent.id}


class DisputeRequest(BaseModel):
    raised_by: uuid.UUID
    reason: str


@router.post("/{milestone_id}/dispute")
async def dispute_milestone(milestone_id: uuid.UUID, req: DisputeRequest, db: AsyncSession = Depends(get_db)):
    milestone = await db.get(Milestone, milestone_id)
    if milestone is None:
        raise HTTPException(status_code=404, detail="Milestone not found")

    dispute = await ArbitrationService.open_dispute(
        db, milestone_id=milestone.id, raised_by=req.raised_by, reason=req.reason,
        excluded_user_ids={req.raised_by},
    )
    milestone.status = MilestoneStatus.disputed
    await db.commit()
    return {"dispute_id": str(dispute.id), "ticket_ref": dispute.anonymized_ticket_ref, "status": dispute.status}


class VoteRequest(BaseModel):
    juror_id: uuid.UUID
    decision: VoteDecision
    split_client_pct: float | None = None
    rationale: str = ""


@router.post("/disputes/{dispute_id}/vote")
async def cast_vote(dispute_id: uuid.UUID, req: VoteRequest, db: AsyncSession = Depends(get_db)):
    await ArbitrationService.cast_vote(
        db, dispute_id=dispute_id, juror_id=req.juror_id, decision=req.decision,
        split_client_pct=req.split_client_pct, rationale=req.rationale,
    )
    resolution = await ArbitrationService.tally_and_resolve(db, dispute_id)
    return {"status": "vote_recorded", "resolution": resolution}
