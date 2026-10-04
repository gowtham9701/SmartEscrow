# SmartEscrow — Documentation Index

Start here. This folder documents how to run, demo, and productionize SmartEscrow.

## Getting started & demo
- [DEMO_CREDENTIALS.md](./DEMO_CREDENTIALS.md) — all sample logins, firm-registration
  details, mock payment cards, and a demo script.
- [LOCAL_NO_COST_SETUP.md](./LOCAL_NO_COST_SETUP.md) — run everything locally for free.
- [FREE_TIER_DEPLOYMENT.md](./FREE_TIER_DEPLOYMENT.md) — deploy to Render + Vercel free tiers.

## Email / OTP
- [SMTP_CREDENTIALS_GUIDE.md](./SMTP_CREDENTIALS_GUIDE.md) — **how to get & set** free
  SMTP credentials (Gmail App Password / Brevo / Resend) to enable real email OTP.
- [OTP_EMAIL_SETUP.md](./OTP_EMAIL_SETUP.md) — how OTP delivery modes work.

## Productionizing
- [PRODUCTION_GUIDE.md](./PRODUCTION_GUIDE.md) — **every workflow mapped to file
  paths**, with `MVP:` (what exists) vs `PROD:` (what to change): job posting,
  employer registration, freelancer activities, payments/escrow, AI, data,
  security, real-time, deployment, and a 90%-ready checklist.

## Business / academic
- [Business_Architecture.md](./Business_Architecture.md)
- [NO_COST_OPEN_SOURCE_STACK.md](./NO_COST_OPEN_SOURCE_STACK.md)
- [thesis/](./thesis) — MBA capstone chapters.

## Where the code lives (quick map)
| Area | Path |
|------|------|
| Backend API | `backend/app/api/marketplace.py` |
| Business logic + persistence | `backend/app/marketplace/store.py` |
| DB schema / migrations | `backend/app/marketplace/db.py` |
| AI (summaries, resume, matching) | `backend/app/marketplace/ai.py` |
| Email / OTP | `backend/app/marketplace/notifications.py` |
| Config / env | `backend/app/core/config.py` |
| Frontend pages | `frontend/app/` |
| Frontend API client / state | `frontend/lib/` |
| Dashboards (role UIs) | `frontend/components/dashboard/` |

See [PRODUCTION_GUIDE.md](./PRODUCTION_GUIDE.md) for the full file-by-file breakdown.
