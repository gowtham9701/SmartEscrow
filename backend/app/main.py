"""
SmartEscrow FastAPI application entrypoint.
Run locally (zero cloud dependency):
    uvicorn app.main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import assessments, auth, dashboard, milestones, webhooks
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="Algorithmic B2B Infrastructure for Tech Talent — fiat escrow with INR settlement and secure automated milestone workflows.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.vercel\.app|https://.*\.netlify\.app|http://localhost:3000|http://127.0.0.1:3000",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(assessments.router, prefix=settings.API_V1_PREFIX)
app.include_router(milestones.router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard.router, prefix=settings.API_V1_PREFIX)
app.include_router(webhooks.router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENV}
