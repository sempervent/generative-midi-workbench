"""Bassline generation: root-following with rhythmic syncopation."""

import random
from typing import Literal

from midinecromancer.music.theory import Mode, get_chord_notes, roman_to_degree

PPQ = 480  # Ticks per quarter note


def generate_bassline(
    tonic: str,
    mode: Mode,
    bars: int,
    time_signature_num: int,
    time_signature_den: int,
    chord_progression: list[dict],
    seed: int,
    octave: int = 3,
    syncopation: float = 0.3,
) -> list[dict]:
    """Generate bassline following chord roots.

    Args:
        tonic: Key tonic
        mode: Mode
        bars: Number of bars
        time_signature_num: Time signature numerator
        time_signature_den: Time signature denominator
        chord_progression: List of chord events with roman_numeral, start_bar, length_bars
        seed: Random seed
        octave: Bass octave (default 3)
        syncopation: Syncopation probability (0.0-1.0)

    Returns:
        List of note events: {pitch, velocity, start_tick, duration_tick}
    """
    rng = random.Random(seed)

    # Calculate timing
    quarter_notes_per_bar = (time_signature_num * 4) / time_signature_den
    ticks_per_bar = int(quarter_notes_per_bar * PPQ)
    total_ticks = bars * ticks_per_bar

    events = []

    # Create chord map by bar
    chord_by_bar: dict[int, dict] = {}
    for chord in chord_progression:
        for bar_offset in range(chord["length_bars"]):
            bar = chord["start_bar"] + bar_offset
            chord_by_bar[bar] = chord

    # Generate bass notes
    for bar in range(bars):
        chord = chord_by_bar.get(bar, chord_progression[0] if chord_progression else None)
        if not chord:
            continue

        # Get root note
        degree = roman_to_degree(chord["roman_numeral"])
        chord_notes = get_chord_notes(tonic, mode, degree, "triad", octave)
        root = chord_notes[0]

        # Pattern: root on beat 1, sometimes on beat 3, occasional approach notes
        beat_1_tick = bar * ticks_per_bar
        beat_3_tick = bar * ticks_per_bar + ticks_per_bar // 2

        # Beat 1: always root
        events.append(
            {
                "pitch": root,
                "velocity": 100,
                "start_tick": beat_1_tick,
                "duration_tick": ticks_per_bar // 2,
            }
        )

        # Beat 3: root or approach note
        if rng.random() > 0.2:  # 80% chance
            if rng.random() < syncopation:
                # Syncopated: start slightly before beat 3
                tick = beat_3_tick - PPQ // 8
            else:
                tick = beat_3_tick

            # Sometimes use approach note (scale step below root)
            if rng.random() < 0.3:
                approach_pitch = root - 2  # Whole step below
            else:
                approach_pitch = root

            events.append(
                {
                    "pitch": approach_pitch,
                    "velocity": 90,
                    "start_tick": tick,
                    "duration_tick": ticks_per_bar // 4,
                }
            )

        # Occasional 8th note fills
        if rng.random() < 0.2:
            fill_tick = bar * ticks_per_bar + 3 * ticks_per_bar // 4
            events.append(
                {
                    "pitch": root,
                    "velocity": 85,
                    "start_tick": fill_tick,
                    "duration_tick": PPQ // 4,
                }
            )

    return events
