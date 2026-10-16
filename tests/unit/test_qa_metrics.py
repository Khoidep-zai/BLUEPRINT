"""Unit tests for QA metrics + threshold evaluation (design §2 qa)."""
from __future__ import annotations

import numpy as np
from PIL import Image

from photoai.qa import metrics
from photoai.qa.evaluator import evaluate


def test_ssim_identical_is_one(synthetic_portrait):
    assert metrics.ssim(synthetic_portrait, synthetic_portrait) == 1.0


def test_structure_and_identity_identical(synthetic_portrait):
    assert metrics.structure_similarity(synthetic_portrait, synthetic_portrait) == 1.0
    assert metrics.identity_cosine(synthetic_portrait, synthetic_portrait) == 1.0


def test_clip_ratio_counts_saturated_pixels():
    white = Image.new("RGB", (10, 10), (255, 255, 255))
    assert metrics.clip_ratio(white) == 1.0
    mid = Image.new("RGB", (10, 10), (128, 128, 128))
    assert metrics.clip_ratio(mid) == 0.0


def test_texture_variance_positive_on_noise():
    rng = np.random.default_rng(2)
    noisy = Image.fromarray(rng.integers(0, 255, (32, 32, 3), dtype=np.uint8), "RGB")
    assert metrics.texture_variance(noisy) > 0


def test_delta_e_skin_zero_for_identical(synthetic_portrait):
    mask = Image.new("L", synthetic_portrait.size, 255)
    assert metrics.delta_e_skin(synthetic_portrait, synthetic_portrait, mask) == 0.0


def test_delta_e_skin_handles_empty_mask(synthetic_portrait):
    empty = Image.new("L", synthetic_portrait.size, 0)
    assert metrics.delta_e_skin(synthetic_portrait, synthetic_portrait, empty) == 0.0


def test_outside_mask_ssim_ignores_masked_region():
    original = Image.new("RGB", (32, 32), (100, 100, 100))
    edited = original.copy()
    edited.paste((255, 0, 0), (0, 0, 16, 32))  # change left half
    mask = Image.new("L", (32, 32), 0)
    mask.paste(255, (0, 0, 16, 32))  # ...which is the masked-out half
    assert metrics.outside_mask_ssim(original, edited, mask) == 1.0


def test_evaluate_min_max_and_boolean_gates():
    report = evaluate(
        {"identity_cosine": 0.9, "clip_ratio": 0.02, "ocr_recheck": True},
        {"identity_cosine_min": 0.8, "clip_ratio_max": 0.05, "ocr_recheck": True},
    )
    assert report.passed

    failed = evaluate(
        {"identity_cosine": 0.5, "clip_ratio": 0.2, "ocr_recheck": False},
        {"identity_cosine_min": 0.8, "clip_ratio_max": 0.05, "ocr_recheck": True},
    )
    assert not failed.passed
    assert set(failed.failed_checks()) == {"identity_cosine_min", "clip_ratio_max", "ocr_recheck"}
