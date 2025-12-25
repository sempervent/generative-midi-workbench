"""Tests for suggestion generation."""

import pytest
import uuid

from midinecromancer.music.analysis import ProjectAnalysis
from midinecromancer.music.suggest import (
    deterministic_suggestion_seed,
    generate_all_suggestions,
    generate_harmony_suggestions,
)


def test_deterministic_suggestion_seed():
    """Test that suggestion seed generation is stable."""
    base_seed = 12345
    project_id = uuid.uuid4()
    kind = "harmony"
    index = 0

    seed1 = deterministic_suggestion_seed(base_seed, project_id, kind, index)
    seed2 = deterministic_suggestion_seed(base_seed, project_id, kind, index)

    assert seed1 == seed2

    # Different indices produce different seeds
    seed3 = deterministic_suggestion_seed(base_seed, project_id, kind, 1)
    assert seed1 != seed3


def test_generate_harmony_suggestions_deterministic():
    """Test that harmony suggestions are deterministic."""
    analysis = ProjectAnalysis(detected_key="C", detected_mode="ionian")
    project_id = uuid.uuid4()
    seed = 12345

    suggestions1 = generate_harmony_suggestions(
        analysis=analysis,
        project_id=project_id,
        project_seed=seed,
        bars=8,
        time_signature_num=4,
        time_signature_den=4,
        bpm=120,
        chord_events=[],
        complexity=0.5,
        tension=0.5,
    )

    suggestions2 = generate_harmony_suggestions(
        analysis=analysis,
        project_id=project_id,
        project_seed=seed,
        bars=8,
        time_signature_num=4,
        time_signature_den=4,
        bpm=120,
        chord_events=[],
        complexity=0.5,
        tension=0.5,
    )

    assert len(suggestions1) == len(suggestions2)
    for s1, s2 in zip(suggestions1, suggestions2):
        assert s1.title == s2.title
        assert s1.explanation == s2.explanation
        assert s1.score == s2.score
        assert len(s1.preview_events) == len(s2.preview_events)


def test_suggestions_sorted_by_score():
    """Test that suggestions are sorted by score."""
    analysis = ProjectAnalysis(detected_key="C", detected_mode="ionian")
    project_id = uuid.uuid4()

    suggestions = generate_all_suggestions(
        analysis=analysis,
        project_id=project_id,
        project_seed=12345,
        bars=8,
        time_signature_num=4,
        time_signature_den=4,
        bpm=120,
        chord_events=[],
        lanes=None,
        params={},
    )

    # Check sorting: scores should be descending
    scores = [s.score for s in suggestions]
    assert scores == sorted(scores, reverse=True)

    # If scores are equal, should be sorted by title
    for i in range(len(suggestions) - 1):
        if suggestions[i].score == suggestions[i + 1].score:
            assert suggestions[i].title <= suggestions[i + 1].title


def test_suggestion_preview_events_format():
    """Test that preview events have correct format."""
    analysis = ProjectAnalysis(detected_key="C", detected_mode="ionian")
    project_id = uuid.uuid4()

    suggestions = generate_harmony_suggestions(
        analysis=analysis,
        project_id=project_id,
        project_seed=12345,
        bars=8,
        time_signature_num=4,
        time_signature_den=4,
        bpm=120,
        chord_events=[],
    )

    for suggestion in suggestions:
        for event in suggestion.preview_events:
            assert "pitch" in event
            assert "velocity" in event
            assert "start_tick" in event
            assert "duration_tick" in event
            assert "channel" in event
            assert 0 <= event["pitch"] <= 127
            assert 1 <= event["velocity"] <= 127
            assert event["start_tick"] >= 0
            assert event["duration_tick"] > 0


def test_commit_plan_format():
    """Test that commit plans have required fields."""
    analysis = ProjectAnalysis(detected_key="C", detected_mode="ionian")
    project_id = uuid.uuid4()

    suggestions = generate_all_suggestions(
        analysis=analysis,
        project_id=project_id,
        project_seed=12345,
        bars=8,
        time_signature_num=4,
        time_signature_den=4,
        bpm=120,
        chord_events=[],
        lanes=None,
        params={},
    )

    for suggestion in suggestions:
        commit_plan = suggestion.commit_plan
        assert "action" in commit_plan
        assert commit_plan["action"] in [
            "create_chord_event",
            "create_chord_events",
            "create_notes",
            "append_notes",
            "update_lane_rotation",
        ]
