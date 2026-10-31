# -*- coding: utf-8 -*-
"""
Functional tests for the SmartEscrow marketplace features.

These tests exercise the core business logic in app.marketplace.store against a
real PostgreSQL database (configured via DATABASE_URL). They cover registration,
escrow, disputes, fiat-staking, the GitHub merge handler and reputation.

Run with:  DATABASE_URL=postgresql+asyncpg://postgres@localhost:5433/smartescrow \
           ../.venv/bin/python -m pytest app/tests/test_marketplace.py -q
"""
import os
import uuid

os.environ.setdefault("ENV", "local")
os.environ.setdefault("OTP_DELIVERY", "demo")

from app.marketplace import store, db  # noqa: E402


def _uniq(prefix: str) -> str:
    return f"{prefix}{uuid.uuid4().hex[:8]}"


def _new_contributor():
    u = _uniq("c")
    s = store.start_registration(username=u, email=f"{u}@test.io", phone=f"+1{uuid.uuid4().int % 10**10:010d}",
                                 password="Password123!", full_name="Test Contributor", role="contributor")
    return store.verify_registration(s["registration_id"], s["demo_email_otp"])


def _new_client():
    u = _uniq("cl")
    return store.create_user(email=f"{u}@test.io", password="Password123!", full_name="Test Client",
                             role="client", username=u, firm_verified=1)


def _funded_engagement(rate=70):
    client = _new_client()
    contrib = _new_contributor()
    store.deposit_to_wallet(client["id"], 5000, "ch_test", "seed")
    job = store.create_job(client["id"], {"title": "T", "description": "d", "skills_required": ["Python"],
                                           "hourly_rate_min": 50, "hourly_rate_max": 90})
    app = store.apply_to_job(job["id"], contrib["id"], rate, "cover")
    store.update_application_status(app["id"], "hired")
    eng = [e for e in store.engagements_for_user(contrib["id"], "contributor") if e["job_id"] == job["id"]][0]
    return client, contrib, job, eng


def test_registration_and_login():
    c = _new_contributor()
    assert c["email_verified"] == 1
    found = store.get_user_by_login(c["username"])
    assert found and found["id"] == c["id"]
    raw = store._get_user_raw(c["id"])
    assert store.verify_password("Password123!", raw["password_hash"])


def test_escrow_block_and_release():
    client, contrib, job, eng = _funded_engagement()
    store.fund_escrow(eng["id"], 10)
    pay = [p for p in store.payments_for_user(client["id"], "client") if p["status"] == "in_escrow"][0]
    before = store.get_wallet(contrib["id"])["available_balance"]
    store.release_payment(pay["id"])
    after = store.get_wallet(contrib["id"])["available_balance"]
    assert round(after - before, 2) == 700.0


def test_application_stake_held_and_refunded():
    client = _new_client()
    contrib = _new_contributor()
    store.deposit_to_wallet(contrib["id"], 500, "ch", "seed")
    job = store.create_job(client["id"], {"title": "S", "description": "d", "skills_required": ["Go"],
                                           "hourly_rate_min": 50, "hourly_rate_max": 90})
    before = store.get_wallet(contrib["id"])["available_balance"]
    app = store.apply_to_job(job["id"], contrib["id"], 60, "c")
    held = store.get_wallet(contrib["id"])
    assert held.get("staked_balance") == 10.0
    assert round(before - held["available_balance"], 2) == 10.0
    store.update_application_status(app["id"], "rejected")
    after = store.get_wallet(contrib["id"])
    assert after.get("staked_balance") == 0
    assert round(after["available_balance"], 2) == round(before, 2)


def test_dispute_refund_verdict():
    client, contrib, job, eng = _funded_engagement()
    store.fund_escrow(eng["id"], 10)
    d = store.raise_dispute(client["id"], eng["id"], "Not delivered")
    jurors = db.op_get(d["id"])["jurors"]
    assert len(jurors) == 3
    assert client["id"] not in jurors and contrib["id"] not in jurors
    before = store.get_wallet(client["id"])["available_balance"]
    store.cast_vote(d["id"], jurors[0], "refund")
    store.cast_vote(d["id"], jurors[1], "refund")
    resolved = db.op_get(d["id"])
    assert resolved["status"] == "resolved" and resolved["verdict"] == "refund"
    after = store.get_wallet(client["id"])["available_balance"]
    assert round(after - before, 2) == 700.0


def test_dispute_blind_jury_anonymizes_parties():
    client, contrib, job, eng = _funded_engagement()
    store.fund_escrow(eng["id"], 10)
    d = store.raise_dispute(contrib["id"], eng["id"], "Client withholding")
    jurors = db.op_get(d["id"])["jurors"]
    view = store._enrich_dispute(db.op_get(d["id"]), viewer_id=jurors[0])
    assert view["raised_by"] == "Party A" and view["against"] == "Party B"
    assert "client_id" not in view


def test_github_merge_releases_escrow():
    client, contrib, job, eng = _funded_engagement()
    repo = _uniq("acme/repo-")
    store.fund_escrow(eng["id"], 10, repo=repo)
    before = store.get_wallet(contrib["id"])["available_balance"]
    res = store.process_github_merge(repo, delivery_id=_uniq("d"), branch="main")
    assert res["status"] == "processed" and len(res["payments_released"]) == 1
    after = store.get_wallet(contrib["id"])["available_balance"]
    assert round(after - before, 2) == 700.0


def test_github_merge_is_idempotent():
    client, contrib, job, eng = _funded_engagement()
    repo = _uniq("acme/idem-")
    store.fund_escrow(eng["id"], 10, repo=repo)
    delivery = _uniq("d")
    store.process_github_merge(repo, delivery_id=delivery, branch="main")
    res2 = store.process_github_merge(repo, delivery_id=delivery, branch="main")
    assert res2["status"] == "already_processed"


def test_reputation_score_present():
    c = _new_contributor()
    pub = store.get_user(c["id"])
    assert "reputation" in pub and 0 <= pub["reputation"] <= 100


def test_analytics_shape():
    an = store.platform_analytics()
    for key in ("total_users", "verified_contributors", "disputes_total",
                "total_staked_held", "refunded_escrow"):
        assert key in an
