"""Unit tests for the classical CV operations (design §3.2-§3.4)."""
from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from photoai.processors.cv_ops import color_lighting, geometry_tps, studio_physics
from photoai.processors.cv_ops.frequency_sep import FrequencySeparator


def test_frequency_recombine_preserves_pixels_outside_mask():
    rng = np.random.default_rng(3)
    rgb = rng.integers(0, 255, (32, 32, 3), dtype=np.uint8)
    _, high = FrequencySeparator.decompose(rgb)

    mask = np.zeros((32, 32), dtype=np.float32)
    mask[8:24, 8:24] = 1.0
    edited = rgb.copy()
    edited[8:24, 8:24] = 210

    out = FrequencySeparator.recombine(edited, high, mask)
    assert np.array_equal(out[0, 0], rgb[0, 0])  # outside mask untouched
    assert out.shape == rgb.shape


def test_gray_world_white_balance_neutralises_cast():
    arr = np.full((16, 16, 3), 120, dtype=np.uint8)
    arr[..., 2] = 180  # strong blue cast
    before = arr.reshape(-1, 3).mean(axis=0)
    balanced = color_lighting.gray_world_white_balance(arr)
    after = balanced.reshape(-1, 3).mean(axis=0)
    assert (after.max() - after.min()) < (before.max() - before.min())


def test_lab_roundtrip_is_close():
    rng = np.random.default_rng(4)
    rgb = rng.integers(0, 255, (8, 8, 3), dtype=np.uint8)
    restored = color_lighting.lab_to_srgb(color_lighting.srgb_to_lab(rgb))
    assert np.abs(restored.astype(int) - rgb.astype(int)).max() <= 3


def test_film_grain_is_deterministic():
    rgb = np.full((16, 16, 3), 128, dtype=np.uint8)
    a = color_lighting.film_grain(rgb, seed=7)
    b = color_lighting.film_grain(rgb, seed=7)
    assert np.array_equal(a, b)


def test_studio_compositor_keeps_product_pixels():
    orig = np.full((48, 48, 3), 90, dtype=np.uint8)
    orig[12:36, 12:36] = (200, 40, 40)
    alpha = np.zeros((48, 48), dtype=np.uint8)
    alpha[12:36, 12:36] = 255
    backdrop = np.full((48, 48, 3), 230, dtype=np.uint8)

    out = studio_physics.compose_luxury_studio_product(orig, alpha, backdrop)
    locked = alpha == 255
    assert np.array_equal(out[locked], orig[locked])  # product bit-identical


def test_chin_warp_pins_borders_and_keeps_shape():
    rng = np.random.default_rng(5)
    img = rng.integers(0, 255, (64, 64, 3), dtype=np.uint8)
    landmarks = np.zeros((68, 2), dtype=np.float64)
    landmarks[:, 0] = np.linspace(20, 44, 68)
    landmarks[:, 1] = np.linspace(16, 48, 68)

    warped = geometry_tps.subtle_perspective_chin_warp(img, landmarks)
    assert warped.shape == img.shape
    assert np.array_equal(warped[0, 0], img[0, 0])  # border pinned


def test_tps_identity_when_control_points_match():
    points = np.array([[0, 0], [10, 0], [0, 10], [10, 10], [5, 5]], dtype=np.float64)
    coeffs = geometry_tps.tps_fit(points, points)
    probe = np.array([[2.0, 3.0], [7.0, 7.0]])
    mapped = geometry_tps.tps_apply(coeffs, points, probe)
    assert np.allclose(mapped, probe, atol=1e-6)
