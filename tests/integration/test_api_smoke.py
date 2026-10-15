"""E2E smoke test for P0 API (mock runner)."""
from fastapi.testclient import TestClient

from photoai_api.main import app


def test_healthz():
    c = TestClient(app)
    r = c.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_create_and_get_job():
    c = TestClient(app)
    r = c.post(
        "/v1/jobs",
        json={"recipe_id": "open_eyes", "input_asset_id": "ast_1", "params": {"strength": 0.5}},
    )
    assert r.status_code == 202, r.text
    job = r.json()
    assert job["status"] in ("done", "failed", "queued")
    assert job["job_id"].startswith("job_")

    g = c.get(f"/v1/jobs/{job['job_id']}")
    assert g.status_code == 200
    assert g.json()["job_id"] == job["job_id"]

    # watermark without ownership -> 403
    r2 = c.post(
        "/v1/jobs",
        json={"recipe_id": "remove_watermark", "input_asset_id": "ast_1"},
    )
    assert r2.status_code == 403
