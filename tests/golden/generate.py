"""Deterministic synthetic golden-set generator.

Creates ``COUNT_PER_RECIPE`` images per editing function under
``tests/golden/<recipe_id>/images/``. Images are fully deterministic (derived
from ``crc32(recipe_id:index)``) so QA measurements are reproducible on any
machine without downloading models or sample photos.

Run from the project root:

    python tests/golden/generate.py
"""
from __future__ import annotations

import zlib
from pathlib import Path

import numpy as np
from PIL import Image

GOLDEN_ROOT = Path(__file__).resolve().parent
COUNT_PER_RECIPE = 20

ALL_RECIPES = [
    "open_eyes",
    "skin_retouch",
    "chin_fix",
    "remove_bystanders",
    "remove_watermark",
    "restore_old_photo",
    "golden_hour",
    "low_light_fix",
    "upscale_4k",
    "product_studio",
]

SKIN = np.array([198.0, 158.0, 134.0], dtype=np.float32)
SKIN_DARK = np.array([168.0, 128.0, 106.0], dtype=np.float32)


def _seed(recipe_id: str, index: int) -> int:
    return zlib.crc32(f"{recipe_id}:{index}".encode("utf-8")) & 0xFFFFFFFF


def _gradient(size: int, color_a: tuple, color_b: tuple) -> np.ndarray:
    ramp = np.linspace(0.0, 1.0, size, dtype=np.float32)
    field = np.tile(ramp, (size, 1))
    base = np.zeros((size, size, 3), dtype=np.float32)
    for channel in range(3):
        base[:, :, channel] = color_a[channel] + (color_b[channel] - color_a[channel]) * field
    return base


def _noise(rng: np.random.Generator, size: int, amount: float) -> np.ndarray:
    return rng.normal(0.0, amount, (size, size, 3)).astype(np.float32)


