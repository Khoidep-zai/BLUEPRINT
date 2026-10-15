"""Tests for detectors and mask utilities (AGENT_SKILLS S3/S4)."""
import numpy as np
import pytest
from PIL import Image

from photoai_worker import masking
from photoai_worker.detectors import eyes_ear, face, person, text_logo


def _image(size=(120, 90)) -> Image.Image:
    rng = np.random.default_rng(0)
    array = rng.integers(0, 256, size=(size[1], size[0], 3), dtype=np.uint8)
    return Image.fromarray(array, mode="RGB")


def test_compute_ear_formula():
    # Horizontal span 10, vertical spans 2 and 2 -> (2+2)/(2*10) = 0.2
    points = [(0, 0), (2, -1), (4, -1), (10, 0), (4, 1), (2, 1)]
    assert eyes_ear.compute_ear(points) == pytest.approx(0.2)


def test_compute_ear_requires_six_points():
    with pytest.raises(ValueError):
        eyes_ear.compute_ear([(0, 0), (1, 1)])


def test_compute_ear_zero_horizontal():
    # p1 == p4 -> zero horizontal span -> EAR is defined as 0.0
    points = [(5, 5), (5, 1), (5, 2), (5, 5), (5, 4), (5, 3)]
    assert eyes_ear.compute_ear(points) == 0.0


def test_eye_landmarks_target_ear_is_recovered():
    box = face.FaceBox(x=0, y=0, width=100, height=100)
    points = eyes_ear.eye_landmarks(box, ear=0.15, eye="left")
    assert eyes_ear.compute_ear(points) == pytest.approx(0.15, abs=1e-6)


def test_detect_eyes_closed_flag():
    box = face.FaceBox(x=0, y=0, width=100, height=100)
    state = eyes_ear.detect_eyes(_image(), box, left_ear=0.1, right_ear=0.1, threshold=0.2)
    assert state.eyes_closed is True
    assert state.ear == pytest.approx(0.1, abs=1e-6)
    open_state = eyes_ear.detect_eyes(_image(), box, left_ear=0.4, right_ear=0.4)
    assert open_state.eyes_closed is False


def test_detect_eyes_none_without_face():
    assert eyes_ear.detect_eyes(_image(), face=None) is None


def test_detect_faces_returns_centred_box():
    image = _image((120, 90))
    faces = face.detect_faces(image)
    assert len(faces) == 1
    box = faces[0]
    assert box.width == 40 and box.height == 30
    assert box.center == (60.0, 45.0)
    assert face.largest_face(faces) is box
    assert face.largest_face([]) is None


def test_main_subject_prefers_larger_central_person():
    persons = [
        person.PersonBox(x=0, y=0, width=20, height=20),  # corner, small
        person.PersonBox(x=30, y=20, width=60, height=60),  # bigger, central
    ]
    chosen = person.main_subject(persons, (120, 90))
    assert chosen is persons[1]
    assert person.main_subject([], (120, 90)) is None


def test_merge_regions_bounding_box():
    regions = [
        text_logo.TextRegion(x=0, y=0, width=10, height=10),
        text_logo.TextRegion(x=20, y=30, width=10, height=10),
    ]
    merged = text_logo.merge_regions(regions)
    assert (merged.x, merged.y, merged.width, merged.height) == (0, 0, 30, 40)
    assert text_logo.merge_regions([]) is None


def test_box_mask_and_coverage():
    mask = masking.box_mask((100, 100), (25, 25, 75, 75))
    assert array_sum(mask) > 0
    assert masking.mask_coverage(mask) == pytest.approx(0.25, abs=0.01)


def array_sum(mask):
    return int(np.asarray(mask).sum())


def test_box_mask_clamps_to_bounds():
    mask = masking.box_mask((10, 10), (-5, -5, 100, 100))
    assert masking.mask_coverage(mask) == pytest.approx(1.0)


def test_dilate_grows_mask():
    mask = masking.box_mask((100, 100), (40, 40, 60, 60))
    grown = masking.dilate_mask(mask, 5)
    assert masking.mask_coverage(grown) > masking.mask_coverage(mask)


def test_feather_softens_edges():
    mask = masking.box_mask((100, 100), (40, 40, 60, 60))
    feathered = masking.feather_mask(mask, 4)
    values = np.unique(np.asarray(feathered))
    # Feathering introduces intermediate values between 0 and 255.
    assert np.any((values > 0) & (values < 255))


def test_prepare_mask_noop_without_params():
    mask = masking.box_mask((50, 50), (10, 10, 20, 20))
    assert np.array_equal(np.asarray(masking.prepare_mask(mask)), np.asarray(mask))
