"""Chord rendering endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from midinecromancer.db.base import get_session
from midinecromancer.models.clip import Clip
from midinecromancer.models.clip_chord_settings import ClipChordSettings
from midinecromancer.models.project import Project
from midinecromancer.models.track import Track
from midinecromancer.schemas.chord_projections import (
    ChordCommitRequest,
    ChordCommitResponse,
    ChordPreviewRequest,
    ChordPreviewResponse,
    ClipChordSettingsResponse,
    ClipChordSettingsUpdate,
    NoteEventResponse,
)
from midinecromancer.services.chords import ChordService

router = APIRouter()


@router.get("/clips/{clip_id}/settings", response_model=ClipChordSettingsResponse)
async def get_clip_chord_settings(
    clip_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> ClipChordSettingsResponse:
    """Get chord settings for a clip."""
    result = await session.execute(
        select(ClipChordSettings).where(ClipChordSettings.clip_id == clip_id)
    )
    settings = result.scalar_one_or_none()
    if not settings:
        raise HTTPException(status_code=404, detail="Chord settings not found for clip")
    return ClipChordSettingsResponse.model_validate(settings)


@router.put("/clips/{clip_id}/settings", response_model=ClipChordSettingsResponse)
async def update_clip_chord_settings(
    clip_id: UUID,
    data: ClipChordSettingsUpdate,
    session: AsyncSession = Depends(get_session),
) -> ClipChordSettingsResponse:
    """Update chord settings for a clip."""
    # Check clip exists
    result = await session.execute(select(Clip).where(Clip.id == clip_id))
    clip = result.scalar_one_or_none()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    # Get or create settings
    result = await session.execute(
        select(ClipChordSettings).where(ClipChordSettings.clip_id == clip_id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        settings = ClipChordSettings(clip_id=clip_id)
        session.add(settings)

    # Update fields
    if data.projection_profile_id is not None:
        settings.projection_profile_id = data.projection_profile_id
    if data.gate_pct is not None:
        settings.gate_pct = data.gate_pct
    if data.strum_ms is not None:
        settings.strum_ms = data.strum_ms
    if data.humanize_ms is not None:
        settings.humanize_ms = data.humanize_ms
    if data.offset_ticks is not None:
        settings.offset_ticks = data.offset_ticks
    if data.subdivision is not None:
        settings.subdivision = data.subdivision
    if data.pattern is not None:
        settings.pattern = data.pattern
    if data.voicing_low_midi is not None:
        settings.voicing_low_midi = data.voicing_low_midi
    if data.voicing_high_midi is not None:
        settings.voicing_high_midi = data.voicing_high_midi
    if data.inversion_policy is not None:
        settings.inversion_policy = data.inversion_policy

    await session.commit()
    await session.refresh(settings)
    return ClipChordSettingsResponse.model_validate(settings)


@router.post("/preview", response_model=ChordPreviewResponse)
async def preview_chords(
    request: ChordPreviewRequest,
    session: AsyncSession = Depends(get_session),
) -> ChordPreviewResponse:
    """Preview chord rendering without committing."""
    service = ChordService(session)
    return await service.preview_chords(request)


@router.post("/commit", response_model=ChordCommitResponse)
async def commit_chords(
    request: ChordCommitRequest,
    session: AsyncSession = Depends(get_session),
) -> ChordCommitResponse:
    """Commit chord rendering to clip notes."""
    service = ChordService(session)
    return await service.commit_chords(request)
