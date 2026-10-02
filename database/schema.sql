-- =====================================================================
-- SmartEscrow :: PostgreSQL Core Ledger Schema
-- Algorithmic B2B Infrastructure for Tech Talent
-- Strict USD Fiat-native. No crypto/tokens/stablecoins.
-- Target: PostgreSQL 15+, local Docker on Apple Silicon (Mac M5 Air)
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ---------------------------------------------------------------------
-- ENUM TYPES
-- ---------------------------------------------------------------------
CREATE TYPE user_role AS ENUM ('client', 'freelancer', 'arbiter', 'admin');
CREATE TYPE kyc_status AS ENUM ('pending', 'verified', 'rejected');
CREATE TYPE milestone_status AS ENUM (
    'draft', 'funded', 'in_progress', 'submitted',
    'approved', 'disputed', 'released', 'refunded', 'cancelled'
);
CREATE TYPE escrow_tx_type AS ENUM ('deposit', 'release', 'refund', 'split', 'stake_lock', 'stake_slash');
CREATE TYPE escrow_tx_status AS ENUM ('pending', 'processing', 'succeeded', 'failed', 'reversed');
CREATE TYPE dispute_status AS ENUM ('open', 'jury_assigned', 'voting', 'resolved', 'closed');
CREATE TYPE vote_decision AS ENUM ('favor_client', 'favor_freelancer', 'split');
CREATE TYPE tax_form_type AS ENUM ('W8-BEN', 'W9');

-- ---------------------------------------------------------------------
-- USERS & IDENTITY
-- ---------------------------------------------------------------------
CREATE TABLE users (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email               VARCHAR(255) UNIQUE NOT NULL,
    hashed_password     TEXT NOT NULL,
    full_name           VARCHAR(255) NOT NULL,
    role                user_role NOT NULL DEFAULT 'freelancer',
    country_code        CHAR(2) NOT NULL,
    kyc_status          kyc_status NOT NULL DEFAULT 'pending',
    stripe_account_id   VARCHAR(255),           -- Stripe Connect account (payout rail)
    plaid_item_id       VARCHAR(255),            -- Plaid linked bank item (for clients funding escrow)
    github_username     VARCHAR(255),
    github_access_token TEXT,                    -- encrypted at application layer (pgcrypto / KMS)
    reputation_score     NUMERIC(5,2) DEFAULT 0,  -- 0-100 composite trust score
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_github_username ON users(github_username);

-- Tax compliance documents (W-8BEN for foreign freelancers, W-9 for domestic entities)
CREATE TABLE tax_documents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    form_type       tax_form_type NOT NULL,
    document_url    TEXT NOT NULL,       -- pointer to encrypted object storage (local MinIO/filesystem)
    tax_id_last4    VARCHAR(4),          -- last 4 digits of SSN/EIN/TIN only, never full PII in DB
    verified        BOOLEAN NOT NULL DEFAULT FALSE,
    submitted_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at      TIMESTAMPTZ
);

-- Fiat-Staking Integrity Model: refundable USD deposit required to unlock bidding/negotiation
CREATE TABLE integrity_stakes (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount_usd_cents    BIGINT NOT NULL CHECK (amount_usd_cents >= 0),
    stripe_payment_intent_id VARCHAR(255),
    locked              BOOLEAN NOT NULL DEFAULT TRUE,
    slashed_amount_cents BIGINT NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    released_at         TIMESTAMPTZ
);

