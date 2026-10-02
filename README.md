# SmartEscrow

SmartEscrow is a local-first platform for hiring and verifying software engineering talent using objective code signals, automated milestone escrow, and peer-led technical dispute resolution.

This version is optimized for the Indian market and uses Razorpay as the payment gateway, with fiat settlement in INR instead of USD-only rails.

## Core purpose

- Replace resume-heavy hiring with repository-based technical verification
- Automate milestone funding and payouts in INR via Razorpay
- Reduce platform fees and manual admin work
- Improve dispute speed with a blind peer jury system

## Local stack

- Backend: FastAPI + PostgreSQL
- Frontend: Next.js + Tailwind
- AI: Ollama with DeepSeek-Coder or Llama models
- Payment: Razorpay India
- Hosting options: Vercel + Render + Neon

## Repository layout

```text
SmartEscrow/
├── backend/
│   ├── app/
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── app/
│   ├── components/
│   └── package.json
├── database/
│   └── schema.sql
├── docs/
│   ├── Business_Architecture.md
│   └── thesis/
├── docker-compose.yml
├── render.yaml
├── vercel.json
├── README.md
└── .gitignore
```

## Quickstart

```bash
# Start PostgreSQL locally
cd SmartEscrow
docker compose up -d postgres

# Start backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000

# Start frontend
cd ../frontend
npm install
npm run dev
```

## Required env variables

See `backend/.env.example` and `frontend/.env.example` for setup values.

The backend uses:
- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`
- `RAZORPAY_WEBHOOK_SECRET`
- `PAYMENT_CURRENCY=INR`
- `JWT_SECRET_KEY`
- `DATABASE_URL`
- `GITHUB_WEBHOOK_SECRET`
- `GITHUB_APP_TOKEN`

## Deployment

- Frontend: Vercel
- Backend: Render
- Database: Neon Postgres

## Business model

SmartEscrow is designed around SaaS subscriptions, premium vetting reports, and low transaction friction instead of traditional percentage-heavy marketplace commissions.

