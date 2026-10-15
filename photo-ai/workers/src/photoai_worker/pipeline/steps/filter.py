"""Filter step (AGENT_SKILLS S1/S3).

Decides whether the input is worth editing (e.g. only proceed when the eyes are
actually closed). Rejections carry a standard error code so the API can return
a clear message instead of crashing (design §6).
"""
from __future__ import annotations

from typing import Any, Dict

from ...pipeline.context import JobContext
from ...pipeline.errors import FilterRejected, NoClosedEyes, NoFaceDetected


def run(context: JobContext, config: Dict[str, Any]) -> JobContext:
    """Apply the recipe's filter rules; raise :class:`PipelineError` on reject."""
    config = config or {}

    if config.get("only_closed_eyes"):
        eyes = context.detections.get("eyes")
        if eyes is None:
            raise NoFaceDetected("Không tìm thấy khuôn mặt.")
        threshold = float(config.get("ear_below", eyes.threshold))
        if eyes.ear >= threshold:
            raise NoClosedEyes("Mắt đã mở, không có gì để sửa.")

    if config.get("require_face") and not context.detections.get("main_face"):
        raise NoFaceDetected("Không tìm thấy khuôn mặt.")

    context.log("filter", "ok")
    return context
