from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    phone: Optional[str] = Field(default=None, max_length=20)
    address: Optional[str] = Field(default=None, max_length=250)
    facility_name: Optional[str] = Field(default=None, max_length=150)
    district: Optional[str] = Field(default=None, max_length=100)
    role: UserRole = UserRole.HEALTH_WORKER


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: UserRole
    phone: Optional[str] = None
    address: Optional[str] = None
    facility_name: Optional[str] = None
    district: Optional[str] = None
    preferred_language: str
    theme: str


class AuthResponse(BaseModel):
    user: UserOut
    tokens: TokenPair


class UpdatePreferencesRequest(BaseModel):
    preferred_language: Optional[str] = None
    theme: Optional[str] = None
