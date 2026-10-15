"""Job endpoints: select function -> upload image -> process -> output.

The flow is deliberately synchronous (self-hosted CPU): one POST carries the
image, runs the pipeline, and the job row plus QA report are ready by the time
the response returns. The original upload is never modified (invariant S2.1).
"""
from __future__ import annotations

import json
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import Response

from ..errors import APIError, ErrorCode
from ..imaging import decode_image, encode_png, sha256_hex
from ..models import Job, JobStatus
from ..security.upload_guard import validate_file
from ..services.processing import ProcessingService
from ..store import default_store as store

router = APIRouter(prefix="/jobs", tags=["jobs"])

_OWNERSHIP_MESSAGE = (
    "Tính năng xóa watermark yêu cầu xác nhận quyền sở hữu ảnh "
    "(ownership_confirmed=true)."
)


def _report_payload(job_id: str) -> Optional[Dict[str, Any]]:
    """Return the latest QA report for a job, if any."""
    reports = store.get_qa_reports_for_job(job_id)
    if not reports:
        return None
    report = reports[-1]
    return {
        "passed": report.passed,
        "attempt": report.attempt,
        "metrics": report.metrics,
        "thresholds": report.thresholds,
    }


def _job_payload(job: Job) -> Dict[str, Any]:
    """Serialise a job (plus its QA report) for the API responses."""
    return {
        "job_id": job.id,
        "recipe_id": job.recipe_id,
        "status": job.status,
        "warnings": list(job.warnings or []),
        "error_code": job.error_code,
        "result_url": f"/api/jobs/{job.id}/result" if job.result_asset_id else None,
        "qa_report": _report_payload(job.id),
        "created_at": job.created_at.isoformat(),
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
    }


@router.post("")
async def create_job(
    file: UploadFile = File(...),
    recipe_id: str = Form(...),
    params: str = Form("{}"),
    ownership_confirmed: bool = Form(False),
):
    """Process one image with the selected function and return the result job."""
    data = await file.read()
    ok, reason = validate_file(file.filename or "", file.content_type or "", len(data))
    if not ok:
        raise APIError(ErrorCode(reason), "Tệp tải lên không hợp lệ.")

    service = ProcessingService()
    recipe = service.get_recipe(recipe_id)
    info = service.get_info(recipe_id)

    try:
        params_dict = json.loads(params or "{}")
        if not isinstance(params_dict, dict):
            raise ValueError("params must be a JSON object")
    except ValueError as exc:
        raise APIError(ErrorCode.INVALID_PARAMS, f"Tham số không hợp lệ: {exc}") from None
    params_dict["ownership_confirmed"] = bool(ownership_confirmed)

    if info.requires_ownership and not ownership_confirmed:
        store.log_audit(action="watermark_blocked", detail={"recipe_id": recipe_id})
        raise APIError(ErrorCode.OWNERSHIP_REQUIRED, _OWNERSHIP_MESSAGE)

    try:
        image = decode_image(data)
    except ValueError as exc:
        raise APIError(ErrorCode.INVALID_FILE_TYPE, str(exc)) from exc

    digest = sha256_hex(data)
    input_key = f"inputs/{digest[:16]}"
    store.put_blob(input_key, data)
    input_asset = store.create_asset(
        kind="original",
        storage_key=input_key,
        mime=file.content_type or "image/png",
        width=image.width,
        height=image.height,
        sha256=digest,
    )

    job = store.create_job(
        recipe_id=recipe.id,
        input_asset_id=input_asset.id,
        params=params_dict,
        ownership_confirmed=bool(ownership_confirmed),
    )
    store.update_status(job, JobStatus.RUNNING.value)

    try:
        result = service.process(recipe, image, params_dict)
    except APIError as exc:
        from ..models.base import utc_now

        job.error_code = exc.code.value if isinstance(exc.code, ErrorCode) else str(exc.code)
        job.finished_at = utc_now()
        store.update_status(job, JobStatus.FAILED.value)
        raise

    output = encode_png(result.image)
    output_key = f"results/{job.id}"
    store.put_blob(output_key, output)
    result_asset = store.create_asset(
        kind="result",
        storage_key=output_key,
        mime="image/png",
        width=result.image.width,
        height=result.image.height,
        sha256=sha256_hex(output),
    )
    store.set_result(job, result_asset.id, result.warnings)
    store.create_qa_report(
        job_id=job.id,
        attempt=result.report.attempt,
        metrics=result.report.metrics,
        thresholds=result.report.thresholds,
        passed=result.report.passed,
    )
    if info.requires_ownership:
        store.log_audit(
            action="watermark_confirmed",
            detail={"recipe_id": recipe.id},
            job_id=job.id,
        )
    return _job_payload(job)


@router.get("")
def list_jobs(limit: int = 20) -> Dict[str, Any]:
    """Return the most recent jobs (newest first)."""
    jobs = store.list_jobs(limit=max(1, min(limit, 100)))
    return {"jobs": [_job_payload(job) for job in jobs]}


@router.get("/{job_id}")
def get_job(job_id: str) -> Dict[str, Any]:
    """Return one job with its QA report."""
    job = store.get_job(job_id)
    if job is None:
        raise APIError(ErrorCode.JOB_NOT_FOUND, f"Không tìm thấy job: {job_id}")
    return _job_payload(job)


@router.get("/{job_id}/result")
def get_result(job_id: str) -> Response:
    """Download the processed output image (PNG)."""
    job = store.get_job(job_id)
    if job is None or not job.result_asset_id:
        raise APIError(ErrorCode.JOB_NOT_FOUND, f"Job chưa có kết quả: {job_id}")
    asset = store.get_asset(job.result_asset_id)
    blob = store.get_blob(asset.storage_key) if asset else None
    if blob is None:
        raise APIError(ErrorCode.JOB_NOT_FOUND, "Không tìm thấy tệp kết quả.")
    filename = f"{job.recipe_id}_{job.id}.png"
    return Response(
        content=blob,
        media_type=asset.mime,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
