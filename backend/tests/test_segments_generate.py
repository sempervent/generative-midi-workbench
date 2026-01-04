"""Tests for segment generation."""

import pytest
from uuid import uuid4

from midinecromancer.schemas.segment import (
    BassModel,
    BeatsModel,
    ChordsModel,
    MelodyModel,
    SegmentCreateRequest,
)
from midinecromancer.services.segments import SegmentService


@pytest.mark.asyncio
async def test_generate_segments_preview_no_db_writes(session, project):
    """Test that preview mode does not write to database."""
    service = SegmentService(session)

    request = SegmentCreateRequest(
        project_id=project.id,
        start_bar=0,
        length_bars=4,
        seed=12345,
        kinds=["beats", "chords"],
        models={
            "beats": BeatsModel(),
            "chords": ChordsModel(),
        },
        preview=True,
    )

    result = await service.generate_segments(request)

    assert result.preview is True
    assert len(result.clips) == 2
    # Check that clips have preview IDs
    assert all(clip["id"].startswith("preview_") for clip in result.clips)

    # Verify no DB writes (check clip count)
    from midinecromancer.models.clip import Clip
    from sqlalchemy import select, func

    count_result = await session.execute(select(func.count(Clip.id)))
    clip_count = count_result.scalar()
    assert clip_count == 0  # No clips should be created


@pytest.mark.asyncio
async def test_generate_segments_apply_creates_clips(session, project):
    """Test that apply mode creates clips in database."""
    service = SegmentService(session)

    request = SegmentCreateRequest(
        project_id=project.id,
        start_bar=0,
        length_bars=4,
        seed=12345,
        kinds=["beats", "chords", "bass", "melody"],
        models={
            "beats": BeatsModel(),
            "chords": ChordsModel(),
            "bass": BassModel(),
            "melody": MelodyModel(),
        },
        preview=False,
    )

    result = await service.generate_segments(request)

    assert result.preview is False
    assert len(result.clips) == 4

    # Verify clips were created in DB
    from midinecromancer.models.clip import Clip
    from sqlalchemy import select

    result_query = await session.execute(select(Clip))
    clips = result_query.scalars().all()
    assert len(clips) == 4

    # Verify each clip has notes or chord events
    for clip in clips:
        assert clip.start_bar == 0
        assert clip.length_bars == 4


@pytest.mark.asyncio
async def test_generate_segments_deterministic(session, project):
    """Test that same seed produces same output."""
    service = SegmentService(session)

    request1 = SegmentCreateRequest(
        project_id=project.id,
        start_bar=0,
        length_bars=4,
        seed=99999,
        kinds=["beats"],
        models={"beats": BeatsModel()},
        preview=True,
    )

    request2 = SegmentCreateRequest(
        project_id=project.id,
        start_bar=0,
        length_bars=4,
        seed=99999,
        kinds=["beats"],
        models={"beats": BeatsModel()},
        preview=True,
    )

    result1 = await service.generate_segments(request1)
    result2 = await service.generate_segments(request2)

    # Same seed should produce same events
    events1 = result1.events_by_clip.get(result1.clips[0]["id"], [])
    events2 = result2.events_by_clip.get(result2.clips[0]["id"], [])

    assert len(events1) == len(events2)
    # Compare first few events
    for e1, e2 in zip(events1[:5], events2[:5]):
        assert e1["pitch"] == e2["pitch"]
        assert e1["start_tick"] == e2["start_tick"]


@pytest.mark.asyncio
async def test_generate_chords_produces_notes(session, project):
    """Test that chord generation produces note events for playback."""
    service = SegmentService(session)

    request = SegmentCreateRequest(
        project_id=project.id,
        start_bar=0,
        length_bars=4,
        seed=12345,
        kinds=["chords"],
        models={"chords": ChordsModel()},
        preview=False,
    )

    result = await service.generate_segments(request)

    assert len(result.clips) == 1
    clip_id = result.clips[0]["id"]

    # Check that chord events were created
    assert clip_id in result.chords_by_clip
    chord_events = result.chords_by_clip[clip_id]
    assert len(chord_events) > 0

    # Check that notes were generated for playback
    assert clip_id in result.events_by_clip
    note_events = result.events_by_clip[clip_id]
    assert len(note_events) > 0  # Chords should render to notes

    # Verify notes have valid pitch/velocity
    for note in note_events:
        assert 0 <= note["pitch"] <= 127
        assert 0 < note["velocity"] <= 127

