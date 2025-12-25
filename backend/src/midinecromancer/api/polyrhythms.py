"""Polyrhythm profile endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from midinecromancer.db.base import get_session
from midinecromancer.music.polyrhythm import CycleSpec, render_to_events
from midinecromancer.music.theory import PPQ
from midinecromancer.models.polyrhythm_profile import PolyrhythmProfile
from midinecromancer.schemas.polyrhythm import (
    NoteEventResponse,
    PolyrhythmProfileCreate,
    PolyrhythmProfileResponse,
    PolyrhythmProfileUpdate,
    PolyrhythmPreviewRequest,
)

router = APIRouter()


@router.post("", response_model=PolyrhythmProfileResponse, status_code=201)
async def create_polyrhythm_profile(
    data: PolyrhythmProfileCreate,
    session: AsyncSession = Depends(get_session),
) -> PolyrhythmProfileResponse:
    """Create a new polyrhythm profile."""
    profile = PolyrhythmProfile(**data.model_dump())
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return PolyrhythmProfileResponse.model_validate(profile)


@router.get("", response_model=list[PolyrhythmProfileResponse])
async def list_polyrhythm_profiles(
    session: AsyncSession = Depends(get_session),
) -> list[PolyrhythmProfileResponse]:
    """List all polyrhythm profiles."""
    result = await session.execute(
        select(PolyrhythmProfile).order_by(PolyrhythmProfile.created_at.desc())
    )
    profiles = list(result.scalars().all())
    return [PolyrhythmProfileResponse.model_validate(p) for p in profiles]


@router.get("/{profile_id}", response_model=PolyrhythmProfileResponse)
async def get_polyrhythm_profile(
    profile_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> PolyrhythmProfileResponse:
    """Get polyrhythm profile by ID."""
    profile = await session.get(PolyrhythmProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Polyrhythm profile not found")
    return PolyrhythmProfileResponse.model_validate(profile)


@router.put("/{profile_id}", response_model=PolyrhythmProfileResponse)
async def update_polyrhythm_profile(
    profile_id: UUID,
    data: PolyrhythmProfileUpdate,
    session: AsyncSession = Depends(get_session),
) -> PolyrhythmProfileResponse:
    """Update polyrhythm profile."""
    profile = await session.get(PolyrhythmProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Polyrhythm profile not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)

    await session.commit()
    await session.refresh(profile)
    return PolyrhythmProfileResponse.model_validate(profile)


@router.delete("/{profile_id}", status_code=204)
async def delete_polyrhythm_profile(
    profile_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete polyrhythm profile."""
    profile = await session.get(PolyrhythmProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Polyrhythm profile not found")

    await session.delete(profile)
    await session.commit()


@router.post("/preview", response_model=list[NoteEventResponse])
async def preview_polyrhythm(
    request: PolyrhythmPreviewRequest,
    project_id: UUID = Query(...),
    session: AsyncSession = Depends(get_session),
) -> list[NoteEventResponse]:
    """Preview polyrhythm events for a project configuration."""
    from midinecromancer.models.project import Project

    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    cycle = CycleSpec(
        steps=request.steps,
        pulses=request.pulses,
        cycle_beats=float(request.cycle_beats),
        rotation=request.rotation,
        swing=float(request.swing) if request.swing is not None else None,
    )

    events = render_to_events(
        cycle=cycle,
        clip_start_bar=request.clip_start_bar,
        clip_length_bars=request.clip_length_bars,
        project_bpm=project.bpm,
        time_signature_num=project.time_signature_num,
        time_signature_den=project.time_signature_den,
        seed=project.seed,
        pitch=request.pitch,
        velocity=request.velocity,
    )

    # Convert to response format with beat positions
    quarter_notes_per_bar = (project.time_signature_num * 4) / project.time_signature_den
    ticks_per_bar = int(quarter_notes_per_bar * PPQ)

    responses = []
    for event in events:
        start_bar = event["start_tick"] // ticks_per_bar
        bar_offset_ticks = event["start_tick"] % ticks_per_bar
        start_beat = start_bar * quarter_notes_per_bar + (bar_offset_ticks / PPQ)
        duration_beats = event["duration_tick"] / PPQ

        responses.append(
            NoteEventResponse(
                pitch=event["pitch"],
                velocity=event["velocity"],
                start_tick=event["start_tick"],
                duration_tick=event["duration_tick"],
                start_beat=start_beat,
                duration_beats=duration_beats,
            )
        )

    return responses
