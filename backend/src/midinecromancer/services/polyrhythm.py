"""Service for polyrhythm lane operations."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from midinecromancer.music.polyrhythm import (
    CycleSpec,
    LaneSpec,
    render_lanes_to_events,
)
from midinecromancer.models.clip import Clip
from midinecromancer.models.clip_polyrhythm_lane import ClipPolyrhythmLane
from midinecromancer.models.note import Note
from midinecromancer.models.polyrhythm_profile import PolyrhythmProfile
from midinecromancer.models.project import Project


async def render_clip_lanes_to_notes(
    clip: Clip,
    project: Project,
    session: AsyncSession,
) -> list[Note]:
    """Render polyrhythm lanes for a clip to Note objects.

    This is used for MIDI export and ensures lanes are converted to notes
    that can be stored/exported.

    Args:
        clip: Clip with lanes
        project: Project for timing/BPM
        session: Database session

    Returns:
        List of Note objects (not yet persisted)
    """
    # Check if clip has lanes
    if clip.grid_mode == "polyrhythm_multi" and clip.polyrhythm_lanes:
        lanes_data = clip.polyrhythm_lanes
    elif clip.grid_mode == "polyrhythm" and clip.polyrhythm_profile_id:
        # Legacy mode: check if lanes exist (from migration), otherwise use profile
        result = await session.execute(
            select(ClipPolyrhythmLane).where(ClipPolyrhythmLane.clip_id == clip.id)
        )
        existing_lanes = list(result.scalars().all())
        if existing_lanes:
            lanes_data = existing_lanes
        else:
            # True legacy: use profile directly
            profile = await session.get(PolyrhythmProfile, clip.polyrhythm_profile_id)
            if profile:
                import uuid

                virtual_lane = ClipPolyrhythmLane(
                    id=uuid.uuid4(),
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
            else:
                return []
    else:
        return []

    # Convert to LaneSpec
    lane_specs = []
    for lane in lanes_data:
        if not hasattr(lane, "polyrhythm_profile") or not lane.polyrhythm_profile:
            profile = await session.get(PolyrhythmProfile, lane.polyrhythm_profile_id)
            if not profile:
                continue
            lane.polyrhythm_profile = profile

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

    if not lane_specs:
        return []

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

    # Convert to Note objects
    # Note: events from render_lanes_to_events have absolute tick positions
    # We need to convert to relative ticks within the clip
    notes = []
    quarter_notes_per_bar = (project.time_signature_num * 4) / project.time_signature_den
    ticks_per_bar = int(quarter_notes_per_bar * 480)  # PPQ
    clip_start_tick = clip.start_bar * ticks_per_bar

    for event in events:
        # Events have absolute tick positions, convert to relative
        absolute_tick = event["start_tick"]
        relative_tick = absolute_tick - clip_start_tick

        # Note: Offsets are applied during export/playback, not here
        # This keeps the stored notes clean and allows offset changes without regeneration

        note = Note(
            clip_id=clip.id,
            pitch=event["pitch"],
            velocity=event["velocity"],
            start_tick=relative_tick,
            duration_tick=event["duration_tick"],
            probability=1.0,
        )
        notes.append(note)

    return notes
