# SmartEscrow: Zero-Cost Open-Source Stack

This project can be built, tested, and demonstrated without paying a single rupee for the MVP.

## Recommended stack

- Backend: FastAPI + SQLAlchemy + PostgreSQL
- Frontend: Next.js + Tailwind + shadcn/ui
- AI: Ollama with DeepSeek-Coder or Llama on the Mac M5 Air
- Payment layer: mock provider by default
- Hosting: Vercel free tier for frontend, Render free tier or local backend for API
- Database: local Docker PostgreSQL or Neon free tier

## Why the mock payment provider is the correct default

A genuinely no-cost payment API with real transaction processing, KYC, and payouts does not exist in the fully open-source ecosystem. Most payment providers are either:
- commercial products with no-code SaaS pricing
- self-hosted but not legally compliant for production payouts without banking integration
- free test/sandbox modes that still require vendor account creation

So the correct zero-cost strategy is:
1. Keep the payment provider abstraction generic.
2. Default to a local mock provider in development.
3. Switch only to a provider sandbox account when you need sample payment flows or formal testing.

## Default config

The project now defaults to:

PAYMENT_PROVIDER=mock
PAYMENT_CURRENCY=INR

This means the backend can run locally, simulate escrow and refund operations, and test the project logic without paying any vendor fees.

## When to add a real provider

A live provider is only needed when:
- You want payment flow testing with a sandbox account
- You need real webhook verification
- You want to support live payouts and settlement after validation

At that stage, use a provider like Razorpay test mode or Stripe test mode, but only after you have validated the business and technical model.

## Final recommendation

For the current phase, stay fully open-source and zero-cost by using:
- local AI through Ollama
- local Postgres via Docker
- free frontend hosting
- local/mock payment logic

This keeps costs at zero while still giving you a realistic product prototype.
