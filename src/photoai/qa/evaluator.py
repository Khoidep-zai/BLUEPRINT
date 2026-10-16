"""Threshold matching and QA report assembly (design §2 qa/evaluator.py).

Threshold keys encode their comparison direction:

* ``*_min`` -> metric must be >= threshold
* ``*_max`` -> metric must be <= threshold
* ``ocr_recheck`` / ``person_recheck`` -> boolean, must be truthy
* anything else -> recorded but not enforced

The report is the contract returned to the UI and stored in ``qa_reports``.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

_BOOLEAN_KEYS = {"ocr_recheck", "person_recheck"}


@dataclass
class QaReport:
    passed: bool
    attempt: int
    metrics: Dict[str, Any] = field(default_factory=dict)
    thresholds: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def failed_checks(self) -> List[str]:
        """Return the threshold keys that were not satisfied."""
        failed: List[str] = []
        for key, threshold in self.thresholds.items():
            if threshold is None:
                continue
            if key.endswith("_min"):
                value = self.metrics.get(key[: -len("_min")])
                if value is None or value < threshold:
                    failed.append(key)
            elif key.endswith("_max"):
                value = self.metrics.get(key[: -len("_max")])
                if value is None or value > threshold:
                    failed.append(key)
            elif key in _BOOLEAN_KEYS and not self.metrics.get(key):
                failed.append(key)
        return failed


def evaluate(metrics: Dict[str, Any], thresholds: Dict[str, Any], attempt: int = 1) -> QaReport:
    """Evaluate ``metrics`` against ``thresholds`` and build a report."""
    clean = {k: v for k, v in thresholds.items() if v is not None}
    report = QaReport(passed=True, attempt=attempt, metrics=dict(metrics), thresholds=clean)
    failed = report.failed_checks()
    if failed:
        report.passed = False
        report.warnings = [f"QA check failed: {key}" for key in failed]
    return report


def best_effort_report(report: QaReport, attempts: int) -> QaReport:
    """Annotate a failed report that is returned as a best-effort result."""
    annotated = QaReport(
        passed=False,
        attempt=report.attempt,
        metrics=dict(report.metrics),
        thresholds=dict(report.thresholds),
        warnings=list(report.warnings),
    )
    annotated.warnings.append(f"QA failed after {attempts} attempt(s); returning best-effort result")
    return annotated


__all__ = ["QaReport", "evaluate", "best_effort_report"]
