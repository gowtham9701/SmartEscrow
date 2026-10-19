# SmartEscrow

SmartEscrow is a local-first platform for hiring and verifying software engineering talent using objective code signals, automated milestone escrow, and peer-led technical dispute resolution.

## 🔗 Live URLs

| Service | URL |
|---------|-----|
| **Web App (UI)** | https://smart-escrow-gamma.vercel.app |
| **Backend API** | https://smartescrow.onrender.com · health: https://smartescrow.onrender.com/health · docs: https://smartescrow.onrender.com/docs |
| **Database (Neon console)** | https://console.neon.tech/app/projects/autumn-tooth-47053286/branches/br-dawn-butterfly-b4lcb8x0 |

> **Notes**
> - The backend is hosted on Render (free tier) and may take ~30–60s to wake from
>   sleep on the first request after inactivity.
> - The database connection string is **secret** and is intentionally **not** listed
>   here — it lives only in Render's private environment variables.

This version is optimized for the Indian market and uses Razorpay as the payment gateway, with fiat settlement in INR instead of USD-only rails.

## Core purpose

- Replace resume-heavy hiring with repository-based technical verification
- Automate milestone funding and payouts in INR with a zero-cost mock provider by default
- Reduce platform fees and manual admin work
- Improve dispute speed with a blind peer jury system

## Zero-cost / open-source stack

This project is designed to run without paying for infrastructure while you are building and validating the MVP.

Recommended no-cost setup:
- Frontend: Vercel free tier
- Backend: Render free tier or local FastAPI on Mac
- Database: local PostgreSQL via Docker or Neon free tier
- AI: Ollama running locally on Apple Silicon
- Payments: mock provider by default; later switch to Razorpay test mode or another sandbox provider only after the product is validated

Important: there is no truly open-source production payment processor that handles legally compliant real payouts in India without some vendor service, KYC, or account registration. The realistic zero-cost path is a local mock payment provider for development and free sandbox/test mode for experimentation.

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


## Mock payment test data (simulated gateway)

SmartEscrow ships with a **simulated USD card gateway** — no real money moves.
Use the dummy cards below to fund a wallet, create escrow, and exercise the full
checkout → webhook → release flow. Any **future** expiry date works; CVV is any
3 digits (4 for Amex). Card PIN is any 4 digits **except `0000`** (which
simulates a bank decline).

### Successful cards

| Brand       | Card Number         | Expiry | CVV  | Result     |
|-------------|---------------------|--------|------|------------|
| Visa        | 4242 4242 4242 4242 | 12/30  | 123  | Success    |
| Visa        | 4000 0566 5566 5556 | 04/29  | 123  | Success    |
| Mastercard  | 5555 5555 5555 4444 | 11/28  | 123  | Success    |
| Mastercard  | 5200 8282 8282 8210 | 03/30  | 123  | Success    |
| Amex        | 3782 822463 10005   | 09/28  | 1234 | Success    |

### Failure / edge-case cards

| Brand       | Card Number         | Expiry | CVV  | Result               |
|-------------|---------------------|--------|------|----------------------|
| Visa        | 4000 0000 0000 0002 | 12/30  | 123  | Declined             |
| Visa        | 4000 0000 0000 9995 | 12/30  | 123  | Insufficient funds   |
| (any above) | —                   | —      | —    | PIN `0000` → declined |

> These are standard, publicly documented **test** card numbers (Luhn-valid,
> non-chargeable). They are safe to commit and are for local/demo use only.

## Sample resumes

The [`/sample`](./sample) folder contains five distinct elite-engineer resumes
you can upload on the **Dashboard → Resume** tab to exercise the AI vetting and
skill-ranking engine:

| File | Profile |
|------|---------|
| `ava-chen-staff-fullstack.md`      | Staff full-stack (Python/FastAPI/React) |
| `diego-morales-ml-llm.md`          | ML / LLM engineer (PyTorch/RAG/Ollama)  |
| `sam-okafor-devops-sre.md`         | DevOps / SRE (Kubernetes/Terraform/AWS) |
| `priya-raman-product-designer.md`  | Senior product designer (Figma/UI-UX)   |
| `lena-kowalski-security-engineer.md` | Application security engineer (STRIDE/pentest) |
