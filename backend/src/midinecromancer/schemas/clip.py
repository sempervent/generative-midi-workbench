"""Clip schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ClipCreate(BaseModel):
    """Clip creation schema."""

    start_bar: int = Field(..., ge=0)
    length_bars: int = Field(..., ge=1)


class ClipResponse(BaseModel):
    """Clip response schema."""

    id: UUID
    track_id: UUID
    start_bar: int
    length_bars: int
    is_muted: bool
    is_soloed: bool
    intensity: float = 1.0
    params: dict = {}
    created_at: datetime

    class Config:
        from_attributes = True
