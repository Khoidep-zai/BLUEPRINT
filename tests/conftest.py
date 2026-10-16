"""Shared test fixtures: a hermetic workspace and synthetic images."""
from __future__ import annotations

import os
import tempfile

import numpy as np
import pytest
from PIL import Image

# Point the app at a throwaway workspace *before* photoai.config is imported,
# so tests never touch the user's ~/.photo-ai-desktop.
_TMP = tempfile.mkdtemp(prefix="photoai-test-")
os.environ["PHOTOAI_WORKSPACE"] = os.path.join(_TMP, "workspace")
os.environ["PHOTOAI_DB_PATH"] = os.path.join(_TMP, "workspace", "test.db")


@pytest.fixture
def synthetic_portrait() -> Image.Image:
    """A deterministic 64x64 frame with a skin-like face patch in the centre."""
    rng = np.random.default_rng(0)
    arr = rng.integers(50, 110, size=(64, 64, 3), dtype=np.uint8)
    arr[16:48, 20:44] = np.array([205, 150, 120], dtype=np.uint8)
    return Image.fromarray(arr, "RGB")


@pytest.fixture
def random_rgb() -> Image.Image:
    rng = np.random.default_rng(1)
    arr = rng.integers(0, 255, size=(48, 48, 3), dtype=np.uint8)
    return Image.fromarray(arr, "RGB")
