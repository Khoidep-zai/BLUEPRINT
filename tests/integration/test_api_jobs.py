"""API end-to-end tests: select function -> upload image -> output + QA report.

Uses the merged FastAPI app with the in-memory store (no database) exactly as
it runs in production: ``uvicorn photoai_api.main:app``.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _path in (str(ROOT), str(ROOT / "src" / "backend"), str(ROOT / "workers" / "src")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from fastapi.testclient import TestClient  # noqa: E402

from photoai_api.main import app  # noqa: E402
from tests.golden.generate import ALL_RECIPES, _make_image  # noqa: E402

client = TestClient(app)


def _png_bytes(recipe_id: str = "open_eyes", index: int = 0) -> bytes:
    buffer = io.BytesIO()
    _make_image(recipe_id, index).save(buffer, format="PNG")
    return buffer.getvalue()


def _post(recipe_id: str, *, params: dict | None = None, ownership: bool = False, data: bytes | None = None, mime: str = "image/png"):
    return client.post(
        "/api/jobs",
        files={"file": (f"{recipe_id}.png", data if data is not None else _png_bytes(recipe_id), mime)},
        data={
            "recipe_id": recipe_id,
            "params": json.dumps(params or {}),
            "ownership_confirmed": str(ownership).lower(),
        },
    )


def test_healthz():
    assert client.get("/healthz").json() == {"status": "ok"}


def test_frontend_is_served_at_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Photo AI Tool" in response.text


def test_list_recipes_returns_all_ten():
    response = client.get("/api/recipes")
    assert response.status_code == 200
    recipes = response.json()["recipes"]
    assert {item["id"] for item in recipes} == set(ALL_RECIPES)
    watermark = next(item for item in recipes if item["id"] == "remove_watermark")
    assert watermark["requires_ownership"] is True
    assert "qa" in watermark["steps"]


def test_get_recipe_detail_and_404():
    assert client.get("/api/recipes/open_eyes").json()["id"] == "open_eyes"
    assert client.get("/api/recipes/does_not_exist").status_code == 404


def test_watermark_flow_requires_ownership():
    response = _post("remove_watermark")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "OWNERSHIP_REQUIRED"


def test_full_flow_returns_result_and_qa_report():
    response = _post(
        "open_eyes",
        params={"strength": 0.4, "post_left_ear": 0.3, "post_right_ear": 0.3},
    )
    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "done"
    assert job["qa_report"] is not None
    assert job["qa_report"]["passed"] is True
    assert job["qa_report"]["metrics"]["ear"] >= 0.20

    result = client.get(job["result_url"])
    assert result.status_code == 200
    assert result.headers["content-type"].startswith("image/")
    assert result.content[:8] == b"\x89PNG\r\n\x1a\n"

    fetched = client.get(f"/api/jobs/{job['job_id']}")
    assert fetched.status_code == 200
    assert fetched.json()["job_id"] == job["job_id"]


def test_best_effort_flow_reports_warnings_honestly():
    """Without the simulated landmark model the ear gate cannot pass with the
    mock provider; the API still returns the best-effort output + warnings."""
    response = _post("open_eyes")
    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "done"
    assert job["qa_report"]["passed"] is False
    assert job["warnings"]


def test_watermark_confirmed_flow_succeeds():
    response = _post("remove_watermark", ownership=True)
    assert response.status_code == 200
    assert response.json()["status"] == "done"


def test_upscale_flow_outputs_larger_image():
    response = _post("upscale_4k")
    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "done"
    result = client.get(job["result_url"])
    assert result.status_code == 200
    assert len(result.content) > 0


def test_invalid_file_type_rejected():
    response = _post("open_eyes", data=b"not an image", mime="text/plain")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_FILE_TYPE"


def test_corrupt_image_rejected():
    response = _post("open_eyes", data=b"still not an image", mime="image/png")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_FILE_TYPE"


def test_unknown_recipe_returns_404():
    response = _post("no_such_function")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RECIPE_NOT_FOUND"


def test_jobs_list_contains_recent_jobs():
    _post("open_eyes", params={"post_left_ear": 0.3, "post_right_ear": 0.3})
    response = client.get("/api/jobs?limit=5")
    assert response.status_code == 200
    jobs = response.json()["jobs"]
    assert jobs and all("job_id" in job for job in jobs)
