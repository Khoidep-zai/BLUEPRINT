"""Automatic quality assessment (design §2 qa)."""
from . import metrics  # noqa: F401
from .evaluator import QaReport, best_effort_report, evaluate  # noqa: F401

__all__ = ["metrics", "QaReport", "evaluate", "best_effort_report"]
