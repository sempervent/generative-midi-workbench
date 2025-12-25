"""Track schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TrackCreate(BaseModel):
    """Track creation schema."""

    name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., pattern="^(drums|chords|bass|melody)$")
    midi_channel: int = Field(default=0, ge=0, le=15)
    midi_program: int = Field(default=0, ge=0, le=127)
    is_muted: bool = Field(default=False)


class TrackResponse(BaseModel):
    """Track response schema."""

    id: UUID
    project_id: UUID
    name: str
    role: str
    midi_channel: int
    midi_program: int
    is_muted: bool
    created_at: datetime

    class Config:
        from_attributes = True
