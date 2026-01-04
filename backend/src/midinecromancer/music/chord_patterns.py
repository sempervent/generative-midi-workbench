"""Chord pattern rendering - single canonical renderer for all chord events.

This module provides the authoritative implementation for rendering chord events
to note events, used by:
- Arrangement playback plan builder
- Chord audition in modal
- MIDI export
"""

import hashlib
import random
from typing import TYPE_CHECKING

from midinecromancer.music.theory import PPQ, get_chord_notes, roman_to_degree

if TYPE_CHECKING:
    from midinecromancer.models.chord_event import ChordEvent


def deterministic_seed(base_seed: int, chord_id: str, param: str) -> int:
    """Generate deterministic seed for a chord parameter."""
    hash_input = f"{base_seed}:{chord_id}:{param}".encode()
    hash_bytes = hashlib.blake2b(hash_input, digest_size=8).digest()
    return int.from_bytes(hash_bytes, byteorder="big")


def apply_velocity_curve(
    base_velocity: int, note_index: int, total_notes: int, curve: str
) -> int:
    """Apply velocity curve to note velocity.

    Args:
        base_velocity: Base velocity (0-127)
        note_index: Index of note in chord (0-based)
        total_notes: Total number of notes in chord
        curve: Curve type ('flat', 'down', 'up', 'swell', 'dip')

    Returns:
        Adjusted velocity (0-127)
    """
    if curve == "flat" or total_notes == 1:
        return base_velocity
    if curve == "down":
        # First note loudest, descending
        factor = 1.0 - (note_index / (total_notes - 1)) * 0.3
    elif curve == "up":
        # Last note loudest, ascending
        factor = 0.7 + (note_index / (total_notes - 1)) * 0.3
    elif curve == "swell":
        # Middle notes louder
        center = (total_notes - 1) / 2
        distance = abs(note_index - center)
        factor = 1.0 - (distance / center) * 0.2
    elif curve == "dip":
        # Middle notes quieter
        center = (total_notes - 1) / 2
        distance = abs(note_index - center)
        factor = 0.8 + (distance / center) * 0.2
    else:
        factor = 1.0

    return max(1, min(127, int(base_velocity * factor)))


