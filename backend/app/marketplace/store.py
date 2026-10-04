"""
SmartEscrow marketplace data store (PostgreSQL / Neon-backed, two-table model).

All persistence lives in two physical tables (see db.py): `users` and
`operations`. This module keeps the rich business logic for the two-sided
talent marketplace — users, jobs, applications, engagements, timesheets,
wallets, escrow holds (QuickRide-style fund blocking), a simulated card
payment gateway, payouts, and an activity trail — while delegating storage to
the document-style repository in db.py.
"""
from __future__ import annotations

import hashlib
import logging
import secrets
import threading
import uuid
from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.config import settings
from app.marketplace import ai, db, notifications

logger = logging.getLogger("smartescrow.store")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ago(**kwargs) -> str:
    return (datetime.now(timezone.utc) - timedelta(**kwargs)).isoformat(timespec="seconds")


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(8)
    digest = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, _ = stored.split("$", 1)
    except ValueError:
        return False
    return secrets.compare_digest(hash_password(password, salt), stored)


def create_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": user_id, "exp": expire, "scope": "marketplace"},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload.get("sub")
    except Exception:
        return None


def audit(actor_id: str | None, action: str, entity_type: str = "", entity_id: str = "", detail: dict | None = None) -> None:
    """Record an application operation (activity trail) in the operations table."""
    actor_name = ""
    if actor_id:
        u = db.user_get(actor_id)
        actor_name = u["full_name"] if u else ""
    category = action.split(".")[0] if "." in action else "general"
    db.op_insert("activity", {
        "id": _id("act"),
        "user_id": actor_id,
        "user_name": actor_name,
        "action": action,
        "category": category,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "details": detail or {},
        "created_at": _now(),
    }, actor=actor_id)


# --------------------------------------------------------------------------- #
# Serialization
# --------------------------------------------------------------------------- #
_JSON_USER_FIELDS = ("skills", "services", "experiences", "achievements", "portfolio", "languages")

_USER_DEFAULTS = {
    "firm_reg_number": None, "firm_work_email": None,
    "resume_text": None, "resume_url": None, "resume_filename": None, "resume_updated_at": None,
    "title": "", "headline": "", "bio": "", "location": "Remote", "country_code": "US",
    "hourly_rate_usd": None, "years_experience": None, "availability": None,
    "github_username": "", "company_name": None, "company_size": None, "industry": None,
    "website": None, "rating": 0.0, "completed_jobs": 0, "jobs_posted": 0, "avatar_hue": 210,
}


def _row_to_user(rec, public: bool = True) -> dict | None:
    if rec is None:
        return None
    u = dict(rec)
    for key, default in _USER_DEFAULTS.items():
        u.setdefault(key, default)
    for f in _JSON_USER_FIELDS:
        value = u.get(f)
        u[f] = value if isinstance(value, list) else ([] if f != "languages" else ["English"])
    if public:
        u.pop("password_hash", None)
    return u


def public_user(u: dict) -> dict:
    return {k: v for k, v in u.items() if k != "password_hash"}


def _row_to_job(rec) -> dict | None:
    if rec is None:
        return None
    j = dict(rec)
    sk = j.get("skills_required")
    j["skills_required"] = sk if isinstance(sk, list) else []
    aijson = j.get("ai")
    j["ai"] = aijson if isinstance(aijson, dict) else {}
    j["applicant_count"] = db.op_count("application", job_id=j["id"])
    return j


# --------------------------------------------------------------------------- #
# Users / auth
# --------------------------------------------------------------------------- #
def get_user(user_id: str) -> dict | None:
    return _row_to_user(db.user_get(user_id))


def _get_user_raw(user_id: str) -> dict | None:
    return _row_to_user(db.user_get(user_id), public=False)


def get_user_by_email(email: str) -> dict | None:
    return _row_to_user(db.user_find(email=email.lower()), public=False)


def get_user_by_username(username: str) -> dict | None:
    return _row_to_user(db.user_find(username=username.lower()), public=False)


def get_user_by_login(identifier: str) -> dict | None:
    ident = identifier.strip().lower()
    return get_user_by_username(ident) or get_user_by_email(ident)


def get_user_by_phone(phone: str) -> dict | None:
    return _row_to_user(db.user_find(phone=phone), public=False)


