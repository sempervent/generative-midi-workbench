"""Tests for polyrhythm generation."""

import pytest

from midinecromancer.music.polyrhythm import (
    CycleSpec,
    calculate_ratio,
    generate_euclidean_pattern,
    lcm_resolution,
    render_to_events,
)


def test_euclidean_pattern():
    """Test Euclidean pattern generation."""
    pattern = generate_euclidean_pattern(8, 3, 0)
    assert len(pattern) == 8
    assert sum(pattern) == 3
    # Should be [True, False, False, True, False, False, True, False] for 8,3
    assert pattern[0] is True
    assert pattern[3] is True
    assert pattern[6] is True


def test_cycle_spec():
    """Test CycleSpec creation."""
    cycle = CycleSpec(steps=8, pulses=3, cycle_beats=4.0, rotation=0)
    assert cycle.steps == 8
    assert cycle.pulses == 3
    assert cycle.cycle_beats == 4.0
    assert cycle.rotation == 0


def test_lcm_resolution():
    """Test LCM resolution calculation."""
    cycles = [
        CycleSpec(steps=3, pulses=2, cycle_beats=3.0),
        CycleSpec(steps=4, pulses=3, cycle_beats=4.0),
    ]
    lcm = lcm_resolution(cycles)
    assert lcm == 12  # LCM of 3 and 4

    cycles2 = [
        CycleSpec(steps=5, pulses=3, cycle_beats=5.0),
        CycleSpec(steps=7, pulses=4, cycle_beats=7.0),
    ]
    lcm2 = lcm_resolution(cycles2)
    assert lcm2 == 35  # LCM of 5 and 7


def test_render_to_events_deterministic():
    """Test that rendering is deterministic."""
    cycle = CycleSpec(steps=5, pulses=3, cycle_beats=4.0, rotation=0)

    events1 = render_to_events(
        cycle=cycle,
        clip_start_bar=0,
        clip_length_bars=2,
        project_bpm=120,
        time_signature_num=4,
        time_signature_den=4,
        seed=12345,
        pitch=60,
        velocity=100,
    )

    events2 = render_to_events(
        cycle=cycle,
        clip_start_bar=0,
        clip_length_bars=2,
        project_bpm=120,
        time_signature_num=4,
        time_signature_den=4,
        seed=12345,
        pitch=60,
        velocity=100,
    )

    assert len(events1) == len(events2)
    for e1, e2 in zip(events1, events2):
        assert e1["pitch"] == e2["pitch"]
        assert e1["start_tick"] == e2["start_tick"]
        assert e1["duration_tick"] == e2["duration_tick"]


def test_calculate_ratio():
    """Test ratio calculation."""
    cycle1 = CycleSpec(steps=3, pulses=2, cycle_beats=3.0)
    assert "2:3" in calculate_ratio(cycle1) or "2 over 3" in calculate_ratio(cycle1)

    cycle2 = CycleSpec(steps=5, pulses=3, cycle_beats=5.0)
    ratio = calculate_ratio(cycle2)
    assert "3" in ratio and "5" in ratio


def test_render_polyrhythm_3_over_2():
    """Test rendering a 3:2 polyrhythm."""
    cycle = CycleSpec(steps=3, pulses=2, cycle_beats=2.0)  # 2 beats for 3 steps

    events = render_to_events(
        cycle=cycle,
        clip_start_bar=0,
        clip_length_bars=1,
        project_bpm=120,
        time_signature_num=4,
        time_signature_den=4,
        seed=42,
        pitch=60,
        velocity=100,
    )

    # Should have 2 events per cycle, and at least 1 cycle in 1 bar
    assert len(events) >= 2
    # Events should be spaced within the cycle
    if len(events) >= 2:
        # First two events should be within 2 beats (1920 ticks at 120 BPM)
        assert events[1]["start_tick"] - events[0]["start_tick"] < 1920
