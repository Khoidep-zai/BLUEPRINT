"""Audit service (P0 task 6; mandatory for remove_watermark)."""
from __future__ import annotations

import hashlib
from typing import Optional

from sqlalchemy.orm import Session

from ..repositories.audit_repository import AuditRepository


class AuditService:
    def __init__(self, db: Session) -> None:
        self.repo = AuditRepository(db)

    def log(self, action: str, detail: dict, user_id: Optional[str] = None, job_id: Optional[str] = None, ip: Optional[str] = None):
        ip_hash = None
        if ip:
            ip_hash = hashlib.sha256(ip.encode("utf-8")).hexdigest()
        return self.repo.create(action=action, detail=detail, user_id=user_id, job_id=job_id, ip_hash=ip_hash)
