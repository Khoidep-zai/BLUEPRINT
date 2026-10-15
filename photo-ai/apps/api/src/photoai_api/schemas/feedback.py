"""Feedback schemas."""
from typing import Optional

from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    job_id: str
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    feedback_id: str
    status: str
