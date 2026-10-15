"""Asset schemas."""
from pydantic import BaseModel


class AssetDeleteResponse(BaseModel):
    asset_id: str
    deleted: bool
