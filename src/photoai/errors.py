"""Standard pipeline exceptions (design §2 errors.py).

Every error carries a stable ``code`` so the UI (and the SQLite audit log) can
react without matching on message text.
"""
from __future__ import annotations


class PipelineError(Exception):
    """Base class for pipeline errors carrying a standard error code."""

    code = "INTERNAL_ERROR"

    def __init__(self, message: str, code: str | None = None) -> None:
        if code is not None:
            self.code = code
        self.message = message
        super().__init__(message)


class FilterRejectedError(PipelineError):
    code = "FILTER_REJECTED"


class NoFaceDetectedError(PipelineError):
    code = "NO_FACE_DETECTED"


class NoClosedEyesError(PipelineError):
    code = "NO_CLOSED_EYES"


class OwnershipError(PipelineError):
    """Raised when a legally sensitive recipe runs without ownership consent."""

    code = "OWNERSHIP_REQUIRED"


class ModelUnavailableError(PipelineError):
    """Raised when a GPU model is required but its runtime/weights are missing."""

    code = "MODEL_UNAVAILABLE"


# Backwards-compatible aliases (older call sites / imported names).
FilterRejected = FilterRejectedError
NoFaceDetected = NoFaceDetectedError
NoClosedEyes = NoClosedEyesError
OwnershipRequired = OwnershipError

__all__ = [
    "PipelineError",
    "FilterRejectedError",
    "NoFaceDetectedError",
    "NoClosedEyesError",
    "OwnershipError",
    "ModelUnavailableError",
    "FilterRejected",
    "NoFaceDetected",
    "NoClosedEyes",
    "OwnershipRequired",
]
