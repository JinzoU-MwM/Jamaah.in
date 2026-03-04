"""
Audit logging helpers.
"""
import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def record_audit_event(
    db: Session,
    *,
    user_id: int,
    action: str,
    resource_type: str,
    resource_id: str | int,
    details: dict[str, Any] | None = None,
) -> AuditLog:
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id),
        details_json=json.dumps(details or {}, ensure_ascii=True),
    )
    db.add(entry)
    return entry
