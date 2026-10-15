"""Job repository."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from ..models import Job, JobStatus


class JobRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, **kwargs) -> Job:
        job = Job(**kwargs)
        self.db.add(job)
        self.db.flush()
        self.db.refresh(job)
        return job

    def get(self, job_id: str) -> Optional[Job]:
        return self.db.get(Job, job_id)

    def get_by_idempotency_key(self, key: str) -> Optional[Job]:
        return self.db.query(Job).filter(Job.idempotency_key == key).first()

    def update_status(self, job: Job, status: str) -> Job:
        job.status = status
        self.db.add(job)
        self.db.flush()
        return job

    def set_result(self, job: Job, result_asset_id: str, warnings: list) -> Job:
        job.result_asset_id = result_asset_id
        job.warnings = warnings
        job.status = JobStatus.DONE.value
        self.db.add(job)
        self.db.flush()
        return job
