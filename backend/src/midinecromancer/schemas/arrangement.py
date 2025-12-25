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
    roman_numeral: str
    chord_name: str

    class Config:
        from_attributes = True


class ClipInArrangement(BaseModel):
    """Clip in arrangement."""

    id: UUID
    start_bar: int
    length_bars: int
    is_muted: bool
    is_soloed: bool
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