def create_user(email: str, password: str, full_name: str, role: str, **extra) -> dict:
    if get_user_by_email(email):
        raise ValueError("A user with this email already exists.")
    username = (extra.get("username") or email.split("@")[0]).lower()
    if get_user_by_username(username):
        raise ValueError("That username is already taken.")
    uid = _id("usr")
    hue = (hash(full_name) % 360 + 360) % 360
    is_freelancer = 1 if role == "contributor" else 0
    is_employer = 1 if role == "client" and int(extra.get("firm_verified", 0)) else 0
    active_mode = "employer" if role == "client" else "freelancer"
    record = {
        "id": uid,
        "email": email.lower(),
        "username": username,
        "phone": extra.get("phone", ""),
        "password_hash": hash_password(password),
        "full_name": full_name,
        "role": role,
        "active_mode": active_mode,
        "is_freelancer": is_freelancer,
        "is_employer": is_employer,
        "firm_verified": int(extra.get("firm_verified", 0)),
        "email_verified": int(extra.get("email_verified", 1)),
        "phone_verified": int(extra.get("phone_verified", 1)),
        "title": extra.get("title", "Independent Contributor" if role == "contributor" else ""),
        "headline": extra.get("headline", ""),
        "bio": extra.get("bio", ""),
        "location": extra.get("location", "Remote"),
        "country_code": extra.get("country_code", "US"),
        "hourly_rate_usd": extra.get("hourly_rate_usd", 55) if role == "contributor" else None,
        "years_experience": extra.get("years_experience", 1) if role == "contributor" else None,
        "availability": "available" if role == "contributor" else None,
        "github_username": extra.get("github_username", ""),
        "company_name": extra.get("company_name", full_name) if role == "client" else None,
        "company_size": extra.get("company_size", "1-10") if role == "client" else None,
        "industry": extra.get("industry", "Technology") if role == "client" else None,
        "website": extra.get("website", "") if role == "client" else None,
        "rating": 0.0,
        "completed_jobs": 0,
        "jobs_posted": 0,
        "avatar_hue": hue,
        "skills": extra.get("skills", []),
        "services": extra.get("services", []),
        "experiences": [],
        "achievements": [],
        "portfolio": [],
        "languages": ["English"],
        "created_at": _now(),
    }
    db.user_insert(record)
    ensure_wallet(uid)
    audit(uid, "user.register", "user", uid, {"role": role, "email": email.lower(), "username": username})
    return _get_user_raw(uid)


def _otp() -> str:
    return f"{secrets.randbelow(1000000):06d}"


def start_registration(username: str, email: str, phone: str, password: str,
                       full_name: str, role: str, **extra) -> dict:
    """Begin a registration: validate uniqueness, generate an email OTP."""
    username = (username or "").strip().lower()
    email = (email or "").strip().lower()
    phone = (phone or "").strip()
    if len(username) < 3:
        raise ValueError("Username must be at least 3 characters.")
    if not username.replace("_", "").replace(".", "").isalnum():
        raise ValueError("Username may only contain letters, numbers, dots and underscores.")
    if get_user_by_username(username):
        raise ValueError("That username is already taken.")
    if get_user_by_email(email):
        raise ValueError("An account with this email already exists.")
    if phone and get_user_by_phone(phone):
        raise ValueError("An account with this mobile number already exists.")

    # Clear any stale pending registrations for the same email/username.
    db.op_delete_where("pending_registration", email=email)
    db.op_delete_where("pending_registration", username=username)

    reg_id = _id("reg")
    email_otp = _otp()
    db.op_insert("pending_registration", {
        "id": reg_id,
        "username": username,
        "email": email,
        "phone": phone,
        "password_hash": hash_password(password),
        "full_name": full_name,
        "role": role,
        "title": extra.get("title", ""),
        "hourly_rate_usd": extra.get("hourly_rate_usd", 55),
        "company_name": extra.get("company_name", ""),
        "skills": extra.get("skills", []),
        "location": extra.get("location", "Remote"),
        "email_otp": email_otp,
        "attempts": 0,
        "created_at": _now(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_TTL_MINUTES)).isoformat(timespec="seconds"),
    })
    audit(None, "registration.start", "pending_registration", reg_id, {"email": email, "username": username})

    if settings.ENV != "production":
        logger.info("[DEV] Registration code for %s: %s", email, email_otp)

    mode = notifications.delivery_mode()
    result = {"registration_id": reg_id, "email": email, "phone": phone, "delivery": mode}
    if mode == "email":
        threading.Thread(
            target=notifications.send_registration_otp,
            args=(email, full_name, email_otp),
            daemon=True,
        ).start()
    if mode == "demo" or settings.ENV != "production":
        result["demo_email_otp"] = email_otp
    return result