-- ---------------------------------------------------------------------
-- AI TECHNICAL VERIFICATION ENGINE
-- ---------------------------------------------------------------------
CREATE TABLE code_assessments (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id                 UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    repo_full_name          VARCHAR(255) NOT NULL,      -- e.g. "org/repo"
    pull_request_number     INTEGER,
    commit_sha              VARCHAR(64),
    llm_model_used          VARCHAR(100) NOT NULL,       -- e.g. 'deepseek-coder:6.7b', 'llama3.1:8b'
    cyclomatic_complexity   NUMERIC(8,2),
    maintainability_index   NUMERIC(6,2),
    test_coverage_pct       NUMERIC(5,2),
    code_smell_count        INTEGER DEFAULT 0,
    delivery_velocity_score NUMERIC(5,2),                -- commits/PR cadence normalized score
    architecture_score      NUMERIC(5,2),
    overall_talent_grade    NUMERIC(5,2) NOT NULL,        -- 0-100 composite objective grade
    raw_llm_output          JSONB,                        -- full structured LLM evaluation payload
    assessed_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_code_assessments_user ON code_assessments(user_id);
CREATE INDEX idx_code_assessments_grade ON code_assessments(overall_talent_grade DESC);

-- ---------------------------------------------------------------------
-- PROJECTS & MILESTONES
-- ---------------------------------------------------------------------
CREATE TABLE projects (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id       UUID NOT NULL REFERENCES users(id),
    freelancer_id   UUID REFERENCES users(id),
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    github_repo_full_name VARCHAR(255) NOT NULL,
    target_branch   VARCHAR(100) NOT NULL DEFAULT 'main',
    total_budget_usd_cents BIGINT NOT NULL CHECK (total_budget_usd_cents >= 0),
    status          VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE milestones (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id          UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    sequence_number      INTEGER NOT NULL,
    title                VARCHAR(255) NOT NULL,
    description          TEXT,
    amount_usd_cents     BIGINT NOT NULL CHECK (amount_usd_cents >= 0),
    status               milestone_status NOT NULL DEFAULT 'draft',
    required_pr_merge    BOOLEAN NOT NULL DEFAULT TRUE,
    github_pr_number     INTEGER,
    github_merge_commit_sha VARCHAR(64),
    due_date             DATE,
    funded_at            TIMESTAMPTZ,
    submitted_at         TIMESTAMPTZ,
    released_at          TIMESTAMPTZ,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (project_id, sequence_number)
);

CREATE INDEX idx_milestones_project ON milestones(project_id);
CREATE INDEX idx_milestones_status ON milestones(status);

-- ---------------------------------------------------------------------
-- AUTOMATED USD ESCROW LEDGER (Stripe Connect + Plaid Sandbox)
-- ---------------------------------------------------------------------
CREATE TABLE escrow_transactions (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    milestone_id            UUID NOT NULL REFERENCES milestones(id) ON DELETE CASCADE,
    tx_type                 escrow_tx_type NOT NULL,
    status                  escrow_tx_status NOT NULL DEFAULT 'pending',
    amount_usd_cents        BIGINT NOT NULL CHECK (amount_usd_cents >= 0),
    stripe_payment_intent_id VARCHAR(255),
    stripe_transfer_id       VARCHAR(255),
    stripe_charge_id         VARCHAR(255),
    plaid_transaction_id     VARCHAR(255),
    initiated_by             UUID REFERENCES users(id),
    idempotency_key          VARCHAR(255) UNIQUE,
    failure_reason            TEXT,
    created_at                TIMESTAMPTZ NOT NULL DEFAULT now(),
    settled_at                 TIMESTAMPTZ
);

CREATE INDEX idx_escrow_tx_milestone ON escrow_transactions(milestone_id);
CREATE INDEX idx_escrow_tx_status ON escrow_transactions(status);

-- Immutable webhook event log (GitHub + Stripe) driving the automated flow
CREATE TABLE webhook_events (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source          VARCHAR(50) NOT NULL,        -- 'github' | 'stripe' | 'plaid'
    event_type      VARCHAR(100) NOT NULL,
    external_event_id VARCHAR(255),
    payload         JSONB NOT NULL,
    processed       BOOLEAN NOT NULL DEFAULT FALSE,
    processing_error TEXT,
    received_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed_at    TIMESTAMPTZ
);

CREATE INDEX idx_webhook_events_source_type ON webhook_events(source, event_type);
CREATE UNIQUE INDEX idx_webhook_events_external_id ON webhook_events(source, external_event_id)
    WHERE external_event_id IS NOT NULL;

-- ---------------------------------------------------------------------
-- PEER-LED DISPUTE RESOLUTION (Blind Jury Matrix)
-- ---------------------------------------------------------------------
CREATE TABLE disputes (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    milestone_id    UUID NOT NULL REFERENCES milestones(id) ON DELETE CASCADE,
    raised_by       UUID NOT NULL REFERENCES users(id),
    reason          TEXT NOT NULL,
    status          dispute_status NOT NULL DEFAULT 'open',
    anonymized_ticket_ref VARCHAR(64) NOT NULL UNIQUE DEFAULT encode(gen_random_bytes(16), 'hex'),
    resolution_summary TEXT,
    client_award_pct   NUMERIC(5,2),   -- resolved split percentage to client (0-100)
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at      TIMESTAMPTZ
);

CREATE INDEX idx_disputes_milestone ON disputes(milestone_id);
CREATE INDEX idx_disputes_status ON disputes(status);

-- Randomized, double-blind jury assignment (3 senior engineers per dispute)
CREATE TABLE arbitration_jurors (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dispute_id       UUID NOT NULL REFERENCES disputes(id) ON DELETE CASCADE,
    juror_id          UUID NOT NULL REFERENCES users(id),
    assigned_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    recused           BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (dispute_id, juror_id)
);

CREATE TABLE arbitration_votes (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dispute_id       UUID NOT NULL REFERENCES disputes(id) ON DELETE CASCADE,
    juror_id          UUID NOT NULL REFERENCES users(id),
    decision          vote_decision NOT NULL,
    split_client_pct  NUMERIC(5,2),         -- only populated when decision = 'split'
    rationale          TEXT,
    incentive_usd_cents BIGINT NOT NULL DEFAULT 500,  -- micro-incentive paid to juror (e.g. $5.00)
    voted_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (dispute_id, juror_id)
);

CREATE INDEX idx_arbitration_votes_dispute ON arbitration_votes(dispute_id);

-- ---------------------------------------------------------------------
-- AUDIT TRAIL (institutional-grade immutability for compliance/AML review)
-- ---------------------------------------------------------------------
CREATE TABLE audit_log (
    id              BIGSERIAL PRIMARY KEY,
    actor_user_id    UUID REFERENCES users(id),
    entity_type      VARCHAR(100) NOT NULL,
    entity_id         UUID NOT NULL,
    action            VARCHAR(100) NOT NULL,
    metadata          JSONB,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_log_entity ON audit_log(entity_type, entity_id);

-- ---------------------------------------------------------------------
-- TRIGGERS: updated_at maintenance
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_milestones_updated_at BEFORE UPDATE ON milestones
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
