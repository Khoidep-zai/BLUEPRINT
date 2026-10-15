"""Retry policy for QA failures (§11 S11).

Fail QA -> retry tối đa 2 lần (giảm strength, đổi seed); vẫn fail -> trả bản tốt nhất kèm warnings.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RetryPolicy:
    max_attempts: int = 2
    strength_step: float = -0.1
    reseed: bool = True

    def next_strength(self, current: float, attempt: int) -> float:
        return max(0.0, min(1.0, current + self.strength_step * attempt))

    def should_retry(self, attempt: int, passed: bool) -> bool:
        return (not passed) and attempt < self.max_attempts
