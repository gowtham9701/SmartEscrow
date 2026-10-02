# SmartEscrow: Free-Tier Deployment Guide

This guide explains how to deploy the project using free-tier hosting approaches without paying for the prototype.

## Frontend on Vercel

1. Sign in to https://vercel.com
2. Import the repository
3. Set project root to `frontend`
4. Framework preset: Next.js
5. Build command:
   ```bash
   npm install && npm run build
   ```
6. Output directory:
   ```bash
   .next
   ```
7. Add environment variable:
   ```env
   NEXT_PUBLIC_API_BASE_URL=https://<your-render-backend-url>
   ```
8. Deploy

## Backend on Render

1. Sign in to https://render.com
2. Create a new Web Service
3. Connect the GitHub repo
4. Use:
   - Build command: `pip install -r backend/requirements.txt`
   - Start command: `cd backend && gunicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables from `backend/.env.production.example`
6. Keep `PAYMENT_PROVIDER=mock` for the zero-cost prototype
7. Deploy

## Database options

### Option A: local Docker (free)

```bash
docker compose up -d postgres
```

### Option B: Neon free tier

1. Create a database at https://neon.tech
2. Copy the Postgres connection string
3. Put it into `DATABASE_URL`

Example:
```env
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname?sslmode=require
```

## Example Render environment variables

```env
ENV=production
APP_NAME=SmartEscrow
API_V1_PREFIX=/api/v1
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname?sslmode=require
JWT_SECRET_KEY=generate_a_long_random_secret
JWT_ALGORITHM=HS256
PAYMENT_PROVIDER=mock
PAYMENT_CURRENCY=INR
GITHUB_WEBHOOK_SECRET=random_secret
GITHUB_APP_TOKEN=ghp_your_token
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=deepseek-coder:6.7b
```

## Recommended free stack

- Frontend: Vercel
- Backend: Render
- Database: local Docker or Neon free tier
- AI: Ollama on Mac
- Payment: mock mode for prototype

## Final recommendation

Stay on local mock mode for as long as possible while you validate founder-market fit, user flow, and MVP viability. Only move to a real provider after you are ready for production compliance and live settlements.
