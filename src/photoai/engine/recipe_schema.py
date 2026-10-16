"""Pydantic schema for ``recipes/*.yaml`` (design §2 recipe_schema.py).

A recipe is an ordered list of step blocks (``detect`` / ``filter`` / ``edit`` /
``blend`` / ``qa``). Adding a new capability therefore never touches the core
runner — it is a data change.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DetectStep(BaseModel):
    """Which detectors stage 2 must run."""

    model_config = ConfigDict(extra="ignore")

    faces: bool = False
    eyes_gaze: bool = False
    persons: bool = False
    text_logo: bool = False
    scratches: bool = False
    product: bool = False


class FilterStep(BaseModel):
    """Business guards that can abort a job before any GPU work happens."""

    only_closed_eyes: bool = False
    ear_below: float = 0.20
    require_face: bool = False


class EditStep(BaseModel):
    """Which hybrid CV + GPU editor stage 4 runs, and with what strength."""

    model_config = ConfigDict(extra="allow")

    editor: str = "inpaint"
    strength: float = Field(default=0.5, ge=0.0, le=1.0)
    padding: float = 0.3
    scale: float = 2.0
    prompt_id: Optional[str] = None


class BlendStep(BaseModel):
    method: str = "feather"  # feather | poisson | none
    radius_px: int = 8


class QAStep(BaseModel):
    """Numeric QA thresholds. Suffix encodes the comparison direction.

    ``*_min`` -> metric must be >= threshold, ``*_max`` -> metric must be <=,
    ``ocr_recheck`` / ``person_recheck`` -> boolean gate.
    """

    model_config = ConfigDict(extra="allow")

    ear_min: Optional[float] = None
    identity_cosine_min: Optional[float] = None
    outside_mask_ssim_min: Optional[float] = None
    structure_similarity_min: Optional[float] = None
    clip_ratio_max: Optional[float] = None
    delta_e_skin_max: Optional[float] = None
    texture_variance_min: Optional[float] = None
    product_pixel_diff_max: Optional[float] = None
    ocr_recheck: Optional[bool] = None
    person_recheck: Optional[bool] = None


class RetryConfig(BaseModel):
    max: int = 2
    strength_step: float = -0.1
    reseed: bool = True


class PromptConfig(BaseModel):
    vi: str = ""
    en: str = ""


class Recipe(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    version: int = 1
    name_vi: str = ""
    name_en: str = ""
    ownership_required: bool = False
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    prompt: PromptConfig = Field(default_factory=PromptConfig)

    # --- convenience accessors over the ordered step list -----------------
    def _block(self, name: str) -> Dict[str, Any]:
        for step in self.steps:
            if name in step and step[name] is not None:
                return dict(step[name])
        return {}

    @property
    def detect(self) -> DetectStep:
        return DetectStep(**self._block("detect"))

    @property
    def filter(self) -> FilterStep:
        return FilterStep(**self._block("filter"))

    @property
    def edit(self) -> EditStep:
        return EditStep(**self._block("edit"))

    @property
    def blend(self) -> BlendStep:
        return BlendStep(**self._block("blend"))

    @property
    def qa(self) -> QAStep:
        return QAStep(**self._block("qa"))

    def step(self, name: str) -> Optional[Dict[str, Any]]:
        block = self._block(name)
        return block or None


__all__ = [
    "Recipe",
    "DetectStep",
    "FilterStep",
    "EditStep",
    "BlendStep",
    "QAStep",
    "RetryConfig",
    "PromptConfig",
]
