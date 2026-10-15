"""Golden-set calibration: measure every recipe against its golden images.

Runs each recipe through the real recipe runner with the mock provider and
writes ``tests/golden/<recipe_id>/expected.json``:

    {
      "recipe": ..., "images": 20, "runner_params": {...},
      "pass_rate": ..., "best_effort_rate": ...,
      "aggregates": {metric: {"min", "max", "mean"}},
      "per_image": [{"file", "passed", "best_effort", "attempts", "metrics"}]
    }

The metrics recorded here are *measured*, never assumed: gates that the current
provider cannot satisfy are recorded as failed (best-effort) and flagged in
PROGRESS.md instead of being weakened.

Run from the project root:

    python tests/golden/calibrate.py
"""
from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _path in (str(ROOT), str(ROOT / "workers" / "src")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from PIL import Image  # noqa: E402

from photoai_worker.pipeline.loader import load_recipe  # noqa: E402
from photoai_worker.pipeline.runner import RecipeRunner  # noqa: E402
from providers.mock import MockProvider  # noqa: E402

from tests.golden import ALL_RECIPES, expected_path, images_dir  # noqa: E402

RECIPES_DIR = ROOT / "recipes"

# Per-recipe runner params (deterministic). open_eyes uses the default closed
# eyes on purpose: without a real model the ear gate must fail honestly.
RUNNER_PARAMS: dict[str, dict] = {
    "remove_watermark": {"ownership_confirmed": True},
}


def run_one(recipe_id: str, image_path: Path) -> dict:
    """Run one golden image and return its measured record."""
    recipe = load_recipe(str(RECIPES_DIR / f"{recipe_id}.yaml"))
    runner = RecipeRunner(provider=MockProvider())
    params = dict(RUNNER_PARAMS.get(recipe_id, {}))
    image = Image.open(image_path).convert("RGB")
    result = runner.run(recipe, image, params=params)
    return {
        "file": image_path.name,
        "passed": bool(result.passed),
        "best_effort": bool(result.best_effort),
        "attempts": int(result.report.attempt),
        "metrics": dict(result.report.metrics),
        "warnings": list(result.warnings),
    }


def calibrate_recipe(recipe_id: str) -> dict:
    """Measure all golden images of one recipe and write expected.json."""
    directory = images_dir(recipe_id)
    files = sorted(directory.glob("*.png"))
    if not files:
        raise SystemExit(
            f"Không có ảnh golden cho {recipe_id}. Chạy: python tests/golden/generate.py"
        )

    per_image = [run_one(recipe_id, path) for path in files]

    metrics_series: dict[str, list[float]] = {}
    for record in per_image:
        for key, value in record["metrics"].items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                metrics_series.setdefault(key, []).append(float(value))

    aggregates = {
        key: {
            "min": round(min(values), 6),
            "max": round(max(values), 6),
            "mean": round(statistics.fmean(values), 6),
        }
        for key, values in metrics_series.items()
    }

    passed_count = sum(1 for record in per_image if record["passed"])
    best_effort_count = sum(1 for record in per_image if record["best_effort"])
    payload = {
        "recipe": recipe_id,
        "images": len(per_image),
        "runner_params": RUNNER_PARAMS.get(recipe_id, {}),
        "pass_rate": round(passed_count / len(per_image), 6),
        "best_effort_rate": round(best_effort_count / len(per_image), 6),
        "aggregates": aggregates,
        "per_image": per_image,
    }
    expected_path(recipe_id).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return payload


def main() -> None:
    started = time.perf_counter()
    print(f"{'recipe':20s} {'pass':>5s} {'best':>5s}  key metrics (min/mean/max)")
    for recipe_id in ALL_RECIPES:
        payload = calibrate_recipe(recipe_id)
        key_metric = None
        for candidate in ("identity_cosine", "outside_mask_ssim"):
            if candidate in payload["aggregates"]:
                key_metric = candidate
                break
        detail = ""
        if key_metric:
            agg = payload["aggregates"][key_metric]
            detail = f"{key_metric}: {agg['min']:.4f}/{agg['mean']:.4f}/{agg['max']:.4f}"
        print(
            f"{recipe_id:20s} {payload['pass_rate']:5.2f} {payload['best_effort_rate']:5.2f}  {detail}"
        )
    elapsed = time.perf_counter() - started
    print(f"\nDone in {elapsed:.1f}s — expected.json written for {len(ALL_RECIPES)} recipes.")


if __name__ == "__main__":
    main()
