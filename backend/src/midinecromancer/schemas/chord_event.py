"""Chord event schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ChordEventResponse(BaseModel):
    """Chord event response schema."""

    id: UUID
    clip_id: UUID
    start_tick: int
    duration_tick: int
    roman_numeral: str
    chord_name: str
    created_at: datetime

    class Config:
        from_attributes = True
