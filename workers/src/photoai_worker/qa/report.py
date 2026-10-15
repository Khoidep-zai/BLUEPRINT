"""QA report module (S11 §112) - builds qa_report JSON for a job attempt."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class QAReport:
    passed: bool
    attempt: int
    metrics: dict[str, float] = field(default_factory=dict)
    thresholds: dict[str, float] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "attempt": self.attempt,
            "metrics": dict(self.metrics),
            "thresholds": dict(self.thresholds),
            "warnings": list(self.warnings),
        }

    def merge(self, other: "QAReport") -> "QAReport":
        """Merge another report into this one (keep best metrics)."""
        self.metrics.update(other.metrics)
        self.thresholds.update(other.thresholds)
        self.warnings.extend(other.warnings)
        self.passed = self.passed and other.passed
        return self
