"""Pipeline-level errors mapped to API error codes (design §6)."""
from __future__ import annotations


class PipelineError(Exception):
    """Base class for pipeline errors carrying a standard error code."""

    code = "INTERNAL_ERROR"

    def __init__(self, message: str, code: str = None):
        self.code = code or self.code
        self.message = message
        super().__init__(message)


class FilterRejected(PipelineError):
    """A filter step rejected the input (e.g. eyes are already open)."""

    code = "FILTER_REJECTED"


class NoFaceDetected(PipelineError):
    """A face is required but none was detected."""

    code = "NO_FACE_DETECTED"


class NoClosedEyes(PipelineError):
    """The eyes are already open; there is nothing to fix."""

    code = "NO_CLOSED_EYES"


class OwnershipRequired(PipelineError):
    """Watermark removal requires ``ownership_confirmed=true``."""

    code = "OWNERSHIP_REQUIRED"
