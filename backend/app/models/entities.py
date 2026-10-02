"""
SQLAlchemy ORM models mirroring database/schema.sql
"""
import uuid
import enum
from datetime import datetime

from sqlalchemy import (
    String, Boolean, Integer, BigInteger, Numeric, ForeignKey, DateTime,
    Enum, Text, JSON, UniqueConstraint, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    client = "client"
    freelancer = "freelancer"
    arbiter = "arbiter"
    admin = "admin"


class KYCStatus(str, enum.Enum):
    pending = "pending"
    verified = "verified"
    rejected = "rejected"


class MilestoneStatus(str, enum.Enum):
    draft = "draft"
    funded = "funded"
    in_progress = "in_progress"
    submitted = "submitted"
    approved = "approved"
    disputed = "disputed"
    released = "released"
    refunded = "refunded"
    cancelled = "cancelled"


class EscrowTxType(str, enum.Enum):
    deposit = "deposit"
    release = "release"
    refund = "refund"
    split = "split"
    stake_lock = "stake_lock"
    stake_slash = "stake_slash"


class EscrowTxStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    succeeded = "succeeded"
    failed = "failed"
    reversed = "reversed"


class DisputeStatus(str, enum.Enum):
    open = "open"
    jury_assigned = "jury_assigned"
    voting = "voting"
    resolved = "resolved"
    closed = "closed"


class VoteDecision(str, enum.Enum):
    favor_client = "favor_client"
    favor_freelancer = "favor_freelancer"
    split = "split"


def _uuid_col():
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = _uuid_col()
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), default=UserRole.freelancer)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    kyc_status: Mapped[KYCStatus] = mapped_column(Enum(KYCStatus, name="kyc_status"), default=KYCStatus.pending)
    stripe_account_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    plaid_item_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    github_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    github_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    reputation_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CodeAssessment(Base):
    __tablename__ = "code_assessments"

    id: Mapped[uuid.UUID] = _uuid_col()
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    repo_full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    pull_request_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    commit_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    llm_model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    cyclomatic_complexity: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    maintainability_index: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    test_coverage_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    code_smell_count: Mapped[int] = mapped_column(Integer, default=0)
    delivery_velocity_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    architecture_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    overall_talent_grade: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    raw_llm_output: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = _uuid_col()
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    freelancer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    github_repo_full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_branch: Mapped[str] = mapped_column(String(100), default="main")
    total_budget_usd_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    milestones: Mapped[list["Milestone"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class Milestone(Base):
    __tablename__ = "milestones"
    __table_args__ = (UniqueConstraint("project_id", "sequence_number"),)

    id: Mapped[uuid.UUID] = _uuid_col()
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount_usd_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[MilestoneStatus] = mapped_column(Enum(MilestoneStatus, name="milestone_status"), default=MilestoneStatus.draft)
    required_pr_merge: Mapped[bool] = mapped_column(Boolean, default=True)
    github_pr_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    github_merge_commit_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    funded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="milestones")
    escrow_transactions: Mapped[list["EscrowTransaction"]] = relationship(back_populates="milestone", cascade="all, delete-orphan")


class EscrowTransaction(Base):
    __tablename__ = "escrow_transactions"

    id: Mapped[uuid.UUID] = _uuid_col()
    milestone_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("milestones.id", ondelete="CASCADE"))
    tx_type: Mapped[EscrowTxType] = mapped_column(Enum(EscrowTxType, name="escrow_tx_type"), nullable=False)
    status: Mapped[EscrowTxStatus] = mapped_column(Enum(EscrowTxStatus, name="escrow_tx_status"), default=EscrowTxStatus.pending)
    amount_usd_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_transfer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    milestone: Mapped["Milestone"] = relationship(back_populates="escrow_transactions")


class Dispute(Base):
    __tablename__ = "disputes"

    id: Mapped[uuid.UUID] = _uuid_col()
    milestone_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("milestones.id", ondelete="CASCADE"))
    raised_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[DisputeStatus] = mapped_column(Enum(DisputeStatus, name="dispute_status"), default=DisputeStatus.open)
    anonymized_ticket_ref: Mapped[str] = mapped_column(String(64), unique=True)
    resolution_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_award_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ArbitrationJuror(Base):
    __tablename__ = "arbitration_jurors"
    __table_args__ = (UniqueConstraint("dispute_id", "juror_id"),)

    id: Mapped[uuid.UUID] = _uuid_col()
    dispute_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("disputes.id", ondelete="CASCADE"))
    juror_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    recused: Mapped[bool] = mapped_column(Boolean, default=False)


class ArbitrationVote(Base):
    __tablename__ = "arbitration_votes"
    __table_args__ = (UniqueConstraint("dispute_id", "juror_id"),)

    id: Mapped[uuid.UUID] = _uuid_col()
    dispute_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("disputes.id", ondelete="CASCADE"))
    juror_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    decision: Mapped[VoteDecision] = mapped_column(Enum(VoteDecision, name="vote_decision"), nullable=False)
    split_client_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    incentive_usd_cents: Mapped[int] = mapped_column(BigInteger, default=500)
    voted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
