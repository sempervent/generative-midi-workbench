"""Polyrhythm generation engine with LCM alignment."""

import hashlib
import math
import random
from dataclasses import dataclass
from fractions import Fraction
from typing import Literal
from uuid import UUID

from midinecromancer.music.theory import PPQ


class CycleSpec:
    """Specification for a polyrhythm cycle."""

    def __init__(
        self,
        steps: int,
        pulses: int,
        cycle_beats: float,
        rotation: int = 0,
        swing: float | None = None,
    ):
        """Initialize cycle specification.

        Args:
            steps: Number of grid steps in the cycle
            pulses: Number of onsets (active steps)
            cycle_beats: Length of cycle in beats
            rotation: Rotation offset (0 to steps-1)
            swing: Swing amount (0.0-1.0, None for no swing)
        """
        self.steps = steps
        self.pulses = pulses
        self.cycle_beats = cycle_beats
        self.rotation = rotation % steps if steps > 0 else 0
        self.swing = swing

    def __repr__(self) -> str:
        return (
            f"CycleSpec(steps={self.steps}, pulses={self.pulses}, "
            f"cycle_beats={self.cycle_beats}, rotation={self.rotation})"
        )


def lcm_resolution(cycles: list[CycleSpec]) -> int:
    """Calculate LCM resolution for aligning multiple cycles.

    Args:
        cycles: List of cycle specifications

    Returns:
        LCM of all cycle step counts, or 1 if empty
    """
    if not cycles:
        return 1

    step_counts = [c.steps for c in cycles]
    lcm = step_counts[0]
    for count in step_counts[1:]:
        lcm = lcm * count // math.gcd(lcm, count)
    return lcm


def generate_euclidean_pattern(steps: int, pulses: int, rotation: int = 0) -> list[bool]:
    """Generate Euclidean rhythm pattern using Bjorklund algorithm.

    Args:
        steps: Total steps
        pulses: Number of pulses
        rotation: Rotation offset

    Returns:
        List of booleans indicating active steps
    """
    if pulses == 0:
        return [False] * steps
    if pulses >= steps:
        return [True] * steps

    # Bjorklund algorithm
    pattern = [False] * steps
    bucket = pulses

    for i in range(steps):
        bucket += pulses
        if bucket >= steps:
            pattern[i] = True
            bucket -= steps

    # Apply rotation
    if rotation != 0:
        pattern = pattern[rotation:] + pattern[:rotation]

    return pattern


