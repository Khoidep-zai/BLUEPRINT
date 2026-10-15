"""Job service - in-memory store for P0; replaced by DB-backed service in P1."""
from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from photoai_api.schemas.job import JobCreate, JobResponse


class JobService:
    def __init__(self) -> None:
        self._jobs: dict[str, dict] = {}
        self._lock = threading.Lock()

    def create(self, data: JobCreate) -> JobResponse:
        job_id = f"job_{uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        record = {
            "job_id": job_id,
            "recipe_id": data.recipe_id,
            "input_asset_id": data.input_asset_id,
            "mask_asset_id": data.mask_asset_id,
            "params": data.params,
            "ownership_confirmed": data.ownership_confirmed,
            "idempotency_key": data.idempotency_key,
            "status": "queued",
            "result_asset_id": None,
            "warnings": [],
            "qa_report": None,
            "created_at": now,
            "finished_at": None,
        }
        with self._lock:
            self._jobs[job_id] = record
        return JobResponse(**record)

    def get(self, job_id: str) -> Optional[JobResponse]:
        with self._lock:
            rec = self._jobs.get(job_id)
        if rec is None:
            return None
        return JobResponse(**rec)

    def update_status(
        self,
        job_id: str,
        *,
        status: Optional[str] = None,
        result_asset_id: Optional[str] = None,
        warnings: Optional[list[str]] = None,
        qa_report: Optional[dict] = None,
        finished_at: Optional[datetime] = None,
    ) -> Optional[JobResponse]:
        with self._lock:
            rec = self._jobs.get(job_id)
            if rec is None:
                return None
            if status is not None:
                rec["status"] = status
            if result_asset_id is not None:
                rec["result_asset_id"] = result_asset_id
            if warnings is not None:
                rec["warnings"] = warnings
            if qa_report is not None:
                rec["qa_report"] = qa_report
            if finished_at is not None:
                rec["finished_at"] = finished_at
            return JobResponse(**rec)

    def list(self) -> list[JobResponse]:
        with self._lock:
            recs = list(self._jobs.values())
        return [JobResponse(**r) for r in recs]


job_service = JobService()
