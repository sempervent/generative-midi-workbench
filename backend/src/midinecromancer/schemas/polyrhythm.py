"""Polyrhythm profile schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class PolyrhythmProfileCreate(BaseModel):
    """Polyrhythm profile creation schema."""

    name: str = Field(..., min_length=1, max_length=255)
    steps: int = Field(..., ge=1, le=128)
    pulses: int = Field(..., ge=1, le=128)
    rotation: int = Field(default=0, ge=0)
    cycle_beats: Decimal = Field(..., ge=0.1, le=32.0)
    swing: Decimal | None = Field(None, ge=0.0, le=1.0)
    humanize_ms: int | None = Field(None, ge=0, le=100)


class PolyrhythmProfileUpdate(BaseModel):
    """Polyrhythm profile update schema."""

    name: str | None = Field(None, min_length=1, max_length=255)
    steps: int | None = Field(None, ge=1, le=128)
    pulses: int | None = Field(None, ge=1, le=128)
    rotation: int | None = Field(None, ge=0)
    cycle_beats: Decimal | None = Field(None, ge=0.1, le=32.0)
    swing: Decimal | None = Field(None, ge=0.0, le=1.0)
    humanize_ms: int | None = Field(None, ge=0, le=100)


class PolyrhythmProfileResponse(BaseModel):
    """Polyrhythm profile response schema."""

    id: UUID
    name: str
    steps: int
    pulses: int
    rotation: int
    cycle_beats: Decimal
    swing: Decimal | None
    humanize_ms: int | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PolyrhythmPreviewRequest(BaseModel):
    """Request for polyrhythm preview."""

    steps: int = Field(..., ge=1, le=128)
    pulses: int = Field(..., ge=1, le=128)
    rotation: int = Field(default=0, ge=0)
    cycle_beats: Decimal = Field(..., ge=0.1, le=32.0)
    swing: Decimal | None = Field(None, ge=0.0, le=1.0)
    clip_start_bar: int = Field(default=0, ge=0)
    clip_length_bars: int = Field(default=1, ge=1)
    pitch: int = Field(default=60, ge=0, le=127)
    velocity: int = Field(default=100, ge=1, le=127)


class NoteEventResponse(BaseModel):
    """Note event in preview response."""

    pitch: int
    velocity: int
    start_tick: int
    duration_tick: int
    start_beat: float
    duration_beats: float
