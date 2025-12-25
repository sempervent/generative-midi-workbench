"""Music theory utilities: pitch classes, keys, modes, scales."""

from enum import IntEnum
from typing import Literal

# MIDI timing constants
PPQ = 480  # Ticks per quarter note


class PitchClass(IntEnum):
    """MIDI pitch class (0-11)."""

    C = 0
    C_SHARP = 1
    D = 2
    D_SHARP = 3
    E = 4
    F = 5
    F_SHARP = 6
    G = 7
    G_SHARP = 8
    A = 9
    A_SHARP = 10
    B = 11


# Circle of fifths: each key's dominant (V) and subdominant (IV)
CIRCLE_OF_FIFTHS: dict[str, dict[str, str]] = {
    "C": {"dominant": "G", "subdominant": "F"},
    "G": {"dominant": "D", "subdominant": "C"},
    "D": {"dominant": "A", "subdominant": "G"},
    "A": {"dominant": "E", "subdominant": "D"},
    "E": {"dominant": "B", "subdominant": "A"},
    "B": {"dominant": "F#", "subdominant": "E"},
    "F#": {"dominant": "C#", "subdominant": "B"},
    "C#": {"dominant": "G#", "subdominant": "F#"},
    "G#": {"dominant": "D#", "subdominant": "C#"},
    "D#": {"dominant": "A#", "subdominant": "G#"},
    "A#": {"dominant": "F", "subdominant": "D#"},
    "F": {"dominant": "C", "subdominant": "Bb"},
    "Bb": {"dominant": "F", "subdominant": "Eb"},
    "Eb": {"dominant": "Bb", "subdominant": "Ab"},
    "Ab": {"dominant": "Eb", "subdominant": "Db"},
    "Db": {"dominant": "Ab", "subdominant": "Gb"},
    "Gb": {"dominant": "Db", "subdominant": "Cb"},
}

# Mode intervals (semitones from tonic)
Mode = Literal["ionian", "dorian", "phrygian", "lydian", "mixolydian", "aeolian", "locrian"]

MODE_INTERVALS: dict[Mode, list[int]] = {
    "ionian": [0, 2, 4, 5, 7, 9, 11],  # Major
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "lydian": [0, 2, 4, 6, 7, 9, 11],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "aeolian": [0, 2, 3, 5, 7, 8, 10],  # Natural minor
    "locrian": [0, 1, 3, 5, 6, 8, 10],
}

# Roman numeral to scale degree mapping
ROMAN_TO_DEGREE: dict[str, int] = {
    "I": 1,
    "ii": 2,
    "II": 2,
    "iii": 3,
    "III": 3,
    "IV": 4,
    "V": 5,
    "vi": 6,
    "VI": 6,
    "vii": 7,
    "VII": 7,
}


def parse_tonic(tonic: str) -> int:
    """Parse tonic string (e.g., 'C', 'F#', 'Bb') to pitch class."""
    tonic_upper = tonic.upper()
    if tonic_upper == "CB":
        return PitchClass.B
    if tonic_upper == "FB":
        return PitchClass.E

    base = tonic_upper[0]
    accidental = tonic_upper[1:] if len(tonic_upper) > 1 else ""

    pitch_map = {
        "C": PitchClass.C,
        "D": PitchClass.D,
        "E": PitchClass.E,
        "F": PitchClass.F,
        "G": PitchClass.G,
        "A": PitchClass.A,
        "B": PitchClass.B,
    }

    base_pc = pitch_map[base]

    if accidental == "#" or accidental == "SHARP":
        return (base_pc + 1) % 12
    if accidental == "B" or accidental == "FLAT":
        return (base_pc - 1) % 12

    return base_pc


def get_scale_degrees(tonic: str, mode: Mode, octave: int = 4) -> list[int]:
    """Get MIDI note numbers for scale degrees in a key/mode.

    Args:
        tonic: Key tonic (e.g., "C", "F#")
        mode: Mode name
        octave: Starting octave (default 4, middle C = C4 = 60)

    Returns:
        List of MIDI note numbers for scale degrees 1-7
    """
    tonic_pc = parse_tonic(tonic)
    intervals = MODE_INTERVALS[mode]
    base_midi = 12 * octave + tonic_pc

    return [base_midi + interval for interval in intervals]


def pitch_class_to_midi(pitch_class: int, octave: int = 4) -> int:
    """Convert pitch class to MIDI note number.

    Args:
        pitch_class: Pitch class (0-11)
        octave: Octave number (default 4)

    Returns:
        MIDI note number
    """
    return 12 * octave + (pitch_class % 12)


def roman_to_degree(roman: str) -> int:
    """Convert roman numeral to scale degree (1-7).

    Args:
        roman: Roman numeral (e.g., "I", "vi", "V7")

    Returns:
        Scale degree (1-7)
    """
    # Strip quality suffixes (7, m, M, etc.)
    base = roman.rstrip("7mMdimaugsus")
    return ROMAN_TO_DEGREE.get(base, 1)


def get_chord_notes(
    tonic: str, mode: Mode, degree: int, quality: str = "triad", octave: int = 4
) -> list[int]:
    """Get MIDI notes for a chord by scale degree.

    Args:
        tonic: Key tonic
        mode: Mode
        degree: Scale degree (1-7)
        quality: Chord quality ("triad", "7th", etc.)
        octave: Starting octave

    Returns:
        List of MIDI note numbers
    """
    scale = get_scale_degrees(tonic, mode, octave)
    degree_idx = (degree - 1) % 7

    if quality == "triad":
        # 1, 3, 5
        return [
            scale[degree_idx],
            scale[(degree_idx + 2) % 7],
            scale[(degree_idx + 4) % 7],
        ]
    if quality == "7th":
        # 1, 3, 5, 7
        return [
            scale[degree_idx],
            scale[(degree_idx + 2) % 7],
            scale[(degree_idx + 4) % 7],
            scale[(degree_idx + 6) % 7],
        ]

    return [scale[degree_idx]]


def get_relative_key(tonic: str, mode: Mode) -> tuple[str, Mode]:
    """Get relative major/minor key.

    Args:
        tonic: Current tonic
        mode: Current mode

    Returns:
        Tuple of (tonic, mode) for relative key
    """
    if mode == "ionian":
        # Relative minor is 6th degree
        scale = get_scale_degrees(tonic, mode)
        relative_tonic_pc = (scale[5] - 60) % 12
        tonic_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        return (tonic_names[relative_tonic_pc], "aeolian")
    if mode == "aeolian":
        # Relative major is 3rd degree
        scale = get_scale_degrees(tonic, mode)
        relative_tonic_pc = (scale[2] - 60) % 12
        tonic_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        return (tonic_names[relative_tonic_pc], "ionian")

    return (tonic, mode)
