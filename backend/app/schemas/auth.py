from pydantic import BaseModel, EmailStr, Field

from app.models.entities import UserRole


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2)
    role: UserRole = UserRole.client
    country_code: str = "US"


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserProfile(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    country_code: str
    kyc_status: str
    reputation_score: float

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile
