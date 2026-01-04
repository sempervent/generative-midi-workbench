"""Arrangement response schema (full project data)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class NoteInArrangement(BaseModel):
    """Note in arrangement."""

    id: UUID
    pitch: int
    velocity: int
    start_tick: int
    duration_tick: int
    probability: float

    class Config:
        from_attributes = True


class ChordEventInArrangement(BaseModel):
    """Chord event in arrangement."""

    id: UUID
    start_tick: int
    duration_tick: int
    duration_beats: float
    roman_numeral: str
    chord_name: str
    intensity: float
    voicing: str
    inversion: int
    strum_ms: int  # Deprecated, use strum_beats
    humanize_ms: int  # Deprecated, use humanize_beats
    strum_beats: float
    humanize_beats: float
    pattern_type: str = "block"
    duration_gate: float = 0.85
    velocity_curve: str = "flat"
    comp_pattern: dict | None = None
    strum_direction: str = "down"
    strum_spread: float = 1.0
    retrigger: bool = False
    offset_beats: float = 0.0
    strum_curve: str = "linear"
    hit_params: dict | None = None
    velocity_jitter: int
    timing_jitter_ms: int
    is_enabled: bool
    is_locked: bool
    grid_quantum: float | None

    class Config:
        from_attributes = True


class ClipInArrangement(BaseModel):
    """Clip in arrangement."""

    id: UUID
    start_bar: int
    length_bars: int
    is_muted: bool
    is_soloed: bool
    start_offset_ticks: int
    intensity: float = 1.0
    params: dict = {}
    notes: list[NoteInArrangement]
    chord_events: list[ChordEventInArrangement]

    class Config:
        from_attributes = True


class TrackInArrangement(BaseModel):
    """Track in arrangement."""

    id: UUID
    name: str
    role: str
    midi_channel: int
    midi_program: int
    is_muted: bool
    is_soloed: bool
    start_offset_ticks: int
    clips: list[ClipInArrangement]

    class Config:
        from_attributes = True


class ArrangementResponse(BaseModel):
    """Full arrangement response."""

    project_id: UUID
    project_name: str
    bpm: int
    time_signature_num: int
    time_signature_den: int
    bars: int
    key_tonic: str
    mode: str
    seed: int
    tracks: list[TrackInArrangement]
