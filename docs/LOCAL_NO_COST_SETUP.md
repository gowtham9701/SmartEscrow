# SmartEscrow: Strict Local No-Cost Setup Guide

This project is intentionally designed to run without any paid subscriptions during the prototype and validation stage.

## Core principle

Use only open-source and free-tier tools:
- FastAPI for the backend
- PostgreSQL via Docker locally
- Next.js for the frontend
- Ollama for local AI inference on Mac
- Local mock payment engine by default

No paid vendor is required to build, run, or demonstrate the app at this stage.

## Hardware and software

- MacBook with Apple Silicon (M5/M4/M3 supported)
- Docker Desktop
- Python 3.11+
- Node.js 18+
- Git

## 1. Clone the repository

```bash
git clone https://github.com/gowtham9701/SmartEscrow.git
cd SmartEscrow
```

## 2. Start local PostgreSQL

```bash
docker compose up -d postgres
```

Confirm the DB is listening on localhost:5432.

## 3. Create a Python virtual environment

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 4. Run the backend locally

```bash
uvicorn app.main:app --reload --port 8000
```

Open:
- http://localhost:8000/docs
- http://localhost:8000/health

## 5. Start the frontend

```bash
cd ../frontend
npm install
npm run dev
```

Open:
- http://localhost:3000

## 6. Demo credentials

Use the demo login users created by the backend:

- admin@smartescrow.io / SmartEscrow123!
- client@smartescrow.io / SmartEscrow123!
- freelancer@smartescrow.io / SmartEscrow123!
- arbiter@smartescrow.io / SmartEscrow123!

## 7. Demo payment mode

The project runs in mock payment mode by default:

```env
PAYMENT_PROVIDER=mock
PAYMENT_CURRENCY=INR
```

This means all escrow, release, and refund flows are simulated locally without any external API or fee.

## 8. Local AI setup with Ollama

Install Ollama and pull a local model:

```bash
ollama pull deepseek-coder:6.7b
```

Then confirm the endpoint:

```bash
curl http://localhost:11434
```

## 9. Free-tier deployment options

Frontend:
- Vercel free plan
- Netlify free plan

Backend:
- Render free plan, or run locally for prototype

Database:
- Neon free tier, or PostgreSQL local Docker

## 10. Production caution

This local no-cost setup is perfect for MVP validation, but any real payout or production settlement must later use a real compliance-ready payment provider with KYC and bank integration.

For now, the app is intentionally cost-free and open-source-friendly.
