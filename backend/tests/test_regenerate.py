"""Tests for clip regeneration."""

import pytest
from uuid import uuid4

from midinecromancer.services.regenerate import RegenerateService


@pytest.mark.asyncio
async def test_regenerate_preview_no_db_writes(session, project, track, clip):
    """Test that preview mode does not write to database."""
    service = RegenerateService(session)

    result = await service.regenerate_clip(
        clip_id=clip.id,
        kind=track.role,
        seed=12345,
        variation=0.3,
        params={},
        preview=True,
    )

    assert "events" in result or "chord_events" in result or "note_events" in result

    # Verify no DB writes (check note count)
    from midinecromancer.models.note import Note
    from sqlalchemy import select, func

    count_result = await session.execute(select(func.count(Note.id)).where(Note.clip_id == clip.id))
    note_count = count_result.scalar()
    assert note_count == 0  # No notes should be created


@pytest.mark.asyncio
async def test_regenerate_apply_writes_notes(session, project, track, clip):
    """Test that apply mode writes notes to database."""
    service = RegenerateService(session)

    result = await service.regenerate_clip(
        clip_id=clip.id,
        kind=track.role,
        seed=12345,
        variation=0.3,
        params={},
        preview=False,
    )

    # Verify notes were created
    from midinecromancer.models.note import Note
    from sqlalchemy import select

    result_query = await session.execute(select(Note).where(Note.clip_id == clip.id))
    notes = result_query.scalars().all()
    assert len(notes) > 0


@pytest.mark.asyncio
async def test_regenerate_deterministic(session, project, track, clip):
    """Test that same seed produces same output."""
    service = RegenerateService(session)

    result1 = await service.regenerate_clip(
        clip_id=clip.id,
        kind=track.role,
        seed=99999,
        variation=0.3,
        params={},
        preview=True,
    )

    result2 = await service.regenerate_clip(
        clip_id=clip.id,
        kind=track.role,
        seed=99999,
        variation=0.3,
        params={},
        preview=True,
    )

    # Same seed should produce same events
    events1 = result1.get("events", result1.get("note_events", []))
    events2 = result2.get("events", result2.get("note_events", []))

    assert len(events1) == len(events2)
    # Compare first few events
    for e1, e2 in zip(events1[:5], events2[:5]):
        assert e1["pitch"] == e2["pitch"]
        assert e1["start_tick"] == e2["start_tick"]


@pytest.mark.asyncio
async def test_regenerate_variation_produces_different(session, project, track, clip):
    """Test that different variation produces different output."""
    service = RegenerateService(session)

    result1 = await service.regenerate_clip(
        clip_id=clip.id,
        kind=track.role,
        seed=12345,
        variation=0.1,
        params={},
        preview=True,
    )

    result2 = await service.regenerate_clip(
        clip_id=clip.id,
        kind=track.role,
        seed=12345,
        variation=0.9,
        params={},
        preview=True,
    )

    # Different variation should produce different events (with high probability)
    events1 = result1.get("events", result1.get("note_events", []))
    events2 = result2.get("events", result2.get("note_events", []))

    # At least some events should differ
    if len(events1) > 0 and len(events2) > 0:
        # Compare pitches - should have some differences
        pitches1 = [e["pitch"] for e in events1]
        pitches2 = [e["pitch"] for e in events2]
        # Allow for some overlap but not identical
        assert pitches1 != pitches2 or len(pitches1) != len(pitches2)

