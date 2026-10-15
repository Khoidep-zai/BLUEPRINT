"""Simple in-memory store replacing SQLAlchemy/Postgres for P0.

No external database is required. All state lives in plain Python dicts/lists
and is reset when the process restarts, which is acceptable for the P0
self-hosted CPU flow (select function -> upload image -> process -> output).
"""
from __future__ import annotations

from typing import Optional

from .models import Asset, AuditLog, Job, JobStatus, QaReport


class InMemoryStore:
    """Thread-unsafe in-memory store. Good enough for single-process P0."""

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._assets: dict[str, Asset] = {}
        self._qa_reports: dict[str, QaReport] = {}
        self._audit_logs: list[AuditLog] = []
        # idempotency key -> job id
        self._idempotency: dict[str, str] = {}

    # ----- jobs -----
    def create_job(self, **kwargs) -> Job:
        job = Job(**kwargs)
        self._jobs[job.id] = job
        if job.idempotency_key:
            self._idempotency[job.idempotency_key] = job.id
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def get_job_by_idempotency_key(self, key: str) -> Optional[Job]:
        job_id = self._idempotency.get(key)
        if job_id is None:
            return None
        return self._jobs.get(job_id)

    def update_status(self, job: Job, status: str) -> Job:
        job.status = status
        self._jobs[job.id] = job
        return job

    def set_result(
        self, job: Job, result_asset_id: str, warnings: list
    ) -> Job:
        job.result_asset_id = result_asset_id
        job.warnings = warnings
        job.status = JobStatus.DONE.value
        self._jobs[job.id] = job
        return job

    # ----- assets -----
    def create_asset(self, **kwargs) -> Asset:
        asset = Asset(**kwargs)
        self._assets[asset.id] = asset
        return asset

    def get_asset(self, asset_id: str) -> Optional[Asset]:
        return self._assets.get(asset_id)

    # ----- audit -----
    def log_audit(
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
        self._audit_logs.append(log)
        return log

    # ----- qa reports -----
    def create_qa_report(self, **kwargs) -> QaReport:
        report = QaReport(**kwargs)
        self._qa_reports[report.id] = report
        return report

    def get_qa_reports_for_job(self, job_id: str) -> list[QaReport]:
        return [r for r in self._qa_reports.values() if r.job_id == job_id]


# Module-level default store used by dependency injection.
default_store = InMemoryStore()
