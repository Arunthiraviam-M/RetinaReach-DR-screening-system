"""
MongoDB Atlas connection lifecycle, wired through Beanie ODM.

This is the ONLY place a MongoDB client is created. Everything else in the
codebase talks to the database through the Beanie document models, which
gives us schema validation (via Pydantic) on every read/write.

>>> To connect to YOUR MongoDB Atlas cluster:
1. In backend/.env set MONGODB_URI to your Atlas connection string and
   MONGODB_DB_NAME to the database name you want to use.
2. Nothing else needs to change — init_db() below reads those values and
   registers all document models automatically on app startup.
"""
from __future__ import annotations

import logging

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.models.audit_log import AuditLog
from app.models.patient import Patient
from app.models.report import Report
from app.models.simulation import SimulationScenario
from app.models.study import ImageAsset, Study
from app.models.user import User

logger = logging.getLogger("retinascan.db")

_client: AsyncIOMotorClient | None = None


async def init_db() -> None:
    global _client
    _client = AsyncIOMotorClient(settings.MONGODB_URI, uuidRepresentation="standard")
    database = _client[settings.MONGODB_DB_NAME]

    await init_beanie(
        database=database,
        document_models=[
                        User,
                        Patient,
                        Study,
                        ImageAsset,
                        Report,
                        SimulationScenario,
                        AuditLog,
                    ],
    )

    # Verify connectivity early so failures surface at startup, not on the
    # first request from a health worker in the field.
    try:
        await _client.admin.command("ping")
        logger.info("Connected to MongoDB database '%s'", settings.MONGODB_DB_NAME)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "MongoDB ping failed (%s). Check MONGODB_URI in backend/.env, "
            "your Atlas IP allowlist, and DB user credentials.",
            exc,
        )


async def close_db() -> None:
    if _client is not None:
        _client.close()
