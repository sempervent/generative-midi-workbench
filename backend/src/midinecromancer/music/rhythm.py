"""Rhythm generation: Euclidean rhythms and drum patterns."""

import random
from typing import Literal

# MIDI timing
PPQ = 480  # Ticks per quarter note


def generate_euclidean_rhythm(
    steps: int,
    beats: int,
    rotation: int = 0,
    accent_pattern: list[int] | None = None,
) -> list[tuple[int, bool, int]]:
    """Generate Euclidean rhythm pattern.

    Args:
        steps: Total steps in pattern
        beats: Number of beats (onsets)
        rotation: Rotation offset
        accent_pattern: Optional list of step indices to accent

    Returns:
        List of (step_index, is_onset, velocity) tuples
    """
    if beats == 0:
        return [(i, False, 64) for i in range(steps)]

    # Bjorklund algorithm
    pattern = [False] * steps
    bucket = beats

    for i in range(steps):
        bucket += beats
        if bucket >= steps:
            pattern[i] = True
            bucket -= steps

    # Rotate
    pattern = pattern[rotation:] + pattern[:rotation]

    # Apply accents
    result = []
    for i, is_onset in enumerate(pattern):
        velocity = 100 if is_onset else 0
        if is_onset and accent_pattern and i in accent_pattern:
            velocity = 127
        result.append((i, is_onset, velocity))

    return result


def generate_drum_pattern(
    bars: int,
    time_signature_num: int,
    time_signature_den: int,
    seed: int,
    pattern_type: Literal["kick_snare", "hats", "full"] = "full",
    swing: float = 0.0,
    variation: float = 0.1,
) -> list[dict]:
    """Generate drum pattern (kick, snare, hi-hats).

    Args:
        bars: Number of bars
        time_signature_num: Time signature numerator
        time_signature_den: Time signature denominator
        seed: Random seed
        pattern_type: Pattern type
        swing: Swing amount (0.0-1.0)
        variation: Variation probability (0.0-1.0)

    Returns:
        List of note events: {pitch, velocity, start_tick, duration_tick, role}
    """
    rng = random.Random(seed)

    # Calculate ticks per bar
    quarter_notes_per_bar = (time_signature_num * 4) / time_signature_den
    ticks_per_bar = int(quarter_notes_per_bar * PPQ)
    total_ticks = bars * ticks_per_bar

    events = []

    # Kick (36) - typically on 1 and 3 (or 1 and 2.5 in 4/4)
    kick_pattern = [0, ticks_per_bar // 2]  # Beat 1 and 3
    for bar in range(bars):
        for kick_tick in kick_pattern:
            if rng.random() > variation:  # Variation: sometimes skip
                events.append(
                    {
                        "pitch": 36,
                        "velocity": 100 + int(rng.random() * 20),
                        "start_tick": bar * ticks_per_bar + kick_tick,
                        "duration_tick": PPQ // 4,
                        "role": "kick",
                    }
                )

    # Snare (38) - typically on 2 and 4
    snare_pattern = [ticks_per_bar // 4, 3 * ticks_per_bar // 4]
    for bar in range(bars):
        for snare_tick in snare_pattern:
            if rng.random() > variation:
                events.append(
                    {
                        "pitch": 38,
                        "velocity": 90 + int(rng.random() * 30),
                        "start_tick": bar * ticks_per_bar + snare_tick,
                        "duration_tick": PPQ // 4,
                        "role": "snare",
                    }
                )

    # Hi-hats (42) - Euclidean pattern
    if pattern_type in ["hats", "full"]:
        steps_per_bar = 16  # 16th notes
        beats_per_bar = 8  # 8 beats
        hat_pattern = generate_euclidean_rhythm(steps_per_bar, beats_per_bar, rotation=0)
        step_ticks = ticks_per_bar // steps_per_bar

        for bar in range(bars):
            for step_idx, (_, is_onset, velocity) in enumerate(hat_pattern):
                if is_onset and rng.random() > variation * 0.5:  # Less variation for hats
                    tick = bar * ticks_per_bar + step_idx * step_ticks

                    # Apply swing to off-beats
                    if swing > 0 and step_idx % 2 == 1:
                        tick += int(swing * step_ticks * 0.5)

                    events.append(
                        {
                            "pitch": 42,
                            "velocity": velocity,
                            "start_tick": tick,
                            "duration_tick": step_ticks // 2,
                            "role": "hats",
                        }
                    )

    return events
