"""Clip endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from midinecromancer.db.base import get_session
from midinecromancer.models.clip import Clip
from midinecromancer.schemas.clip import ClipResponse

router = APIRouter()


@router.patch("/{clip_id}/mute", response_model=ClipResponse)
async def toggle_clip_mute(
    clip_id: UUID,
    muted: bool,
    session: AsyncSession = Depends(get_session),
) -> ClipResponse:
    """Toggle clip mute state."""
    clip = await session.get(Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    clip.is_muted = muted
    await session.commit()
    await session.refresh(clip)
    return ClipResponse.model_validate(clip)


@router.patch("/{clip_id}/solo", response_model=ClipResponse)
async def toggle_clip_solo(
    clip_id: UUID,
    soloed: bool,
    session: AsyncSession = Depends(get_session),
) -> ClipResponse:
    """Toggle clip solo state."""
    clip = await session.get(Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    clip.is_soloed = soloed
    await session.commit()
    await session.refresh(clip)
    return ClipResponse.model_validate(clip)
