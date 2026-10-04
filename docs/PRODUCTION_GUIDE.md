# SmartEscrow — Production Guide

This document maps every core workflow to the **exact files** that implement it,
explains what the MVP does today, and lists precisely what to change to make it
**production-grade** (real-time, real payments, real DB, hardened security).

Use it as a checklist: each area is marked `MVP:` (what exists) and
`PROD:` (what to do), with the file paths to edit.

- API base path: `/api/v1/market` (router prefix in [`backend/app/main.py`](../backend/app/main.py))
- Frontend API client: [`frontend/lib/api.ts`](../frontend/lib/api.ts)

---

## 0. System map (where everything lives)

| Layer | Path | Responsibility |
|-------|------|----------------|
| App entrypoint | [`backend/app/main.py`](../backend/app/main.py) | FastAPI app, routers, CORS, root/health |
| Config | [`backend/app/core/config.py`](../backend/app/core/config.py) | All env vars (JWT, SMTP, payments, OTP) |
| Marketplace API | [`backend/app/api/marketplace.py`](../backend/app/api/marketplace.py) | All marketplace endpoints |
| Data store | [`backend/app/marketplace/store.py`](../backend/app/marketplace/store.py) | Business logic + persistence |
| DB schema/conn | [`backend/app/marketplace/db.py`](../backend/app/marketplace/db.py) | SQLite schema, migrations, helpers |
| Seed data | [`backend/app/marketplace/seed.py`](../backend/app/marketplace/seed.py) | Demo users/jobs/wallets |
| AI engine | [`backend/app/marketplace/ai.py`](../backend/app/marketplace/ai.py) | Job summary, resume analysis, matching |
| Resume parsing | [`backend/app/marketplace/resume_parser.py`](../backend/app/marketplace/resume_parser.py) | PDF/DOCX/TXT text extraction |
| Email/OTP | [`backend/app/marketplace/notifications.py`](../backend/app/marketplace/notifications.py) | SMTP delivery |
| Frontend app | [`frontend/app/`](../frontend/app) | Next.js pages (routes) |
| Frontend state | [`frontend/lib/`](../frontend/lib) | API client, auth + theme context, types |
| Dashboard UI | [`frontend/components/dashboard/`](../frontend/components/dashboard) | Role dashboards, wallet, resume |

---

## 1. Registration + Email/Mobile OTP

**MVP:**
- Endpoints: `POST /auth/register/start`, `/auth/register/verify`,
  `/auth/register/resend` in [`marketplace.py`](../backend/app/api/marketplace.py) (lines ~205–240).
- Logic: `start_registration()`, `verify_registration()`,
  `resend_registration_otp()` in [`store.py`](../backend/app/marketplace/store.py).
- Pending signups stored in the `pending_registrations` table
  ([`db.py`](../backend/app/marketplace/db.py)); codes are random 6-digit, 15-min TTL.
- Delivery: [`notifications.py`](../backend/app/marketplace/notifications.py) — real email when SMTP set, else demo.
- Frontend: [`frontend/app/register/page.tsx`](../frontend/app/register/page.tsx), [`frontend/app/login/page.tsx`](../frontend/app/login/page.tsx), [`frontend/lib/auth-context.tsx`](../frontend/lib/auth-context.tsx).

**PROD:**
- Set SMTP env vars → see [`SMTP_CREDENTIALS_GUIDE.md`](./SMTP_CREDENTIALS_GUIDE.md). OTP email becomes real with zero code change.
- For real **SMS**, add a `send_sms()` in `notifications.py` (Twilio/MSG91 SDK) and call it from `start_registration()` in `store.py`.
- Switch password hashing from SHA-256 to **bcrypt** — replace `hash_password()`/`verify_password()` in `store.py` with `passlib` bcrypt (already a dependency; see `backend/app/services/auth_service.py` for the pattern).
- Add **rate limiting** on `/auth/*` (e.g. `slowapi`) to stop OTP brute force.

---

## 2. Employer firm registration & verification

**MVP:**
- Endpoint: `POST /profile/register-firm` ([`marketplace.py`](../backend/app/api/marketplace.py) ~281).
- Logic: `register_firm()` in [`store.py`](../backend/app/marketplace/store.py) — validates fields, marks `is_employer=1, firm_verified=1` (instant demo verification).
- Mode switch: `POST /profile/switch-mode` → `switch_mode()` (employer requires `firm_verified`).
- Frontend: [`frontend/components/firm-register-modal.tsx`](../frontend/components/firm-register-modal.tsx), toggle in [`frontend/components/site-header.tsx`](../frontend/components/site-header.tsx).

**PROD:**
- Replace instant verification with a real **KYB** (Know-Your-Business) check in `register_firm()`:
  - Validate the registration number against a registry/API (e.g. local company registry, GLEIF, or a KYB provider like Middesk/Signzy).
  - Verify the work-email domain matches the company domain; send a domain-confirmation email.
  - Set `firm_verified=1` only after the check passes; otherwise keep `pending` and notify an admin review queue.
- Add a `firm_status` column (`pending/verified/rejected`) in `db.py` migrations.

---

## 3. Job posting (real-time)

