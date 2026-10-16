"""Mutable pipeline state threaded through all seven stages (design §2).

``original`` is locked: s1_ingest stores the original as a read-only NumPy array
(``original_rgb``) so it is impossible to overwrite the source pixels — the
design's *Original Immutability* rule.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
from PIL import Image


@dataclass
class StepLog:
    name: str
    status: str
    attempt: int = 1
    detail: str = ""


@dataclass
class PipelineContext:
    """Everything a recipe step needs, carried across s1 → s7."""

    image: Image.Image
    mask: Optional[Image.Image] = None
    params: Dict[str, Any] = field(default_factory=dict)
    recipe_id: str = ""

    # Detection results (stage 2).
    detections: Dict[str, Any] = field(default_factory=dict)

    # Quality metrics + non-fatal notes (stage 6).
    metrics: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    step_log: List[StepLog] = field(default_factory=list)

    # Edited image before / after blending (stages 4-5).
    edited: Optional[Image.Image] = None
    original: Optional[Image.Image] = None
    edit_mask: Optional[Image.Image] = None

    # Regions of interest produced by stage 3.
    rois: List[Any] = field(default_factory=list)

    # Frequency separation layers (stage 3).
    original_rgb: Optional[np.ndarray] = None
    low_freq: Optional[np.ndarray] = None
    high_freq: Optional[np.ndarray] = None

    export_path: Optional[str] = None
    cv_fallback_image: Optional[Image.Image] = None
    job_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.original is None:
            self.original = self.image.copy()

    @property
    def strength(self) -> float:
        return float(self.params.get("strength", 0.5))

    @property
    def seed(self) -> int:
        return int(self.params.get("seed", 42))

    def log(self, name: str, status: str, attempt: int = 1, detail: str = "") -> None:
        self.step_log.append(StepLog(name=name, status=status, attempt=attempt, detail=detail))


# Alias kept for readability in older call sites / docs.
JobContext = PipelineContext

__all__ = ["PipelineContext", "JobContext", "StepLog"]
