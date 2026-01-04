"""Deterministic offset generation for arrangement synchronization."""

import hashlib
from typing import Literal


def deterministic_offset(
    seed: int, object_id: str, kind: Literal["clip", "track", "lane"] = "clip"
) -> int:
    """Generate a deterministic offset in ticks for an object.

    Uses blake2b hash for deterministic but pseudo-random offsets.
    Offsets are in the range [-120, 120] ticks (approximately -1/4 to +1/4 beat).

    Args:
        seed: Base seed for determinism
        object_id: Unique identifier for the object (UUID string)
        kind: Type of object ("clip", "track", or "lane")

    Returns:
        Offset in ticks (can be negative)
    """
    # Create hash input
    hash_input = f"{seed}:{object_id}:{kind}".encode()

    # Use blake2b for deterministic hashing
    hash_bytes = hashlib.blake2b(hash_input, digest_size=8).digest()

    # Convert to integer
    hash_int = int.from_bytes(hash_bytes, byteorder="big")

    # Map to offset range [-120, 120] ticks (1/4 beat at PPQ=480)
    # This gives subtle timing variations without breaking alignment
    offset = (hash_int % 241) - 120

    return offset


def apply_offsets_to_tick(base_tick: int, clip_offset: int = 0, track_offset: int = 0) -> int:
    """Apply clip and track offsets to a base tick position.

    Args:
        base_tick: Original tick position
        clip_offset: Offset from clip.start_offset_ticks
        track_offset: Offset from track.start_offset_ticks

    Returns:
        Adjusted tick position
    """
    return base_tick + clip_offset + track_offset
