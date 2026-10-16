"""Face / person / product detectors (design §2 detectors).

Each detector uses its GPU/OpenCV model when available and a deterministic
classical fallback otherwise, so the pipeline never hard-fails offline.
"""
from . import (  # noqa: F401
    eyes_gaze,
    face_analyzer,
    face_parsing,
    ocr_damage,
    person_depth,
    product_matting,
)

__all__ = [
    "face_analyzer",
    "face_parsing",
    "eyes_gaze",
    "person_depth",
    "product_matting",
    "ocr_damage",
]
