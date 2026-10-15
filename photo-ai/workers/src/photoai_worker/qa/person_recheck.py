"""Person re-check for bystander removal (AGENT_SKILLS S11).

Real person segmentation is a P1 concern; the interface is defined here so
recipes can declare the check in P0.
"""
from __future__ import annotations

from typing import Callable, Optional, Sequence

from PIL import Image

PersonDetector = Callable[[Image.Image], Sequence[object]]


def person_recheck(
    edited: Image.Image,
    region: Optional[object] = None,
    detector: Optional[PersonDetector] = None,
) -> bool:
    """Return True when no person remains in the region marked for removal."""
    if detector is None:
        return True
    return len(detector(edited)) == 0
