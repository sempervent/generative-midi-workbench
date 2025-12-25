"""Tests for music theory module."""

import pytest

from midinecromancer.music.theory import (
    get_scale_degrees,
    parse_tonic,
    pitch_class_to_midi,
    roman_to_degree,
)


def test_parse_tonic():
    """Test tonic parsing."""
    assert parse_tonic("C") == 0
    assert parse_tonic("C#") == 1
    assert parse_tonic("Db") == 1
    assert parse_tonic("F") == 5
    assert parse_tonic("F#") == 6


def test_get_scale_degrees():
    """Test scale degree generation."""
    # C major (ionian)
    scale = get_scale_degrees("C", "ionian", 4)
    assert scale[0] == 60  # C4
    assert scale[1] == 62  # D4
    assert scale[2] == 64  # E4
    assert scale[3] == 65  # F4
    assert scale[4] == 67  # G4
    assert scale[5] == 69  # A4
    assert scale[6] == 71  # B4

    # A minor (aeolian)
    scale = get_scale_degrees("A", "aeolian", 4)
    assert scale[0] == 57  # A4
    assert scale[1] == 59  # B4
    assert scale[2] == 60  # C5
    assert scale[3] == 62  # D5


def test_roman_to_degree():
    """Test roman numeral to degree conversion."""
    assert roman_to_degree("I") == 1
    assert roman_to_degree("ii") == 2
    assert roman_to_degree("V") == 5
    assert roman_to_degree("vi") == 6
    assert roman_to_degree("V7") == 5  # Strips suffix


def test_pitch_class_to_midi():
    """Test pitch class to MIDI conversion."""
    assert pitch_class_to_midi(0, 4) == 48  # C4
    assert pitch_class_to_midi(0, 5) == 60  # C5
    assert pitch_class_to_midi(7, 4) == 55  # G4
