# SmartEscrow on Neon (PostgreSQL) — two-table architecture

The marketplace persists **all** of its data in a Neon PostgreSQL database using
exactly **two tables**:

| Table        | What it holds |
|--------------|---------------|
| `users`      | Identity, auth and profile for freelancers **and** employers. Core columns (id, email, username, phone, password_hash, role, flags) plus a `profile` JSONB document for everything else (title, bio, rates, skills, company info, resume, …). |
| `operations` | Every operational record — job postings, applications, engagements, timesheets, wallets, wallet transactions, payment methods, payments, escrow holds and activity — discriminated by a `type` column with a JSONB `data` document. Common filter columns (`status`, `actor_user_id`, `counterparty_user_id`, `job_id`, `amount_cents`) are promoted for indexing. |

Schema (single source of truth): [`backend/app/marketplace/db.py`](../backend/app/marketplace/db.py)
— also mirrored in [`backend/db/neon_schema.sql`](../backend/db/neon_schema.sql).

## Why Neon was empty before
The app used to persist to a local SQLite file. Nothing ever connected to Neon,
so no tables were created there. The data layer has now been migrated to
PostgreSQL, so pointing `DATABASE_URL` at Neon makes the app create and use the
two tables automatically.

## Setup

### 1. Get your Neon connection string
Neon Console → **Connect** → copy the URI. It looks like:

```
postgresql://USER:PASSWORD@ep-xxx.REGION.aws.neon.tech/neondb?sslmode=require
```

### 2. Set `DATABASE_URL`
In `backend/.env` (local) or your host's environment (Render/Vercel), set it
with the `+asyncpg` suffix (the marketplace layer strips it for its own driver;
the legacy milestone modules need it):

```
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@ep-xxx.REGION.aws.neon.tech/neondb?sslmode=require
```

### 3. Start the backend
On first start the app runs `CREATE TABLE IF NOT EXISTS` for the two tables and
seeds demo data. You'll see `users` and `operations` appear in the Neon console.

Optional manual provisioning / connectivity check:

```bash
cd backend
export DATABASE_URL='postgresql://USER:PASSWORD@ep-xxx.neon.tech/neondb?sslmode=require'
python scripts/provision_neon.py
```

## Local development
Install PostgreSQL locally (e.g. `brew install postgresql@16`) and point
`DATABASE_URL` at it, or just use your Neon database directly. The driver is
`psycopg` (v3), already in `requirements.txt`.

## Resetting / clearing the database
```sql
TRUNCATE users, operations;   -- removes all rows; the app reseeds demo data on next startup
```
