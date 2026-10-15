"""Audit log repository."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from ..models import AuditLog


class AuditRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        action: str,
        detail: dict,
        user_id: Optional[str] = None,
        job_id: Optional[str] = None,
        ip_hash: Optional[str] = None,
    ) -> AuditLog:
        log = AuditLog(
            user_id=user_id,
            job_id=job_id,
            action=action,
            detail=detail,
            ip_hash=ip_hash,
        )
        self.db.add(log)
        self.db.flush()
        self.db.refresh(log)
        return log
