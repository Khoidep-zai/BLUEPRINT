"""Storage tests: SQLite job history, image codec and workspace TTL."""
from __future__ import annotations

from PIL import Image

from photoai.storage import image_codec, workspace
from photoai.storage.db import LocalWorkspaceManager, connect


def test_job_lifecycle_is_recorded():
    manager = LocalWorkspaceManager()
    job_id = manager.create_job("upscale_4k", {"seed": 1})
    assert job_id.startswith("job_")

    manager.finish_job(
        job_id,
        status="done",
        result_path="/tmp/out.png",
        warnings=["w"],
        qa_report={"passed": True, "attempt": 1, "metrics": {"a": 1}, "thresholds": {"a_min": 0.5}},
    )
    manager.audit("test_event", {"k": "v"})

    with connect() as conn:
        job = conn.execute("SELECT status FROM jobs WHERE id = ?", (job_id,)).fetchone()
        assert job["status"] == "done"
        reports = conn.execute("SELECT COUNT(*) AS c FROM qa_reports WHERE job_id = ?", (job_id,)).fetchone()
        assert reports["c"] == 1
        audits = conn.execute("SELECT COUNT(*) AS c FROM audit_logs").fetchone()
        assert audits["c"] >= 1


def test_image_codec_roundtrip(tmp_path):
    image = Image.new("RGB", (8, 8), (10, 20, 30))
    path = tmp_path / "out.png"
    image_codec.save_png(image, path)
    loaded = image_codec.load_image(path)
    assert loaded.size == (8, 8)
    assert loaded.getpixel((0, 0)) == (10, 20, 30)


def test_purge_expired_cache_returns_int():
    removed = workspace.purge_expired_cache()
    assert isinstance(removed, int)
    assert removed >= 0
