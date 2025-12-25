"""Melody generation: scale-constrained motifs with variation."""

import random
from typing import Literal

from midinecromancer.music.theory import Mode, get_scale_degrees

PPQ = 480  # Ticks per quarter note


def generate_melody(
    tonic: str,
    mode: Mode,
    bars: int,
    time_signature_num: int,
    time_signature_den: int,
    seed: int,
    octave: int = 5,
    stepwise_bias: float = 0.7,
    leap_probability: float = 0.2,
) -> list[dict]:
    """Generate melody constrained to scale.

    Args:
        tonic: Key tonic
        mode: Mode
        bars: Number of bars
        time_signature_num: Time signature numerator
        time_signature_den: Time signature denominator
        seed: Random seed
        octave: Starting octave
        stepwise_bias: Probability of stepwise motion (0.0-1.0)
        leap_probability: Probability of leap (0.0-1.0)

    Returns:
        List of note events: {pitch, velocity, start_tick, duration_tick}
    """
    rng = random.Random(seed)

    # Get scale notes (extend to multiple octaves)
    scale_degrees = get_scale_degrees(tonic, mode, octave)
    scale_notes = scale_degrees + [n + 12 for n in scale_degrees] + [n - 12 for n in scale_degrees]
    scale_notes.sort()

    # Calculate timing
    quarter_notes_per_bar = (time_signature_num * 4) / time_signature_den
    ticks_per_bar = int(quarter_notes_per_bar * PPQ)
    total_ticks = bars * ticks_per_bar

    events = []
    current_tick = 0
    current_note_idx = len(scale_notes) // 2  # Start in middle of scale range
    current_pitch = scale_notes[current_note_idx]

    # Rhythmic patterns (in 16th notes)
    patterns = [
        [1, 0, 1, 0, 1, 0, 1, 0],  # Steady 8th notes
        [1, 0, 0, 0, 1, 0, 1, 0],  # Dotted rhythm
        [1, 0, 0, 0, 0, 0, 1, 0],  # Long-short
        [1, 1, 0, 1, 0, 1, 0, 0],  # Syncopated
    ]

    sixteenth_ticks = ticks_per_bar // 16

    while current_tick < total_ticks:
        # Choose rhythmic pattern
        pattern = rng.choice(patterns)
        bar_start_tick = (current_tick // ticks_per_bar) * ticks_per_bar

        for step, is_onset in enumerate(pattern):
            tick = bar_start_tick + step * sixteenth_ticks
            if tick >= total_ticks:
                break

            if is_onset:
                # Determine motion
                if rng.random() < stepwise_bias:
                    # Stepwise motion
                    direction = 1 if rng.random() > 0.5 else -1
                    current_note_idx = max(
                        0, min(len(scale_notes) - 1, current_note_idx + direction)
                    )
                elif rng.random() < leap_probability:
                    # Leap (3rd, 4th, 5th)
                    leap_size = rng.choice([2, 3, 4])  # Scale steps
                    direction = 1 if rng.random() > 0.5 else -1
                    current_note_idx = max(
                        0, min(len(scale_notes) - 1, current_note_idx + direction * leap_size)
                    )
                # else: stay on same note

                current_pitch = scale_notes[current_note_idx]

                # Duration: mostly 8th or quarter notes, sometimes longer
                duration_choices = [sixteenth_ticks * 2, sixteenth_ticks * 4, sixteenth_ticks * 8]
                duration = rng.choice(duration_choices)

                events.append(
                    {
                        "pitch": current_pitch,
                        "velocity": 80 + int(rng.random() * 40),
                        "start_tick": tick,
                        "duration_tick": duration,
                    }
                )

        current_tick += ticks_per_bar

    return events
