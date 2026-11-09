from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


SENSITIVE_FIELDS = {
    "password",
    "hashed_password",
    "access_token",
    "refresh_token",
    "token",
    "merchant_key",
    "passphrase",
    "card_number",
    "cvv",
}


def sanitise_values(values: dict | None) -> dict | None:
    """Remove sensitive fields before storing audit snapshots."""

    if values is None:
        return None

    sanitised = {}

    for key, value in values.items():
        if key.lower() in SENSITIVE_FIELDS:
            continue

        sanitised[key] = value

    return sanitised


def create_audit_log(
    db: Session,
    *,
    user_id: int | None,
    action: str,
    entity_type: str,
    entity_id: Any = None,
    description: str | None = None,
    old_values: dict | None = None,
    new_values: dict | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Create an audit log entry."""

    audit_log = AuditLog(
        user_id=user_id,
        action=action.upper(),
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        description=description,
        old_values=sanitise_values(old_values),
        new_values=sanitise_values(new_values),
        ip_address=ip_address,
    )

    db.add(audit_log)
    db.flush()

    return audit_log