def resend_registration_otp(reg_id: str) -> dict:
    reg = db.op_get(reg_id)
    if not reg:
        raise ValueError("Registration session expired. Please start again.")
    email_otp = _otp()
    db.op_update(reg_id, {"email_otp": email_otp, "attempts": 0})
    if settings.ENV != "production":
        logger.info("[DEV] Resent registration code for %s: %s", reg["email"], email_otp)
    mode = notifications.delivery_mode()
    result = {"registration_id": reg_id, "delivery": mode}
    if mode == "email":
        threading.Thread(
            target=notifications.send_registration_otp,
            args=(reg["email"], reg["full_name"], email_otp),
            daemon=True,
        ).start()
    if mode == "demo" or settings.ENV != "production":
        result["demo_email_otp"] = email_otp
    return result


def verify_registration(reg_id: str, email_otp: str, phone_otp: str = "") -> dict:
    reg = db.op_get(reg_id)
    if not reg:
        raise ValueError("Registration session expired. Please start again.")
    if datetime.fromisoformat(reg["expires_at"]) < datetime.now(timezone.utc):
        db.op_delete(reg_id)
        raise ValueError("OTP expired. Please start registration again.")
    if int(reg.get("attempts", 0)) >= 6:
        db.op_delete(reg_id)
        raise ValueError("Too many attempts. Please start registration again.")
    if str(email_otp).strip() != reg["email_otp"]:
        db.op_update(reg_id, {"attempts": int(reg.get("attempts", 0)) + 1})
        raise ValueError("Incorrect verification code.")

    user = create_user(
        email=reg["email"],
        password="",  # placeholder; overwrite hash below to reuse stored hash
        full_name=reg["full_name"],
        role=reg["role"],
        username=reg["username"],
        phone=reg["phone"],
        email_verified=1,
        phone_verified=1,
        title=reg.get("title", ""),
        hourly_rate_usd=reg.get("hourly_rate_usd", 55),
        company_name=reg.get("company_name", ""),
        skills=reg.get("skills", []),
        location=reg.get("location", "Remote"),
    )
    db.user_update(user["id"], {"password_hash": reg["password_hash"]})
    db.op_delete(reg_id)
    audit(user["id"], "registration.verified", "user", user["id"], {"email": reg["email"]})
    return _get_user_raw(user["id"])


def update_profile(user_id: str, updates: dict) -> dict:
    user = _get_user_raw(user_id)
    if not user:
        raise ValueError("User not found.")
    allowed = {
        "full_name", "title", "headline", "bio", "location", "hourly_rate_usd",
        "years_experience", "availability", "github_username", "company_name",
        "company_size", "industry", "website",
        "resume_text", "resume_url", "resume_filename",
        *_JSON_USER_FIELDS,
    }
    changes = {k: v for k, v in updates.items() if k in allowed and v is not None}
    if changes:
        db.user_update(user_id, changes)
        audit(user_id, "profile.update", "user", user_id, {"fields": list(updates.keys())})
    if updates.get("resume_text") or updates.get("resume_url"):
        db.user_update(user_id, {"is_freelancer": 1, "resume_updated_at": _now()})
    return _get_user_raw(user_id)


# --------------------------------------------------------------------------- #
# Profile mode: freelancer <-> employer
# --------------------------------------------------------------------------- #
def switch_mode(user_id: str, mode: str) -> dict:
    user = _get_user_raw(user_id)
    if not user:
        raise ValueError("User not found.")
    if mode not in ("freelancer", "employer"):
        raise ValueError("Invalid mode.")

    if mode == "employer":
        if not user.get("firm_verified"):
            return {"needs_firm": True, "user": public_user(user)}
        db.user_update(user_id, {"active_mode": "employer", "role": "client", "is_employer": 1})
    else:
        db.user_update(user_id, {"active_mode": "freelancer", "role": "contributor", "is_freelancer": 1})
    audit(user_id, "profile.switch_mode", "user", user_id, {"mode": mode})
    return {"needs_firm": False, "user": public_user(_get_user_raw(user_id))}


def register_firm(user_id: str, payload: dict) -> dict:
    user = _get_user_raw(user_id)
    if not user:
        raise ValueError("User not found.")
    firm_name = (payload.get("firm_name") or "").strip()
    reg_number = (payload.get("firm_reg_number") or "").strip()
    work_email = (payload.get("firm_work_email") or "").strip()
    if len(firm_name) < 2:
        raise ValueError("Please enter a valid company name.")
    if len(reg_number) < 4:
        raise ValueError("Please enter a valid business registration number.")
    if "@" not in work_email:
        raise ValueError("Please enter a valid work email.")

    db.user_update(user_id, {
        "company_name": firm_name,
        "company_size": payload.get("company_size", "1-10"),
        "industry": payload.get("industry", "Technology"),
        "website": payload.get("website", ""),
        "firm_reg_number": reg_number,
        "firm_work_email": work_email,
        "is_employer": 1,
        "firm_verified": 1,
        "active_mode": "employer",
        "role": "client",
    })
    audit(user_id, "firm.verified", "user", user_id, {"firm_name": firm_name, "reg_number": reg_number})
    return public_user(_get_user_raw(user_id))


