"""Chord event CRUD endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from midinecromancer.db.base import get_session
from midinecromancer.models.chord_event import ChordEvent
from midinecromancer.models.clip import Clip
from midinecromancer.models.project import Project
from midinecromancer.models.track import Track
from midinecromancer.schemas.arrangement import ChordEventInArrangement

router = APIRouter()


class ChordEventCreate(BaseModel):
    """Create chord event."""

    clip_id: UUID
    start_tick: int
    duration_tick: int
    duration_beats: float
    roman_numeral: str
    chord_name: str
    intensity: float = 0.85
    voicing: str = "root"
    inversion: int = 0
    strum_ms: int = 0  # Deprecated, use strum_beats
    humanize_ms: int = 0  # Deprecated, use humanize_beats
    strum_beats: float = 0.0
    humanize_beats: float = 0.0
    pattern_type: str = "block"
    duration_gate: float = 0.85
    velocity_curve: str = "flat"
    comp_pattern: dict | None = None
    strum_direction: str = "down"
    strum_spread: float = 1.0
    retrigger: bool = False
    velocity_jitter: int = 0
    timing_jitter_ms: int = 0
    is_enabled: bool = True
    is_locked: bool = False
    grid_quantum: float | None = None


class ChordEventUpdate(BaseModel):
    """Update chord event."""

    start_tick: int | None = None
    duration_tick: int | None = None
    duration_beats: float | None = None
    roman_numeral: str | None = None
    chord_name: str | None = None
    intensity: float | None = None
    voicing: str | None = None
    inversion: int | None = None
    strum_ms: int | None = None  # Deprecated, use strum_beats
    humanize_ms: int | None = None  # Deprecated, use humanize_beats
    strum_beats: float | None = None
    humanize_beats: float | None = None
    pattern_type: str | None = None
    duration_gate: float | None = None
    velocity_curve: str | None = None
    comp_pattern: dict | None = None
    strum_direction: str | None = None
    strum_spread: float | None = None
    retrigger: bool | None = None
    offset_beats: float | None = None
    strum_curve: str | None = None
    hit_params: dict | None = None
    velocity_jitter: int | None = None
    timing_jitter_ms: int | None = None
    is_enabled: bool | None = None
    is_locked: bool | None = None
    grid_quantum: float | None = None


@router.get("/projects/{project_id}/chords", response_model=list[ChordEventInArrangement])
async def list_chord_events(
    project_id: UUID,
    start_bar: int | None = Query(None),
    end_bar: int | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> list[ChordEventInArrangement]:
    """List chord events for a project, optionally filtered by bar range."""
    # Get project
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Calculate ticks per bar
    quarter_notes_per_bar = (project.time_signature_num * 4) / project.time_signature_den
    ticks_per_bar = int(quarter_notes_per_bar * 480)  # PPQ

    # Get chords track
    result = await session.execute(
        select(Track)
        .where(Track.project_id == project_id)
        .where(Track.role == "chords")
        .options(selectinload(Track.clips).selectinload(Clip.chord_events))
    )
    tracks = list(result.scalars().all())

    all_chords = []
    for track in tracks:
        for clip in track.clips:
            for chord in clip.chord_events:
                # Filter by bar range if provided
                if start_bar is not None or end_bar is not None:
                    chord_start_bar = clip.start_bar + (chord.start_tick / ticks_per_bar)
                    if start_bar is not None and chord_start_bar < start_bar:
                        continue
                    if end_bar is not None and chord_start_bar >= end_bar:
                        continue
                all_chords.append(chord)

    return [ChordEventInArrangement.model_validate(c) for c in all_chords]


@router.post("/chords", response_model=ChordEventInArrangement, status_code=201)
async def create_chord_event(
    data: ChordEventCreate,
    session: AsyncSession = Depends(get_session),
) -> ChordEventInArrangement:
    """Create a new chord event."""
    # Verify clip exists
    result = await session.execute(select(Clip).where(Clip.id == data.clip_id))
    clip = result.scalar_one_or_none()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    chord_event = ChordEvent(
        clip_id=data.clip_id,
        start_tick=data.start_tick,
        duration_tick=data.duration_tick,
        duration_beats=data.duration_beats,
        roman_numeral=data.roman_numeral,
        chord_name=data.chord_name,
        intensity=data.intensity,
        voicing=data.voicing,
        inversion=data.inversion,
        strum_ms=data.strum_ms,
        humanize_ms=data.humanize_ms,
        strum_beats=data.strum_beats,
        humanize_beats=data.humanize_beats,
        pattern_type=data.pattern_type,
        duration_gate=data.duration_gate,
        velocity_curve=data.velocity_curve,
        comp_pattern=data.comp_pattern,
        strum_direction=data.strum_direction,
        strum_spread=data.strum_spread,
        retrigger=data.retrigger,
        velocity_jitter=data.velocity_jitter,
        timing_jitter_ms=data.timing_jitter_ms,
        is_enabled=data.is_enabled,
        is_locked=data.is_locked,
        grid_quantum=data.grid_quantum,
    )
    session.add(chord_event)
    await session.commit()
    await session.refresh(chord_event)
    return ChordEventInArrangement.model_validate(chord_event)


@router.put("/chords/{chord_id}", response_model=ChordEventInArrangement)
async def update_chord_event(
    chord_id: UUID,
    data: ChordEventUpdate,
    session: AsyncSession = Depends(get_session),
) -> ChordEventInArrangement:
    """Update a chord event."""
    result = await session.execute(select(ChordEvent).where(ChordEvent.id == chord_id))
    chord_event = result.scalar_one_or_none()
    if not chord_event:
        raise HTTPException(status_code=404, detail="Chord event not found")

    # Allow updates if chord is locked only if we're trying to unlock it
    # Check if we're trying to unlock (is_locked=False) or only updating lock status
    is_trying_to_unlock = data.is_locked is False
    has_other_updates = any(
        getattr(data, field) is not None
        for field in [
            "start_tick",
            "duration_tick",
            "duration_beats",
            "roman_numeral",
            "chord_name",
            "intensity",
            "voicing",
            "inversion",
            "strum_ms",
            "humanize_ms",
            "strum_beats",
            "humanize_beats",
            "pattern_type",
            "duration_gate",
            "velocity_curve",
            "comp_pattern",
            "strum_direction",
            "strum_spread",
            "retrigger",
            "velocity_jitter",
            "timing_jitter_ms",
            "is_enabled",
            "grid_quantum",
        ]
    )

    # Reject if locked and trying to update other fields (but allow unlocking)
    if chord_event.is_locked and has_other_updates and not is_trying_to_unlock:
        raise HTTPException(
            status_code=400, detail="Chord event is locked. Unlock it first to make changes."
        )

    # Update fields
    if data.start_tick is not None:
        chord_event.start_tick = data.start_tick
    if data.duration_tick is not None:
        chord_event.duration_tick = data.duration_tick
    if data.duration_beats is not None:
        chord_event.duration_beats = data.duration_beats
    if data.roman_numeral is not None:
        chord_event.roman_numeral = data.roman_numeral
    if data.chord_name is not None:
        chord_event.chord_name = data.chord_name
    if data.intensity is not None:
        chord_event.intensity = data.intensity
    if data.voicing is not None:
        chord_event.voicing = data.voicing
    if data.inversion is not None:
        chord_event.inversion = data.inversion
    if data.strum_ms is not None:
        chord_event.strum_ms = data.strum_ms
    if data.humanize_ms is not None:
        chord_event.humanize_ms = data.humanize_ms
    if data.strum_beats is not None:
        chord_event.strum_beats = data.strum_beats
    if data.humanize_beats is not None:
        chord_event.humanize_beats = data.humanize_beats
    if data.pattern_type is not None:
        chord_event.pattern_type = data.pattern_type
    if data.duration_gate is not None:
        chord_event.duration_gate = data.duration_gate
    if data.velocity_curve is not None:
        chord_event.velocity_curve = data.velocity_curve
    if data.comp_pattern is not None:
        chord_event.comp_pattern = data.comp_pattern
    if data.strum_direction is not None:
        chord_event.strum_direction = data.strum_direction
    if data.strum_spread is not None:
        chord_event.strum_spread = data.strum_spread
    if data.retrigger is not None:
        chord_event.retrigger = data.retrigger
    if data.velocity_jitter is not None:
        chord_event.velocity_jitter = data.velocity_jitter
    if data.timing_jitter_ms is not None:
        chord_event.timing_jitter_ms = data.timing_jitter_ms
    if data.is_enabled is not None:
        chord_event.is_enabled = data.is_enabled
    if data.is_locked is not None:
        chord_event.is_locked = data.is_locked
    if data.grid_quantum is not None:
        chord_event.grid_quantum = data.grid_quantum

    await session.commit()
    await session.refresh(chord_event)
    return ChordEventInArrangement.model_validate(chord_event)


@router.delete("/chords/{chord_id}")
async def delete_chord_event(
    chord_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a chord event."""
    result = await session.execute(select(ChordEvent).where(ChordEvent.id == chord_id))
    chord_event = result.scalar_one_or_none()
    if not chord_event:
        raise HTTPException(status_code=404, detail="Chord event not found")

    if chord_event.is_locked:
        raise HTTPException(status_code=400, detail="Chord event is locked")

    await session.delete(chord_event)
    await session.commit()