def render_chord_event_to_notes(
    chord_event: "ChordEvent",
    project_context: dict,
    seed: int,
) -> list[dict]:
    """Render a single chord event to note events with pattern support.

    This is the single canonical renderer used by playback, audition, and export.

    Args:
        chord_event: ChordEvent model with pattern fields
        project_context: Dict with tonic, mode, bpm, time_signature_num, time_signature_den
        seed: Base seed for determinism

    Returns:
        List of note dicts: {pitch, start_tick, duration_tick, velocity}
    """
    tonic = project_context["tonic"]
    mode = project_context["mode"]
    bpm = project_context["bpm"]
    time_signature_num = project_context["time_signature_num"]
    time_signature_den = project_context["time_signature_den"]

    # Get chord tones
    roman = chord_event.roman_numeral
    degree = roman_to_degree(roman)
    quality = "7th" if "7" in roman else "triad"
    chord_tones = get_chord_notes(tonic, mode, degree, quality, octave=4)

    # Apply voicing and inversion
    from midinecromancer.services.chord_render import apply_voicing

    voicing_pitches = apply_voicing(
        chord_tones,
        chord_event.voicing or "root",
        chord_event.inversion or 0,
        voicing_low=48,
        voicing_high=72,
    )

    if not voicing_pitches:
        return []

    # Calculate timing
    base_start_tick = chord_event.start_tick
    duration_ticks = int(chord_event.duration_tick)
    intensity = float(chord_event.intensity)
    duration_gate = float(chord_event.duration_gate)

    # Convert beats to ticks
    ticks_per_beat = PPQ
    strum_beats = float(chord_event.strum_beats)
    humanize_beats = float(chord_event.humanize_beats)
    strum_ticks = int(strum_beats * ticks_per_beat)
    humanize_ticks = int(humanize_beats * ticks_per_beat)

    # Generate deterministic seeds
    strum_seed = deterministic_seed(seed, str(chord_event.id), "strum")
    humanize_seed = deterministic_seed(seed, str(chord_event.id), "humanize")
    velocity_seed = deterministic_seed(seed, str(chord_event.id), "velocity")
    pattern_seed = deterministic_seed(seed, str(chord_event.id), "pattern")

    rng_strum = random.Random(strum_seed)
    rng_humanize = random.Random(humanize_seed)
    rng_velocity = random.Random(velocity_seed)
    rng_pattern = random.Random(pattern_seed)

    pattern_type = chord_event.pattern_type or "block"
    notes = []

    if pattern_type == "block":
        # All notes start simultaneously
        note_starts = [(i, base_start_tick, 1.0) for i in range(len(voicing_pitches))]
    elif pattern_type == "strum":
        # Distribute notes across strum duration
        strum_spread = float(chord_event.strum_spread or 1.0)
        effective_strum_ticks = int(strum_ticks * strum_spread)
        direction = chord_event.strum_direction or "down"

        # Determine note order based on direction
        note_indices = list(range(len(voicing_pitches)))
        if direction == "up":
            note_indices.reverse()
        elif direction == "alternate":
            # Alternate: low, high, low+1, high-1, ...
            sorted_pitches = sorted(enumerate(voicing_pitches), key=lambda x: x[1])
            low_indices = [i for i, _ in sorted_pitches[: len(sorted_pitches) // 2]]
            high_indices = [i for i, _ in sorted_pitches[len(sorted_pitches) // 2 :]]
            note_indices = []
            for i in range(max(len(low_indices), len(high_indices))):
                if i < len(low_indices):
                    note_indices.append(low_indices[i])
                if i < len(high_indices):
                    note_indices.append(high_indices[-(i + 1)])
        elif direction == "random":
            rng_strum.shuffle(note_indices)

        # Distribute start times
        note_starts = []
        for i, note_idx in enumerate(note_indices):
            if len(note_indices) > 1 and effective_strum_ticks > 0:
                position = i / (len(note_indices) - 1) if len(note_indices) > 1 else 0
                note_starts.append((note_idx, base_start_tick + int(position * effective_strum_ticks)))
            else:
                note_starts.append((note_idx, base_start_tick))
    elif pattern_type == "comp":
        # Comping pattern: repeated hits based on comp_pattern
        comp_pattern = chord_event.comp_pattern or {}
        grid = comp_pattern.get("grid", "1/8")
        steps = comp_pattern.get("steps", [1, 0, 1, 0, 1, 0, 1, 0])
        accents = comp_pattern.get("accent", [1.0] * len(steps))
        swing = comp_pattern.get("swing", 0.0)
        retrigger = chord_event.retrigger or False

        # Parse grid (e.g., "1/8" = 8th notes)
        grid_denominator = int(grid.split("/")[1]) if "/" in grid else 4
        ticks_per_step = int(PPQ * 4 / grid_denominator)

        # Calculate swing offset
        swing_offset = int(swing * ticks_per_step / 2) if swing > 0 else 0

        note_starts = []
        for step_idx, step_on in enumerate(steps):
            if step_on:
                step_tick = base_start_tick + (step_idx * ticks_per_step)
                # Apply swing to off-beat steps
                if step_idx % 2 == 1:
                    step_tick += swing_offset

                # Clamp to chord duration
                if step_tick < base_start_tick + duration_ticks:
                    accent = accents[step_idx] if step_idx < len(accents) else 1.0
                    # All notes hit at this step
                    for note_idx in range(len(voicing_pitches)):
                        note_starts.append((note_idx, step_tick, accent))

        if not retrigger:
            # Only first hit per note
            seen_notes = set()
            filtered_starts = []
            for item in note_starts:
                note_idx = item[0]
                if note_idx not in seen_notes:
                    seen_notes.add(note_idx)
                    filtered_starts.append(item)
            note_starts = filtered_starts
    else:  # arp or unknown
        # Default to block
        note_starts = [(i, base_start_tick, 1.0) for i in range(len(voicing_pitches))]

    # Generate note events
    for item in note_starts:
        if isinstance(item, tuple) and len(item) == 3:
            note_idx, note_start, accent = item
        elif isinstance(item, tuple) and len(item) == 2:
            note_idx, note_start = item
            accent = 1.0
        else:
            # Fallback for old format
            note_idx = item if isinstance(item, int) else 0
            note_start = base_start_tick
            accent = 1.0

        pitch = voicing_pitches[note_idx]

        # Apply humanization (clamp to chord bounds)
        if humanize_beats > 0:
            humanize_offset = rng_humanize.randint(-humanize_ticks, humanize_ticks)
            note_start += humanize_offset
            # Clamp to chord bounds
            note_start = max(base_start_tick, min(base_start_tick + duration_ticks, note_start))

        # Calculate velocity with intensity, curve, and accent
        base_velocity = int(100 * intensity * accent)
        velocity = apply_velocity_curve(base_velocity, note_idx, len(voicing_pitches), chord_event.velocity_curve or "flat")

        # Apply velocity jitter
        if chord_event.velocity_jitter > 0:
            jitter = rng_velocity.randint(-chord_event.velocity_jitter, chord_event.velocity_jitter)
            velocity += jitter

        velocity = max(1, min(127, velocity))

        # Apply gate (duration as fraction of chord duration)
        gated_duration = int(duration_ticks * duration_gate)

        notes.append({
            "pitch": pitch,
            "start_tick": note_start,
            "duration_tick": gated_duration,
            "velocity": velocity,
        })

    return notes