# --------------------------------------------------------------------------- #
# Resume analysis (AI keyword extraction + job matching + recommendations)
# --------------------------------------------------------------------------- #
def _open_job_skill_pool() -> list[str]:
    pool: list[str] = []
    for j in list_jobs():
        pool.extend(j["skills_required"])
    return pool


def analyze_resume_text(text: str, current_skills: list[str] | None = None) -> dict:
    analysis = ai.analyze_resume(text)
    resume_skills = analysis["skills"]
    combined = list(dict.fromkeys([*(current_skills or []), *resume_skills]))

    matches = []
    for j in list_jobs():
        score = ai.match_score(combined, j["skills_required"], j["description"])
        missing = [s for s in j["skills_required"] if s.lower() not in {c.lower() for c in combined}]
        matches.append({
            "id": j["id"],
            "title": j["title"],
            "company_name": j["company_name"],
            "hourly_rate_min": j["hourly_rate_min"],
            "hourly_rate_max": j["hourly_rate_max"],
            "category": j["category"],
            "match_score": score,
            "missing_skills": missing[:4],
        })
    matches.sort(key=lambda m: m["match_score"], reverse=True)

    recommended_skills = ai.recommend_skills(combined, _open_job_skill_pool(), limit=6)

    return {
        "extracted_skills": resume_skills,
        "all_skills": combined,
        "summary": analysis["summary"],
        "seniority": analysis["seniority"],
        "years_experience": analysis["years_experience"],
        "keywords": analysis["keywords"],
        "top_matches": matches[:5],
        "recommended_skills": recommended_skills,
    }


def save_resume(user_id: str, text: str, filename: str = "") -> dict:
    user = _get_user_raw(user_id)
    if not user:
        raise ValueError("User not found.")
    analysis = analyze_resume_text(text, user.get("skills", []))
    db.user_update(user_id, {
        "resume_text": text,
        "resume_filename": filename or "resume.txt",
        "resume_updated_at": _now(),
        "skills": analysis["all_skills"],
        "is_freelancer": 1,
    })
    audit(user_id, "resume.analyzed", "user", user_id,
          {"filename": filename, "extracted": analysis["extracted_skills"]})
    return {"user": public_user(_get_user_raw(user_id)), "analysis": analysis}


def resume_insights(user_id: str) -> dict:
    user = _get_user_raw(user_id)
    if not user:
        raise ValueError("User not found.")
    text = user.get("resume_text")
    if not text:
        return {"has_resume": False}
    analysis = analyze_resume_text(text, user.get("skills", []))
    analysis["has_resume"] = True
    return analysis


# --------------------------------------------------------------------------- #
# Jobs
# --------------------------------------------------------------------------- #
def list_jobs(search: str = "", category: str = "", skill: str = "") -> list[dict]:
    jobs = [_row_to_job(r) for r in db.op_find("job", status="open")]
    if search:
        s = search.lower()
        jobs = [j for j in jobs if s in j["title"].lower() or s in (j["description"] or "").lower()
                or any(s in sk.lower() for sk in j["skills_required"])]
    if category:
        jobs = [j for j in jobs if (j["category"] or "").lower() == category.lower()]
    if skill:
        jobs = [j for j in jobs if any(skill.lower() == sk.lower() for sk in j["skills_required"])]
    return jobs


def get_job(job_id: str) -> dict | None:
    return _row_to_job(db.op_get(job_id))


def enrich_job(j: dict) -> dict:
    return j


def list_jobs_for_client(client_id: str) -> list[dict]:
    return [_row_to_job(r) for r in db.op_find("job", client_id=client_id)]


def create_job(client_id: str, payload: dict) -> dict:
    client = _get_user_raw(client_id)
    if not client:
        raise ValueError("Client not found.")
    jid = _id("job")
    title = payload.get("title", "Untitled role")
    desc = payload.get("description", "")
    skills = payload.get("skills_required", [])
    db.op_insert("job", {
        "id": jid,
        "client_id": client_id,
        "company_name": client.get("company_name") or client["full_name"],
        "title": title,
        "category": payload.get("category", "Engineering"),
        "description": desc,
        "skills_required": skills,
        "engagement_type": payload.get("engagement_type", "hourly"),
        "hourly_rate_min": payload.get("hourly_rate_min", 50),
        "hourly_rate_max": payload.get("hourly_rate_max", 100),
        "experience_level": payload.get("experience_level", "Senior"),
        "location": payload.get("location", "Remote"),
        "hours_per_week": payload.get("hours_per_week", 30),
        "duration": payload.get("duration", "3-6 months"),
        "status": "open",
        "ai": ai.analyze_job(title, desc, skills),
        "created_at": _now(),
    }, actor=client_id)
    db.user_update(client_id, {"jobs_posted": int(client.get("jobs_posted") or 0) + 1})
    audit(client_id, "job.create", "job", jid, {"title": title})
    return get_job(jid)


