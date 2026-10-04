"""
PostgreSQL (Neon) persistence layer for the SmartEscrow marketplace.

The entire marketplace is stored in just TWO physical tables:

  * users       -> identity, auth and profile for freelancers AND employers.
  * operations  -> every operational record (job postings, applications,
                   engagements, timesheets, wallets, wallet transactions,
                   payment methods, payments, escrow holds and activity),
                   discriminated by the `type` column with a JSONB `data`
                   document holding the record's fields.

This module exposes a small document-style repository API (user_* and op_*)
that the business logic in store.py / seed.py build on, so the two-table
shape is invisible to the rest of the app.

Connection string comes from DATABASE_URL (Neon in production, a local
PostgreSQL in development). Works with psycopg 3.
"""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.core.config import settings

# --------------------------------------------------------------------------- #
# Connection
# --------------------------------------------------------------------------- #
_lock = threading.RLock()
_conn: psycopg.Connection | None = None


def _dsn() -> str:
    """Resolve + normalise the connection string for psycopg."""
    raw = os.environ.get("DATABASE_URL") or settings.DATABASE_URL
    # psycopg speaks plain libpq URLs — strip any SQLAlchemy driver suffix.
    for suffix in ("+asyncpg", "+psycopg", "+psycopg2", "+pg8000"):
        raw = raw.replace(suffix, "")
    return raw


# Two-table schema. Flags are stored as SMALLINT (0/1) to mirror the app's
# existing integer-flag semantics exactly.
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id              TEXT PRIMARY KEY,
    email           TEXT UNIQUE NOT NULL,
    username        TEXT UNIQUE,
    phone           TEXT,
    password_hash   TEXT NOT NULL,
    full_name       TEXT NOT NULL,
    role            TEXT NOT NULL DEFAULT 'contributor',
    active_mode     TEXT NOT NULL DEFAULT 'freelancer',
    is_freelancer   SMALLINT NOT NULL DEFAULT 1,
    is_employer     SMALLINT NOT NULL DEFAULT 0,
    firm_verified   SMALLINT NOT NULL DEFAULT 0,
    email_verified  SMALLINT NOT NULL DEFAULT 0,
    phone_verified  SMALLINT NOT NULL DEFAULT 0,
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
    type                 TEXT NOT NULL,
    status               TEXT,
    actor_user_id        TEXT,
    counterparty_user_id TEXT,
    job_id               TEXT,
    amount_cents         BIGINT,
    currency             TEXT NOT NULL DEFAULT 'USD',
    data                 JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_ops_type         ON operations (type);
CREATE INDEX IF NOT EXISTS idx_ops_status       ON operations (status);
CREATE INDEX IF NOT EXISTS idx_ops_actor        ON operations (actor_user_id);
CREATE INDEX IF NOT EXISTS idx_ops_counterparty ON operations (counterparty_user_id);
CREATE INDEX IF NOT EXISTS idx_ops_job          ON operations (job_id);
CREATE INDEX IF NOT EXISTS idx_ops_type_status  ON operations (type, status);
CREATE INDEX IF NOT EXISTS idx_ops_data_gin     ON operations USING GIN (data);
"""


def _connect() -> psycopg.Connection:
    conn = psycopg.connect(_dsn(), autocommit=True, row_factory=dict_row)
    return conn


def get_conn() -> psycopg.Connection:
    global _conn
    with _lock:
        if _conn is None or _conn.closed:
            _conn = _connect()
            with _conn.cursor() as cur:
                cur.execute(SCHEMA)
        else:
            # Cheap liveness check; reconnect if the server dropped us (Neon idle).
            try:
                with _conn.cursor() as cur:
                    cur.execute("SELECT 1")
            except psycopg.Error:
                try:
                    _conn.close()
                except psycopg.Error:
                    pass
                _conn = _connect()
                with _conn.cursor() as cur:
                    cur.execute(SCHEMA)
        return _conn


def _run(sql: str, params: tuple = (), *, fetch: str | None = None):
    with _lock:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if fetch == "one":
                return cur.fetchone()
            if fetch == "all":
                return cur.fetchall()
            return None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --------------------------------------------------------------------------- #
# JSON helpers (kept for backward-compatible callers)
# --------------------------------------------------------------------------- #
def dumps(value):
    return json.dumps(value if value is not None else [])


def loads(value, default=None):
    if value is None or value == "":
        return default if default is not None else []
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else []


# --------------------------------------------------------------------------- #
# Users repository
# --------------------------------------------------------------------------- #
_USER_CORE = (
    "id", "email", "username", "phone", "password_hash", "full_name", "role",
    "active_mode", "is_freelancer", "is_employer", "firm_verified",
    "email_verified", "phone_verified", "created_at",
)
_USER_FLAGS = ("is_freelancer", "is_employer", "firm_verified", "email_verified", "phone_verified")


def _split_user(record: dict) -> tuple[dict, dict]:
    core = {k: record[k] for k in _USER_CORE if k in record}
    profile = {k: v for k, v in record.items() if k not in _USER_CORE}
    for f in _USER_FLAGS:
        if f in core and core[f] is not None:
            core[f] = int(core[f])
    return core, profile


def _user_row_to_record(row) -> dict | None:
    if row is None:
        return None
    profile = row.get("profile") or {}
    rec = {k: row[k] for k in _USER_CORE if k in row}
    for f in _USER_FLAGS:
        if f in rec and rec[f] is not None:
            rec[f] = int(rec[f])
    created = rec.get("created_at")
    if isinstance(created, datetime):
        rec["created_at"] = created.isoformat(timespec="seconds")
    rec.update(profile)
    return rec


def user_insert(record: dict) -> None:
    core, profile = _split_user(record)
    core.setdefault("created_at", _now())
    cols = list(core.keys()) + ["profile"]
    placeholders = ", ".join(["%s"] * len(cols))
    params = [core[k] for k in core] + [Jsonb(profile)]
    _run(
        f"INSERT INTO users ({', '.join(cols)}) VALUES ({placeholders})",
        tuple(params),
    )


def user_get(user_id: str) -> dict | None:
    row = _run("SELECT * FROM users WHERE id = %s", (user_id,), fetch="one")
    return _user_row_to_record(row)


def user_find(**equals) -> dict | None:
    if not equals:
        return None
    clause = " AND ".join(f"{k} = %s" for k in equals)
    row = _run(f"SELECT * FROM users WHERE {clause} LIMIT 1", tuple(equals.values()), fetch="one")
    return _user_row_to_record(row)


def user_all() -> list[dict]:
    rows = _run("SELECT * FROM users", fetch="all") or []
    return [_user_row_to_record(r) for r in rows]


def user_update(user_id: str, changes: dict) -> None:
    core, profile = _split_user({k: v for k, v in changes.items() if k != "id"})
    sets, params = [], []
    for k, v in core.items():
        sets.append(f"{k} = %s")
        params.append(v)
    if profile:
        sets.append("profile = profile || %s::jsonb")
        params.append(Jsonb(profile))
    if not sets:
        return
    params.append(user_id)
    _run(f"UPDATE users SET {', '.join(sets)} WHERE id = %s", tuple(params))


# --------------------------------------------------------------------------- #
# Operations repository (jobs, applications, engagements, payments, ...)
# --------------------------------------------------------------------------- #
def _op_row_to_record(row) -> dict | None:
    if row is None:
        return None
    rec = dict(row.get("data") or {})
    rec["id"] = row["id"]
    created = row.get("created_at")
    if created is not None and "created_at" not in rec:
        rec["created_at"] = created.isoformat(timespec="seconds") if isinstance(created, datetime) else created
    if "status" not in rec and row.get("status") is not None:
        rec["status"] = row["status"]
    return rec


def op_insert(op_type: str, record: dict, *, actor: str | None = None,
              counter: str | None = None, job: str | None = None,
              amount_cents: int | None = None, currency: str = "USD") -> dict:
    rec = dict(record)
    op_id = rec["id"]
    rec.setdefault("created_at", _now())
    data = {k: v for k, v in rec.items() if k != "id"}
    _run(
        """INSERT INTO operations
           (id, type, status, actor_user_id, counterparty_user_id, job_id, amount_cents, currency, data, created_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (op_id, op_type, rec.get("status"), actor, counter, job, amount_cents, currency,
         Jsonb(data), rec.get("created_at")),
    )
    return op_get(op_id)


