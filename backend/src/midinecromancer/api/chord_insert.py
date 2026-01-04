"""Chord insertion endpoint for adding chords to empty arrangement spaces."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from midinecromancer.db.base import get_session
from midinecromancer.models.chord_event import ChordEvent
from midinecromancer.models.clip import Clip
from midinecromancer.models.project import Project
from midinecromancer.models.track import Track
from midinecromancer.music.theory import PPQ
from midinecromancer.schemas.arrangement import ChordEventInArrangement

router = APIRouter()


class ChordInsertRequest(BaseModel):
    """Request to insert a chord into an empty space."""

    project_id: UUID
    start_bar: int = Field(..., ge=0)
    duration_bars: float = Field(..., gt=0)
    roman_numeral: str
    chord_name: str
    intensity: float = Field(default=0.85, ge=0, le=1)
    voicing: str = Field(default="root")
    inversion: int = Field(default=0, ge=0, le=3)
    strum_beats: float = Field(default=0.0, ge=0, le=2.0)
    humanize_beats: float = Field(default=0.0, ge=0, le=2.0)
    duration_gate: float = Field(default=0.85, ge=0.1, le=1.0)
    pattern_type: str = Field(default="block")
    velocity_curve: str = Field(default="flat")
    comp_pattern: dict | None = None
    strum_direction: str = Field(default="down")
    strum_spread: float = Field(default=1.0)
    retrigger: bool = Field(default=False)


@router.post("/chords/insert", response_model=ChordEventInArrangement, status_code=201)
async def insert_chord(
    request: ChordInsertRequest,
    session: AsyncSession = Depends(get_session),
) -> ChordEventInArrangement:
    """Insert a chord into an empty arrangement space.

    Creates or finds a clip in the chords track and adds the chord event.
    """
    # Get project
    project = await session.get(Project, request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get or create chords track
    result = await session.execute(
        select(Track).where(Track.project_id == request.project_id, Track.role == "chords")
    )
    track = result.scalar_one_or_none()

    if not track:
        track = Track(
            project_id=request.project_id,
            name="Chords",
            role="chords",
            midi_channel=0,
            midi_program=0,
        )
        session.add(track)
        await session.flush()

    # Find or create clip at start_bar
    result = await session.execute(
        select(Clip).where(Clip.track_id == track.id).where(Clip.start_bar == request.start_bar)
    )
    clip = result.scalar_one_or_none()

    if not clip:
        # Create new clip
        clip = Clip(
            track_id=track.id,
            start_bar=request.start_bar,
            length_bars=request.duration_bars,
        )
        session.add(clip)
        await session.flush()

    # Calculate ticks
    quarter_notes_per_bar = (project.time_signature_num * 4) / project.time_signature_den
    ticks_per_bar = int(quarter_notes_per_bar * PPQ)
    start_tick = 0  # Start of clip
    duration_ticks = int(request.duration_bars * ticks_per_bar)

    # Create chord event
    chord_event = ChordEvent(
        clip_id=clip.id,
        start_tick=start_tick,
        duration_tick=duration_ticks,
        duration_beats=request.duration_bars * 4,  # Assume 4 beats per bar
        roman_numeral=request.roman_numeral,
        chord_name=request.chord_name,
        intensity=request.intensity,
        voicing=request.voicing,
        inversion=request.inversion,
        strum_beats=request.strum_beats,
        humanize_beats=request.humanize_beats,
        duration_gate=request.duration_gate,
        pattern_type=request.pattern_type,
        velocity_curve=request.velocity_curve,
        comp_pattern=request.comp_pattern,
        strum_direction=request.strum_direction,
        strum_spread=request.strum_spread,
        retrigger=request.retrigger,
        is_enabled=True,
        is_locked=False,
    )
    session.add(chord_event)
    await session.commit()
    await session.refresh(chord_event)

    return ChordEventInArrangement.model_validate(chord_event)
