"""Pydantic schemas for uploads."""
from pydantic import BaseModel, Field


class PresignRequest(BaseModel):
    filename: str = Field(min_length=1)
    mime: str = Field(min_length=3)
    size: int = Field(gt=0)


class PresignResponse(BaseModel):
    asset_id: str
    upload_url: str
    expires_in: int


class CompleteRequest(BaseModel):
    pass


class CompleteResponse(BaseModel):
    asset_id: str
    status: str
