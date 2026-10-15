"""Pydantic schema for recipe YAML files (§2.3 ADR-002, §6 schema).

Example:
    id: open_eyes
    version: 1
    steps:
      - detect: { faces: true, eyes_ear: true }
      - filter: { only_closed_eyes: true, ear_below: 0.2 }
      - edit:   { provider: inpaint_face, strength: 0.5, padding: 0.3 }
      - blend:  { method: feather, radius_px: 8 }
      - qa:
          ear_min: 0.2
          identity_cosine_min: 0.85
          outside_mask_ssim_min: 0.98
    retry: { max: 2, strength_step: -0.1, reseed: true }
    prompt: { vi: prompts/open_eyes.vi.md, en: prompts/open_eyes.en.md }
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field, model_validator


class DetectStep(BaseModel):
    faces: bool = False
    eyes_ear: bool = False
    person: bool = False
    text_logo: bool = False


class FilterStep(BaseModel):
    only_closed_eyes: bool = False
    ear_below: Optional[float] = None
    min_face_size_px: Optional[int] = None


class EditStep(BaseModel):
    provider: str = "mock"
    strength: float = Field(default=0.5, ge=0.0, le=1.0)
    padding: float = Field(default=0.3, ge=0.0, le=1.0)
    prompt_id: Optional[str] = None


class BlendStep(BaseModel):
    method: str = "feather"
    radius_px: int = 8


class QAStep(BaseModel):
    ear_min: Optional[float] = None
    identity_cosine_min: Optional[float] = None
    outside_mask_ssim_min: Optional[float] = None
    delta_e_skin_max: Optional[float] = None
    clip_ratio_max: Optional[float] = None
    ocr_recheck: bool = False
    person_recheck: bool = False


class RetryConfig(BaseModel):
    max: int = 2
    strength_step: float = -0.1
    reseed: bool = True


class Recipe(BaseModel):
    id: str
    version: int = 1
    steps: list[dict[str, Any]] = Field(default_factory=list)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    prompt: dict[str, str] = Field(default_factory=dict)
    qa: QAStep = Field(default_factory=QAStep)

    @model_validator(mode="after")
    def check_id(self) -> "Recipe":
        if not self.id or not self.id.isidentifier():
            raise ValueError(f"recipe id must be a valid python identifier: {self.id!r}")
        return self

    @classmethod
    def load(cls, path: str | Path) -> "Recipe":
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)
