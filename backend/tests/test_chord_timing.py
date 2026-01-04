"""Tests for beat-based chord timing."""

import pytest
from decimal import Decimal

from midinecromancer.models.chord_event import ChordEvent
from midinecromancer.services.chord_render import render_chord_event_to_notes


@pytest.mark.asyncio
async def test_chord_strum_beats_deterministic(session, project, clip):
    """Test that strum_beats produces deterministic results."""
    chord_event = ChordEvent(
        clip_id=clip.id,
        start_tick=0,
        duration_tick=1920,  # 4 beats at 480 PPQ
        duration_beats=Decimal("4.0"),
        roman_numeral="I",
        chord_name="Cmaj",
        intensity=Decimal("0.85"),
        voicing="root",
        inversion=0,
        strum_beats=Decimal("0.25"),  # 1/4 beat strum
        humanize_beats=Decimal("0.0"),
        is_enabled=True,
        is_locked=False,
    )
    session.add(chord_event)
    await session.flush()

    project_context = {
        "tonic": "C",
        "mode": "ionian",
        "bpm": 120,
        "time_signature_num": 4,
        "time_signature_den": 4,
    }

    # Render twice with same seed
    notes1 = render_chord_event_to_notes(chord_event, project_context, 12345)
    notes2 = render_chord_event_to_notes(chord_event, project_context, 12345)

    # Should produce same results
    assert len(notes1) == len(notes2)
    for n1, n2 in zip(notes1, notes2):
        assert n1["pitch"] == n2["pitch"]
        assert n1["start_tick"] == n2["start_tick"]
        assert n1["velocity"] == n2["velocity"]


@pytest.mark.asyncio
async def test_chord_humanize_beats_clamped(session, project, clip):
    """Test that humanize_beats is clamped to chord bounds."""
    chord_event = ChordEvent(
        clip_id=clip.id,
        start_tick=0,
        duration_tick=1920,
        duration_beats=Decimal("4.0"),
        roman_numeral="I",
        chord_name="Cmaj",
        intensity=Decimal("0.85"),
        voicing="root",
        inversion=0,
        strum_beats=Decimal("0.0"),
        humanize_beats=Decimal("0.125"),  # 1/8 beat humanize
        is_enabled=True,
        is_locked=False,
    )
    session.add(chord_event)
    await session.flush()

    project_context = {
        "tonic": "C",
        "mode": "ionian",
        "bpm": 120,
        "time_signature_num": 4,
        "time_signature_den": 4,
    }

    notes = render_chord_event_to_notes(chord_event, project_context, 12345)

    # All notes should be within chord bounds
    for note in notes:
        assert note["start_tick"] >= 0
        assert note["start_tick"] + note["duration_tick"] <= 1920


@pytest.mark.asyncio
async def test_chord_strum_distributes_notes(session, project, clip):
    """Test that strum distributes notes across strum duration."""
    chord_event = ChordEvent(
        clip_id=clip.id,
        start_tick=0,
        duration_tick=1920,
        duration_beats=Decimal("4.0"),
        roman_numeral="I",
        chord_name="Cmaj",
        intensity=Decimal("0.85"),
        voicing="root",
        inversion=0,
        strum_beats=Decimal("0.5"),  # 1/2 beat strum
        humanize_beats=Decimal("0.0"),
        is_enabled=True,
        is_locked=False,
    )
    session.add(chord_event)
    await session.flush()

    project_context = {
        "tonic": "C",
        "mode": "ionian",
        "bpm": 120,
        "time_signature_num": 4,
        "time_signature_den": 4,
    }

    notes = render_chord_event_to_notes(chord_event, project_context, 12345)

    # Should have multiple notes
    assert len(notes) >= 3

    # Notes should be spread across strum duration
    start_ticks = sorted([n["start_tick"] for n in notes])
    if len(start_ticks) > 1:
        # First and last should be different
        assert start_ticks[0] < start_ticks[-1]
        # Spread should be approximately strum_beats * PPQ
        spread = start_ticks[-1] - start_ticks[0]
        expected_spread = int(0.5 * 480)  # 0.5 beats * 480 PPQ
        assert abs(spread - expected_spread) < 10  # Allow small tolerance

