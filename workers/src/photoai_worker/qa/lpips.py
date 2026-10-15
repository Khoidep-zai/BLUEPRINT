"""Perceptual / structure similarity (AGENT_SKILLS S11).

``structure_similarity`` is implemented here as a normalised, downscaled
luminance difference -- a lightweight, dependency-free proxy for LPIPS used to
detect gross layout changes. A real LPIPS network can be injected later via
``perceptual``.
"""
from __future__ import annotations

from typing import Callable, Optional

import numpy as np
from PIL import Image

Perceptual = Callable[[Image.Image, Image.Image], float]

_WORK_SIZE = (64, 64)


def structure_similarity(
    original: Image.Image,
    edited: Image.Image,
    size: tuple[int, int] = _WORK_SIZE,
) -> float:
    """Return a similarity in [0, 1]; 1.0 means identical structure."""
    a = np.asarray(original.convert("L").resize(size), dtype=np.float64)
    b = np.asarray(edited.convert("L").resize(size), dtype=np.float64)
    # Normalise each to zero mean / unit std so exposure shifts are ignored and
    # only structural change counts.
    a = (a - a.mean()) / (a.std() + 1e-8)
    b = (b - b.mean()) / (b.std() + 1e-8)
    diff = float(np.mean((a - b) ** 2))
    return float(np.clip(1.0 - diff / 2.0, 0.0, 1.0))


def perceptual_similarity(
    original: Image.Image,
    edited: Image.Image,
    model: Optional[Perceptual] = None,
) -> float:
    """Return LPIPS-like similarity (1.0 = identical) using ``model`` if given."""
    if model is not None:
        return float(model(original, edited))
    return structure_similarity(original, edited)
