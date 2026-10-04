"""
SmartEscrow marketplace data store (SQLite-backed).

Provides all persistence and business logic for the two-sided talent
marketplace: users, jobs, applications, engagements, timesheets, wallets,
escrow holds (QuickRide-style fund blocking), a simulated card payment gateway,
payouts, and a full audit trail. Seeds a rich demo dataset on first run.
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
    """Record an application operation in the operations table (full audit trail)."""
    actor_name = ""
    if actor_id:
        row = db.query_one("SELECT full_name FROM users WHERE id = ?", (actor_id,))
        actor_name = row["full_name"] if row else ""
    category = action.split(".")[0] if "." in action else "general"
    db.execute(
        "INSERT INTO operations (user_id, user_name, action, category, entity_type, entity_id, details, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (actor_id, actor_name, action, category, entity_type, entity_id, db.dumps(detail or {}), _now()),
    )


# --------------------------------------------------------------------------- #
# Serialization
# --------------------------------------------------------------------------- #
_JSON_USER_FIELDS = ("skills", "services", "experiences", "achievements", "portfolio", "languages")


def _row_to_user(row, public: bool = True) -> dict:
    if row is None:
        return None
    u = dict(row)
    for f in _JSON_USER_FIELDS:
        u[f] = db.loads(u.get(f), [])
    if public:
        u.pop("password_hash", None)
    return u


def public_user(u: dict) -> dict:
    return {k: v for k, v in u.items() if k != "password_hash"}


def _row_to_job(row) -> dict:
    j = dict(row)
    j["skills_required"] = db.loads(j.get("skills_required"), [])
    j["ai"] = db.loads(j.get("ai"), {})
    j["applicant_count"] = db.query_one(
        "SELECT COUNT(*) c FROM applications WHERE job_id = ?", (j["id"],)
    )["c"]
    return j


# --------------------------------------------------------------------------- #
# Users / auth
# --------------------------------------------------------------------------- #
def get_user(user_id: str) -> dict | None:
    row = db.query_one("SELECT * FROM users WHERE id = ?", (user_id,))
    return _row_to_user(row) if row else None


def _get_user_raw(user_id: str) -> dict | None:
    row = db.query_one("SELECT * FROM users WHERE id = ?", (user_id,))
    return _row_to_user(row, public=False) if row else None


def get_user_by_email(email: str) -> dict | None:
    row = db.query_one("SELECT * FROM users WHERE email = ?", (email.lower(),))
    return _row_to_user(row, public=False) if row else None


def get_user_by_username(username: str) -> dict | None:
    row = db.query_one("SELECT * FROM users WHERE username = ?", (username.lower(),))
    return _row_to_user(row, public=False) if row else None


def get_user_by_login(identifier: str) -> dict | None:
    """Look up a user by username or email."""
    ident = identifier.strip().lower()
    return get_user_by_username(ident) or get_user_by_email(ident)


def get_user_by_phone(phone: str) -> dict | None:
    row = db.query_one("SELECT * FROM users WHERE phone = ?", (phone,))
    return _row_to_user(row, public=False) if row else None


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
    db.execute(
        """INSERT INTO users (
            id, email, username, phone, password_hash, full_name, role,
            active_mode, is_freelancer, is_employer, firm_verified,
            email_verified, phone_verified, title, headline, bio, location,
            country_code, hourly_rate_usd, years_experience, availability, github_username,
            company_name, company_size, industry, website, rating, completed_jobs,
            jobs_posted, avatar_hue, skills, services, experiences, achievements, portfolio,
            languages, created_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            uid, email.lower(), username, extra.get("phone", ""), hash_password(password), full_name, role,
            active_mode, is_freelancer, is_employer, int(extra.get("firm_verified", 0)),
            int(extra.get("email_verified", 1)), int(extra.get("phone_verified", 1)),
            extra.get("title", "Independent Contributor" if role == "contributor" else ""),
            extra.get("headline", ""), extra.get("bio", ""), extra.get("location", "Remote"),
            extra.get("country_code", "US"),
            extra.get("hourly_rate_usd", 55) if role == "contributor" else None,
            extra.get("years_experience", 1) if role == "contributor" else None,
            "available" if role == "contributor" else None,
            extra.get("github_username", ""),
            extra.get("company_name", full_name) if role == "client" else None,
            extra.get("company_size", "1-10") if role == "client" else None,
            extra.get("industry", "Technology") if role == "client" else None,
            extra.get("website", "") if role == "client" else None,
            0.0, 0, 0, hue,
            db.dumps(extra.get("skills", [])), db.dumps(extra.get("services", [])),
            db.dumps([]), db.dumps([]), db.dumps([]), db.dumps(["English"]),
            _now(),
        ),
    )
    ensure_wallet(uid)
    audit(uid, "user.register", "user", uid, {"role": role, "email": email.lower(), "username": username})
    return _get_user_raw(uid)


