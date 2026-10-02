from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.entities import User
from app.schemas.auth import AuthResponse, UserLoginRequest, UserProfile, UserRegisterRequest
from app.services.auth_service import authenticate_user, create_access_token, create_demo_users, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse)
async def register(payload: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    await create_demo_users(db)
    user = await register_user(db, payload)
    token = create_access_token(str(user.id))
    return AuthResponse(
        access_token=token,
        user=UserProfile(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            country_code=user.country_code,
            kyc_status=user.kyc_status.value,
            reputation_score=float(user.reputation_score or 0.0),
        ),
    )


@router.post("/login", response_model=AuthResponse)
async def login(payload: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    await create_demo_users(db)
    user = await authenticate_user(db, payload.email.lower(), payload.password)
    token = create_access_token(str(user.id))
    return AuthResponse(
        access_token=token,
        user=UserProfile(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            country_code=user.country_code,
            kyc_status=user.kyc_status.value,
            reputation_score=float(user.reputation_score or 0.0),
        ),
    )


@router.get("/demo-users")
async def demo_users(db: AsyncSession = Depends(get_db)):
    await create_demo_users(db)
    return {
        "users": [
            {"email": "admin@smartescrow.io", "password": "SmartEscrow123!"},
            {"email": "client@smartescrow.io", "password": "SmartEscrow123!"},
            {"email": "freelancer@smartescrow.io", "password": "SmartEscrow123!"},
            {"email": "arbiter@smartescrow.io", "password": "SmartEscrow123!"},
        ]
    }
