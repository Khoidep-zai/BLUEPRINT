"""Stage 6 — Auto-QA: measure the output and evaluate thresholds (design §2)."""
from __future__ import annotations

from typing import Any, Dict, Optional

from photoai.engine.context import PipelineContext
from photoai.qa.evaluator import QaReport, evaluate
from photoai.qa.metrics import MetricsOptions, compute_metrics

# Backwards-compatible alias for injected detectors.
QAOptions = MetricsOptions


def run(
    context: PipelineContext,
    thresholds: Dict[str, Any],
    attempt: int = 1,
    options: Optional[MetricsOptions] = None,
) -> QaReport:
    metrics = compute_metrics(context, thresholds, options)
    context.metrics = metrics
    report = evaluate(metrics, thresholds or {}, attempt=attempt)
    context.log("qa", "passed" if report.passed else "failed", attempt=attempt)
    return report
