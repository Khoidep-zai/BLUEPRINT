"""Pipeline execution context - carries image, detections, and state through steps."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from PIL import Image


@dataclass
class Detection:
    kind: str  # "face", "eye", "person", "text", "logo"
    bbox: list[int]  # [x0, y0, x1, y1]
    confidence: float
    metadata: dict = field(default_factory=dict)


@dataclass
class PipelineContext:
    job_id: str
    recipe_id: str
    input_image: Image.Image
    mask_image: Optional[Image.Image] = None
    detections: list[Detection] = field(default_factory=list)
    edited_image: Optional[Image.Image] = None
    blend_image: Optional[Image.Image] = None
    qa_report: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    attempt: int = 0
    params: dict = field(default_factory=dict)
    storage_key: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    @property
    def size(self) -> tuple[int, int]:
        return self.input_image.size
