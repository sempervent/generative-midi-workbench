"""Segment generation schemas."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


SegmentKind = Literal["beats", "chords", "bass", "melody"]


class BeatsModel(BaseModel):
    """Beats generation model."""

    kit: Literal["gm_hiphop", "gm_trap", "gm_boom_bap", "gm_blank"] = "gm_hiphop"
    density: float = Field(0.7, ge=0.0, le=1.0)
    swing: float = Field(0.0, ge=0.0, le=0.75)
    humanize_ms: int = Field(0, ge=0, le=30)
    pattern: Literal["straight", "syncopated", "euclidean", "polyrhythm"] = "straight"
    kick_variation: float = Field(0.3, ge=0.0, le=1.0)
    snare_variation: float = Field(0.3, ge=0.0, le=1.0)
    hat_variation: float = Field(0.3, ge=0.0, le=1.0)
    ghost_notes: bool = True
    fills: Literal["none", "ends", "every_4", "random"] = "ends"
    mute_probability: float = Field(0.0, ge=0.0, le=0.5)
    velocity_curve: Literal["flat", "accent_2_4", "accent_1", "ramp"] = "accent_2_4"


class ChordsModel(BaseModel):
    """Chords generation model."""

    key: str = "C"
    mode: Literal[
        "ionian",
        "dorian",
        "phrygian",
        "lydian",
        "mixolydian",
        "aeolian",
        "locrian",
    ] = "aeolian"
    progression_style: Literal["pop", "rap_minor", "jazzy", "modal", "circle_fifths"] = "rap_minor"
    harmonic_rhythm: Literal["1chord/bar", "2chords/bar", "slow", "custom"] = "1chord/bar"
    voicing: Literal["root", "drop2", "spread", "tight"] = "root"
    inversion_bias: float = Field(0.2, ge=0.0, le=1.0)
    intensity: float = Field(0.85, ge=0.0, le=1.0)
    strum_ms: int = Field(0, ge=0, le=80)
    duration_gate: float = Field(0.9, ge=0.1, le=1.0)
    syncopation: float = Field(0.2, ge=0.0, le=1.0)
    borrowed_chords: float = Field(0.1, ge=0.0, le=1.0)
    cadence_strength: float = Field(0.7, ge=0.0, le=1.0)


class BassModel(BaseModel):
    """Bass generation model."""

    style: Literal["root", "walking", "808", "syncopated"] = "808"
    octave: int = Field(2, ge=1, le=4)
    follow_kicks: float = Field(0.8, ge=0.0, le=1.0)
    approach_notes: float = Field(0.3, ge=0.0, le=1.0)
    slides: float = Field(0.2, ge=0.0, le=1.0)
    rhythmic_density: float = Field(0.6, ge=0.0, le=1.0)
    intensity: float = Field(0.85, ge=0.0, le=1.0)


class MelodyModel(BaseModel):
    """Melody generation model."""

    range: Literal["narrow", "medium", "wide"] = "medium"
    motif_repetition: float = Field(0.5, ge=0.0, le=1.0)
    leapiness: float = Field(0.3, ge=0.0, le=1.0)
    call_response: bool = True
    syncopation: float = Field(0.3, ge=0.0, le=1.0)
    intensity: float = Field(0.85, ge=0.0, le=1.0)
    avoid_too_unique: bool = True


class SegmentCreateRequest(BaseModel):
    """Request to create/generate segments."""

    project_id: UUID
    start_bar: int = Field(..., ge=0)
    length_bars: int = Field(..., ge=1)
    bpm: int | None = None  # Optional; default from project
    seed: int
    kinds: list[SegmentKind] = Field(..., min_length=1)
    models: dict[SegmentKind, BeatsModel | ChordsModel | BassModel | MelodyModel] = Field(
        default_factory=dict
    )
    preview: bool = False


class ClipPreview(BaseModel):
    """Preview of a clip (without DB persistence)."""

    kind: SegmentKind
    start_bar: int
    length_bars: int
    notes: list[dict] = Field(default_factory=list)
    chord_events: list[dict] = Field(default_factory=list)
    polyrhythm_lanes: list[dict] = Field(default_factory=list)


class SegmentGenerateResponse(BaseModel):
    """Response from segment generation."""

    clips: list[dict]  # ClipResponse objects if persisted, ClipPreview if preview
    events_by_clip: dict[str, list[dict]] = Field(default_factory=dict)
    chords_by_clip: dict[str, list[dict]] = Field(default_factory=dict)
    lanes_by_clip: dict[str, list[dict]] = Field(default_factory=dict)
    preview: bool = False