def _ellipse(size: int, cx: float, cy: float, rx: float, ry: float) -> np.ndarray:
    ys, xs = np.ogrid[0:size, 0:size]
    return ((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2 <= 1.0


def _rect(size: int, x0: int, y0: int, x1: int, y1: int) -> np.ndarray:
    mask = np.zeros((size, size), dtype=bool)
    mask[max(0, y0):min(size, y1), max(0, x0):min(size, x1)] = True
    return mask


def _portrait(size: int, rng: np.random.Generator, tone: np.ndarray, amount: float = 4.0) -> np.ndarray:
    base = _gradient(size, (168.0, 176.0, 190.0), (120.0, 130.0, 148.0))
    face = _ellipse(size, size * 0.5, size * 0.48, size * 0.26, size * 0.33)
    jitter = rng.uniform(-8.0, 8.0, size=3).astype(np.float32)
    base[face] = np.clip(tone + jitter, 0, 255)
    hair = _ellipse(size, size * 0.5, size * 0.30, size * 0.30, size * 0.18)
    base[hair & ~face] = np.array([58.0, 48.0, 44.0], dtype=np.float32)
    return base + _noise(rng, size, amount)


def _make_image(recipe_id: str, index: int) -> Image.Image:
    rng = np.random.default_rng(_seed(recipe_id, index))
    size = 160 + 8 * (index % 5)  # 160..192, deterministic size ladder

    if recipe_id in {"open_eyes", "chin_fix"}:
        array = _portrait(size, rng, SKIN)

    elif recipe_id == "skin_retouch":
        array = _portrait(size, rng, SKIN, amount=3.0)
        # a few blemish dots the retouch is supposed to smooth
        for _ in range(6):
            bx = int(rng.uniform(size * 0.32, size * 0.68))
            by = int(rng.uniform(size * 0.30, size * 0.62))
            array[max(0, by - 2):by + 2, max(0, bx - 2):bx + 2] -= 22.0

    elif recipe_id == "remove_bystanders":
        array = _gradient(size, (150.0, 162.0, 172.0), (110.0, 118.0, 130.0))
        main = _ellipse(size, size * 0.42, size * 0.58, size * 0.18, size * 0.30)
        array[main] = SKIN
        for cx, cy, r in ((0.82, 0.55, 0.10), (0.18, 0.45, 0.08)):
            blob = _ellipse(size, size * cx, size * cy, size * r, size * r * 1.4)
            array[blob] = SKIN_DARK + rng.uniform(-10.0, 10.0, size=3)
        array += _noise(rng, size, 4.0)

    elif recipe_id == "remove_watermark":
        array = _gradient(size, (232.0, 230.0, 226.0), (196.0, 192.0, 186.0))
        block = _rect(size, int(size * 0.45), int(size * 0.68), int(size * 0.95), int(size * 0.92))
        array[block] = 150.0
        for row in range(4):
            y0 = int(size * (0.70 + 0.05 * row))
            stripe = _rect(size, int(size * 0.48), y0, int(size * 0.92), y0 + max(2, size // 48))
            array[stripe] = 60.0
        array += _noise(rng, size, 3.0)

    elif recipe_id == "restore_old_photo":
        gray = _gradient(size, (200.0, 200.0, 200.0), (110.0, 110.0, 110.0))
        sepia = np.stack([gray[:, :, 0] * 0.62, gray[:, :, 1] * 0.55, gray[:, :, 2] * 0.42], axis=-1)
        face = _ellipse(size, size * 0.5, size * 0.5, size * 0.22, size * 0.28)
        sepia[face] *= 1.06
        array = sepia + _noise(rng, size, 12.0)

    elif recipe_id == "golden_hour":
        array = _gradient(size, (252.0, 186.0, 118.0), (128.0, 84.0, 46.0))
        face = _ellipse(size, size * 0.5, size * 0.52, size * 0.24, size * 0.30)
        array[face] = np.clip(SKIN + np.array([14.0, 2.0, -10.0]), 0, 255)
        array += _noise(rng, size, 4.0)

    elif recipe_id == "low_light_fix":
        array = _gradient(size, (58.0, 58.0, 66.0), (18.0, 18.0, 24.0))
        face = _ellipse(size, size * 0.5, size * 0.5, size * 0.24, size * 0.30)
        array[face] = np.array([74.0, 60.0, 50.0], dtype=np.float32)
        array += _noise(rng, size, 3.0)

    elif recipe_id == "upscale_4k":
        yy, xx = np.mgrid[0:size, 0:size]
        checks = (((xx // 8) + (yy // 8)) % 2).astype(np.float32)
        array = np.stack([checks * 90.0 + 90.0] * 3, axis=-1)
        circle = _ellipse(size, size * 0.5, size * 0.5, size * 0.28, size * 0.28)
        array[circle] = np.array([70.0, 110.0, 150.0], dtype=np.float32)
        array += _noise(rng, size, 6.0)

    else:  # product_studio
        array = _gradient(size, (222.0, 220.0, 216.0), (182.0, 180.0, 176.0))
        obj = _rect(size, int(size * 0.32), int(size * 0.30), int(size * 0.68), int(size * 0.78))
        array[obj] = np.array([64.0, 68.0, 76.0], dtype=np.float32)
        shade = _rect(size, int(size * 0.32), int(size * 0.70), int(size * 0.68), int(size * 0.80))
        array[shade] = np.clip(array[shade] - 26.0, 0, 255)
        array += _noise(rng, size, 3.0)

    return Image.fromarray(np.clip(array, 0, 255).astype(np.uint8), mode="RGB")


def generate_all(force: bool = False) -> dict[str, int]:
    """Write the golden images for every recipe; returns ``{recipe: count}``."""
    counts: dict[str, int] = {}
    for recipe_id in ALL_RECIPES:
        directory = GOLDEN_ROOT / recipe_id / "images"
        directory.mkdir(parents=True, exist_ok=True)
        written = 0
        for index in range(COUNT_PER_RECIPE):
            path = directory / f"{recipe_id}_{index:02d}.png"
            if force or not path.is_file():
                _make_image(recipe_id, index).save(path, format="PNG")
                written += 1
        counts[recipe_id] = len(list(directory.glob("*.png")))
    return counts


if __name__ == "__main__":
    result = generate_all()
    for recipe_id, count in result.items():
        print(f"{recipe_id:20s} {count:3d} images")
