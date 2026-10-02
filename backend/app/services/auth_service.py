import uuid
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.entities import KYCStatus, User, UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


async def create_demo_users(db: AsyncSession) -> None:
    for email, full_name, role in [
        ("admin@smartescrow.io", "Smart Escrow Admin", UserRole.admin),
        ("client@smartescrow.io", "Apex Labs Client", UserRole.client),
        ("freelancer@smartescrow.io", "Nina Developer", UserRole.freelancer),
        ("arbiter@smartescrow.io", "Senior Review Arbiter", UserRole.arbiter),
    ]:
        existing = await db.scalar(select(User).where(User.email == email))
        if existing:
            continue
        user = User(
            id=uuid.uuid4(),
            email=email,
            full_name=full_name,
            hashed_password=hash_password("SmartEscrow123!"),
            role=role,
            country_code="US",
            kyc_status=KYCStatus.verified,
            reputation_score=95.0 if role == UserRole.arbiter else 88.0,
            is_active=True,
        )
        db.add(user)
    await db.commit()


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    user = await db.scalar(select(User).where(User.email == email.lower()))
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")
    return user


async def register_user(db: AsyncSession, payload) -> User:
    normalized_email = payload.email.lower()
    existing = await db.scalar(select(User).where(User.email == normalized_email))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

    user = User(
        email=normalized_email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        country_code=payload.country_code.upper(),
        kyc_status=KYCStatus.pending,
        reputation_score=0.0,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
