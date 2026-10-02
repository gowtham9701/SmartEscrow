from fastapi import APIRouter

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def dashboard_summary():
    return {
        "kpis": {
            "total_value_locked": 1842500,
            "active_projects": 27,
            "completion_rate": 86,
            "disputes_open": 4,
            "verification_score": 92,
            "payout_latency_hours": 18,
        },
        "revenueTrend": [
            {"month": "Jan", "value": 110000},
            {"month": "Feb", "value": 128000},
            {"month": "Mar", "value": 141000},
            {"month": "Apr", "value": 155000},
            {"month": "May", "value": 173000},
            {"month": "Jun", "value": 188000},
        ],
        "pipeline": [
            {"name": "Design Systems", "value": 34, "fill": "#38bdf8"},
            {"name": "AI Integration", "value": 27, "fill": "#22c55e"},
            {"name": "Security Audit", "value": 18, "fill": "#f59e0b"},
            {"name": "API Migration", "value": 21, "fill": "#a78bfa"},
        ],
        "activity": [
            {"title": "Milestone 3 approved", "time": "2h ago", "status": "success"},
            {"title": "GitHub merge webhook released escrow", "time": "4h ago", "status": "success"},
            {"title": "Jury dispute queued for review", "time": "7h ago", "status": "warning"},
            {"title": "New client onboarding complete", "time": "1d ago", "status": "info"},
        ],
        "compliance": [
            {"name": "KYC", "value": 96, "color": "#22c55e"},
            {"name": "Tax docs", "value": 91, "color": "#38bdf8"},
            {"name": "AML review", "value": 88, "color": "#f59e0b"},
        ],
        "projects": [
            {"id": "PRJ-1042", "name": "AI Ops Portal", "client": "Apex Labs", "status": "In Progress", "progress": 72, "value": 42000},
            {"id": "PRJ-1109", "name": "Security Hardening", "client": "Northlane", "status": "Escrow Released", "progress": 100, "value": 28600},
            {"id": "PRJ-1172", "name": "Frontend Modernization", "client": "NovaWorks", "status": "Review", "progress": 58, "value": 31250},
        ],
    }