def op_get(op_id: str) -> dict | None:
    row = _run("SELECT * FROM operations WHERE id = %s", (op_id,), fetch="one")
    return _op_row_to_record(row)


def op_all(op_type: str) -> list[dict]:
    rows = _run(
        "SELECT * FROM operations WHERE type = %s ORDER BY created_at DESC, id DESC",
        (op_type,), fetch="all",
    ) or []
    return [_op_row_to_record(r) for r in rows]


def op_find(op_type: str, **equals) -> list[dict]:
    recs = op_all(op_type)
    if not equals:
        return recs
    return [r for r in recs if all(r.get(k) == v for k, v in equals.items())]


def op_one(op_type: str, **equals) -> dict | None:
    found = op_find(op_type, **equals)
    return found[0] if found else None


def op_count(op_type: str, **equals) -> int:
    return len(op_find(op_type, **equals))


def op_update(op_id: str, changes: dict, *, actor: str | None = None,
              counter: str | None = None, amount_cents: int | None = None) -> dict | None:
    merge = {k: v for k, v in changes.items() if k != "id"}
    sets = ["data = data || %s::jsonb"]
    params: list = [Jsonb(merge)]
    if "status" in merge:
        sets.append("status = %s")
        params.append(merge["status"])
    if actor is not None:
        sets.append("actor_user_id = %s")
        params.append(actor)
    if counter is not None:
        sets.append("counterparty_user_id = %s")
        params.append(counter)
    if amount_cents is not None:
        sets.append("amount_cents = %s")
        params.append(amount_cents)
    params.append(op_id)
    _run(f"UPDATE operations SET {', '.join(sets)} WHERE id = %s", tuple(params))
    return op_get(op_id)


def op_delete(op_id: str) -> None:
    _run("DELETE FROM operations WHERE id = %s", (op_id,))


def op_delete_where(op_type: str, **equals) -> None:
    for r in op_find(op_type, **equals):
        op_delete(r["id"])


# --------------------------------------------------------------------------- #
# Seed flag + reset (stored as a tiny meta operation)
# --------------------------------------------------------------------------- #
_SEED_ID = "meta_seeded"


def is_seeded() -> bool:
    row = _run("SELECT id FROM operations WHERE id = %s", (_SEED_ID,), fetch="one")
    return row is not None


def mark_seeded() -> None:
    _run(
        "INSERT INTO operations (id, type, data, created_at) VALUES (%s, 'meta', %s, %s) "
        "ON CONFLICT (id) DO NOTHING",
        (_SEED_ID, Jsonb({"value": "1"}), _now()),
    )


def reset() -> None:
    """Drop all marketplace data (used for re-seeding in dev)."""
    _run("TRUNCATE users, operations")
