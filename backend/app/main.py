"""
SmartEscrow FastAPI application entrypoint.
Run locally (zero cloud dependency):
    uvicorn app.main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import assessments, milestones, webhooks
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="Algorithmic B2B Infrastructure for Tech Talent — strict USD fiat escrow, no crypto.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(assessments.router, prefix=settings.API_V1_PREFIX)
app.include_router(milestones.router, prefix=settings.API_V1_PREFIX)
app.include_router(webhooks.router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENV}
