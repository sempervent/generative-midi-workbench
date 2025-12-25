"""Note schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class NoteCreate(BaseModel):
    """Note creation schema."""

    pitch: int = Field(..., ge=0, le=127)
    velocity: int = Field(default=100, ge=1, le=127)
    start_tick: int = Field(..., ge=0)
    duration_tick: int = Field(..., ge=1)
    probability: float = Field(default=1.0, ge=0.0, le=1.0)


class NoteResponse(BaseModel):
    """Note response schema."""

    id: UUID
    clip_id: UUID
    pitch: int
    velocity: int
    start_tick: int
    duration_tick: int
    probability: float
    created_at: datetime

    class Config:
        from_attributes = True
