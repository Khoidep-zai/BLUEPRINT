"""Recipe schema definitions.

Recipes are data-driven (AGENT_SKILLS §2.4): adding a feature means adding a
YAML file in ``recipes/``, never hard-coding logic in the core.
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class DetectStep(BaseModel):
    """Detection step configuration."""

    faces: bool = False
    eyes_ear: bool = False
    persons: bool = False
    text_logo: bool = False


class FilterStep(BaseModel):
    """Filter step configuration."""

    only_closed_eyes: bool = False
    ear_below: float = 0.2


class EditStep(BaseModel):
    """Edit step configuration."""

    provider: str = "mock"
    strength: float = Field(default=0.5, ge=0.0, le=1.0)
    padding: float = 0.3


class BlendStep(BaseModel):
    """Blend step configuration."""

    method: str = "feather"
    radius_px: int = 8


class QAStep(BaseModel):
    """QA thresholds for a recipe."""

    ear_min: Optional[float] = None
    identity_cosine_min: Optional[float] = None
    outside_mask_ssim_min: Optional[float] = None
    clip_ratio_max: Optional[float] = None
    delta_e_skin_max: Optional[float] = None
    ocr_recheck: Optional[bool] = None
    person_recheck: Optional[bool] = None


class RetryConfig(BaseModel):
    """Retry configuration."""

    max: int = 2
    strength_step: float = -0.1
    reseed: bool = True


class PromptConfig(BaseModel):
    """Prompt file paths."""

    vi: str = ""
    en: str = ""


class Recipe(BaseModel):
    """A parsed recipe.

    ``steps`` keep their raw ordered form so the runner can execute them in the
    declared order (``detect -> filter -> edit -> blend -> qa``).
    """

    id: str
    version: int
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    prompt: PromptConfig = Field(default_factory=PromptConfig)

    @property
    def qa(self) -> QAStep:
        """Extract QA thresholds from the ``qa`` step, if present."""
        for step in self.steps:
            if "qa" in step:
                return QAStep(**step["qa"])
        return QAStep()

    def step(self, name: str) -> Optional[Dict[str, Any]]:
        """Return the payload of the first step with the given name."""
        for step in self.steps:
            if name in step:
                return step[name]
        return None
