"""Polyrhythm lane endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from midinecromancer.db.base import get_session
from midinecromancer.music.polyrhythm import (
    CycleSpec,
    GridSpec,
    LaneSpec,
    calculate_ratio,
    lcm_grid_for_lanes,
    render_lanes_to_events,
)
from midinecromancer.models.clip import Clip
from midinecromancer.models.clip_polyrhythm_lane import ClipPolyrhythmLane
from midinecromancer.models.polyrhythm_profile import PolyrhythmProfile
from midinecromancer.models.project import Project
from midinecromancer.schemas.polyrhythm_lane import (
    GridSpecResponse,
    LanePreviewInfo,
    PolyrhythmLaneCreate,
    PolyrhythmLaneResponse,
    PolyrhythmLaneUpdate,
    PolyrhythmLanesPreviewResponse,
)

router = APIRouter()


@router.get("/clips/{clip_id}/polyrhythm-lanes", response_model=list[PolyrhythmLaneResponse])
async def list_clip_lanes(
    clip_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> list[PolyrhythmLaneResponse]:
    """List all lanes for a clip."""
    result = await session.execute(
        select(ClipPolyrhythmLane)
        .where(ClipPolyrhythmLane.clip_id == clip_id)
        .order_by(ClipPolyrhythmLane.order_index)
    )
    lanes = list(result.scalars().all())
    return [PolyrhythmLaneResponse.model_validate(lane) for lane in lanes]


@router.post(
    "/clips/{clip_id}/polyrhythm-lanes",
    response_model=PolyrhythmLaneResponse,
    status_code=201,
)
async def create_clip_lane(
    clip_id: UUID,
    data: PolyrhythmLaneCreate,
    session: AsyncSession = Depends(get_session),
) -> PolyrhythmLaneResponse:
    """Create a new lane for a clip."""
    # Verify clip exists
    clip = await session.get(Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    # Verify profile exists
    profile = await session.get(PolyrhythmProfile, data.polyrhythm_profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Polyrhythm profile not found")

    # Get max order_index for this clip
    result = await session.execute(
        select(ClipPolyrhythmLane)
        .where(ClipPolyrhythmLane.clip_id == clip_id)
        .order_by(ClipPolyrhythmLane.order_index.desc())
        .limit(1)
    )
    max_lane = result.scalar_one_or_none()
    order_index = (max_lane.order_index + 1) if max_lane else 0

    lane = ClipPolyrhythmLane(
        clip_id=clip_id,
        polyrhythm_profile_id=data.polyrhythm_profile_id,
        lane_name=data.lane_name,
        instrument_role=data.instrument_role,
        pitch=data.pitch,
        velocity=data.velocity,
        mute=data.mute,
        solo=data.solo,
        order_index=order_index if data.order_index == 0 else data.order_index,
        seed_offset=data.seed_offset,
    )
    session.add(lane)
    await session.commit()
    await session.refresh(lane)
    return PolyrhythmLaneResponse.model_validate(lane)


@router.put("/polyrhythm-lanes/{lane_id}", response_model=PolyrhythmLaneResponse)
async def update_lane(
    lane_id: UUID,
    data: PolyrhythmLaneUpdate,
    session: AsyncSession = Depends(get_session),
) -> PolyrhythmLaneResponse:
    """Update a lane."""
    lane = await session.get(ClipPolyrhythmLane, lane_id)
    if not lane:
        raise HTTPException(status_code=404, detail="Lane not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(lane, key, value)

    await session.commit()
    await session.refresh(lane)
    return PolyrhythmLaneResponse.model_validate(lane)


@router.delete("/polyrhythm-lanes/{lane_id}", status_code=204)
async def delete_lane(
    lane_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a lane."""
    lane = await session.get(ClipPolyrhythmLane, lane_id)
    if not lane:
        raise HTTPException(status_code=404, detail="Lane not found")

    await session.delete(lane)
    await session.commit()


