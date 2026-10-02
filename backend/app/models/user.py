from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

import pymongo
from beanie import Document, Indexed
from pydantic import EmailStr, Field


class UserRole(str, Enum):
    ADMIN = "admin"
    OPHTHALMOLOGIST = "ophthalmologist"
    HEALTH_WORKER = "health_worker"


class User(Document):
    name: str
    email: Indexed(EmailStr, unique=True)
    hashed_password: str
    phone: Optional[str] = None
    address: Optional[str] = None
    facility_name: Optional[str] = None
    district: Optional[str] = None
    role: UserRole = UserRole.HEALTH_WORKER
    is_active: bool = True
    preferred_language: str = "en"
    theme: str = "light"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login_at: Optional[datetime] = None

    class Settings:
        name = "users"
        indexes = [
            pymongo.IndexModel("email", unique=True),
        ]