# --------------------------------------------------------------------------- #
# Talent
# --------------------------------------------------------------------------- #
def list_talent(search: str = "", skill: str = "") -> list[dict]:
    talent = [_row_to_user(u) for u in db.user_all() if int(u.get("is_freelancer") or 0) == 1]
    talent.sort(key=lambda u: u.get("rating") or 0, reverse=True)
    if search:
        s = search.lower()
        talent = [u for u in talent if s in u["full_name"].lower()
                  or s in (u.get("title") or "").lower()
                  or s in (u.get("bio") or "").lower()
                  or any(s in sk.lower() for sk in u.get("skills", []))]
    if skill:
        talent = [u for u in talent if any(skill.lower() == sk.lower() for sk in u.get("skills", []))]
    return talent


# --------------------------------------------------------------------------- #
# Applications
# --------------------------------------------------------------------------- #
def apply_to_job(job_id: str, contributor_id: str, rate: int, cover_letter: str) -> dict:
    if not get_job(job_id):
        raise ValueError("Job not found.")
    if db.op_one("application", job_id=job_id, contributor_id=contributor_id):
        raise ValueError("You have already applied to this job.")
    aid = _id("app")
    db.op_insert("application", {
        "id": aid,
        "job_id": job_id,
        "contributor_id": contributor_id,
        "proposed_hourly_rate": rate,
        "status": "submitted",
        "cover_letter": cover_letter,
        "created_at": _now(),
    }, actor=contributor_id, job=job_id)
    audit(contributor_id, "application.submit", "application", aid, {"job_id": job_id, "rate": rate})
    return _enrich_application(db.op_get(aid))


def _enrich_application(rec) -> dict:
    a = dict(rec)
    a["job"] = get_job(a["job_id"])
    a["contributor"] = get_user(a["contributor_id"])
    return a


def applications_for_contributor(contributor_id: str) -> list[dict]:
    return [_enrich_application(r) for r in db.op_find("application", contributor_id=contributor_id)]


def applications_for_client(client_id: str) -> list[dict]:
    job_ids = {j["id"] for j in db.op_find("job", client_id=client_id)}
    return [_enrich_application(a) for a in db.op_all("application") if a["job_id"] in job_ids]


def update_application_status(application_id: str, status: str) -> dict:
    row = db.op_get(application_id)
    if not row:
        raise ValueError("Application not found.")
    db.op_update(application_id, {"status": status})
    audit(None, "application.status", "application", application_id, {"status": status})
    if status == "hired":
        job = get_job(row["job_id"])
        existing = db.op_one("engagement", job_id=row["job_id"], contributor_id=row["contributor_id"])
        if job and not existing:
            eid = _id("eng")
            db.op_insert("engagement", {
                "id": eid,
                "job_id": job["id"],
                "client_id": job["client_id"],
                "contributor_id": row["contributor_id"],
                "title": job["title"],
                "hourly_rate": row["proposed_hourly_rate"],
                "hours_logged": 0,
                "status": "active",
                "started_at": _now(),
                "created_at": _now(),
            }, actor=row["contributor_id"], counter=job["client_id"], job=job["id"])
            audit(job["client_id"], "engagement.create", "engagement", eid,
                  {"contributor_id": row["contributor_id"], "rate": row["proposed_hourly_rate"]})
    return _enrich_application(db.op_get(application_id))


# --------------------------------------------------------------------------- #
# Engagements + timesheets
# --------------------------------------------------------------------------- #
def _enrich_engagement(rec) -> dict:
    e = dict(rec)
    e["client"] = get_user(e["client_id"])
    e["contributor"] = get_user(e["contributor_id"])
    e["total_billed"] = int(e.get("hours_logged") or 0) * int(e.get("hourly_rate") or 0)
    ts = db.op_find("timesheet", engagement_id=e["id"])
    e["timesheets"] = sorted(ts, key=lambda t: t.get("created_at") or "")
    holds = db.op_find("escrow_hold", engagement_id=e["id"], status="held")
    e["escrow_held"] = sum(h.get("amount_usd") or 0 for h in holds)
    return e


def engagements_for_user(user_id: str, role: str) -> list[dict]:
    key = "client_id" if role == "client" else "contributor_id"
    return [_enrich_engagement(r) for r in db.op_find("engagement", **{key: user_id})]


