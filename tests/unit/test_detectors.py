"""Unit tests for the six detectors (design §2 detectors)."""
from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from photoai.detectors import eyes_gaze, face_analyzer, face_parsing, ocr_damage, person_depth, product_matting


def test_face_analyzer_returns_box_and_landmarks(synthetic_portrait):
    faces = face_analyzer.detect_faces(synthetic_portrait)
    assert faces
    main = face_analyzer.largest_face(faces)
    assert main is not None and main.area > 0

    landmarks = face_analyzer.landmarks_68(main)
    assert landmarks.shape == (68, 2)


def test_face_analyzer_embedding_is_unit_norm(synthetic_portrait):
    vector = face_analyzer.embed(synthetic_portrait)
    assert abs(float(np.linalg.norm(vector)) - 1.0) < 1e-9


def test_compute_ear_matches_formula():
    points = [(0, 0), (0.5, -1), (0.5, 1), (2, 0), (1.5, 1), (1.5, -1)]
    # vertical = |p2-p6| + |p3-p5| = 1 + 1 = 2, horizontal = 2 -> EAR = 0.5
    assert eyes_gaze.compute_ear(points) == 0.5


def test_detect_eyes_targets_requested_ear(synthetic_portrait):
    face = face_analyzer.largest_face(face_analyzer.detect_faces(synthetic_portrait))
    state = eyes_gaze.detect_eyes(synthetic_portrait, face=face, left_ear=0.18, right_ear=0.22)
    assert state is not None
    assert state.left_ear == pytest.approx(0.18, abs=1e-6)
    assert state.right_ear == pytest.approx(0.22, abs=1e-6)
    assert state.ear == pytest.approx(0.18, abs=1e-6)


def test_face_parsing_returns_skin_mask(synthetic_portrait):
    mask = face_parsing.skin_mask(synthetic_portrait)
    assert mask.mode == "L"
    assert mask.size == synthetic_portrait.size
    assert face_parsing.skin_coverage(synthetic_portrait) > 0


def test_person_depth_helpers(synthetic_portrait):
    persons = person_depth.detect_persons(synthetic_portrait)
    assert isinstance(persons, list)
    depth = person_depth.depth_map(synthetic_portrait)
    assert depth.size == synthetic_portrait.size


def test_product_matting_returns_alpha(synthetic_portrait):
    alpha = product_matting.product_alpha(synthetic_portrait)
    assert alpha.mode == "L"
    assert alpha.size == synthetic_portrait.size
    assert product_matting.product_bounding_box(alpha) is not None


def test_ocr_damage_detectors_return_regions(synthetic_portrait):
    assert isinstance(ocr_damage.detect_text_logo(synthetic_portrait), list)
    assert isinstance(ocr_damage.detect_scratches(synthetic_portrait), list)


def test_product_alpha_uses_supplied_mask():
    img = Image.new("RGB", (20, 20), (128, 128, 128))
    mask = Image.new("L", (20, 20), 0)
    mask.paste(255, (5, 5, 15, 15))
    alpha = product_matting.product_alpha(img, mask)
    assert np.asarray(alpha)[10, 10] == 255