**MVP:**
- Endpoints: `POST /jobs`, `GET /jobs`, `GET /jobs/{id}` ([`marketplace.py`](../backend/app/api/marketplace.py) ~323–344).
- Logic: `create_job()`, `list_jobs()`, `get_job()` in [`store.py`](../backend/app/marketplace/store.py); rows in the `jobs` table.
- AI summary auto-generated on create via `ai.analyze_job()` ([`ai.py`](../backend/app/marketplace/ai.py)).
- Frontend: [`frontend/app/jobs/new/page.tsx`](../frontend/app/jobs/new/page.tsx) (live AI preview), [`frontend/app/jobs/page.tsx`](../frontend/app/jobs/page.tsx), [`frontend/app/jobs/[id]/page.tsx`](../frontend/app/jobs/[id]/page.tsx).
- "Real-time" today = fresh fetch on navigation.

**PROD — make it truly real-time:**
- Add a WebSocket/SSE channel so new jobs/applicants push instantly:
  - New file `backend/app/api/realtime.py` with a FastAPI `WebSocket` endpoint `/ws`; broadcast `job.created`, `application.received`, `payment.released` events.
  - Emit events from `create_job()`, `apply_to_job()`, `release_payment()` in `store.py`.
  - Frontend: a `frontend/lib/realtime.ts` client that subscribes and refreshes lists / shows toasts.
- Add full-text search + filters at the DB layer (Postgres `tsvector`, or a search service) in `list_jobs()`.
- Add pagination to `GET /jobs` (offset/limit) in `marketplace.py` + `store.py`.

---

## 4. Freelancer activities (resume, apply, work, earnings)

**MVP:**
- Resume: `POST /profile/resume-upload` (file) + `/profile/resume-text`
  ([`marketplace.py`](../backend/app/api/marketplace.py) ~289–315) →
  `resume_parser.extract_text()` + `store.save_resume()` + `ai.analyze_resume()`.
- Applying: `POST /jobs/{id}/apply` → `apply_to_job()` (requires a resume on file).
- Work tracking: `POST /engagements/{id}/log-hours` → `log_hours()`.
- Earnings/withdraw: `POST /wallet/withdraw` → `withdraw_from_wallet()`.
- Frontend: [`frontend/components/dashboard/resume-manager.tsx`](../frontend/components/dashboard/resume-manager.tsx), [`frontend/components/dashboard/dashboard-client.tsx`](../frontend/components/dashboard/dashboard-client.tsx).

**PROD:**
- Store uploaded resume **files** in object storage (S3/Cloudflare R2/Supabase Storage) instead of keeping only extracted text; save the URL in `resume_url`. Add the upload in `save_resume()` / a new `storage.py`.
- Swap the heuristic skill extractor in `ai.py` for a real LLM call (see §6) for higher-quality extraction + matching.
- Add escrow-backed timesheet approval (employer approves logged hours before release).

---

## 5. Payments & escrow (wallet, fund, release, withdraw)

**MVP (simulated gateway):**
- Deposit: `POST /wallet/deposit` → `process_card_payment()` (Luhn + test cards) → `deposit_to_wallet()`.
- Escrow block: `POST /engagements/{id}/fund-escrow` → `fund_escrow()` (moves `available → blocked`).
- Release: `POST /payments/{id}/release` → `release_payment()` (blocked → contributor).
- Withdraw: `POST /wallet/withdraw` → `withdraw_from_wallet()`.
- Tables: `wallets`, `wallet_transactions`, `escrow_holds`, `payments`, `payment_methods` ([`db.py`](../backend/app/marketplace/db.py)).
- Frontend: [`frontend/components/payment-gateway-modal.tsx`](../frontend/components/payment-gateway-modal.tsx), [`frontend/components/dashboard/wallet-panel.tsx`](../frontend/components/dashboard/wallet-panel.tsx).

**PROD — real money (Stripe recommended for USD):**
- Create `backend/app/marketplace/payments.py` wrapping Stripe:
  - `create_payment_intent()` for deposits (replace `process_card_payment()`); never handle raw PAN — use Stripe Elements on the frontend so card data never hits your server (PCI scope ↓).
  - **Stripe Connect** for payouts to freelancers (`transfers` / `payouts`), replacing `withdraw_from_wallet()`.
  - Escrow = hold funds on the platform balance; release = `Transfer` to the connected account.
- Add a webhook endpoint `POST /webhooks/stripe` (new `backend/app/api/stripe_webhooks.py`) to confirm `payment_intent.succeeded`, `transfer.paid`, etc. — the source of truth for state changes. Mirror the existing GitHub webhook pattern in [`backend/app/api/webhooks.py`](../backend/app/api/webhooks.py).
- Keep `payments`/`escrow_holds` tables as the ledger; reconcile against Stripe events.
- Set `PAYMENT_PROVIDER=stripe` in config and add `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` to `config.py` + env.

---

## 6. AI (job summaries, resume analysis, matching, recommendations)

**MVP (local, dependency-free heuristics):**
- All in [`ai.py`](../backend/app/marketplace/ai.py): `analyze_job()`, `analyze_resume()`, `extract_skills()`, `match_score()`, `recommend_skills()`.
- Resume matching + recommendations assembled in `store.analyze_resume_text()`.