def log_hours(engagement_id: str, hours: int, note: str) -> dict:
    row = db.op_get(engagement_id)
    if not row:
        raise ValueError("Engagement not found.")
    tid = _id("ts")
    week_num = db.op_count("timesheet", engagement_id=engagement_id) + 1
    db.op_insert("timesheet", {
        "id": tid,
        "engagement_id": engagement_id,
        "week": f"Week {week_num}",
        "hours": hours,
        "note": note or "Logged hours",
        "created_at": _now(),
    })
    db.op_update(engagement_id, {"hours_logged": int(row.get("hours_logged") or 0) + hours})
    audit(row["contributor_id"], "timesheet.log", "engagement", engagement_id, {"hours": hours})
    return _enrich_engagement(db.op_get(engagement_id))


# --------------------------------------------------------------------------- #
# Wallets + escrow (QuickRide-style fund blocking)
# --------------------------------------------------------------------------- #
def ensure_wallet(user_id: str) -> dict:
    wallet = db.op_one("wallet", user_id=user_id)
    if wallet:
        return wallet
    wid = _id("wal")
    return db.op_insert("wallet", {
        "id": wid,
        "user_id": user_id,
        "available_balance": 0,
        "blocked_balance": 0,
        "currency": "USD",
        "created_at": _now(),
    }, actor=user_id)


def get_wallet(user_id: str) -> dict:
    return ensure_wallet(user_id)


def _wallet_tx(wallet: dict, user_id: str, tx_type: str, amount: float, ref: str = "", note: str = "") -> None:
    db.op_insert("wallet_txn", {
        "id": _id("wtx"),
        "wallet_id": wallet["id"],
        "user_id": user_id,
        "type": tx_type,
        "amount": amount,
        "available_after": wallet["available_balance"],
        "blocked_after": wallet["blocked_balance"],
        "ref": ref,
        "note": note,
        "created_at": _now(),
    }, actor=user_id, amount_cents=round(amount * 100))


def deposit_to_wallet(user_id: str, amount: float, gateway_ref: str, note: str = "Card deposit") -> dict:
    wallet = ensure_wallet(user_id)
    new_available = wallet["available_balance"] + amount
    db.op_update(wallet["id"], {"available_balance": new_available})
    wallet["available_balance"] = new_available
    _wallet_tx(wallet, user_id, "deposit", amount, gateway_ref, note)
    audit(user_id, "wallet.deposit", "wallet", wallet["id"], {"amount": amount, "gateway_ref": gateway_ref})
    return get_wallet(user_id)


def withdraw_from_wallet(user_id: str, amount: float) -> dict:
    wallet = ensure_wallet(user_id)
    if amount <= 0:
        raise ValueError("Amount must be positive.")
    if amount > wallet["available_balance"]:
        raise ValueError("Insufficient available balance.")
    new_available = wallet["available_balance"] - amount
    db.op_update(wallet["id"], {"available_balance": new_available})
    wallet["available_balance"] = new_available
    _wallet_tx(wallet, user_id, "withdrawal", -amount, _id("po"), "Payout to bank")
    audit(user_id, "wallet.withdraw", "wallet", wallet["id"], {"amount": amount})
    return get_wallet(user_id)


def fund_escrow(engagement_id: str, hours: int) -> dict:
    """Client blocks funds from available balance into escrow for an engagement."""
    eng = db.op_get(engagement_id)
    if not eng:
        raise ValueError("Engagement not found.")
    amount = hours * int(eng.get("hourly_rate") or 0)
    wallet = ensure_wallet(eng["client_id"])
    if amount > wallet["available_balance"]:
        raise ValueError("Insufficient wallet balance. Please top up your wallet first.")
    new_available = wallet["available_balance"] - amount
    new_blocked = wallet["blocked_balance"] + amount
    db.op_update(wallet["id"], {"available_balance": new_available, "blocked_balance": new_blocked})
    wallet["available_balance"] = new_available
    wallet["blocked_balance"] = new_blocked
    _wallet_tx(wallet, eng["client_id"], "escrow_block", -amount, engagement_id, f"Blocked for {hours}h of work")

    hid = _id("esc")
    db.op_insert("escrow_hold", {
        "id": hid,
        "engagement_id": engagement_id,
        "client_id": eng["client_id"],
        "contributor_id": eng["contributor_id"],
        "amount_usd": amount,
        "hours": hours,
        "status": "held",
        "created_at": _now(),
    }, actor=eng["contributor_id"], counter=eng["client_id"], amount_cents=round(amount * 100))
    pid = _id("pay")
    db.op_insert("payment", {
        "id": pid,
        "engagement_id": engagement_id,
        "client_id": eng["client_id"],
        "contributor_id": eng["contributor_id"],
        "amount_usd": amount,
        "type": "escrow_funded",
        "status": "in_escrow",
        "hours": hours,
        "gateway_ref": hid,
        "note": f"Escrow blocked — {hours}h",
        "created_at": _now(),
    }, actor=eng["contributor_id"], counter=eng["client_id"], amount_cents=round(amount * 100))
    audit(eng["client_id"], "escrow.fund", "engagement", engagement_id, {"amount": amount, "hours": hours, "hold_id": hid})
    return _enrich_engagement(db.op_get(engagement_id))


