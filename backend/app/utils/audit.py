from __future__ import annotations

from typing import Optional

from app.core.config import settings
from app.models.audit_log import AuditLog


async def log_action(
    actor_user_id: str,
    actor_role: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> None:
    if not settings.AUDIT_LOG_ENABLED:
        return
    entry = AuditLog(
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
    )
    await entry.insert()
