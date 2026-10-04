"""
SmartEscrow marketplace API.

A dependency-free, database-optional set of endpoints powering the two-sided
talent marketplace: auth, jobs, talent search, applications, engagements,
payment tracking, and AI summaries/recommendations.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, EmailStr, Field

from app.marketplace import ai, resume_parser, store

router = APIRouter(prefix="/market", tags=["marketplace"])


# --------------------------------------------------------------------------- #
# Schemas
# --------------------------------------------------------------------------- #
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2)
    role: str = Field("contributor", pattern="^(contributor|client)$")
    title: Optional[str] = None
    hourly_rate_usd: Optional[int] = None
    company_name: Optional[str] = None
    skills: Optional[list[str]] = None
    location: Optional[str] = None


class RegisterStartRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    phone: str = Field(..., min_length=6, max_length=20)
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2)
    role: str = Field("contributor", pattern="^(contributor|client)$")
    title: Optional[str] = None
    hourly_rate_usd: Optional[int] = None
    company_name: Optional[str] = None
    skills: Optional[list[str]] = None
    location: Optional[str] = None


class RegisterVerifyRequest(BaseModel):
    registration_id: str
    email_otp: str
    phone_otp: str = ""


class ResendOtpRequest(BaseModel):
    registration_id: str


class LoginRequest(BaseModel):
    identifier: Optional[str] = None
    email: Optional[str] = None
    password: str


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    title: Optional[str] = None
    headline: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    hourly_rate_usd: Optional[int] = None
    years_experience: Optional[int] = None
    availability: Optional[str] = None
    skills: Optional[list[str]] = None
    services: Optional[list[dict]] = None
    experiences: Optional[list[dict]] = None
    achievements: Optional[list[str]] = None
    portfolio: Optional[list[dict]] = None
    languages: Optional[list[str]] = None
    github_username: Optional[str] = None
    company_name: Optional[str] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    resume_text: Optional[str] = None
    resume_url: Optional[str] = None
    resume_filename: Optional[str] = None


class SwitchModeRequest(BaseModel):
    mode: str = Field(..., pattern="^(freelancer|employer)$")


class FirmRegisterRequest(BaseModel):
    firm_name: str = Field(..., min_length=2)
    firm_reg_number: str = Field(..., min_length=4)
    firm_work_email: str = Field(..., min_length=5)
    company_size: str = "1-10"
    industry: str = "Technology"
    website: str = ""


class JobCreate(BaseModel):
    title: str = Field(..., min_length=4)
    category: str = "Engineering"
    description: str = Field(..., min_length=10)
    skills_required: list[str] = []
    hourly_rate_min: int = 50
    hourly_rate_max: int = 100
    experience_level: str = "Senior"
    hours_per_week: int = 30
    duration: str = "3-6 months"
    location: str = "Remote"


class ApplyRequest(BaseModel):
    proposed_hourly_rate: int = Field(..., gt=0)
    cover_letter: str = Field("", max_length=4000)


class StatusUpdate(BaseModel):
    status: str


class LogHoursRequest(BaseModel):
    hours: int = Field(..., gt=0, le=168)
    note: str = ""


class SummarizeRequest(BaseModel):
    title: str = ""
    text: str


class ChargeRequest(BaseModel):
    amount: float = Field(..., gt=0)
    card_number: str
    exp_month: int = Field(..., ge=1, le=12)
    exp_year: int
    cvv: str
    pin: str
    holder_name: str = ""
    save_card: bool = True


class WithdrawRequest(BaseModel):
    amount: float = Field(..., gt=0)


class AddCardRequest(BaseModel):
    card_number: str
    exp_month: int = Field(..., ge=1, le=12)
    exp_year: int
    holder_name: str = ""


class FundEscrowRequest(BaseModel):
    hours: int = Field(..., gt=0, le=1000)


# --------------------------------------------------------------------------- #
# Auth dependency
# --------------------------------------------------------------------------- #
def get_current_user(authorization: Optional[str] = Header(default=None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    user_id = store.decode_token(token)
    user = store.get_user(user_id) if user_id else None
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return user


def _auth_response(user: dict) -> dict:
    return {
        "access_token": store.create_token(user["id"]),
        "token_type": "bearer",
        "user": store.public_user(user),
    }


# --------------------------------------------------------------------------- #
# Auth
# --------------------------------------------------------------------------- #
@router.post("/auth/register")
def register(payload: RegisterRequest):
    try:
        user = store.create_user(
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            role=payload.role,
            title=payload.title,
            hourly_rate_usd=payload.hourly_rate_usd or 60,
            company_name=payload.company_name,
            skills=payload.skills or [],
            location=payload.location or "Remote",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return _auth_response(user)


@router.post("/auth/register/start")
def register_start(payload: RegisterStartRequest):
    try:
        result = store.start_registration(
            username=payload.username,
            email=payload.email,
            phone=payload.phone,
            password=payload.password,
            full_name=payload.full_name,
            role=payload.role,
            title=payload.title or "",
            hourly_rate_usd=payload.hourly_rate_usd or 55,
            company_name=payload.company_name or "",
            skills=payload.skills or [],
            location=payload.location or "Remote",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return result


@router.post("/auth/register/verify")
def register_verify(payload: RegisterVerifyRequest):
    try:
        user = store.verify_registration(payload.registration_id, payload.email_otp, payload.phone_otp)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return _auth_response(user)


@router.post("/auth/register/resend")
def register_resend(payload: ResendOtpRequest):
    try:
        return store.resend_registration_otp(payload.registration_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/auth/login")
def login(payload: LoginRequest):
    identifier = payload.identifier or payload.email
    if not identifier:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email is required")
    user = store.get_user_by_login(identifier)
    if not user or not store.verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username/email or password")
    return _auth_response(user)


@router.get("/auth/me")
def me(user: dict = Depends(get_current_user)):
    return store.public_user(user)


@router.get("/auth/demo-users")
def demo_users():
    return {
        "contributor": {"email": "ava.chen@smartescrow.io", "password": "Password123!"},
        "client": {"email": "client@apexlabs.io", "password": "Password123!"},
    }


# --------------------------------------------------------------------------- #
# Profile
# --------------------------------------------------------------------------- #
@router.patch("/profile")
def update_profile(payload: ProfileUpdate, user: dict = Depends(get_current_user)):
    updated = store.update_profile(user["id"], payload.model_dump(exclude_none=True))
    return store.public_user(updated)


@router.post("/profile/switch-mode")
def switch_mode(payload: SwitchModeRequest, user: dict = Depends(get_current_user)):
    return store.switch_mode(user["id"], payload.mode)


@router.post("/profile/register-firm")
def register_firm(payload: FirmRegisterRequest, user: dict = Depends(get_current_user)):
    try:
        return store.register_firm(user["id"], payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/profile/resume-upload")
async def resume_upload(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5MB).")
    text = resume_parser.extract_text(file.filename or "resume.txt", data)
    if len(text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Could not read enough text from this file. Try a text-based PDF, DOCX, or paste the text.")
    return store.save_resume(user["id"], text, file.filename or "resume.txt")


class ResumeTextRequest(BaseModel):
    text: str = Field(..., min_length=20)
    filename: Optional[str] = None


@router.post("/profile/resume-text")
def resume_text(payload: ResumeTextRequest, user: dict = Depends(get_current_user)):
    return store.save_resume(user["id"], payload.text, payload.filename or "resume.txt")


@router.post("/ai/analyze-resume")
def analyze_resume(payload: ResumeTextRequest, user: dict = Depends(get_current_user)):
    return store.analyze_resume_text(payload.text, user.get("skills", []))


@router.get("/ai/resume-insights")
def resume_insights(user: dict = Depends(get_current_user)):
    return store.resume_insights(user["id"])


# --------------------------------------------------------------------------- #
# Jobs
# --------------------------------------------------------------------------- #
@router.get("/jobs")
def list_jobs(search: str = "", category: str = "", skill: str = ""):
    return {"jobs": store.list_jobs(search=search, category=category, skill=skill)}


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job["recommended_talent"] = store.recommend_talent_for(job_id, limit=4)
    return job


@router.post("/jobs")
def create_job(payload: JobCreate, user: dict = Depends(get_current_user)):
    if not user.get("is_employer") or not user.get("firm_verified"):
        raise HTTPException(status_code=403, detail="Register and verify your firm to post jobs")
    return store.create_job(user["id"], payload.model_dump())


@router.get("/jobs/{job_id}/applicants")
def job_applicants(job_id: str, user: dict = Depends(get_current_user)):
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if user["role"] != "client" or job["client_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    apps = [a for a in store.applications_for_client(user["id"]) if a["job_id"] == job_id]
    return {"applicants": apps}


# --------------------------------------------------------------------------- #
# Talent
# --------------------------------------------------------------------------- #
@router.get("/talent")
def list_talent(search: str = "", skill: str = ""):
    return {"talent": store.list_talent(search=search, skill=skill)}


@router.get("/talent/{talent_id}")
def get_talent(talent_id: str):
    u = store.get_user(talent_id)
    if not u or not u.get("is_freelancer"):
        raise HTTPException(status_code=404, detail="Talent not found")
    return store.public_user(u)


# --------------------------------------------------------------------------- #
# Applications
# --------------------------------------------------------------------------- #
@router.post("/jobs/{job_id}/apply")
def apply(job_id: str, payload: ApplyRequest, user: dict = Depends(get_current_user)):
    if not user.get("is_freelancer") or not (user.get("resume_text") or user.get("resume_url")):
        raise HTTPException(status_code=403, detail="Complete your freelancer profile and add a resume to apply")
    try:
        app = store.apply_to_job(job_id, user["id"], payload.proposed_hourly_rate, payload.cover_letter)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return app


@router.get("/applications")
def my_applications(user: dict = Depends(get_current_user)):
    if user["role"] == "client":
        return {"applications": store.applications_for_client(user["id"])}
    return {"applications": store.applications_for_contributor(user["id"])}


@router.patch("/applications/{application_id}")
def set_application_status(application_id: str, payload: StatusUpdate, user: dict = Depends(get_current_user)):
    if user["role"] != "client":
        raise HTTPException(status_code=403, detail="Only clients can update applications")
    try:
        return store.update_application_status(application_id, payload.status)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# --------------------------------------------------------------------------- #
# Engagements
# --------------------------------------------------------------------------- #
@router.get("/engagements")
def my_engagements(user: dict = Depends(get_current_user)):
    return {"engagements": store.engagements_for_user(user["id"], user["role"])}


@router.post("/engagements/{engagement_id}/log-hours")
def log_hours(engagement_id: str, payload: LogHoursRequest, user: dict = Depends(get_current_user)):
    try:
        return store.log_hours(engagement_id, payload.hours, payload.note)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# --------------------------------------------------------------------------- #
# Payments
# --------------------------------------------------------------------------- #
@router.get("/payments")
def my_payments(user: dict = Depends(get_current_user)):
    return {"payments": store.payments_for_user(user["id"], user["role"])}


@router.post("/payments/{payment_id}/release")
def release_payment(payment_id: str, user: dict = Depends(get_current_user)):
    if user["role"] != "client":
        raise HTTPException(status_code=403, detail="Only clients can release escrow")
    try:
        return store.release_payment(payment_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# --------------------------------------------------------------------------- #
# AI + dashboard
# --------------------------------------------------------------------------- #
@router.post("/ai/summarize")
def ai_summarize(payload: SummarizeRequest):
    return ai.analyze_job(payload.title, payload.text)


@router.get("/ai/recommend-jobs")
def recommend_jobs(user: dict = Depends(get_current_user)):
    return {"jobs": store.recommend_jobs_for(user["id"])}


@router.get("/stats")
def stats():
    return store.platform_stats()


@router.get("/dashboard")
def dashboard(user: dict = Depends(get_current_user)):
    role = user["role"]
    data = {
        "user": store.public_user(user),
        "stats": store.platform_stats(),
        "engagements": store.engagements_for_user(user["id"], role),
        "payments": store.payments_for_user(user["id"], role),
        "wallet": store.get_wallet(user["id"]),
    }
    if role == "contributor":
        data["applications"] = store.applications_for_contributor(user["id"])
        data["recommended_jobs"] = store.recommend_jobs_for(user["id"])
        data["resume_insights"] = store.resume_insights(user["id"])
    else:
        data["applications"] = store.applications_for_client(user["id"])
        data["jobs"] = [j for j in store.list_jobs_for_client(user["id"])]
    return data


# --------------------------------------------------------------------------- #
# Wallet + simulated payment gateway
# --------------------------------------------------------------------------- #
@router.get("/wallet")
def wallet(user: dict = Depends(get_current_user)):
    return store.wallet_summary(user["id"])


@router.post("/wallet/deposit")
def wallet_deposit(payload: ChargeRequest, user: dict = Depends(get_current_user)):
    result = store.process_card_payment(
        user_id=user["id"],
        amount=payload.amount,
        number=payload.card_number,
        exp_month=payload.exp_month,
        exp_year=payload.exp_year,
        cvv=payload.cvv,
        pin=payload.pin,
        holder_name=payload.holder_name,
        save_card=payload.save_card,
    )
    if not result["success"]:
        raise HTTPException(status_code=402, detail=result["message"])
    result["wallet"] = store.get_wallet(user["id"])
    return result


@router.post("/wallet/withdraw")
def wallet_withdraw(payload: WithdrawRequest, user: dict = Depends(get_current_user)):
    try:
        wallet = store.withdraw_from_wallet(user["id"], payload.amount)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"success": True, "wallet": wallet}


@router.post("/wallet/add-card")
def wallet_add_card(payload: AddCardRequest, user: dict = Depends(get_current_user)):
    try:
        card = store.add_card(user["id"], payload.card_number, payload.exp_month, payload.exp_year, payload.holder_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return card


@router.post("/engagements/{engagement_id}/fund-escrow")
def fund_escrow(engagement_id: str, payload: FundEscrowRequest, user: dict = Depends(get_current_user)):
    if user["role"] != "client":
        raise HTTPException(status_code=403, detail="Only clients can fund escrow")
    try:
        return store.fund_escrow(engagement_id, payload.hours)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/audit")
def audit(user: dict = Depends(get_current_user)):
    return {"events": store.audit_for_user(user["id"])}

