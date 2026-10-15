"""Services (P0 task 6) backed by the in-memory store."""
from __future__ import annotations

from typing import Optional

from ..errors import APIError, ErrorCode
from ..models import Job, JobStatus
from ..store import default_store


class JobService:
    def __init__(self, store=None) -> None:
        self.store = store or default_store

    def create(self, **kwargs) -> Job:
        key = kwargs.get("idempotency_key")
        if key:
            existing = self.store.get_job_by_idempotency_key(key)
            if existing:
                return existing
        job = self.store.create_job(**kwargs)
        return job

    def get(self, job_id: str) -> Optional[Job]:
        return self.store.get_job(job_id)

    def require(self, job_id: str) -> Job:
        job = self.get(job_id)
        if not job:
            raise APIError(ErrorCode.INTERNAL_ERROR, f"Job not found: {job_id}")
        return job

    def update_status(self, job: Job, status: str) -> Job:
        return self.store.update_status(job, status)

    def set_result(self, job: Job, result_asset_id: str, warnings: list) -> Job:
        return self.store.set_result(job, result_asset_id, warnings)

    def list_statuses(self) -> list[str]:
        return [s.value for s in JobStatus]


class AssetService:
    def __init__(self, store=None) -> None:
        self.store = store or default_store

    def create(self, **kwargs):
        return self.store.create_asset(**kwargs)

    def get(self, asset_id: str):
        return self.store.get_asset(asset_id)


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
