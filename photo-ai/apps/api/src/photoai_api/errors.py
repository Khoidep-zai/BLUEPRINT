"""Standard error codes and responses."""
from enum import Enum


class ErrorCode(str, Enum):
    """Standard error codes."""

    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    IMAGE_TOO_SMALL = "IMAGE_TOO_SMALL"
    IMAGE_TOO_LARGE = "IMAGE_TOO_LARGE"
    NO_FACE_DETECTED = "NO_FACE_DETECTED"
    NO_CLOSED_EYES = "NO_CLOSED_EYES"
    OWNERSHIP_REQUIRED = "OWNERSHIP_REQUIRED"
    RATE_LIMITED = "RATE_LIMITED"
    QA_FAILED_BEST_EFFORT = "QA_FAILED_BEST_EFFORT"
    PROVIDER_TIMEOUT = "PROVIDER_TIMEOUT"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class APIError(Exception):
    """API error."""

    def __init__(self, code: ErrorCode, message: str, request_id: str = None):
        self.code = code
        self.message = message
        self.request_id = request_id
        super().__init__(message)
