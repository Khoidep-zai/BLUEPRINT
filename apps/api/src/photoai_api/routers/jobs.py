"""Job router (§6 API contract). P0: in-memory service; worker runs mock inline."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from photoai_api.config import settings
from photoai_api.services.job_service import job_service
from photoai_api.schemas.job import (
    JobCreate,
    JobListItem,
    JobResponse,
    PresignRequest,
    PresignResponse,
)

router = APIRouter(prefix="/v1")


class ErrorResponse(BaseModel):
    code: str
    message: str
    request_id: str


@router.get("/healthz", response_model=dict, tags=["health"])
async def healthz():
    return {"status": "ok"}


@router.post("/uploads/presign", response_model=PresignResponse, tags=["uploads"])
async def presign(req: PresignRequest):
    if req.size > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=422, detail="IMAGE_TOO_LARGE")
    asset_id = f"ast_{uuid4().hex[:12]}"
    return PresignResponse(
        asset_id=asset_id,
        upload_url=f"/storage/originals/{asset_id}",
        expires_in=900,
    )


@router.post("/jobs", response_model=JobResponse, status_code=202, tags=["jobs"])
async def create_job(data: JobCreate):
    # Watermark recipe requires ownership confirmation (§2 immutable rule #8)
    if data.recipe_id == "remove_watermark" and not data.ownership_confirmed:
        raise HTTPException(
            status_code=403,
            detail="OWNERSHIP_REQUIRED",
        )
    job = job_service.create(data)
    # P0: run recipe inline with mock provider
    try:
        await _run_job(job.job_id, data)
    except Exception as exc:  # noqa: BLE001
        job_service.update_status(
            job.job_id, status="failed", warnings=[str(exc)],
            finished_at=datetime.now(timezone.utc),
        )
    return job_service.get(job.job_id) or job


@router.get("/jobs/{job_id}", response_model=JobResponse, tags=["jobs"])
async def get_job(job_id: str):
    job = job_service.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="JOB_NOT_FOUND")
    return job


@router.get("/jobs", response_model=list[JobListItem], tags=["jobs"])
async def list_jobs(limit: int = Query(50, ge=1, le=200)):
    return job_service.list()[:limit]


@router.get("/jobs/{job_id}/result", tags=["jobs"])
async def get_result(job_id: str):
    job = job_service.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="JOB_NOT_FOUND")
    if job.status != "done" or not job.result_asset_id:
        raise HTTPException(status_code=404, detail="RESULT_NOT_READY")
    return {
        "job_id": job.job_id,
        "result_asset_id": job.result_asset_id,
        "download_url": f"/storage/results/{job.result_asset_id}",
    }


@router.post("/jobs/{job_id}/retry", response_model=JobResponse, tags=["jobs"])
async def retry_job(job_id: str):
    job = job_service.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="JOB_NOT_FOUND")
    create = JobCreate(
        recipe_id=job.recipe_id,
        input_asset_id=job.input_asset_id,
        mask_asset_id=job.mask_asset_id,
        params=job.params,
        ownership_confirmed=job.ownership_confirmed,
        idempotency_key=f"retry-{uuid4().hex[:8]}",
    )
    return await create_job(create)


async def _run_job(job_id: str, data: JobCreate) -> None:
    """Run the recipe with the mock provider (P0 inline runner)."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "workers" / "src"))
    sys.path.insert(0, str(Path(__file__).resolve().parents[5]))

    from photoai_worker.pipeline.recipe_schema import Recipe
    from photoai_worker.pipeline.runner import Runner
    from providers.mock import MockProvider
    from PIL import Image

    job_service.update_status(job_id, status="running")
    try:
        # Build a synthetic input image if asset doesn't exist yet (P0)
        image = Image.new("RGB", (512, 512), (120, 160, 200))
        recipe = Recipe(
            id=data.recipe_id,
            version=1,
            steps=[{"detect": {"faces": True}}, {"edit": {}}, {"qa": {}}],
            retry={"max": 2},
            prompt={},
        )
        provider = MockProvider(delay_ms=5.0)
        runner = Runner(provider=provider)
        result = await runner.run(
            job_id, recipe, image, params={"strength": 0.5, "seed": 42}
        )
        result_asset_id = f"ast_res_{uuid4().hex[:12]}"
        job_service.update_status(
            job_id,
            status="done",
            result_asset_id=result_asset_id,
            warnings=list(result.get("warnings", [])),
            qa_report=result.get("qa_report"),
            finished_at=datetime.now(timezone.utc),
        )
    except Exception:
        job_service.update_status(
            job_id,
            status="failed",
            finished_at=datetime.now(timezone.utc),
        )
        raise


@router.get("/recipes", tags=["recipes"])
async def list_recipes():
    return [
        {"id": "upscale_4k", "name": "Nâng cấp 4K"},
        {"id": "skin_retouch", "name": "Retouch da"},
        {"id": "chin_fix", "name": "Sửa nọng cằm"},
        {"id": "open_eyes", "name": "Cứu ảnh nhắm mắt"},
        {"id": "remove_watermark", "name": "Xóa watermark"},
        {"id": "remove_bystanders", "name": "Xóa người hậu cảnh"},
        {"id": "restore_old_photo", "name": "Phục chế ảnh cũ"},
        {"id": "golden_hour", "name": "Chân portrait giờ vàng"},
        {"id": "low_light_fix", "name": "Sửa ảnh thiếu sáng"},
        {"id": "product_studio", "name": "Điện thoại → Studio"},
    ]
