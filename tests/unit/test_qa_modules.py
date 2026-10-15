"""Tests for QA measurement modules and report evaluation (P0 task 8)."""
import numpy as np
import pytest
from PIL import Image

from photoai_worker.qa import clip_ratio, identity, lpips, ocr_recheck, person_recheck, ssim
from photoai_worker.qa import skin_color
from photoai_worker.qa.report import best_effort_report, evaluate


def _uniform(value: int, size=(24, 24)) -> Image.Image:
    return Image.new("RGB", size, (value, value, value))


def _random(seed: int = 0, size=(24, 24)) -> Image.Image:
    rng = np.random.default_rng(seed)
    array = rng.integers(0, 256, size=(size[1], size[0], 3), dtype=np.uint8)
    return Image.fromarray(array, mode="RGB")


def test_ssim_identical_is_one():
    image = _random(1)
    assert ssim.ssim(image, image.copy()) == pytest.approx(1.0, abs=1e-6)


def test_ssim_is_symmetric_and_bounded():
    a = _random(1)
    b = _random(2)
    value = ssim.ssim(a, b)
    assert -1.0 <= value <= 1.0
    assert ssim.ssim(a, b) == pytest.approx(ssim.ssim(b, a), abs=1e-9)


def test_outside_mask_ssim_ignores_inside_changes():
    original = _uniform(128)
    edited = original.copy()
    # Change only a small centre block.
    edited.paste(_uniform(255, (8, 8)), (8, 8))
    mask = Image.new("L", (24, 24), 0)
    mask.paste(Image.new("L", (8, 8), 255), (8, 8))
    assert ssim.outside_mask_ssim(original, edited, mask) == pytest.approx(1.0, abs=1e-6)
    # Without the mask the overall SSIM drops.
    assert ssim.outside_mask_ssim(original, edited, None) < 1.0


def test_clip_ratio_detects_clipping():
    assert clip_ratio.clip_ratio(_uniform(128)) == 0.0
    assert clip_ratio.clip_ratio(_uniform(0)) == 1.0
    assert clip_ratio.clip_ratio(_uniform(255)) == 1.0


def test_identity_cosine_identical_is_high():
    image = _random(3)
    assert identity.identity_cosine(image, image.copy()) == pytest.approx(1.0, abs=1e-6)


def test_identity_cosine_handles_zero_vector():
    zero = np.zeros(10)
    assert identity.cosine_similarity(zero, zero) == 0.0


def test_structure_similarity_identical_and_different():
    image = _random(4)
    assert lpips.structure_similarity(image, image.copy()) == pytest.approx(1.0, abs=1e-6)
    assert lpips.structure_similarity(image, _random(5)) < 1.0


def test_delta_e_skin_zero_for_identical():
    image = _random(6)
    assert skin_color.delta_e_skin(image, image.copy()) == pytest.approx(0.0, abs=1e-6)


def test_delta_e_skin_increases_with_colour_shift():
    image = _uniform(140)
    warmer = _uniform(180)
    assert skin_color.delta_e_skin(image, warmer) > 0.0


def test_texture_variance_positive():
    assert skin_color.texture_variance(_random(7)) > 0.0


def test_ocr_and_person_recheck_default_true():
    image = _uniform(128)
    assert ocr_recheck.ocr_recheck(image) is True
    assert person_recheck.person_recheck(image) is True


def test_ocr_and_person_recheck_with_detectors():
    image = _uniform(128)
    assert ocr_recheck.ocr_recheck(image, detector=lambda img: []) is True
    assert ocr_recheck.ocr_recheck(image, detector=lambda img: ["wm"]) is False
    assert person_recheck.person_recheck(image, detector=lambda img: []) is True
    assert person_recheck.person_recheck(image, detector=lambda img: [1]) is False


def test_evaluate_passes_when_all_thresholds_met():
    metrics = {"ear": 0.27, "identity_cosine": 0.93, "outside_mask_ssim": 0.991}
    thresholds = {"ear_min": 0.2, "identity_cosine_min": 0.85, "outside_mask_ssim_min": 0.98}
    report = evaluate(metrics, thresholds, attempt=1)
    assert report.passed is True
    assert report.failed_checks() == []
    assert report.warnings == []


def test_evaluate_fails_and_lists_checks():
    metrics = {"ear": 0.1, "identity_cosine": 0.9, "clip_ratio": 0.5}
    thresholds = {"ear_min": 0.2, "identity_cosine_min": 0.85, "clip_ratio_max": 0.01}
    report = evaluate(metrics, thresholds, attempt=2)
    assert report.passed is False
    assert set(report.failed_checks()) == {"ear_min", "clip_ratio_max"}
    assert report.attempt == 2


def test_evaluate_boolean_checks():
    report = evaluate(
        {"ocr_recheck": False, "person_recheck": True},
        {"ocr_recheck": True, "person_recheck": True},
    )
    assert report.passed is False
    assert report.failed_checks() == ["ocr_recheck"]


def test_evaluate_missing_metric_fails_min_check():
    report = evaluate({}, {"ear_min": 0.2})
    assert report.passed is False
    assert report.failed_checks() == ["ear_min"]


def test_best_effort_report_adds_warning():
    report = evaluate({"ear": 0.1}, {"ear_min": 0.2}, attempt=3)
    annotated = best_effort_report(report, attempts=3)
    assert annotated.passed is False
    assert any("best-effort" in w for w in annotated.warnings)
    assert annotated.to_dict()["attempt"] == 3
