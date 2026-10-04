"""
SQLite persistence layer for SmartEscrow.

Uses Python's built-in sqlite3 (zero extra dependencies). A single file-backed
database gives real persistence across requests and restarts, while remaining
100% free and runnable locally on a Mac or on free-tier hosting. Every mutation
in the marketplace is recorded in the audit_log table for full traceability.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading

# Database file lives next to the backend app (override with SMARTESCROW_DB_PATH).
_DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "smartescrow.db")
DB_PATH = os.environ.get("SMARTESCROW_DB_PATH", _DEFAULT_PATH)

_lock = threading.RLock()
_conn: sqlite3.Connection | None = None


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE,
    phone TEXT,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL,
    active_mode TEXT DEFAULT 'freelancer',
    is_freelancer INTEGER DEFAULT 0,
    is_employer INTEGER DEFAULT 0,
    firm_verified INTEGER DEFAULT 0,
    firm_reg_number TEXT,
    firm_work_email TEXT,
    resume_text TEXT,
    resume_url TEXT,
    resume_filename TEXT,
    resume_updated_at TEXT,
    email_verified INTEGER DEFAULT 1,
    phone_verified INTEGER DEFAULT 1,
    title TEXT,
    headline TEXT,
    bio TEXT,
    location TEXT,
    country_code TEXT,
    hourly_rate_usd REAL,
    years_experience INTEGER,
    availability TEXT,
    github_username TEXT,
    company_name TEXT,
    company_size TEXT,
    industry TEXT,
    website TEXT,
    rating REAL DEFAULT 0,
    completed_jobs INTEGER DEFAULT 0,
    jobs_posted INTEGER DEFAULT 0,
    avatar_hue INTEGER DEFAULT 210,
    skills TEXT DEFAULT '[]',
    services TEXT DEFAULT '[]',
    experiences TEXT DEFAULT '[]',
    achievements TEXT DEFAULT '[]',
    portfolio TEXT DEFAULT '[]',
    languages TEXT DEFAULT '[]',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    company_name TEXT,
    title TEXT NOT NULL,
    category TEXT,
    description TEXT,
    skills_required TEXT DEFAULT '[]',
    engagement_type TEXT DEFAULT 'hourly',
    hourly_rate_min INTEGER,
    hourly_rate_max INTEGER,
    experience_level TEXT,
    location TEXT,
    hours_per_week INTEGER,
    duration TEXT,
    status TEXT DEFAULT 'open',
    ai TEXT DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS applications (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    contributor_id TEXT NOT NULL,
    proposed_hourly_rate INTEGER,
    status TEXT DEFAULT 'submitted',
    cover_letter TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS engagements (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    client_id TEXT NOT NULL,
    contributor_id TEXT NOT NULL,
    title TEXT,
    hourly_rate INTEGER,
    hours_logged INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    started_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS timesheets (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    week TEXT,
    hours INTEGER,
    note TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS wallets (
    id TEXT PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    available_balance REAL DEFAULT 0,
    blocked_balance REAL DEFAULT 0,
    currency TEXT DEFAULT 'USD',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS wallet_transactions (
    id TEXT PRIMARY KEY,
    wallet_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    type TEXT NOT NULL,
    amount REAL NOT NULL,
    available_after REAL,
    blocked_after REAL,
    ref TEXT,
    note TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS payment_methods (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    brand TEXT,
    last4 TEXT,
    exp_month INTEGER,
    exp_year INTEGER,
    holder_name TEXT,
    is_default INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS payments (
    id TEXT PRIMARY KEY,
    engagement_id TEXT,
    client_id TEXT NOT NULL,
    contributor_id TEXT NOT NULL,
    amount_usd REAL NOT NULL,
    type TEXT NOT NULL,
    status TEXT NOT NULL,
    hours INTEGER DEFAULT 0,
    gateway_ref TEXT,
    note TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS escrow_holds (
    id TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL,
    client_id TEXT NOT NULL,
    contributor_id TEXT NOT NULL,
    amount_usd REAL NOT NULL,
    hours INTEGER DEFAULT 0,
    status TEXT DEFAULT 'held',
    created_at TEXT NOT NULL,
    released_at TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor_id TEXT,
    actor_name TEXT,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id TEXT,
    detail TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    user_name TEXT,
    action TEXT NOT NULL,
    category TEXT,
    entity_type TEXT,
    entity_id TEXT,
    details TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pending_registrations (
    id TEXT PRIMARY KEY,
    username TEXT,
    email TEXT,
    phone TEXT,
    password_hash TEXT,
    full_name TEXT,
    role TEXT,
    title TEXT,
    hourly_rate_usd REAL,
    company_name TEXT,
    skills TEXT DEFAULT '[]',
    location TEXT,
    email_otp TEXT,
    phone_otp TEXT,
    email_verified INTEGER DEFAULT 0,
    phone_verified INTEGER DEFAULT 0,
    attempts INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


# Columns added after the initial release — applied idempotently on startup so
# existing databases pick up new fields without a destructive reset.
_MIGRATIONS = {
    "users": {
        "username": "TEXT",
        "phone": "TEXT",
        "email_verified": "INTEGER DEFAULT 1",
        "phone_verified": "INTEGER DEFAULT 1",
        "active_mode": "TEXT DEFAULT 'freelancer'",
        "is_freelancer": "INTEGER DEFAULT 0",
        "is_employer": "INTEGER DEFAULT 0",
        "firm_verified": "INTEGER DEFAULT 0",
        "firm_reg_number": "TEXT",
        "firm_work_email": "TEXT",
        "resume_text": "TEXT",
        "resume_url": "TEXT",
        "resume_filename": "TEXT",
        "resume_updated_at": "TEXT",
    },
}


def _migrate(conn) -> None:
    for table, columns in _MIGRATIONS.items():
        existing = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        for col, decl in columns.items():
            if col not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")
    conn.commit()


def get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        with _lock:
            if _conn is None:
                _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
                _conn.row_factory = sqlite3.Row
                _conn.execute("PRAGMA journal_mode=WAL;")
                _conn.execute("PRAGMA foreign_keys=ON;")
                _conn.executescript(SCHEMA)
                _migrate(_conn)
                _conn.commit()
    return _conn


def execute(sql: str, params: tuple = ()) -> sqlite3.Cursor:
    with _lock:
        conn = get_conn()
        cur = conn.execute(sql, params)
        conn.commit()
        return cur


def query_all(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    with _lock:
        conn = get_conn()
        return conn.execute(sql, params).fetchall()


def query_one(sql: str, params: tuple = ()) -> sqlite3.Row | None:
    with _lock:
        conn = get_conn()
        return conn.execute(sql, params).fetchone()


def dumps(value) -> str:
    return json.dumps(value or [])


def loads(value, default=None):
    if value is None or value == "":
        return default if default is not None else []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else []


def is_seeded() -> bool:
    row = query_one("SELECT value FROM meta WHERE key = 'seeded'")
    return bool(row and row["value"] == "1")


def mark_seeded() -> None:
    execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('seeded', '1')")


def reset() -> None:
    """Drop all data (used for re-seeding in dev)."""
    with _lock:
        conn = get_conn()
        for table in (
            "users", "jobs", "applications", "engagements", "timesheets",
            "wallets", "wallet_transactions", "payment_methods", "payments",
            "escrow_holds", "audit_log", "operations", "pending_registrations", "meta",
        ):
            conn.execute(f"DELETE FROM {table}")
        conn.commit()
