"""Chord progression generation using circle-of-fifths and music theory."""

import random
from typing import Literal

from midinecromancer.music.theory import (
    CIRCLE_OF_FIFTHS,
    Mode,
    get_chord_notes,
    get_relative_key,
    roman_to_degree,
)


def generate_chord_progression(
    tonic: str,
    mode: Mode,
    bars: int,
    seed: int,
    start_on: Literal["I", "vi"] = "I",
    prefer_circle_motion: bool = True,
    cadence_ending: bool = True,
) -> list[dict]:
    """Generate a chord progression.

    Args:
        tonic: Key tonic
        mode: Mode
        bars: Number of bars
        seed: Random seed
        start_on: Starting chord ("I" or "vi")
        prefer_circle_motion: Prefer motion by fifths
        cadence_ending: End with cadence (V->I or ii->V->I)

    Returns:
        List of chord events with roman_numeral, chord_name, start_bar, length_bars
    """
    rng = random.Random(seed)

    # Common progressions by mode
    if mode == "ionian":
        # Major key progressions
        common_progressions = [
            ["I", "V", "vi", "IV"],  # Pop progression
            ["I", "vi", "IV", "V"],  # 50s progression
            ["vi", "IV", "I", "V"],  # vi-IV-I-V
            ["I", "IV", "V", "I"],  # Basic
        ]
        cadence_options = [["V", "I"], ["ii", "V", "I"]]
    else:
        # Minor key (aeolian) progressions
        common_progressions = [
            ["i", "iv", "V", "i"],
            ["i", "VI", "III", "VII"],
            ["i", "v", "iv", "i"],
        ]
        cadence_options = [["V", "i"], ["iv", "V", "i"]]

    events = []
    current_bar = 0

    # Start chord
    if start_on == "vi" and mode == "ionian":
        first_chord = "vi"
    else:
        first_chord = "I" if mode == "ionian" else "i"

    # Generate progression
    while current_bar < bars:
        if cadence_ending and current_bar >= bars - 2:
            # Use cadence for last 2 bars
            cadence = rng.choice(cadence_options)
            for chord_roman in cadence:
                if current_bar >= bars:
                    break
                events.append(
                    {
                        "roman_numeral": chord_roman,
                        "chord_name": _roman_to_chord_name(chord_roman, tonic, mode),
                        "start_bar": current_bar,
                        "length_bars": 1,
                    }
                )
                current_bar += 1
            break

        # Choose progression pattern
        if prefer_circle_motion and rng.random() > 0.3:
            # Use circle-of-fifths motion
            if events:
                last_degree = roman_to_degree(events[-1]["roman_numeral"])
                # Move by fifth (dominant or subdominant)
                if rng.random() > 0.5:
                    # Dominant motion (up a fifth = down a fourth)
                    next_degree = ((last_degree + 3) % 7) + 1
                else:
                    # Subdominant motion (up a fourth = down a fifth)
                    next_degree = ((last_degree - 3) % 7) + 1
                chord_roman = _degree_to_roman(next_degree, mode)
            else:
                chord_roman = first_chord
        else:
            # Use common progression
            if events and current_bar < bars - 1:
                prog = rng.choice(common_progressions)
                idx = (current_bar // 2) % len(prog)
                chord_roman = prog[idx]
            else:
                chord_roman = first_chord

        length = 1 if rng.random() > 0.3 else 2  # Mostly 1 bar, sometimes 2
        if current_bar + length > bars:
            length = bars - current_bar

        events.append(
            {
                "roman_numeral": chord_roman,
                "chord_name": _roman_to_chord_name(chord_roman, tonic, mode),
                "start_bar": current_bar,
                "length_bars": length,
            }
        )
        current_bar += length

    return events


def _degree_to_roman(degree: int, mode: Mode) -> str:
    """Convert scale degree to roman numeral based on mode."""
    if mode == "ionian":
        # Major: I, ii, iii, IV, V, vi, vii°
        mapping = {1: "I", 2: "ii", 3: "iii", 4: "IV", 5: "V", 6: "vi", 7: "vii"}
    else:
        # Minor: i, ii°, III, iv, v, VI, VII
        mapping = {1: "i", 2: "ii", 3: "III", 4: "iv", 5: "v", 6: "VI", 7: "VII"}

    return mapping.get(degree, "I")


def _roman_to_chord_name(roman: str, tonic: str, mode: Mode) -> str:
    """Convert roman numeral to chord name (e.g., "Am", "G7")."""
    degree = roman_to_degree(roman)
    scale = [60 + i for i in range(12)]  # Simplified - would use actual scale
    # For now, return a simple mapping
    # In a full implementation, this would compute the actual chord name
    tonic_pc_map = {
        "C": 0,
        "C#": 1,
        "D": 2,
        "D#": 3,
        "E": 4,
        "F": 5,
        "F#": 6,
        "G": 7,
        "G#": 8,
        "A": 9,
        "A#": 10,
        "B": 11,
        "Bb": 10,
        "Eb": 3,
        "Ab": 8,
        "Db": 1,
        "Gb": 6,
    }

    tonic_pc = tonic_pc_map.get(tonic, 0)
    intervals = [0, 2, 4, 5, 7, 9, 11] if mode == "ionian" else [0, 2, 3, 5, 7, 8, 10]
    root_pc = (tonic_pc + intervals[degree - 1]) % 12

    pc_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    root_name = pc_names[root_pc]

    # Determine quality
    if mode == "ionian":
        qualities = {1: "", 2: "m", 3: "m", 4: "", 5: "", 6: "m", 7: "dim"}
    else:
        qualities = {1: "m", 2: "dim", 3: "", 4: "m", 5: "m", 6: "", 7: ""}

    quality = qualities.get(degree, "")
    if "7" in roman:
        quality += "7"

    return root_name + quality
