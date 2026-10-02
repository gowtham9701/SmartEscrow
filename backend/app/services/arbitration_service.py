"""
Peer-Led Dispute Resolution: blind, randomized, micro-incentivized jury matrix.
"""
import random
import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import (
    ArbitrationJuror, ArbitrationVote, Dispute, DisputeStatus, User, UserRole, VoteDecision,
)

JURY_SIZE = 3
MIN_REPUTATION_FOR_JUROR = 75.0


class ArbitrationService:
    """Randomized double-blind jury selection + majority-vote resolution."""

    @staticmethod
    def generate_anonymized_ticket_ref() -> str:
        return secrets.token_hex(16)

    @staticmethod
    async def select_eligible_jurors(db: AsyncSession, exclude_user_ids: set, pool_size: int = JURY_SIZE) -> list[User]:
        stmt = select(User).where(
            User.role == UserRole.arbiter,
            User.reputation_score >= MIN_REPUTATION_FOR_JUROR,
            User.id.notin_(exclude_user_ids) if exclude_user_ids else True,
        )
        result = await db.execute(stmt)
        candidates = list(result.scalars().all())
        random.shuffle(candidates)  # randomized assignment — no human admin selection bias
        return candidates[:pool_size]

    @classmethod
    async def open_dispute(cls, db: AsyncSession, milestone_id, raised_by, reason: str,
                            excluded_user_ids: set) -> Dispute:
        dispute = Dispute(
            milestone_id=milestone_id,
            raised_by=raised_by,
            reason=reason,
            status=DisputeStatus.open,
            anonymized_ticket_ref=cls.generate_anonymized_ticket_ref(),
        )
        db.add(dispute)
        await db.flush()

        jurors = await cls.select_eligible_jurors(db, excluded_user_ids)
        for juror in jurors:
            db.add(ArbitrationJuror(dispute_id=dispute.id, juror_id=juror.id))
        dispute.status = DisputeStatus.jury_assigned if jurors else DisputeStatus.open
        await db.commit()
        await db.refresh(dispute)
        return dispute

    @staticmethod
    async def cast_vote(db: AsyncSession, dispute_id, juror_id, decision: VoteDecision,
                         split_client_pct: float | None, rationale: str) -> ArbitrationVote:
        vote = ArbitrationVote(
            dispute_id=dispute_id,
            juror_id=juror_id,
            decision=decision,
            split_client_pct=split_client_pct,
            rationale=rationale,
        )
        db.add(vote)
        await db.commit()
        await db.refresh(vote)
        return vote

    @classmethod
    async def tally_and_resolve(cls, db: AsyncSession, dispute_id) -> dict | None:
        """Majority vote resolution. Returns resolution dict once quorum (3 votes) reached."""
        stmt = select(ArbitrationVote).where(ArbitrationVote.dispute_id == dispute_id)
        votes = list((await db.execute(stmt)).scalars().all())
        if len(votes) < JURY_SIZE:
            return None  # quorum not yet reached

        decisions = [v.decision for v in votes]
        winner = max(set(decisions), key=decisions.count)

        client_award_pct = 100.0 if winner == VoteDecision.favor_client else (
            0.0 if winner == VoteDecision.favor_freelancer else
            round(sum(v.split_client_pct or 50.0 for v in votes if v.decision == VoteDecision.split)
                  / max(1, decisions.count(VoteDecision.split)), 2)
        )

        dispute = await db.get(Dispute, dispute_id)
        dispute.status = DisputeStatus.resolved
        dispute.client_award_pct = client_award_pct
        dispute.resolution_summary = f"Majority vote: {winner.value} ({decisions.count(winner)}/{len(votes)})"
        await db.commit()

        return {
            "winner": winner,
            "client_award_pct": client_award_pct,
            "vote_breakdown": {d.value: decisions.count(d) for d in set(decisions)},
        }
