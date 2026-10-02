from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

import pymongo
from beanie import Document, Indexed
from pydantic import Field


class Sex(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class DiabetesStatus(str, Enum):
    KNOWN = "known"
    UNKNOWN = "unknown"
    NOT_DIABETIC = "not_diabetic"


class Patient(Document):
    patient_code: Indexed(str, unique=True)  # human-friendly ID, e.g. RS-2026-000123
    full_name: str
    age: int
    sex: Sex
    phone: Optional[str] = None
    village: Optional[str] = None
    district: Optional[str] = None
    state: str = "Tamil Nadu"

    diabetes_status: DiabetesStatus = DiabetesStatus.UNKNOWN
    diabetes_duration_years: Optional[float] = None
    hba1c: Optional[float] = None
    other_conditions: Optional[str] = None

    registered_by: str  # user id (string) of the health worker who registered them
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "patients"
        indexes = [
            pymongo.IndexModel("patient_code", unique=True),
            pymongo.IndexModel("district"),
            pymongo.IndexModel("full_name"),
            pymongo.IndexModel([("created_at", pymongo.DESCENDING)]),
        ]
