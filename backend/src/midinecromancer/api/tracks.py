"""Track endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from midinecromancer.db.base import get_session
from midinecromancer.models.track import Track
from midinecromancer.schemas.track import TrackCreate, TrackResponse

router = APIRouter()


@router.post("", response_model=TrackResponse, status_code=201)
async def create_track(
    project_id: UUID,
    data: TrackCreate,
    session: AsyncSession = Depends(get_session),
) -> TrackResponse:
    """Create a track for a project."""
    from midinecromancer.models.project import Project

    # Verify project exists
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    track = Track(project_id=project_id, **data.model_dump())
    session.add(track)
    await session.commit()
    await session.refresh(track)
    return TrackResponse.model_validate(track)


@router.get("/{track_id}", response_model=TrackResponse)
async def get_track(
    track_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> TrackResponse:
    """Get track by ID."""
    track = await session.get(Track, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return TrackResponse.model_validate(track)


@router.patch("/{track_id}/mute", response_model=TrackResponse)
async def toggle_track_mute(
    track_id: UUID,
    muted: bool,
    session: AsyncSession = Depends(get_session),
) -> TrackResponse:
    """Toggle track mute state."""
    track = await session.get(Track, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    track.is_muted = muted
    await session.commit()
    await session.refresh(track)
    return TrackResponse.model_validate(track)
