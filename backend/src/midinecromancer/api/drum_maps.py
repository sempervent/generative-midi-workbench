"""Drum map profile API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from midinecromancer.db.base import get_session
from midinecromancer.models.drum_map_profile import DrumMapProfile
from midinecromancer.schemas.drum_map import DrumMapProfileCreate, DrumMapProfileResponse

router = APIRouter()


@router.get("", response_model=list[DrumMapProfileResponse])
async def list_drum_maps(
    session: AsyncSession = Depends(get_session),
) -> list[DrumMapProfileResponse]:
    """List all drum map profiles."""
    result = await session.execute(select(DrumMapProfile).order_by(DrumMapProfile.name))
    profiles = result.scalars().all()
    return [DrumMapProfileResponse.model_validate(p) for p in profiles]


@router.get("/{profile_id}", response_model=DrumMapProfileResponse)
async def get_drum_map(
    profile_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> DrumMapProfileResponse:
    """Get a drum map profile by ID."""
    profile = await session.get(DrumMapProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Drum map profile not found")
    return DrumMapProfileResponse.model_validate(profile)


@router.post("", response_model=DrumMapProfileResponse)
async def create_drum_map(
    data: DrumMapProfileCreate,
    session: AsyncSession = Depends(get_session),
) -> DrumMapProfileResponse:
    """Create a new drum map profile."""
    profile = DrumMapProfile(
        name=data.name,
        kick_note=data.kick_note,
        snare_note=data.snare_note,
        clap_note=data.clap_note,
        closed_hat_note=data.closed_hat_note,
        open_hat_note=data.open_hat_note,
        rim_note=data.rim_note,
        perc_notes=data.perc_notes,
    )
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return DrumMapProfileResponse.model_validate(profile)