**PROD — higher quality:**
- Point the AI functions at a real model:
  - **Local & free:** run Ollama (already in config: `OLLAMA_HOST`, `OLLAMA_MODEL`) and call it from `ai.py` for extraction/summaries.
  - **Hosted:** OpenAI/Anthropic — add `AI_PROVIDER` + API key to `config.py`, implement a client in a new `backend/app/marketplace/llm.py`, and have `analyze_job()`/`analyze_resume()` call it with a structured-output prompt; keep the heuristic as a fallback.
- Add embeddings-based job↔talent matching (pgvector) for better recommendations than keyword overlap.

---

## 7. Data persistence (SQLite → Postgres)

**MVP:**
- SQLite file via [`db.py`](../backend/app/marketplace/db.py) (`SMARTESCROW_DB_PATH`). Auto-creates schema + runs light migrations; seeds once.
- Great locally and for demos; **resets on redeploy** on ephemeral hosts.

**PROD:**
- Move the marketplace store to Postgres:
  - Easiest: keep the same table shapes, swap `sqlite3` for `psycopg`/SQLAlchemy in `db.py` (`get_conn`, `execute`, `query_all/one`), parameterised SQL stays the same (change `?` → `%s`).
  - Or adopt SQLAlchemy models (the legacy modules already use async SQLAlchemy — see [`backend/app/models/entities.py`](../backend/app/models/entities.py)) and manage schema with **Alembic** (already a dependency).
- Use a managed Postgres (Neon/Supabase/Render Postgres — all have free tiers).
- Replace "seed on empty" with proper migrations + an optional `--seed` script for staging only.

---

## 8. Security hardening (do before go-live)

Edit points are in `store.py`, `marketplace.py`, `main.py`, `config.py`:
- **Passwords:** switch `hash_password`/`verify_password` in `store.py` to bcrypt.
- **JWT:** set a strong `JWT_SECRET_KEY` (32+ random chars) in env; shorten `ACCESS_TOKEN_EXPIRE_MINUTES`; add refresh tokens if needed.
- **CORS:** in [`main.py`](../backend/app/main.py) the dev regex allows all localhost ports — in production restrict `allow_origin_regex` to your exact Vercel domain.
- **Rate limiting:** add `slowapi` to `/auth/*`, `/wallet/*`.
- **Input validation:** Pydantic models already validate; add size/type checks on uploads (already capped at 5 MB in `resume_upload`).
- **Secrets:** never commit `.env`; use host env vars. `.env`, `*.db` are gitignored.
- **HTTPS:** terminate TLS at the host (Render/Vercel do this automatically).
- **Audit:** every mutation is logged to the `operations` table via `audit()` in `store.py` — keep this; ship logs to a log sink in prod.

---

## 9. Real-time strategy (summary)

Add a single WebSocket hub and emit domain events from `store.py`:
- `job.created` → update job lists live (candidates see new roles instantly).
- `application.received` → employer applicant list + toast.
- `application.status` → freelancer sees shortlist/hire updates live.
- `escrow.funded` / `payment.released` → wallet balances update live.

Files to add: `backend/app/api/realtime.py` (hub + `/ws`), `frontend/lib/realtime.ts`
(client); emit calls inside the existing `store.py` mutation functions.

---

## 10. Deployment

- **Backend → Render** (Docker): [`backend/Dockerfile`](../backend/Dockerfile), blueprint [`render.yaml`](../render.yaml). Set all env vars (DB, JWT, SMTP, Stripe) in the Render dashboard. Start command runs Gunicorn/Uvicorn.
- **Frontend → Vercel**: root `frontend`, build `npm run build`, env `NEXT_PUBLIC_API_BASE_URL=https://<your-backend>.onrender.com`. See [`FREE_TIER_DEPLOYMENT.md`](./FREE_TIER_DEPLOYMENT.md).
- `NEXT_PUBLIC_*` vars are inlined at **build time** — set them before building.

---

## 11. 90%-ready checklist

Done (MVP, demo-ready):
- [x] Two-sided marketplace: jobs, talent, applications, engagements
- [x] Dual-mode profiles (freelancer/employer) + firm registration
- [x] Wallet + escrow (block/release) + simulated card gateway
- [x] OTP registration (real email ready via SMTP) + username/password login
- [x] Resume upload (PDF/DOCX/TXT) + AI skill extraction, matching, recommendations
- [x] AI job summaries + talent matching
- [x] Light/dark theme, responsive UI, audited operations table
- [x] Deployable to Render + Vercel free tiers

The remaining ~10% for real production:
- [ ] Postgres + Alembic migrations (replace SQLite) — §7
- [ ] Real payments via Stripe Connect + webhooks — §5
- [ ] bcrypt passwords + rate limiting + locked-down CORS — §8
- [ ] WebSocket/SSE real-time events — §3, §9
- [ ] Real KYB firm verification — §2
- [ ] Object storage for resume files — §4
- [ ] (Optional) LLM-backed AI via Ollama/OpenAI — §6
