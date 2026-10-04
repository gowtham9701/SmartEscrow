#!/usr/bin/env python3
"""
Provision the SmartEscrow Neon (PostgreSQL) database — creates the two tables
(`users` and `operations`) the app uses. Normally unnecessary (the backend
runs CREATE TABLE IF NOT EXISTS on startup), but handy to verify connectivity
and see the tables appear in the Neon console.

Usage
-----
  # 1. Neon Console -> Connect -> copy the connection string (URI), e.g.
  #    postgresql://USER:PASSWORD@ep-xxx.REGION.aws.neon.tech/neondb?sslmode=require
  export DATABASE_URL='postgresql://...neon.tech/neondb?sslmode=require'

  # 2. Run from the backend/ directory:
  python scripts/provision_neon.py

Safe to run repeatedly. Uses the exact schema defined in app/marketplace/db.py.
"""
from __future__ import annotations

import os
import sys


def _normalise(url: str) -> str:
    for suffix in ("+asyncpg", "+psycopg", "+psycopg2", "+pg8000"):
        url = url.replace(suffix, "")
    if "sslmode=" not in url and "neon.tech" in url:
        url += ("&" if "?" in url else "?") + "sslmode=require"
    return url


def main() -> int:
    db_url = os.environ.get("DATABASE_URL", "").strip()
    if not db_url:
        print("ERROR: set DATABASE_URL to your Neon connection string first.\n"
              "  export DATABASE_URL='postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require'",
              file=sys.stderr)
        return 2

    try:
        import psycopg
    except ImportError:
        print("ERROR: psycopg is not installed. Run: pip install -r requirements.txt",
              file=sys.stderr)
        return 2

    # Reuse the app's canonical schema so there is a single source of truth.
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from app.marketplace.db import SCHEMA

    dsn = _normalise(db_url)
    print("Connecting to the database and applying the two-table schema ...")
    with psycopg.connect(dsn, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA)
            cur.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name"
            )
            tables = [r[0] for r in cur.fetchall()]

    print("Done. Tables now in the public schema:")
    for t in tables:
        print(f"  - {t}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