@router.post("/polyrhythms/preview-lanes", response_model=PolyrhythmLanesPreviewResponse)
async def preview_polyrhythm_lanes(
    project_id: UUID = Query(...),
    clip_id: UUID = Query(...),
    session: AsyncSession = Depends(get_session),
) -> PolyrhythmLanesPreviewResponse:
    """Preview multi-lane polyrhythm events for a clip."""
    # Get project
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get clip with lanes
    result = await session.execute(
        select(Clip)
        .where(Clip.id == clip_id)
        .options(
            selectinload(Clip.polyrhythm_lanes).selectinload(ClipPolyrhythmLane.polyrhythm_profile)
        )
    )
    clip = result.scalar_one_or_none()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    # Handle legacy single-profile mode
    lanes_data: list[ClipPolyrhythmLane] = []
    if clip.grid_mode == "polyrhythm_multi" and clip.polyrhythm_lanes:
        lanes_data = clip.polyrhythm_lanes
    elif clip.grid_mode == "polyrhythm" and clip.polyrhythm_profile_id:
        # Legacy mode: create a virtual lane from the profile
        profile = await session.get(PolyrhythmProfile, clip.polyrhythm_profile_id)
        if profile:
            # Create a temporary lane object for rendering
            import uuid

            virtual_lane = ClipPolyrhythmLane(
                id=uuid.uuid4(),  # Generate a temporary ID
                clip_id=clip.id,
                polyrhythm_profile_id=profile.id,
                lane_name="Legacy Lane",
                pitch=60,
                velocity=100,
                mute=False,
                solo=False,
                order_index=0,
                seed_offset=0,
            )
            virtual_lane.polyrhythm_profile = profile
            lanes_data = [virtual_lane]

    if not lanes_data:
        raise HTTPException(status_code=400, detail="Clip has no polyrhythm lanes or profile")

    # Convert to LaneSpec
    lane_specs = []
    lane_infos = []
    for lane in lanes_data:
        profile = lane.polyrhythm_profile
        cycle = CycleSpec(
            steps=profile.steps,
            pulses=profile.pulses,
            cycle_beats=float(profile.cycle_beats),
            rotation=profile.rotation,
            swing=float(profile.swing) if profile.swing is not None else None,
        )

        lane_spec = LaneSpec(
            cycle=cycle,
            lane_id=lane.id,
            clip_id=clip.id,
            pitch=lane.pitch,
            velocity=lane.velocity,
            mute=lane.mute,
            solo=lane.solo,
            order_index=lane.order_index,
            seed_offset=lane.seed_offset,
            humanize_ms=profile.humanize_ms,
        )
        lane_specs.append(lane_spec)

        ratio = calculate_ratio(cycle)
        lane_infos.append(
            LanePreviewInfo(
                lane_id=lane.id,
                lane_name=lane.lane_name,
                ratio=ratio,
                pitch=lane.pitch,
                velocity=lane.velocity,
                mute=lane.mute,
                solo=lane.solo,
            )
        )

    # Render events
    events = render_lanes_to_events(
        lanes=lane_specs,
        clip_start_bar=clip.start_bar,
        clip_length_bars=clip.length_bars,
        project_bpm=project.bpm,
        time_signature_num=project.time_signature_num,
        time_signature_den=project.time_signature_den,
        base_seed=project.seed,
    )

    # Calculate grid spec
    grid_spec = lcm_grid_for_lanes(
        lanes=lane_specs,
        time_signature_num=project.time_signature_num,
        time_signature_den=project.time_signature_den,
    )

    return PolyrhythmLanesPreviewResponse(
        lanes=lane_infos,
        events=events,
        grid_spec=GridSpecResponse(
            ticks_per_bar=grid_spec.ticks_per_bar,
            ticks_per_step=grid_spec.ticks_per_step,
            grid_steps_per_bar=grid_spec.grid_steps_per_bar,
            lcm_steps=grid_spec.lcm_steps,
        ),
    )
