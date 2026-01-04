"""Schemas for chord projections."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ChordProjectionProfileCreate(BaseModel):
    """Create chord projection profile."""

    name: str
    kind: str  # block, arpeggio, broken, rhythm_pattern
    settings: dict | None = None


class ChordProjectionProfileUpdate(BaseModel):
    """Update chord projection profile."""

    name: str | None = None
    kind: str | None = None
    settings: dict | None = None


class ChordProjectionProfileResponse(BaseModel):
    """Chord projection profile response."""

    id: UUID
    name: str
    kind: str
    settings: dict | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ClipChordSettingsCreate(BaseModel):
    """Create clip chord settings."""

    projection_profile_id: UUID | None = None
    gate_pct: int = 90
    strum_ms: int = 0
    humanize_ms: int = 0
    offset_ticks: int = 0
    subdivision: str = "1/4"
    pattern: dict | None = None
    voicing_low_midi: int = 48
    voicing_high_midi: int = 72
    inversion_policy: str = "smooth"


class ClipChordSettingsUpdate(BaseModel):
    """Update clip chord settings."""

    projection_profile_id: UUID | None = None
    gate_pct: int | None = None
    strum_ms: int | None = None
    humanize_ms: int | None = None
    offset_ticks: int | None = None
    subdivision: str | None = None
    pattern: dict | None = None
    voicing_low_midi: int | None = None
    voicing_high_midi: int | None = None
    inversion_policy: str | None = None


class ClipChordSettingsResponse(BaseModel):
    """Clip chord settings response."""

    id: UUID
    clip_id: UUID
    projection_profile_id: UUID | None
    gate_pct: int
    strum_ms: int
    humanize_ms: int
    offset_ticks: int
    subdivision: str
    pattern: dict | None
    voicing_low_midi: int
    voicing_high_midi: int
    inversion_policy: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChordPreviewRequest(BaseModel):
    """Request for chord preview."""

    project_id: UUID
    bars_range: tuple[int, int] | None = None  # (start_bar, end_bar)
    progression_source: str  # "existing" | "suggestion:{id}" | "inline"
    chord_events: list[dict] | None = None  # For inline
    suggestion_id: UUID | None = None  # For suggestion
    settings: dict
    seed: int | None = None


class NoteEventResponse(BaseModel):
    """Note event response."""

    pitch: int
    start_tick: int
    duration_tick: int
    velocity: int


class ChordPreviewResponse(BaseModel):
    """Chord preview response."""

    note_events: list[NoteEventResponse]
    summary: dict  # e.g., {"voicing_stats": {...}}


class ChordCommitRequest(BaseModel):
    """Request to commit chord rendering."""

    project_id: UUID
    clip_id: UUID
    settings: dict
    seed: int | None = None
    commit_key: str | None = None  # For idempotency


class ChordCommitResponse(BaseModel):
    """Chord commit response."""

    clip_id: UUID
    notes_created: int
    notes_updated: int

