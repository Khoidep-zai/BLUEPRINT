"""Stage 1 — Ingest: normalise to RGB and lock the original (design §2, rule 2)."""
from __future__ import annotations

import numpy as np

from photoai.engine.context import PipelineContext
from photoai.storage.image_codec import normalize_orientation


def run(context: PipelineContext) -> PipelineContext:
    rgb = normalize_orientation(context.image.convert("RGB"))
    context.image = rgb
    context.original = rgb.copy()

    # Lock the source pixels: Original Immutability (design §1.2 rule 2).
    arr = np.asarray(rgb, dtype=np.uint8)
    arr.flags.writeable = False
    context.original_rgb = arr

    context.log("ingest", "ok", detail=f"{rgb.width}x{rgb.height}")
    return context
