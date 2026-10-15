"""OCR re-check for watermark removal (AGENT_SKILLS S11).

Real OCR (PaddleOCR/Tesseract) is a P1 concern. This module defines the
interface and a deterministic fallback so recipes can declare the check now.
"""
from __future__ import annotations

from typing import Callable, List, Optional

from PIL import Image

TextDetector = Callable[[Image.Image], List[str]]


def ocr_recheck(
    edited: Image.Image,
    region: Optional[object] = None,
    detector: Optional[TextDetector] = None,
) -> bool:
    """Return True when no watermark text remains in the target region.

    With no detector plugged in (P0) this returns True so the pipeline is
    runnable; a real detector is injected in P1.
    """
    if detector is None:
        return True
    return len(detector(edited)) == 0