def release_payment(payment_id: str) -> dict:
    """Release blocked escrow from client to contributor wallet."""
    pay = db.op_get(payment_id)
    if not pay:
        raise ValueError("Payment not found.")
    if pay["status"] != "in_escrow":
        return _enrich_payment(pay)
    amount = pay["amount_usd"]

    client_wallet = ensure_wallet(pay["client_id"])
    new_blocked = max(0, client_wallet["blocked_balance"] - amount)
    db.op_update(client_wallet["id"], {"blocked_balance": new_blocked})
    client_wallet["blocked_balance"] = new_blocked
    _wallet_tx(client_wallet, pay["client_id"], "escrow_release", -amount, payment_id, "Released to contributor")

    contrib_wallet = ensure_wallet(pay["contributor_id"])
    new_available = contrib_wallet["available_balance"] + amount
    db.op_update(contrib_wallet["id"], {"available_balance": new_available})
    contrib_wallet["available_balance"] = new_available
    _wallet_tx(contrib_wallet, pay["contributor_id"], "earning", amount, payment_id, "Escrow payout received")

    db.op_update(payment_id, {"status": "completed", "type": "released"})
    if pay.get("gateway_ref"):
        db.op_update(pay["gateway_ref"], {"status": "released", "released_at": _now()})
    contrib = _get_user_raw(pay["contributor_id"])
    if contrib:
        db.user_update(pay["contributor_id"], {"completed_jobs": int(contrib.get("completed_jobs") or 0) + 1})
    audit(pay["client_id"], "escrow.release", "payment", payment_id,
          {"amount": amount, "contributor_id": pay["contributor_id"]})
    return _enrich_payment(db.op_get(payment_id))


def wallet_transactions(user_id: str, limit: int = 25) -> list[dict]:
    return db.op_find("wallet_txn", user_id=user_id)[:limit]


def wallet_summary(user_id: str) -> dict:
    wallet = ensure_wallet(user_id)
    return {
        "wallet": wallet,
        "transactions": wallet_transactions(user_id),
        "payment_methods": list_cards(user_id),
    }


# --------------------------------------------------------------------------- #
# Payment methods + simulated gateway
# --------------------------------------------------------------------------- #
_TEST_CARDS = {
    "4242424242424242": ("Visa", "success"),
    "4000056655665556": ("Visa", "success"),
    "5555555555554444": ("Mastercard", "success"),
    "5200828282828210": ("Mastercard", "success"),
    "378282246310005": ("Amex", "success"),
    "4000000000000002": ("Visa", "declined"),
    "4000000000009995": ("Visa", "insufficient_funds"),
}


def _luhn_ok(number: str) -> bool:
    digits = [int(d) for d in number if d.isdigit()]
    if len(digits) < 12:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def _card_brand(number: str) -> str:
    if number.startswith("4"):
        return "Visa"
    if number[:2] in {"51", "52", "53", "54", "55"} or number.startswith("2"):
        return "Mastercard"
    if number[:2] in {"34", "37"}:
        return "Amex"
    return "Card"


def add_card(user_id: str, number: str, exp_month: int, exp_year: int, holder_name: str) -> dict:
    digits = "".join(c for c in number if c.isdigit())
    if len(digits) < 12:
        raise ValueError("Invalid card number.")
    brand, _ = _TEST_CARDS.get(digits, (_card_brand(digits), "success"))
    cid = _id("pm")
    is_default = 0 if db.op_one("payment_method", user_id=user_id) else 1
    return db.op_insert("payment_method", {
        "id": cid,
        "user_id": user_id,
        "brand": brand,
        "last4": digits[-4:],
        "exp_month": exp_month,
        "exp_year": exp_year,
        "holder_name": holder_name,
        "is_default": is_default,
        "created_at": _now(),
    }, actor=user_id)


def list_cards(user_id: str) -> list[dict]:
    return db.op_find("payment_method", user_id=user_id)


