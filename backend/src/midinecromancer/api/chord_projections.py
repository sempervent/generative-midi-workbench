"""Chord projection endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from midinecromancer.db.base import get_session
from midinecromancer.models.chord_projection_profile import ChordProjectionProfile
from midinecromancer.schemas.chord_projections import (
    ChordProjectionProfileCreate,
    ChordProjectionProfileResponse,
    ChordProjectionProfileUpdate,
)

router = APIRouter()


@router.get("", response_model=list[ChordProjectionProfileResponse])
async def list_projection_profiles(
    session: AsyncSession = Depends(get_session),
) -> list[ChordProjectionProfileResponse]:
    """List all chord projection profiles."""
    result = await session.execute(
        select(ChordProjectionProfile).order_by(ChordProjectionProfile.created_at)
    )
    profiles = list(result.scalars().all())
    return [ChordProjectionProfileResponse.model_validate(p) for p in profiles]


@router.post("", response_model=ChordProjectionProfileResponse)
async def create_projection_profile(
    data: ChordProjectionProfileCreate,
    session: AsyncSession = Depends(get_session),
) -> ChordProjectionProfileResponse:
    """Create a new chord projection profile."""
    profile = ChordProjectionProfile(
        name=data.name,
        kind=data.kind,
        settings=data.settings,
    )
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return ChordProjectionProfileResponse.model_validate(profile)


@router.get("/{profile_id}", response_model=ChordProjectionProfileResponse)
async def get_projection_profile(
    profile_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> ChordProjectionProfileResponse:
    """Get a chord projection profile by ID."""
    result = await session.execute(
        select(ChordProjectionProfile).where(ChordProjectionProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Projection profile not found")
    return ChordProjectionProfileResponse.model_validate(profile)


@router.put("/{profile_id}", response_model=ChordProjectionProfileResponse)
async def update_projection_profile(
    profile_id: UUID,
    data: ChordProjectionProfileUpdate,
    session: AsyncSession = Depends(get_session),
) -> ChordProjectionProfileResponse:
    """Update a chord projection profile."""
    result = await session.execute(
        select(ChordProjectionProfile).where(ChordProjectionProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Projection profile not found")

    if data.name is not None:
        profile.name = data.name
    if data.kind is not None:
        profile.kind = data.kind
    if data.settings is not None:
        profile.settings = data.settings

    await session.commit()
    await session.refresh(profile)
    return ChordProjectionProfileResponse.model_validate(profile)


@router.delete("/{profile_id}")
async def delete_projection_profile(
    profile_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a chord projection profile."""
    result = await session.execute(
        select(ChordProjectionProfile).where(ChordProjectionProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Projection profile not found")

    await session.delete(profile)
    await session.commit()
