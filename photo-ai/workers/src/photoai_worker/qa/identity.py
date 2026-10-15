"""Identity similarity (AGENT_SKILLS S11).

The public ``identity_cosine`` function keeps the real interface so a real
ArcFace/InsightFace embedder can be plugged in later. In P0 (no AI) an
``embedder`` callable can be injected; the default returns a deterministic
placeholder so the pipeline is runnable and testable with the mock provider.
"""
from __future__ import annotations

from typing import Callable, Optional

import numpy as np
from PIL import Image

Embedder = Callable[[Image.Image], np.ndarray]


def default_placeholder_embedder(image: Image.Image) -> np.ndarray:
    """Deterministic, dependency-free stand-in for a face embedder.

    NOTE: this is *not* a real identity model. It exists so the pipeline and QA
    plumbing can be exercised in P0; it must be replaced in P1.
    """
    gray = np.asarray(image.convert("L").resize((16, 16)), dtype=np.float64)
    vector = gray.flatten()
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two vectors, robust to zero vectors."""
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0.0:
        return 0.0
    return float(np.dot(a, b) / denom)


def identity_cosine(
    original: Image.Image,
    edited: Image.Image,
    embedder: Optional[Embedder] = None,
) -> float:
    """Return the cosine similarity between original and edited identity."""
    embedder = embedder or default_placeholder_embedder
    return cosine_similarity(embedder(original), embedder(edited))
