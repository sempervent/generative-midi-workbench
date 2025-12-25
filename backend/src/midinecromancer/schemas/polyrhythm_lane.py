"""Polyrhythm lane schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PolyrhythmLaneCreate(BaseModel):
    """Polyrhythm lane creation schema."""

    polyrhythm_profile_id: UUID
    lane_name: str = Field(default="Lane 1", max_length=255)
    instrument_role: str | None = Field(None, max_length=50)
    pitch: int = Field(default=60, ge=0, le=127)
    velocity: int = Field(default=100, ge=1, le=127)
    mute: bool = Field(default=False)
    solo: bool = Field(default=False)
    order_index: int = Field(default=0, ge=0)
    seed_offset: int = Field(default=0)


class PolyrhythmLaneUpdate(BaseModel):
    """Polyrhythm lane update schema."""

    polyrhythm_profile_id: UUID | None = None
    lane_name: str | None = Field(None, max_length=255)
    instrument_role: str | None = Field(None, max_length=50)
    pitch: int | None = Field(None, ge=0, le=127)
    velocity: int | None = Field(None, ge=1, le=127)
    mute: bool | None = None
    solo: bool | None = None
    order_index: int | None = Field(None, ge=0)
    seed_offset: int | None = None


class PolyrhythmLaneResponse(BaseModel):
    """Polyrhythm lane response schema."""

    id: UUID
    clip_id: UUID
    polyrhythm_profile_id: UUID
    lane_name: str
    instrument_role: str | None
    pitch: int
    velocity: int
    mute: bool
    solo: bool
    order_index: int
    seed_offset: int
    created_at: datetime

    class Config:
        from_attributes = True


class LanePreviewInfo(BaseModel):
    """Lane information in preview response."""

    lane_id: UUID
    lane_name: str
    ratio: str
    pitch: int
    velocity: int
    mute: bool
    solo: bool


class GridSpecResponse(BaseModel):
    """Grid specification response."""

    ticks_per_bar: int
    ticks_per_step: int
    grid_steps_per_bar: int
    lcm_steps: int


class PolyrhythmLanesPreviewResponse(BaseModel):
    """Preview response for multi-lane polyrhythm."""

    lanes: list[LanePreviewInfo]
    events: list[dict]
    grid_spec: GridSpecResponse
