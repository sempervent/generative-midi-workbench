"""Music theory and generation modules."""

from .theory import (
    CIRCLE_OF_FIFTHS,
    Mode,
    PitchClass,
    get_scale_degrees,
    pitch_class_to_midi,
    roman_to_degree,
)
from .progression import generate_chord_progression
from .rhythm import generate_euclidean_rhythm, generate_drum_pattern
from .melody import generate_melody
from .bass import generate_bassline

__all__ = [
    "CIRCLE_OF_FIFTHS",
    "Mode",
    "PitchClass",
    "get_scale_degrees",
    "pitch_class_to_midi",
    "roman_to_degree",
    "generate_chord_progression",
    "generate_euclidean_rhythm",
    "generate_drum_pattern",
    "generate_melody",
    "generate_bassline",
]
