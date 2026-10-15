"""Golden-set regression: 20 measured images per function, reproducible QA.

The ``expected.json`` files are produced by ``tests/golden/calibrate.py``
(measure, don't assume). These tests replay the recipes and require the
measured metrics to reproduce exactly (deterministic pipeline).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _path in (str(ROOT), str(ROOT / "workers" / "src")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import pytest  # noqa: E402

from tests.golden import ALL_RECIPES, expected_path, images_dir  # noqa: E402
from tests.golden.calibrate import run_one  # noqa: E402
from tests.golden.generate import generate_all  # noqa: E402

# Full replay for the P1-prioritised functions; a deterministic subset for the
# rest (the calibration script measures all 20 for every recipe).
FULL_REPLAY = {"open_eyes", "remove_bystanders", "remove_watermark", "upscale_4k"}
SUBSET_SIZE = 5


@pytest.fixture(scope="session", autouse=True)
def _ensure_golden_images():
    """Generate any missing golden images (they are not committed: 11MB+)."""
    counts = generate_all()
    assert all(count >= 20 for count in counts.values())


def _expected(recipe_id: str) -> dict:
    path = expected_path(recipe_id)
    if not path.is_file() or path.read_text(encoding="utf-8").strip() in ("", "{}"):
        pytest.fail(
            f"expected.json chưa được hiệu chuẩn cho {recipe_id}; "
            "chạy: python tests/golden/calibrate.py"
        )
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("recipe_id", ALL_RECIPES)
def test_golden_set_has_twenty_measured_images(recipe_id):
    files = sorted(images_dir(recipe_id).glob("*.png"))
    payload = _expected(recipe_id)
    assert len(files) >= 20
    assert payload["recipe"] == recipe_id
    assert payload["images"] == len(files)
    assert len(payload["per_image"]) == len(files)
    assert payload["aggregates"], "no measured aggregates recorded"


@pytest.mark.parametrize("recipe_id", ALL_RECIPES)
def test_golden_replay_reproduces_measurements(recipe_id):
    payload = _expected(recipe_id)
    expected_by_file = {record["file"]: record for record in payload["per_image"]}
    files = sorted(images_dir(recipe_id).glob("*.png"))
    if recipe_id not in FULL_REPLAY:
        files = files[:SUBSET_SIZE]

    for path in files:
        measured = run_one(recipe_id, path)
        expected = expected_by_file[path.name]
        assert measured["passed"] == expected["passed"]
        assert measured["best_effort"] == expected["best_effort"]
        assert measured["attempts"] == expected["attempts"]
        assert set(measured["metrics"]) == set(expected["metrics"])
        for key, value in measured["metrics"].items():
            expected_value = expected["metrics"][key]
            if isinstance(value, bool):
                assert value == expected_value
            else:
                assert value == pytest.approx(expected_value, rel=1e-6, abs=1e-6)