def render_to_events(
    cycle: CycleSpec,
    clip_start_bar: int,
    clip_length_bars: int,
    project_bpm: int,
    time_signature_num: int,
    time_signature_den: int,
    seed: int,
    pitch: int = 60,
    velocity: int = 100,
) -> list[dict]:
    """Render polyrhythm cycle to note events.

    Args:
        cycle: Cycle specification
        clip_start_bar: Starting bar of clip
        clip_length_bars: Length of clip in bars
        project_bpm: Project BPM
        time_signature_num: Time signature numerator
        time_signature_den: Time signature denominator
        seed: Random seed for variation
        pitch: MIDI pitch for events
        velocity: MIDI velocity for events

    Returns:
        List of note events: {pitch, velocity, start_tick, duration_tick}
    """
    rng = random.Random(seed)

    # Calculate timing
    quarter_notes_per_bar = (time_signature_num * 4) / time_signature_den
    ticks_per_bar = int(quarter_notes_per_bar * PPQ)
    clip_start_tick = clip_start_bar * ticks_per_bar

    # Generate pattern
    pattern = generate_euclidean_pattern(cycle.steps, cycle.pulses, cycle.rotation)

    # Calculate step duration in ticks
    cycle_ticks = int(cycle.cycle_beats * PPQ)
    step_ticks = cycle_ticks // cycle.steps if cycle.steps > 0 else 0

    events = []
    total_cycles = 0
    max_cycles = int((clip_length_bars * ticks_per_bar) / cycle_ticks) + 1

    while total_cycles * cycle_ticks < clip_length_bars * ticks_per_bar:
        for step_idx, is_active in enumerate(pattern):
            cycle_offset = total_cycles * cycle_ticks
            step_offset = step_idx * step_ticks
            event_tick = clip_start_tick + cycle_offset + step_offset

            # Check if event is within clip bounds
            clip_end_tick = clip_start_tick + (clip_length_bars * ticks_per_bar)
            if event_tick >= clip_end_tick:
                break

            if is_active:
                # Apply swing if specified
                if cycle.swing is not None and cycle.swing > 0:
                    # Swing applies to off-beat steps (odd indices)
                    if step_idx % 2 == 1:
                        swing_offset = int(step_ticks * cycle.swing * 0.5)
                        event_tick += swing_offset

                # Apply humanization if specified (not implemented in v1, but structure ready)
                # if cycle.humanize_ms:
                #     humanize_ticks = int((cycle.humanize_ms / 1000) * (PPQ * project_bpm / 60))
                #     event_tick += rng.randint(-humanize_ticks, humanize_ticks)

                # Duration: typically 1/16th note or step-based
                duration = step_ticks // 2  # Half of step duration

                events.append(
                    {
                        "pitch": pitch,
                        "velocity": velocity + rng.randint(-10, 10),  # Slight variation
                        "start_tick": event_tick,
                        "duration_tick": max(duration, PPQ // 32),  # Minimum duration
                    }
                )

        total_cycles += 1
        if total_cycles >= max_cycles:
            break

    return events


def calculate_ratio(cycle: CycleSpec) -> str:
    """Calculate and return a human-readable ratio for the cycle.

    Args:
        cycle: Cycle specification

    Returns:
        String like "3:2" or "5 over 4"
    """
    if cycle.pulses == 0:
        return "0:1"

    # Simplify ratio
    gcd = math.gcd(cycle.steps, cycle.pulses)
    simplified_steps = cycle.steps // gcd
    simplified_pulses = cycle.pulses // gcd

    # If cycle_beats suggests a different ratio, show both
    if cycle.cycle_beats != float(simplified_steps):
        return f"{simplified_pulses} over {simplified_steps} ({cycle.cycle_beats} beats)"
    return f"{simplified_pulses}:{simplified_steps}"


def align_events_to_lcm(
    events: list[dict],
    cycles: list[CycleSpec],
    project_bpm: int,
    time_signature_num: int,
    time_signature_den: int,
) -> list[dict]:
    """Align events to LCM grid for visualization/export.

    Args:
        events: List of note events
        cycles: List of cycle specifications
        project_bpm: Project BPM
        time_signature_num: Time signature numerator
        time_signature_den: Time signature denominator

    Returns:
        Events with tick positions aligned to LCM grid
    """
    if not cycles:
        return events

    lcm_steps = lcm_resolution(cycles)
    quarter_notes_per_bar = (time_signature_num * 4) / time_signature_den
    ticks_per_bar = int(quarter_notes_per_bar * PPQ)
    lcm_subdivision = ticks_per_bar // lcm_steps if lcm_steps > 0 else ticks_per_bar

    aligned = []
    for event in events:
        # Round to nearest LCM subdivision
        rounded_tick = round(event["start_tick"] / lcm_subdivision) * lcm_subdivision
        aligned_event = event.copy()
        aligned_event["start_tick"] = int(rounded_tick)
        aligned.append(aligned_event)

    return aligned


@dataclass
class LaneSpec:
    """Specification for a polyrhythm lane."""

    cycle: CycleSpec
    lane_id: UUID
    clip_id: UUID
    pitch: int
    velocity: int
    mute: bool
    solo: bool
    order_index: int
    seed_offset: int
    humanize_ms: int | None = None

    def __repr__(self) -> str:
        return (
            f"LaneSpec(lane_id={self.lane_id}, pitch={self.pitch}, "
            f"order={self.order_index}, cycle={self.cycle})"
        )


@dataclass
class GridSpec:
    """Specification for LCM-aligned grid."""

    ticks_per_bar: int
    ticks_per_step: int
    grid_steps_per_bar: int
    lcm_steps: int

    def __repr__(self) -> str:
        return (
            f"GridSpec(ticks_per_bar={self.ticks_per_bar}, "
            f"ticks_per_step={self.ticks_per_step}, "
            f"grid_steps_per_bar={self.grid_steps_per_bar}, lcm={self.lcm_steps})"
        )


def deterministic_seed(base_seed: int, clip_id: UUID, lane_id: UUID, seed_offset: int) -> int:
    """Generate deterministic seed for a lane using stable hashing.

    Args:
        base_seed: Base project seed
        clip_id: Clip UUID
        lane_id: Lane UUID
        seed_offset: Additional offset

    Returns:
        Deterministic integer seed
    """
    # Use blake2b for stable hashing (not affected by Python hash randomization)
    clip_bytes = str(clip_id).encode()
    lane_bytes = str(lane_id).encode()
    combined = f"{base_seed}:{clip_id}:{lane_id}:{seed_offset}".encode()

    hash_obj = hashlib.blake2b(combined, digest_size=8)
    hash_int = int.from_bytes(hash_obj.digest(), byteorder="big")
    # Combine with base seed using XOR
    return base_seed ^ hash_int ^ seed_offset


def lcm_grid_for_lanes(
    lanes: list[LaneSpec],
    time_signature_num: int,
    time_signature_den: int,
) -> GridSpec:
    """Calculate LCM grid specification for multiple lanes.

    Args:
        lanes: List of lane specifications
        time_signature_num: Time signature numerator
        time_signature_den: Time signature denominator

    Returns:
        GridSpec with LCM-aligned grid parameters
    """
    if not lanes:
        # Default grid
        quarter_notes_per_bar = (time_signature_num * 4) / time_signature_den
        ticks_per_bar = int(quarter_notes_per_bar * PPQ)
        return GridSpec(
            ticks_per_bar=ticks_per_bar,
            ticks_per_step=PPQ // 4,  # 16th notes
            grid_steps_per_bar=16,
            lcm_steps=16,
        )

    # Get LCM of all lane step counts
    step_counts = [lane.cycle.steps for lane in lanes]
    lcm_steps = step_counts[0]
    for count in step_counts[1:]:
        lcm_steps = lcm_steps * count // math.gcd(lcm_steps, count)

    # Calculate grid based on time signature
    quarter_notes_per_bar = (time_signature_num * 4) / time_signature_den
    ticks_per_bar = int(quarter_notes_per_bar * PPQ)

    # Normalize grid steps per bar to a reasonable resolution
    # Use LCM steps, but ensure it's a multiple of common subdivisions
    grid_steps_per_bar = max(lcm_steps, 16)  # At least 16th note resolution
    ticks_per_step = ticks_per_bar // grid_steps_per_bar

    return GridSpec(
        ticks_per_bar=ticks_per_bar,
        ticks_per_step=ticks_per_step,
        grid_steps_per_bar=grid_steps_per_bar,
        lcm_steps=lcm_steps,
    )


def render_lanes_to_events(
    lanes: list[LaneSpec],
    clip_start_bar: int,
    clip_length_bars: int,
    project_bpm: int,
    time_signature_num: int,
    time_signature_den: int,
    base_seed: int,
) -> list[dict]:
    """Render multiple polyrhythm lanes to a merged event list.

    Args:
        lanes: List of lane specifications
        clip_start_bar: Starting bar of clip
        clip_length_bars: Length of clip in bars
        project_bpm: Project BPM
        time_signature_num: Time signature numerator
        time_signature_den: Time signature denominator
        base_seed: Base project seed

    Returns:
        Merged list of note events, sorted by start_tick, then order_index, then pitch
    """
    all_events = []

    # Check if any lane is soloed
    has_solo = any(lane.solo for lane in lanes)

    for lane in lanes:
        # Apply mute/solo logic
        if lane.mute:
            continue
        if has_solo and not lane.solo:
            continue

        # Generate deterministic seed for this lane
        lane_seed = deterministic_seed(base_seed, lane.clip_id, lane.lane_id, lane.seed_offset)

        # Render events for this lane
        lane_events = render_to_events(
            cycle=lane.cycle,
            clip_start_bar=clip_start_bar,
            clip_length_bars=clip_length_bars,
            project_bpm=project_bpm,
            time_signature_num=time_signature_num,
            time_signature_den=time_signature_den,
            seed=lane_seed,
            pitch=lane.pitch,
            velocity=lane.velocity,
        )

        # Apply humanization if specified (deterministic)
        if lane.humanize_ms and lane.humanize_ms > 0:
            rng = random.Random(lane_seed)
            humanize_ticks = int((lane.humanize_ms / 1000) * (PPQ * project_bpm / 60))
            quarter_notes_per_bar = (time_signature_num * 4) / time_signature_den
            ticks_per_bar = int(quarter_notes_per_bar * PPQ)
            clip_start_tick = clip_start_bar * ticks_per_bar
            clip_end_tick = clip_start_tick + (clip_length_bars * ticks_per_bar)

            for event in lane_events:
                # Humanize within bounds
                offset = rng.randint(-humanize_ticks, humanize_ticks)
                new_tick = event["start_tick"] + offset
                # Clamp to clip bounds
                new_tick = max(
                    clip_start_tick, min(new_tick, clip_end_tick - event["duration_tick"])
                )
                event["start_tick"] = new_tick

        # Add lane metadata for sorting
        for event in lane_events:
            event["_lane_order"] = lane.order_index
            event["_lane_id"] = str(lane.lane_id)

        all_events.extend(lane_events)

    # Sort: start_tick, then order_index, then pitch
    all_events.sort(key=lambda e: (e["start_tick"], e.get("_lane_order", 0), e["pitch"]))

    # Remove metadata before returning
    for event in all_events:
        event.pop("_lane_order", None)
        event.pop("_lane_id", None)

    return all_events