def _otp() -> str:
    return f"{secrets.randbelow(1000000):06d}"


def start_registration(username: str, email: str, phone: str, password: str,
                       full_name: str, role: str, **extra) -> dict:
    """Begin a registration: validate uniqueness, generate email + phone OTPs."""
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
    db.execute("DELETE FROM pending_registrations WHERE email = ? OR username = ?", (email, username))

    reg_id = _id("reg")
    email_otp = _otp()
    db.execute(
        """INSERT INTO pending_registrations (
            id, username, email, phone, password_hash, full_name, role, title,
            hourly_rate_usd, company_name, skills, location, email_otp, phone_otp,
            email_verified, phone_verified, attempts, created_at, expires_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            reg_id, username, email, phone, hash_password(password), full_name, role,
            extra.get("title", ""), extra.get("hourly_rate_usd", 55),
            extra.get("company_name", ""), db.dumps(extra.get("skills", [])),
            extra.get("location", "Remote"), email_otp, "", 0, 1, 0,
            _now(), (datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_TTL_MINUTES)).isoformat(timespec="seconds"),
        ),
    )
    audit(None, "registration.start", "pending_registration", reg_id, {"email": email, "username": username})

    # Dev aid: in local/non-production, log the code to the backend console so the
    # flow can be tested without a configured email provider. Never logs in prod.
    if settings.ENV != "production":
        logger.info("[DEV] Registration code for %s: %s", email, email_otp)

    # Deliver the single email code. Email is sent in the background so the
    # request returns instantly (no waiting on SMTP). Demo mode returns the code.
    mode = notifications.delivery_mode()
    result = {
        "registration_id": reg_id,
        "email": email,
        "phone": phone,
        "delivery": mode,
    }
    if mode == "email":
        threading.Thread(
            target=notifications.send_registration_otp,
            args=(email, full_name, email_otp),
            daemon=True,
        ).start()
    # Expose the code only in non-production so testers can read it from the
    # browser console (it is never rendered in the UI). Never exposed in prod.
    if mode == "demo" or settings.ENV != "production":
        result["demo_email_otp"] = email_otp
    return result


def resend_registration_otp(reg_id: str) -> dict:
    row = db.query_one("SELECT * FROM pending_registrations WHERE id = ?", (reg_id,))
    if not row:
        raise ValueError("Registration session expired. Please start again.")
    reg = dict(row)
    email_otp = _otp()
    db.execute(
        "UPDATE pending_registrations SET email_otp = ?, attempts = 0 WHERE id = ?",
        (email_otp, reg_id),
    )
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
    row = db.query_one("SELECT * FROM pending_registrations WHERE id = ?", (reg_id,))
    if not row:
        raise ValueError("Registration session expired. Please start again.")
    reg = dict(row)
    if datetime.fromisoformat(reg["expires_at"]) < datetime.now(timezone.utc):
        db.execute("DELETE FROM pending_registrations WHERE id = ?", (reg_id,))
        raise ValueError("OTP expired. Please start registration again.")
    if reg["attempts"] >= 6:
        db.execute("DELETE FROM pending_registrations WHERE id = ?", (reg_id,))
        raise ValueError("Too many attempts. Please start registration again.")
    if str(email_otp).strip() != reg["email_otp"]:
        db.execute("UPDATE pending_registrations SET attempts = attempts + 1 WHERE id = ?", (reg_id,))
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
        title=reg["title"],
        hourly_rate_usd=reg["hourly_rate_usd"],
        company_name=reg["company_name"],
        skills=db.loads(reg["skills"], []),
        location=reg["location"],
    )
    # Reuse the password hash captured at start (so the user's chosen password works).
    db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (reg["password_hash"], user["id"]))
    db.execute("DELETE FROM pending_registrations WHERE id = ?", (reg_id,))
    audit(user["id"], "registration.verified", "user", user["id"], {"email": reg["email"]})
    return _get_user_raw(user["id"])


def update_profile(user_id: str, updates: dict) -> dict:
    user = _get_user_raw(user_id)
    if not user:
        raise ValueError("User not found.")
    scalar = {
        "full_name", "title", "headline", "bio", "location", "hourly_rate_usd",
        "years_experience", "availability", "github_username", "company_name",
        "company_size", "industry", "website",
        "resume_text", "resume_url", "resume_filename",
    }
    json_fields = set(_JSON_USER_FIELDS)
    sets, params = [], []
    for key, value in updates.items():
        if value is None:
            continue
        if key in scalar:
            sets.append(f"{key} = ?")
            params.append(value)
        elif key in json_fields:
            sets.append(f"{key} = ?")
            params.append(db.dumps(value))
    if sets:
        params.append(user_id)
        db.execute(f"UPDATE users SET {', '.join(sets)} WHERE id = ?", tuple(params))
        audit(user_id, "profile.update", "user", user_id, {"fields": list(updates.keys())})
    # Setting resume enables freelancer capability.
    if updates.get("resume_text") or updates.get("resume_url"):
        db.execute(
            "UPDATE users SET is_freelancer = 1, resume_updated_at = ? WHERE id = ?",
            (_now(), user_id),
        )
    return _get_user_raw(user_id)


# --------------------------------------------------------------------------- #
# Profile mode: freelancer <-> employer
# --------------------------------------------------------------------------- #
def switch_mode(user_id: str, mode: str) -> dict:
    """Switch the active profile mode. Employer requires a verified firm."""
    user = _get_user_raw(user_id)
    if not user:
        raise ValueError("User not found.")
    if mode not in ("freelancer", "employer"):
        raise ValueError("Invalid mode.")

    if mode == "employer":
        if not user.get("firm_verified"):
            return {"needs_firm": True, "user": public_user(user)}
        db.execute(
            "UPDATE users SET active_mode = 'employer', role = 'client', is_employer = 1 WHERE id = ?",
            (user_id,),
        )
    else:
        db.execute(
            "UPDATE users SET active_mode = 'freelancer', role = 'contributor', is_freelancer = 1 WHERE id = ?",
            (user_id,),
        )
    audit(user_id, "profile.switch_mode", "user", user_id, {"mode": mode})
    return {"needs_firm": False, "user": public_user(_get_user_raw(user_id))}


def register_firm(user_id: str, payload: dict) -> dict:
    """Separate firm registration + verification to unlock employer rights."""
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

    db.execute(
        """UPDATE users SET
            company_name = ?, company_size = ?, industry = ?, website = ?,
            firm_reg_number = ?, firm_work_email = ?,
            is_employer = 1, firm_verified = 1, active_mode = 'employer', role = 'client'
        WHERE id = ?""",
        (
            firm_name, payload.get("company_size", "1-10"), payload.get("industry", "Technology"),
            payload.get("website", ""), reg_number, work_email, user_id,
        ),
    )
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
    """Run AI extraction on resume text and build job matches + recommendations."""
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
    """Store resume text, extract skills, merge into profile, return AI analysis."""
    user = _get_user_raw(user_id)
    if not user:
        raise ValueError("User not found.")
    analysis = analyze_resume_text(text, user.get("skills", []))
    db.execute(
        """UPDATE users SET resume_text = ?, resume_filename = ?, resume_updated_at = ?,
            skills = ?, is_freelancer = 1 WHERE id = ?""",
        (text, filename or "resume.txt", _now(), db.dumps(analysis["all_skills"]), user_id),
    )
    audit(user_id, "resume.analyzed", "user", user_id,
          {"filename": filename, "extracted": analysis["extracted_skills"]})
    return {"user": public_user(_get_user_raw(user_id)), "analysis": analysis}


def resume_insights(user_id: str) -> dict:
    """AI insights for the current user's stored resume (for dashboard)."""
    user = _get_user_raw(user_id)
    if not user:
        raise ValueError("User not found.")
    text = user.get("resume_text") or ""
    if not text:
        return {"has_resume": False}
    analysis = analyze_resume_text(text, user.get("skills", []))
    analysis["has_resume"] = True
    return analysis


# --------------------------------------------------------------------------- #
# Jobs
# --------------------------------------------------------------------------- #
def list_jobs(search: str = "", category: str = "", skill: str = "") -> list[dict]:
    rows = db.query_all("SELECT * FROM jobs WHERE status = 'open' ORDER BY created_at DESC")
    jobs = [_row_to_job(r) for r in rows]
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
    row = db.query_one("SELECT * FROM jobs WHERE id = ?", (job_id,))
    return _row_to_job(row) if row else None


def enrich_job(j: dict) -> dict:
    return j


def list_jobs_for_client(client_id: str) -> list[dict]:
    rows = db.query_all("SELECT * FROM jobs WHERE client_id = ? ORDER BY created_at DESC", (client_id,))
    return [_row_to_job(r) for r in rows]


def create_job(client_id: str, payload: dict) -> dict:
    client = _get_user_raw(client_id)
    if not client:
        raise ValueError("Client not found.")
    jid = _id("job")
    title = payload.get("title", "Untitled role")
    desc = payload.get("description", "")
    skills = payload.get("skills_required", [])
    db.execute(
        """INSERT INTO jobs (
            id, client_id, company_name, title, category, description, skills_required,
            engagement_type, hourly_rate_min, hourly_rate_max, experience_level, location,
            hours_per_week, duration, status, ai, created_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            jid, client_id, client.get("company_name") or client["full_name"], title,
            payload.get("category", "Engineering"), desc, db.dumps(skills),
            payload.get("engagement_type", "hourly"), payload.get("hourly_rate_min", 50),
            payload.get("hourly_rate_max", 100), payload.get("experience_level", "Senior"),
            payload.get("location", "Remote"), payload.get("hours_per_week", 30),
            payload.get("duration", "3-6 months"), "open",
            db.dumps(ai.analyze_job(title, desc, skills)), _now(),
        ),
    )
    db.execute("UPDATE users SET jobs_posted = jobs_posted + 1 WHERE id = ?", (client_id,))
    audit(client_id, "job.create", "job", jid, {"title": title})
    return get_job(jid)


# --------------------------------------------------------------------------- #
# Talent
# --------------------------------------------------------------------------- #
def list_talent(search: str = "", skill: str = "") -> list[dict]:
    rows = db.query_all("SELECT * FROM users WHERE is_freelancer = 1 ORDER BY rating DESC")
    talent = [_row_to_user(r) for r in rows]
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
    existing = db.query_one(
        "SELECT id FROM applications WHERE job_id = ? AND contributor_id = ?",
        (job_id, contributor_id),
    )
    if existing:
        raise ValueError("You have already applied to this job.")
    aid = _id("app")
    db.execute(
        "INSERT INTO applications (id, job_id, contributor_id, proposed_hourly_rate, status, cover_letter, created_at) "
        "VALUES (?,?,?,?,?,?,?)",
        (aid, job_id, contributor_id, rate, "submitted", cover_letter, _now()),
    )
    audit(contributor_id, "application.submit", "application", aid, {"job_id": job_id, "rate": rate})
    return _enrich_application(db.query_one("SELECT * FROM applications WHERE id = ?", (aid,)))


def _enrich_application(row) -> dict:
    a = dict(row)
    a["job"] = get_job(a["job_id"])
    a["contributor"] = get_user(a["contributor_id"])
    return a


def applications_for_contributor(contributor_id: str) -> list[dict]:
    rows = db.query_all(
        "SELECT * FROM applications WHERE contributor_id = ? ORDER BY created_at DESC",
        (contributor_id,),
    )
    return [_enrich_application(r) for r in rows]


def applications_for_client(client_id: str) -> list[dict]:
    rows = db.query_all(
        """SELECT a.* FROM applications a JOIN jobs j ON a.job_id = j.id
           WHERE j.client_id = ? ORDER BY a.created_at DESC""",
        (client_id,),
    )
    return [_enrich_application(r) for r in rows]


def update_application_status(application_id: str, status: str) -> dict:
    row = db.query_one("SELECT * FROM applications WHERE id = ?", (application_id,))
    if not row:
        raise ValueError("Application not found.")
    db.execute("UPDATE applications SET status = ? WHERE id = ?", (status, application_id))
    audit(None, "application.status", "application", application_id, {"status": status})
    if status == "hired":
        job = get_job(row["job_id"])
        existing = db.query_one(
            "SELECT id FROM engagements WHERE job_id = ? AND contributor_id = ?",
            (row["job_id"], row["contributor_id"]),
        )
        if job and not existing:
            eid = _id("eng")
            db.execute(
                "INSERT INTO engagements (id, job_id, client_id, contributor_id, title, hourly_rate, hours_logged, status, started_at) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (eid, job["id"], job["client_id"], row["contributor_id"], job["title"],
                 row["proposed_hourly_rate"], 0, "active", _now()),
            )
            db.execute(
                "UPDATE users SET completed_jobs = completed_jobs + 0 WHERE id = ?",
                (row["contributor_id"],),
            )
            audit(job["client_id"], "engagement.create", "engagement", eid,
                  {"contributor_id": row["contributor_id"], "rate": row["proposed_hourly_rate"]})
    return _enrich_application(db.query_one("SELECT * FROM applications WHERE id = ?", (application_id,)))


# --------------------------------------------------------------------------- #
# Engagements + timesheets
# --------------------------------------------------------------------------- #
def _enrich_engagement(row) -> dict:
    e = dict(row)
    e["client"] = get_user(e["client_id"])
    e["contributor"] = get_user(e["contributor_id"])
    e["total_billed"] = e["hours_logged"] * e["hourly_rate"]
    ts = db.query_all("SELECT * FROM timesheets WHERE engagement_id = ? ORDER BY created_at", (e["id"],))
    e["timesheets"] = [dict(t) for t in ts]
    hold = db.query_one(
        "SELECT COALESCE(SUM(amount_usd),0) s FROM escrow_holds WHERE engagement_id = ? AND status = 'held'",
        (e["id"],),
    )
    e["escrow_held"] = hold["s"] if hold else 0
    return e


def engagements_for_user(user_id: str, role: str) -> list[dict]:
    key = "client_id" if role == "client" else "contributor_id"
    rows = db.query_all(f"SELECT * FROM engagements WHERE {key} = ? ORDER BY started_at DESC", (user_id,))
    return [_enrich_engagement(r) for r in rows]


def log_hours(engagement_id: str, hours: int, note: str) -> dict:
    row = db.query_one("SELECT * FROM engagements WHERE id = ?", (engagement_id,))
    if not row:
        raise ValueError("Engagement not found.")
    tid = _id("ts")
    week_num = db.query_one(
        "SELECT COUNT(*) c FROM timesheets WHERE engagement_id = ?", (engagement_id,)
    )["c"] + 1
    db.execute(
        "INSERT INTO timesheets (id, engagement_id, week, hours, note, created_at) VALUES (?,?,?,?,?,?)",
        (tid, engagement_id, f"Week {week_num}", hours, note or "Logged hours", _now()),
    )
    db.execute("UPDATE engagements SET hours_logged = hours_logged + ? WHERE id = ?", (hours, engagement_id))
    audit(row["contributor_id"], "timesheet.log", "engagement", engagement_id, {"hours": hours})
    return _enrich_engagement(db.query_one("SELECT * FROM engagements WHERE id = ?", (engagement_id,)))


# --------------------------------------------------------------------------- #
# Wallets + escrow (QuickRide-style fund blocking)
# --------------------------------------------------------------------------- #
def ensure_wallet(user_id: str) -> dict:
    row = db.query_one("SELECT * FROM wallets WHERE user_id = ?", (user_id,))
    if row:
        return dict(row)
    wid = _id("wal")
    db.execute(
        "INSERT INTO wallets (id, user_id, available_balance, blocked_balance, currency, created_at) VALUES (?,?,?,?,?,?)",
        (wid, user_id, 0, 0, "USD", _now()),
    )
    return dict(db.query_one("SELECT * FROM wallets WHERE id = ?", (wid,)))


def get_wallet(user_id: str) -> dict:
    return ensure_wallet(user_id)


def _wallet_tx(wallet: dict, user_id: str, tx_type: str, amount: float, ref: str = "", note: str = "") -> None:
    db.execute(
        "INSERT INTO wallet_transactions (id, wallet_id, user_id, type, amount, available_after, blocked_after, ref, note, created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",
        (_id("wtx"), wallet["id"], user_id, tx_type, amount,
         wallet["available_balance"], wallet["blocked_balance"], ref, note, _now()),
    )


def deposit_to_wallet(user_id: str, amount: float, gateway_ref: str, note: str = "Card deposit") -> dict:
    wallet = ensure_wallet(user_id)
    new_available = wallet["available_balance"] + amount
    db.execute("UPDATE wallets SET available_balance = ? WHERE id = ?", (new_available, wallet["id"]))
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
    db.execute("UPDATE wallets SET available_balance = ? WHERE id = ?", (new_available, wallet["id"]))
    wallet["available_balance"] = new_available
    _wallet_tx(wallet, user_id, "withdrawal", -amount, _id("po"), "Payout to bank")
    audit(user_id, "wallet.withdraw", "wallet", wallet["id"], {"amount": amount})
    return get_wallet(user_id)


def fund_escrow(engagement_id: str, hours: int) -> dict:
    """Client blocks funds from available balance into escrow for an engagement."""
    eng = db.query_one("SELECT * FROM engagements WHERE id = ?", (engagement_id,))
    if not eng:
        raise ValueError("Engagement not found.")
    amount = hours * eng["hourly_rate"]
    wallet = ensure_wallet(eng["client_id"])
    if amount > wallet["available_balance"]:
        raise ValueError("Insufficient wallet balance. Please top up your wallet first.")
    # Move available -> blocked (the "block" that guarantees payment).
    new_available = wallet["available_balance"] - amount
    new_blocked = wallet["blocked_balance"] + amount
    db.execute(
        "UPDATE wallets SET available_balance = ?, blocked_balance = ? WHERE id = ?",
        (new_available, new_blocked, wallet["id"]),
    )
    wallet["available_balance"] = new_available
    wallet["blocked_balance"] = new_blocked
    _wallet_tx(wallet, eng["client_id"], "escrow_block", -amount, engagement_id, f"Blocked for {hours}h of work")

    hid = _id("esc")
    db.execute(
        "INSERT INTO escrow_holds (id, engagement_id, client_id, contributor_id, amount_usd, hours, status, created_at) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (hid, engagement_id, eng["client_id"], eng["contributor_id"], amount, hours, "held", _now()),
    )
    pid = _id("pay")
    db.execute(
        "INSERT INTO payments (id, engagement_id, client_id, contributor_id, amount_usd, type, status, hours, gateway_ref, note, created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (pid, engagement_id, eng["client_id"], eng["contributor_id"], amount, "escrow_funded", "in_escrow",
         hours, hid, f"Escrow blocked — {hours}h", _now()),
    )
    audit(eng["client_id"], "escrow.fund", "engagement", engagement_id, {"amount": amount, "hours": hours, "hold_id": hid})
    return _enrich_engagement(db.query_one("SELECT * FROM engagements WHERE id = ?", (engagement_id,)))


def release_payment(payment_id: str) -> dict:
    """Release blocked escrow from client to contributor wallet."""
    pay = db.query_one("SELECT * FROM payments WHERE id = ?", (payment_id,))
    if not pay:
        raise ValueError("Payment not found.")
    if pay["status"] != "in_escrow":
        return _enrich_payment(pay)
    amount = pay["amount_usd"]

    client_wallet = ensure_wallet(pay["client_id"])
    new_blocked = max(0, client_wallet["blocked_balance"] - amount)
    db.execute("UPDATE wallets SET blocked_balance = ? WHERE id = ?", (new_blocked, client_wallet["id"]))
    client_wallet["blocked_balance"] = new_blocked
    _wallet_tx(client_wallet, pay["client_id"], "escrow_release", -amount, payment_id, "Released to contributor")

    contrib_wallet = ensure_wallet(pay["contributor_id"])
    new_available = contrib_wallet["available_balance"] + amount
    db.execute("UPDATE wallets SET available_balance = ? WHERE id = ?", (new_available, contrib_wallet["id"]))
    contrib_wallet["available_balance"] = new_available
    _wallet_tx(contrib_wallet, pay["contributor_id"], "earning", amount, payment_id, "Escrow payout received")

    db.execute("UPDATE payments SET status = 'completed', type = 'released' WHERE id = ?", (payment_id,))
    if pay["gateway_ref"]:
        db.execute(
            "UPDATE escrow_holds SET status = 'released', released_at = ? WHERE id = ?",
            (_now(), pay["gateway_ref"]),
        )
    db.execute(
        "UPDATE users SET completed_jobs = completed_jobs + 1 WHERE id = ?",
        (pay["contributor_id"],),
    )
    audit(pay["client_id"], "escrow.release", "payment", payment_id,
          {"amount": amount, "contributor_id": pay["contributor_id"]})
    return _enrich_payment(db.query_one("SELECT * FROM payments WHERE id = ?", (payment_id,)))


def wallet_transactions(user_id: str, limit: int = 25) -> list[dict]:
    rows = db.query_all(
        "SELECT * FROM wallet_transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit),
    )
    return [dict(r) for r in rows]


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
    is_default = 0 if db.query_one("SELECT id FROM payment_methods WHERE user_id = ?", (user_id,)) else 1
    db.execute(
        "INSERT INTO payment_methods (id, user_id, brand, last4, exp_month, exp_year, holder_name, is_default, created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (cid, user_id, brand, digits[-4:], exp_month, exp_year, holder_name, is_default, _now()),
    )
    audit(user_id, "card.add", "payment_method", cid, {"brand": brand, "last4": digits[-4:]})
    return dict(db.query_one("SELECT * FROM payment_methods WHERE id = ?", (cid,)))


def list_cards(user_id: str) -> list[dict]:
    rows = db.query_all("SELECT * FROM payment_methods WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    return [dict(r) for r in rows]


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
    if save_card and not db.query_one(
        "SELECT id FROM payment_methods WHERE user_id = ? AND last4 = ?", (user_id, digits[-4:])
    ):
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
def _enrich_payment(row) -> dict:
    p = dict(row)
    eng = db.query_one("SELECT title FROM engagements WHERE id = ?", (p["engagement_id"],)) if p["engagement_id"] else None
    p["engagement_title"] = eng["title"] if eng else ""
    cu = db.query_one("SELECT full_name FROM users WHERE id = ?", (p["contributor_id"],))
    cl = db.query_one("SELECT company_name, full_name FROM users WHERE id = ?", (p["client_id"],))
    p["contributor_name"] = cu["full_name"] if cu else ""
    p["client_name"] = (cl["company_name"] or cl["full_name"]) if cl else ""
    return p


def payments_for_user(user_id: str, role: str) -> list[dict]:
    key = "client_id" if role == "client" else "contributor_id"
    rows = db.query_all(f"SELECT * FROM payments WHERE {key} = ? ORDER BY created_at DESC", (user_id,))
    return [_enrich_payment(r) for r in rows]


# --------------------------------------------------------------------------- #
# Recommendations + stats + audit
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
    def scalar(sql, params=()):
        return db.query_one(sql, params)["v"]
    return {
        "open_jobs": scalar("SELECT COUNT(*) v FROM jobs WHERE status = 'open'"),
        "contributors": scalar("SELECT COUNT(*) v FROM users WHERE role = 'contributor'"),
        "clients": scalar("SELECT COUNT(*) v FROM users WHERE role = 'client'"),
        "active_engagements": scalar("SELECT COUNT(*) v FROM engagements WHERE status = 'active'"),
        "total_paid_out": scalar("SELECT COALESCE(SUM(amount_usd),0) v FROM payments WHERE status = 'completed'"),
        "in_escrow": scalar("SELECT COALESCE(SUM(amount_usd),0) v FROM payments WHERE status = 'in_escrow'"),
    }


def audit_for_user(user_id: str, limit: int = 30) -> list[dict]:
    rows = db.query_all(
        "SELECT * FROM operations WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit)
    )
    out = []
    for r in rows:
        d = dict(r)
        d["detail"] = db.loads(d.get("details"), {})
        out.append(d)
    return out


# Import seed at the bottom to avoid circulars, then run it once.
from app.marketplace.seed import seed_if_empty  # noqa: E402

seed_if_empty()
