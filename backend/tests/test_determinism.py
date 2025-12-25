"""Tests for deterministic generation."""

import pytest

from midinecromancer.music.bass import generate_bassline
from midinecromancer.music.melody import generate_melody
from midinecromancer.music.progression import generate_chord_progression
from midinecromancer.music.rhythm import generate_drum_pattern


def test_chord_progression_determinism():
    """Test that chord progression generation is deterministic."""
    seed = 12345
    params = {"start_on": "I", "prefer_circle_motion": True, "cadence_ending": True}

    result1 = generate_chord_progression("C", "ionian", 8, seed, **params)
    result2 = generate_chord_progression("C", "ionian", 8, seed, **params)

    assert len(result1) == len(result2)
    for c1, c2 in zip(result1, result2):
        assert c1["roman_numeral"] == c2["roman_numeral"]
        assert c1["chord_name"] == c2["chord_name"]
        assert c1["start_bar"] == c2["start_bar"]
        assert c1["length_bars"] == c2["length_bars"]


def test_drum_pattern_determinism():
    """Test that drum pattern generation is deterministic."""
    seed = 12345
    params = {"pattern_type": "full", "swing": 0.0, "variation": 0.1}

    result1 = generate_drum_pattern(8, 4, 4, seed, **params)
    result2 = generate_drum_pattern(8, 4, 4, seed, **params)

    assert len(result1) == len(result2)
    for n1, n2 in zip(result1, result2):
        assert n1["pitch"] == n2["pitch"]
        assert n1["start_tick"] == n2["start_tick"]
        assert n1["duration_tick"] == n2["duration_tick"]


def test_melody_determinism():
    """Test that melody generation is deterministic."""
    seed = 12345
    params = {"octave": 5, "stepwise_bias": 0.7, "leap_probability": 0.2}

    result1 = generate_melody("C", "ionian", 8, 4, 4, seed, **params)
    result2 = generate_melody("C", "ionian", 8, 4, 4, seed, **params)

    assert len(result1) == len(result2)
    for n1, n2 in zip(result1, result2):
        assert n1["pitch"] == n2["pitch"]
        assert n1["start_tick"] == n2["start_tick"]
        assert n1["duration_tick"] == n2["duration_tick"]


def test_bassline_determinism():
    """Test that bassline generation is deterministic."""
    seed = 12345
    progression = [
        {"roman_numeral": "I", "start_bar": 0, "length_bars": 2},
        {"roman_numeral": "V", "start_bar": 2, "length_bars": 2},
        {"roman_numeral": "vi", "start_bar": 4, "length_bars": 2},
        {"roman_numeral": "IV", "start_bar": 6, "length_bars": 2},
    ]
    params = {"octave": 3, "syncopation": 0.3}

    result1 = generate_bassline("C", "ionian", 8, 4, 4, progression, seed, **params)
    result2 = generate_bassline("C", "ionian", 8, 4, 4, progression, seed, **params)

    assert len(result1) == len(result2)
    for n1, n2 in zip(result1, result2):
        assert n1["pitch"] == n2["pitch"]
        assert n1["start_tick"] == n2["start_tick"]
        assert n1["duration_tick"] == n2["duration_tick"]
