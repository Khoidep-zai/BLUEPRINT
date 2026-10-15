"""Audit service (P0 task 6; mandatory for remove_watermark)."""
from __future__ import annotations

from typing import Optional

from ..store import default_store


class AuditService:
    def __init__(self, store=None) -> None:
        self.store = store or default_store

    def log(self, action: str, detail: dict, user_id: Optional[str] = None, job_id: Optional[str] = None, ip: Optional[str] = None):
        ip_hash = None
        if ip:
            import hashlib

            ip_hash = hashlib.sha256(ip.encode("utf-8")).hexdigest()
        return self.store.log_audit(
            action=action, detail=detail, user_id=user_id, job_id=job_id, ip_hash=ip_hash
        )
