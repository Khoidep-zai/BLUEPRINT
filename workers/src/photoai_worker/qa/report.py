"""QA report assembly and threshold evaluation (P0 task 8 / AGENT_SKILLS S11).

The report is the machine-readable contract returned to the API and stored in
``qa_reports``:

    {"passed": bool, "attempt": int, "metrics": {...}, "thresholds": {...}}

Threshold keys encode their comparison direction in the suffix:

* ``*_min``  -> metric must be >= threshold
* ``*_max``  -> metric must be <= threshold
* ``ocr_recheck`` / ``person_recheck`` -> boolean, must be truthy
* anything else -> recorded as a metric but not enforced
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

_BOOLEAN_CHECKS = {"ocr_recheck", "person_recheck"}


@dataclass
class QaReport:
    """Result of evaluating QA metrics against a recipe's thresholds."""

    passed: bool
    attempt: int
    metrics: Dict[str, Any] = field(default_factory=dict)
    thresholds: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def failed_checks(self) -> List[str]:
        """Return the list of threshold keys that were not satisfied."""
        failed: List[str] = []
        for key, threshold in self.thresholds.items():
            if threshold is None:
                continue
            if key.endswith("_min"):
                metric_key = key[: -len("_min")]
                value = self.metrics.get(metric_key)
                if value is None or value < threshold:
                    failed.append(key)
            elif key.endswith("_max"):
                metric_key = key[: -len("_max")]
                value = self.metrics.get(metric_key)
                if value is None or value > threshold:
                    failed.append(key)
            elif key in _BOOLEAN_CHECKS:
                if not self.metrics.get(key):
                    failed.append(key)
        return failed


def evaluate(
    metrics: Dict[str, Any],
    thresholds: Dict[str, Any],
    attempt: int = 1,
) -> QaReport:
    """Evaluate ``metrics`` against ``thresholds`` and build a :class:`QaReport`."""
    clean_thresholds = {k: v for k, v in thresholds.items() if v is not None}
    report = QaReport(
        passed=True,
        attempt=attempt,
        metrics=dict(metrics),
        thresholds=clean_thresholds,
    )
    failed = report.failed_checks()
    if failed:
        report.passed = False
        report.warnings = [
            f"QA check failed: {key}" for key in failed
        ]
    return report


def best_effort_report(report: QaReport, attempts: int) -> QaReport:
    """Annotate a failed report returned as a best-effort result (P0 flow step 6)."""
    annotated = QaReport(
        passed=False,
        attempt=report.attempt,
        metrics=dict(report.metrics),
        thresholds=dict(report.thresholds),
        warnings=list(report.warnings),
    )
    annotated.warnings.append(
        f"QA failed after {attempts} attempt(s); returning best-effort result"
    )
    return annotated
