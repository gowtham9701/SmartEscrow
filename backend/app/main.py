"""
SmartEscrow FastAPI application entrypoint.
Run locally (zero cloud dependency):
    uvicorn app.main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import assessments, auth, dashboard, marketplace, milestones, webhooks
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="SmartEscrow — algorithmic B2B talent marketplace with AI vetting, hourly engagements, and automated USD escrow.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.vercel\.app|https://.*\.netlify\.app|http://localhost(:\d+)?|http://127\.0\.0\.1(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(assessments.router, prefix=settings.API_V1_PREFIX)
app.include_router(milestones.router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard.router, prefix=settings.API_V1_PREFIX)
app.include_router(webhooks.router, prefix=settings.API_V1_PREFIX)
app.include_router(marketplace.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "status": "live",
        "docs": "/docs",
        "health": "/health",
        "api": settings.API_V1_PREFIX,
    }


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENV}
