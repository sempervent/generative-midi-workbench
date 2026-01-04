"""Tests for offset functionality."""

import pytest

from midinecromancer.music.offsets import apply_offsets_to_tick, deterministic_offset


def test_deterministic_offset():
    """Test that deterministic offsets are consistent."""
    seed = 12345
    object_id = "test-id-123"

    offset1 = deterministic_offset(seed, object_id, "clip")
    offset2 = deterministic_offset(seed, object_id, "clip")

    # Same seed + object_id should produce same offset
    assert offset1 == offset2

    # Different object_id should produce different offset
    offset3 = deterministic_offset(seed, "different-id", "clip")
    assert offset1 != offset3

    # Different seed should produce different offset
    offset4 = deterministic_offset(99999, object_id, "clip")
    assert offset1 != offset4

    # Offset should be in range [-120, 120]
    assert -120 <= offset1 <= 120


def test_apply_offsets_to_tick():
    """Test offset application."""
    base_tick = 1000

    # No offsets
    result = apply_offsets_to_tick(base_tick, 0, 0)
    assert result == 1000

    # Clip offset only
    result = apply_offsets_to_tick(base_tick, 60, 0)
    assert result == 1060

    # Track offset only
    result = apply_offsets_to_tick(base_tick, 0, 120)
    assert result == 1120

    # Both offsets
    result = apply_offsets_to_tick(base_tick, 60, 120)
    assert result == 1180

    # Negative offsets
    result = apply_offsets_to_tick(base_tick, -60, -120)
    assert result == 820

