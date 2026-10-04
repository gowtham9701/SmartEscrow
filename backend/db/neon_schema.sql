-- =====================================================================
-- SmartEscrow — Neon (PostgreSQL) schema: exactly TWO tables
-- =====================================================================
-- This mirrors the schema the backend creates automatically in
-- app/marketplace/db.py (the single source of truth). You normally do NOT
-- need to run this by hand — the app runs CREATE TABLE IF NOT EXISTS on
-- startup. It is provided so you can inspect/provision Neon manually.
--
-- Two tables by design:
--   1. users       -> account + profile data (freelancers AND employers).
--   2. operations  -> every operational record (job postings, applications,
--                     engagements, timesheets, wallets, wallet transactions,
--                     payment methods, payments, escrow holds, activity),
--                     discriminated by `type` with a JSONB `data` document.
--
-- Run it with:
--   * Neon Console -> SQL Editor -> paste -> Run, OR
--   * psql "$DATABASE_URL" -f db/neon_schema.sql, OR
--   * python scripts/provision_neon.py   (uses DATABASE_URL)
-- =====================================================================

CREATE TABLE IF NOT EXISTS users (
    id              TEXT PRIMARY KEY,
    email           TEXT UNIQUE NOT NULL,
    username        TEXT UNIQUE,
    phone           TEXT,
    password_hash   TEXT NOT NULL,
    full_name       TEXT NOT NULL,
    role            TEXT NOT NULL DEFAULT 'contributor',   -- contributor | client
    active_mode     TEXT NOT NULL DEFAULT 'freelancer',    -- freelancer | employer
    is_freelancer   SMALLINT NOT NULL DEFAULT 1,
    is_employer     SMALLINT NOT NULL DEFAULT 0,
    firm_verified   SMALLINT NOT NULL DEFAULT 0,
    email_verified  SMALLINT NOT NULL DEFAULT 0,
    phone_verified  SMALLINT NOT NULL DEFAULT 0,
    -- title, headline, bio, rates, skills[], company info, resume, etc.
    profile         JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_users_role          ON users (role);
CREATE INDEX IF NOT EXISTS idx_users_active_mode   ON users (active_mode);
CREATE INDEX IF NOT EXISTS idx_users_is_freelancer ON users (is_freelancer);
CREATE INDEX IF NOT EXISTS idx_users_is_employer   ON users (is_employer);
CREATE INDEX IF NOT EXISTS idx_users_profile_gin   ON users USING GIN (profile);

CREATE TABLE IF NOT EXISTS operations (
    id                   TEXT PRIMARY KEY,
    type                 TEXT NOT NULL,          -- job | application | engagement |
                                                 -- timesheet | wallet | wallet_txn |
                                                 -- payment_method | payment | escrow_hold |
                                                 -- activity | pending_registration | meta
    status               TEXT,
    actor_user_id        TEXT,                   -- freelancer / initiator / owner
    counterparty_user_id TEXT,                   -- employer / other side
    job_id               TEXT,                   -- links child records to a job
    amount_cents         BIGINT,                 -- money in integer cents (USD)
    currency             TEXT NOT NULL DEFAULT 'USD',
    data                 JSONB NOT NULL DEFAULT '{}'::jsonb,  -- type-specific fields
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_ops_type         ON operations (type);
CREATE INDEX IF NOT EXISTS idx_ops_status       ON operations (status);
CREATE INDEX IF NOT EXISTS idx_ops_actor        ON operations (actor_user_id);
CREATE INDEX IF NOT EXISTS idx_ops_counterparty ON operations (counterparty_user_id);
CREATE INDEX IF NOT EXISTS idx_ops_job          ON operations (job_id);
CREATE INDEX IF NOT EXISTS idx_ops_type_status  ON operations (type, status);
CREATE INDEX IF NOT EXISTS idx_ops_data_gin     ON operations USING GIN (data);