def process_card_payment(user_id: str, amount: float, number: str, exp_month: int,
                         exp_year: int, cvv: str, pin: str, holder_name: str,
                         save_card: bool = True) -> dict:
    """Simulated payment gateway. Validates the card and funds the wallet."""
    digits = "".join(c for c in number if c.isdigit())
    if amount <= 0:
        return {"success": False, "status": "invalid_amount", "message": "Enter a valid amount."}
    if len(digits) < 12 or not (_luhn_ok(digits) or digits in _TEST_CARDS):
        return {"success": False, "status": "invalid_card", "message": "Invalid card number."}
    if not cvv or len(cvv) < 3:
        return {"success": False, "status": "invalid_cvv", "message": "Invalid CVV."}
    if not pin or len(pin) < 4:
        return {"success": False, "status": "invalid_pin", "message": "Enter your 4-digit PIN."}
    if pin == "0000":
        return {"success": False, "status": "pin_declined", "message": "Transaction declined by bank (PIN)."}

    brand, result = _TEST_CARDS.get(digits, (_card_brand(digits), "success"))
    if result == "declined":
        audit(user_id, "gateway.declined", "wallet", "", {"amount": amount, "last4": digits[-4:]})
        return {"success": False, "status": "declined", "message": "Your card was declined."}
    if result == "insufficient_funds":
        return {"success": False, "status": "insufficient_funds", "message": "Insufficient funds on card."}

    gateway_ref = f"ch_{uuid.uuid4().hex[:16]}"
    if save_card and not db.op_one("payment_method", user_id=user_id, last4=digits[-4:]):
        add_card(user_id, digits, exp_month, exp_year, holder_name)
    deposit_to_wallet(user_id, amount, gateway_ref, f"{brand} •••• {digits[-4:]} deposit")
    return {
        "success": True,
        "status": "succeeded",
        "message": "Payment successful.",
        "gateway_ref": gateway_ref,
        "brand": brand,
        "last4": digits[-4:],
        "amount": amount,
    }


# --------------------------------------------------------------------------- #
# Payments views
# --------------------------------------------------------------------------- #
def _enrich_payment(rec) -> dict:
    p = dict(rec)
    eng = db.op_get(p["engagement_id"]) if p.get("engagement_id") else None
    p["engagement_title"] = eng["title"] if eng else ""
    cu = get_user(p["contributor_id"])
    cl = get_user(p["client_id"])
    p["contributor_name"] = cu["full_name"] if cu else ""
    p["client_name"] = (cl.get("company_name") or cl["full_name"]) if cl else ""
    return p


def payments_for_user(user_id: str, role: str) -> list[dict]:
    key = "client_id" if role == "client" else "contributor_id"
    return [_enrich_payment(r) for r in db.op_find("payment", **{key: user_id})]


# --------------------------------------------------------------------------- #
# Recommendations + stats + activity trail
# --------------------------------------------------------------------------- #
def recommend_jobs_for(contributor_id: str, limit: int = 4) -> list[dict]:
    user = get_user(contributor_id)
    if not user or user["role"] != "contributor":
        return list_jobs()[:limit]
    scored = []
    for j in list_jobs():
        j = dict(j)
        j["match_score"] = ai.match_score(user.get("skills", []), j["skills_required"], j["description"])
        scored.append(j)
    scored.sort(key=lambda j: j["match_score"], reverse=True)
    return scored[:limit]


def recommend_talent_for(job_id: str, limit: int = 4) -> list[dict]:
    job = get_job(job_id)
    if not job:
        return list_talent()[:limit]
    scored = []
    for u in list_talent():
        u = dict(u)
        u["match_score"] = ai.match_score(u.get("skills", []), job["skills_required"], job["description"])
        scored.append(u)
    scored.sort(key=lambda u: u["match_score"], reverse=True)
    return scored[:limit]


def platform_stats() -> dict:
    users = db.user_all()
    payments = db.op_all("payment")
    return {
        "open_jobs": db.op_count("job", status="open"),
        "contributors": len([u for u in users if u.get("role") == "contributor"]),
        "clients": len([u for u in users if u.get("role") == "client"]),
        "active_engagements": db.op_count("engagement", status="active"),
        "total_paid_out": sum(p.get("amount_usd") or 0 for p in payments if p.get("status") == "completed"),
        "in_escrow": sum(p.get("amount_usd") or 0 for p in payments if p.get("status") == "in_escrow"),
    }


def audit_for_user(user_id: str, limit: int = 30) -> list[dict]:
    rows = db.op_find("activity", user_id=user_id)[:limit]
    out = []
    for r in rows:
        d = dict(r)
        d["detail"] = r.get("details", {}) or {}
        out.append(d)
    return out


# Import seed at the bottom to avoid circulars, then run it once.
from app.marketplace.seed import seed_if_empty  # noqa: E402

seed_if_empty()
