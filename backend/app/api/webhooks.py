"""
GitHub Webhook Listener
------------------------
Intercepts a successful, approved Merge Event on the target repository branch
and programmatically triggers Stripe escrow release — zero human intervention.
"""
import hashlib
import hmac

from fastapi import APIRouter, Header, HTTPException, Request, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.entities import Milestone, MilestoneStatus, Project, EscrowTransaction, EscrowTxType, EscrowTxStatus
from app.services.escrow_service import EscrowService

router = APIRouter(prefix="/webhooks/github", tags=["github-webhooks"])


def verify_signature(payload_body: bytes, signature_header: str | None) -> None:
    if not signature_header:
        raise HTTPException(status_code=401, detail="Missing X-Hub-Signature-256 header")
    expected = "sha256=" + hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode(), payload_body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, signature_header):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")


@router.post("")
async def handle_github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    body = await request.body()
    verify_signature(body, x_hub_signature_256)
    payload = await request.json()

    if x_github_event != "pull_request":
        return {"status": "ignored", "reason": f"unsupported event {x_github_event}"}

    action = payload.get("action")
    pr = payload.get("pull_request", {})
    merged = pr.get("merged", False)
    target_branch = pr.get("base", {}).get("ref")
    repo_full_name = payload.get("repository", {}).get("full_name")
    pr_number = pr.get("number")
    merge_commit_sha = pr.get("merge_commit_sha")

    # c. GitHub Webhook intercepts a successful, APPROVED Merge Event on target branch
    if action != "closed" or not merged:
        return {"status": "ignored", "reason": "not a merge event"}

    stmt = select(Milestone).join(Project).where(
        Project.github_repo_full_name == repo_full_name,
        Project.target_branch == target_branch,
        Milestone.github_pr_number == pr_number,
        Milestone.status.in_([MilestoneStatus.in_progress, MilestoneStatus.submitted]),
    )
    milestone = (await db.execute(stmt)).scalar_one_or_none()
    if milestone is None:
        return {"status": "ignored", "reason": "no matching funded milestone for this PR"}

    # d. -> e. Securely trigger backend listener -> release escrowed USD
    deposit_tx_stmt = select(EscrowTransaction).where(
        EscrowTransaction.milestone_id == milestone.id,
        EscrowTransaction.tx_type == EscrowTxType.deposit,
        EscrowTransaction.status == EscrowTxStatus.succeeded,
    )
    deposit_tx = (await db.execute(deposit_tx_stmt)).scalar_one_or_none()
    if deposit_tx is None:
        raise HTTPException(status_code=409, detail="No funded deposit found for milestone")

    project = await db.get(Project, milestone.project_id)
    from app.models.entities import User
    freelancer = await db.get(User, project.freelancer_id)

    try:
        transfer = EscrowService.release_to_freelancer(
            payment_intent_id=deposit_tx.stripe_payment_intent_id,
            freelancer_stripe_account_id=freelancer.stripe_account_id,
            amount_usd_cents=milestone.amount_usd_cents,
            idempotency_key=f"release-{milestone.id}",
        )
        release_tx = EscrowTransaction(
            milestone_id=milestone.id,
            tx_type=EscrowTxType.release,
            status=EscrowTxStatus.succeeded,
            amount_usd_cents=milestone.amount_usd_cents,
            stripe_transfer_id=transfer.id,
            idempotency_key=f"release-{milestone.id}",
        )
        milestone.status = MilestoneStatus.released
        milestone.github_merge_commit_sha = merge_commit_sha
        db.add(release_tx)
        await db.commit()
        return {"status": "released", "milestone_id": str(milestone.id), "transfer_id": transfer.id}
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=502, detail=f"Stripe release failed: {exc}") from exc
