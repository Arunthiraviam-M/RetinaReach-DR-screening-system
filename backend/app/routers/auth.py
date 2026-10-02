from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.schemas_auth import (
    AuthResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UpdatePreferencesRequest,
    UserOut,
)
from app.models.user import User
from app.utils.audit import log_action

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _user_out(user: User) -> UserOut:
    return UserOut(
        id=str(user.id),
        name=user.name,
        email=user.email,
        role=user.role,
        phone=user.phone,
        address=user.address,
        facility_name=user.facility_name,
        district=user.district,
        preferred_language=user.preferred_language,
        theme=user.theme,
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, request: Request):
    existing = await User.find_one(User.email == payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        phone=payload.phone,
        address=payload.address,
        facility_name=payload.facility_name,
        district=payload.district,
        role=payload.role,
    )
    await user.insert()

    access = create_access_token(str(user.id), user.role.value)
    refresh = create_refresh_token(str(user.id), user.role.value)

    await log_action(str(user.id), user.role.value, "register", "user", str(user.id), ip_address=request.client.host if request.client else None)

    return AuthResponse(user=_user_out(user), tokens=TokenPair(access_token=access, refresh_token=refresh))


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, request: Request):
    user = await User.find_one(User.email == payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account has been deactivated. Contact your administrator.")

    user.last_login_at = datetime.now(timezone.utc)
    await user.save()

    access = create_access_token(str(user.id), user.role.value)
    refresh = create_refresh_token(str(user.id), user.role.value)

    await log_action(str(user.id), user.role.value, "login", "user", str(user.id), ip_address=request.client.host if request.client else None)

    return AuthResponse(user=_user_out(user), tokens=TokenPair(access_token=access, refresh_token=refresh))


@router.post("/refresh", response_model=TokenPair)
async def refresh_token(payload: RefreshRequest):
    data = decode_token(payload.refresh_token)
    if data is None or data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token.")

    user = await User.get(data["sub"])
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User no longer active.")

    access = create_access_token(str(user.id), user.role.value)
    refresh = create_refresh_token(str(user.id), user.role.value)
    return TokenPair(access_token=access, refresh_token=refresh)


@router.get("/me", response_model=UserOut)
async def read_current_user(user: User = Depends(get_current_user)):
    return _user_out(user)


@router.patch("/me/preferences", response_model=UserOut)
async def update_preferences(payload: UpdatePreferencesRequest, user: User = Depends(get_current_user)):
    if payload.preferred_language is not None:
        user.preferred_language = payload.preferred_language
    if payload.theme is not None:
        user.theme = payload.theme
    await user.save()
    return _user_out(user)
