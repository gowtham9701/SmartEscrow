# SmartEscrow

**Algorithmic B2B Infrastructure for Tech Talent** — an MBA capstone entrepreneur
project (LPU Online, Category C) that replaces resume-based hiring, percentage-commission
marketplaces, and centralized dispute administration with programmatic, AI-verified,
fiat-native USD infrastructure.

> **Strict USD fiat-native. No cryptocurrency, tokens, or stablecoins anywhere in this
> project.** All monetary values are integer USD cents, settled through Stripe Connect
> and Plaid **sandbox** environments.

Runs 100% locally and free of charge on Apple Silicon (Mac M5 Air) — zero cloud hosting
dependency. The only inference compute required is local Ollama (DeepSeek-Coder 6.7B /
Llama 3.1 8B).

## Repository Layout

```
SmartEscrow/
├── backend/                  FastAPI application (Python)
│   ├── app/
│   │   ├── ai_engine/        Local LLM + static-analysis code verification engine
│   │   ├── api/              REST endpoints (assessments, milestones, GitHub webhooks)
│   │   ├── core/             Config + async SQLAlchemy/PostgreSQL wiring
│   │   ├── models/           ORM entities mirroring database/schema.sql
│   │   └── services/         Escrow (Stripe) + Arbitration (jury) business logic
│   ├── tests/                Pytest unit tests (deterministic, no network calls)
│   ├── requirements.txt
│   └── .env.example
├── database/
│   └── schema.sql            Full PostgreSQL ledger schema
├── docs/
│   ├── Business_Architecture.md   Benchmarking, monetization, compliance matrix
│   └── thesis/
│       └── Chapter1_Introduction.md
├── docker-compose.yml         Local PostgreSQL only (no cloud services)
└── README.md
```

## Quickstart (Local, Zero-Cost)

```bash
# 1. Start local PostgreSQL (schema auto-applied on first boot)
docker compose up -d postgres

# 2. Install Ollama + pull a local model (one-time, ~4-5GB download)
brew install ollama
ollama serve &
ollama pull deepseek-coder:6.7b

# 3. Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in Stripe/Plaid/GitHub SANDBOX credentials
uvicorn app.main:app --reload --port 8000

# 4. Run tests
pytest -q
```

Visit `http://localhost:8000/docs` for the interactive OpenAPI (Swagger) console.

## Core Pillars

1. **AI Technical Verification Engine** — [verification_engine.py](backend/app/ai_engine/verification_engine.py)
2. **Automated USD Escrow (Stripe Connect sandbox)** — [escrow_service.py](backend/app/services/escrow_service.py)
3. **GitHub Merge-Event Webhook → Auto Escrow Release** — [webhooks.py](backend/app/api/webhooks.py)
4. **Peer-Led Blind Jury Arbitration** — [arbitration_service.py](backend/app/services/arbitration_service.py)
5. **PostgreSQL Ledger Schema** — [schema.sql](database/schema.sql)
6. **Business Architecture & Financial Forecast** — [Business_Architecture.md](docs/Business_Architecture.md)
7. **MBA Thesis Report** — [docs/thesis/](docs/thesis/)

## Compliance Posture

- No crypto/token/stablecoin code paths exist anywhere in this repository.
- Tax documentation (W-8BEN / W-9), KYC gating, and AML controls are modeled in
  `database/schema.sql` (`tax_documents`, `kyc_status`).
- GDPR/CCPA: PII minimization (last-4 tax ID digits only), encrypted tokens at the
  application layer.

See [docs/Business_Architecture.md](docs/Business_Architecture.md) for the full
compliance matrix, competitive benchmarking, and 5-year financial forecast.

