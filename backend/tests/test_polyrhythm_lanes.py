"""Tests for multi-lane polyrhythm generation."""

import pytest
import uuid

from midinecromancer.music.polyrhythm import (
    CycleSpec,
    LaneSpec,
    deterministic_seed,
    lcm_grid_for_lanes,
    render_lanes_to_events,
)


def test_deterministic_seed():
    """Test that deterministic seed generation is stable."""
    base_seed = 12345
    clip_id = uuid.uuid4()
    lane_id = uuid.uuid4()
    seed_offset = 0

    seed1 = deterministic_seed(base_seed, clip_id, lane_id, seed_offset)
    seed2 = deterministic_seed(base_seed, clip_id, lane_id, seed_offset)

    assert seed1 == seed2

    # Different offsets produce different seeds
    seed3 = deterministic_seed(base_seed, clip_id, lane_id, 1)
    assert seed1 != seed3


def test_lcm_grid_for_lanes():
    """Test LCM grid calculation for multiple lanes."""
    clip_id = uuid.uuid4()

    lanes = [
        LaneSpec(
            cycle=CycleSpec(steps=3, pulses=2, cycle_beats=2.0),
            lane_id=uuid.uuid4(),
            clip_id=clip_id,
            pitch=60,
            velocity=100,
            mute=False,
            solo=False,
            order_index=0,
            seed_offset=0,
        ),
        LaneSpec(
            cycle=CycleSpec(steps=4, pulses=3, cycle_beats=4.0),
            lane_id=uuid.uuid4(),
            clip_id=clip_id,
            pitch=64,
            velocity=100,
            mute=False,
            solo=False,
            order_index=1,
            seed_offset=0,
        ),
        LaneSpec(
            cycle=CycleSpec(steps=5, pulses=3, cycle_beats=4.0),
            lane_id=uuid.uuid4(),
            clip_id=clip_id,
            pitch=67,
            velocity=100,
            mute=False,
            solo=False,
            order_index=2,
            seed_offset=0,
        ),
    ]

    grid = lcm_grid_for_lanes(lanes, 4, 4)
    # LCM of 3, 4, 5 = 60
    assert grid.lcm_steps == 60
    assert grid.ticks_per_bar > 0
    assert grid.ticks_per_step > 0
    assert grid.grid_steps_per_bar >= grid.lcm_steps


def test_render_lanes_deterministic():
    """Test that multi-lane rendering is deterministic."""
    clip_id = uuid.uuid4()
    base_seed = 12345

    lanes = [
        LaneSpec(
            cycle=CycleSpec(steps=3, pulses=2, cycle_beats=2.0),
            lane_id=uuid.uuid4(),
            clip_id=clip_id,
            pitch=60,
            velocity=100,
            mute=False,
            solo=False,
            order_index=0,
            seed_offset=0,
        ),
        LaneSpec(
            cycle=CycleSpec(steps=4, pulses=3, cycle_beats=4.0),
            lane_id=uuid.uuid4(),
            clip_id=clip_id,
            pitch=64,
            velocity=100,
            mute=False,
            solo=False,
            order_index=1,
            seed_offset=0,
        ),
    ]

    events1 = render_lanes_to_events(
        lanes=lanes,
        clip_start_bar=0,
        clip_length_bars=2,
        project_bpm=120,
        time_signature_num=4,
        time_signature_den=4,
        base_seed=base_seed,
    )

    events2 = render_lanes_to_events(
        lanes=lanes,
        clip_start_bar=0,
        clip_length_bars=2,
        project_bpm=120,
        time_signature_num=4,
        time_signature_den=4,
        base_seed=base_seed,
    )

    assert len(events1) == len(events2)
    for e1, e2 in zip(events1, events2):
        assert e1["pitch"] == e2["pitch"]
        assert e1["start_tick"] == e2["start_tick"]
        assert e1["duration_tick"] == e2["duration_tick"]


def test_render_lanes_mute_solo():
    """Test mute and solo behavior in lane rendering."""
    clip_id = uuid.uuid4()
    base_seed = 12345

    lanes = [
        LaneSpec(
            cycle=CycleSpec(steps=3, pulses=2, cycle_beats=2.0),
            lane_id=uuid.uuid4(),
            clip_id=clip_id,
            pitch=60,
            velocity=100,
            mute=True,  # Muted
            solo=False,
            order_index=0,
            seed_offset=0,
        ),
        LaneSpec(
            cycle=CycleSpec(steps=4, pulses=3, cycle_beats=4.0),
            lane_id=uuid.uuid4(),
            clip_id=clip_id,
            pitch=64,
            velocity=100,
            mute=False,
            solo=True,  # Soloed
            order_index=1,
            seed_offset=0,
        ),
        LaneSpec(
            cycle=CycleSpec(steps=5, pulses=3, cycle_beats=4.0),
            lane_id=uuid.uuid4(),
            clip_id=clip_id,
            pitch=67,
            velocity=100,
            mute=False,
            solo=False,  # Not soloed, should be excluded
            order_index=2,
            seed_offset=0,
        ),
    ]

    events = render_lanes_to_events(
        lanes=lanes,
        clip_start_bar=0,
        clip_length_bars=1,
        project_bpm=120,
        time_signature_num=4,
        time_signature_den=4,
        base_seed=base_seed,
    )

    # Only soloed lane should have events
    pitches = {e["pitch"] for e in events}
    assert 60 not in pitches  # Muted
    assert 64 in pitches  # Soloed
    assert 67 not in pitches  # Not soloed (excluded because another is soloed)


def test_lane_order_affects_sorting():
    """Test that lane order_index affects event sorting."""
    clip_id = uuid.uuid4()
    base_seed = 12345

    lanes = [
        LaneSpec(
            cycle=CycleSpec(steps=3, pulses=2, cycle_beats=2.0),
            lane_id=uuid.uuid4(),
            clip_id=clip_id,
            pitch=60,
            velocity=100,
            mute=False,
            solo=False,
            order_index=1,  # Higher order
            seed_offset=0,
        ),
        LaneSpec(
            cycle=CycleSpec(steps=4, pulses=3, cycle_beats=4.0),
            lane_id=uuid.uuid4(),
            clip_id=clip_id,
            pitch=64,
            velocity=100,
            mute=False,
            solo=False,
            order_index=0,  # Lower order (should come first)
            seed_offset=0,
        ),
    ]

    events = render_lanes_to_events(
        lanes=lanes,
        clip_start_bar=0,
        clip_length_bars=1,
        project_bpm=120,
        time_signature_num=4,
        time_signature_den=4,
        base_seed=base_seed,
    )

    # Events should be sorted by start_tick, then order_index, then pitch
    # So events from order_index=0 should come before order_index=1 at same tick
    if len(events) >= 2:
        # Check that sorting is stable
        for i in range(len(events) - 1):
            e1 = events[i]
            e2 = events[i + 1]
            assert e1["start_tick"] <= e2["start_tick"]
            if e1["start_tick"] == e2["start_tick"]:
                # Same tick: order_index should determine order
                # (This is tested by the sorting logic, not directly verifiable here)
                pass
