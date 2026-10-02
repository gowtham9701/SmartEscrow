from datetime import datetime, timedelta

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class DemoPaymentRequest(BaseModel):
    amount_minor: int
    payment_type: str = "deposit"
    note: str = "Demo escrow transaction"


_MOCK_PAYMENTS = [
    {
        "id": "TXN-1001",
        "type": "deposit",
        "status": "success",
        "amount_minor": 125000,
        "currency": "INR",
        "note": "Milestone 3 deposit",
        "created_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(timespec="seconds") + "Z",
    },
    {
        "id": "TXN-1002",
        "type": "release",
        "status": "success",
        "amount_minor": 98000,
        "currency": "INR",
        "note": "Approved GitHub merge payout",
        "created_at": (datetime.utcnow() - timedelta(days=1)).isoformat(timespec="seconds") + "Z",
    },
    {
        "id": "TXN-1003",
        "type": "stake_lock",
        "status": "success",
        "amount_minor": 2500,
        "currency": "INR",
        "note": "Integrity stake locked",
        "created_at": (datetime.utcnow() - timedelta(days=2)).isoformat(timespec="seconds") + "Z",
    },
]


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
        "mock_payments": _MOCK_PAYMENTS,
    }


@router.get("/mock-payments")
async def mock_payments():
    return {"transactions": _MOCK_PAYMENTS}


@router.post("/demo-payment")
async def create_demo_payment(payload: DemoPaymentRequest):
    tx = {
        "id": f"TXN-{len(_MOCK_PAYMENTS) + 1001}",
        "type": payload.payment_type,
        "status": "success",
        "amount_minor": payload.amount_minor,
        "currency": "INR",
        "note": payload.note,
        "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
    _MOCK_PAYMENTS.insert(0, tx)
    return {"status": "success", "transaction": tx}
