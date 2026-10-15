"""Job service (P0 task 6)."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from ..errors import APIError, ErrorCode
from ..models import Job, JobStatus
from ..repositories.job_repository import JobRepository


class JobService:
    def __init__(self, db: Session) -> None:
        self.repo = JobRepository(db)

    def create(self, **kwargs) -> Job:
        key = kwargs.get("idempotency_key")
        if key:
            existing = self.repo.get_by_idempotency_key(key)
            if existing:
                return existing
        job = self.repo.create(**kwargs)
        return job

    def get(self, job_id: str) -> Optional[Job]:
        return self.repo.get(job_id)

    def require(self, job_id: str) -> Job:
        job = self.get(job_id)
        if not job:
            raise APIError(ErrorCode.INTERNAL_ERROR, f"Job not found: {job_id}")
        return job
