from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import pymongo
from beanie import Document, Indexed
from pydantic import Field


class Report(Document):
    study_id: Indexed(str)
    patient_id: Indexed(str)
    patient_code: str
    generated_by: str
    pdf_path: str
    dr_grade: int
    referable_dr: bool
    confidence: float
    version: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    downloaded_count: int = 0
    last_downloaded_at: Optional[datetime] = None

    class Settings:
        name = "reports"
        indexes = [
            pymongo.IndexModel("study_id"),
            pymongo.IndexModel("patient_id"),
            pymongo.IndexModel([("created_at", pymongo.DESCENDING)]),
        ]
