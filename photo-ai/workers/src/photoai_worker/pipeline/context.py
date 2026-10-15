"""Job context passed through the recipe pipeline (AGENT_SKILLS S1)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from PIL import Image


@dataclass
class StepLog:
    """Timing/outcome record for one pipeline step."""

    name: str
    status: str
    attempt: int = 1
    detail: str = ""


@dataclass
class JobContext:
    """Mutable state threaded through ``detect -> filter -> edit -> blend -> qa``."""

    image: Image.Image
    mask: Optional[Image.Image] = None
    params: Dict[str, Any] = field(default_factory=dict)
    recipe_id: str = ""

    # Detection results keyed by detector name (faces, eyes, persons, text_logo).
    detections: Dict[str, Any] = field(default_factory=dict)
    # QA metrics accumulated during the run.
    metrics: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    # Provider call metadata (one dict per invocation).
    provider_calls: List[Dict[str, Any]] = field(default_factory=list)
    # Per-step audit trail.
    step_log: List[StepLog] = field(default_factory=list)

    edited: Optional[Image.Image] = None
    original: Optional[Image.Image] = None
    # The final (feathered) mask actually used to composite the edit.
    edit_mask: Optional[Image.Image] = None

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
        self.step_log.append(
            StepLog(name=name, status=status, attempt=attempt, detail=detail)
        )
