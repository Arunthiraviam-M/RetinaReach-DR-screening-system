from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import pymongo
from beanie import Document
from pydantic import Field


class AuditLog(Document):
    actor_user_id: str
    actor_role: str
    action: str  # e.g. "login", "study.analyze", "report.download", "grade.override"
    resource_type: str  # "patient" | "study" | "report" | "user"
    resource_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "audit_logs"
        indexes = [
            pymongo.IndexModel([("created_at", pymongo.DESCENDING)]),
            pymongo.IndexModel("actor_user_id"),
            pymongo.IndexModel("resource_type"),
        ]
