"""Musical analysis utilities for project state."""

from collections import Counter
from typing import TYPE_CHECKING

from midinecromancer.music.theory import MODE_INTERVALS, parse_tonic

if TYPE_CHECKING:
    from midinecromancer.models.project import Project
    from midinecromancer.models.track import Track


class ProjectAnalysis:
    """Analysis results for a project."""

    def __init__(
        self,
        detected_key: str | None = None,
        detected_mode: str | None = None,
        harmonic_rhythm: float = 1.0,  # Chords per bar
        rhythmic_density: dict[str, float] | None = None,
        chord_functions: list[dict] | None = None,
    ):
        """Initialize analysis results."""
        self.detected_key = detected_key
        self.detected_mode = detected_mode
        self.harmonic_rhythm = harmonic_rhythm
        self.rhythmic_density = rhythmic_density or {}
        self.chord_functions = chord_functions or []


def analyze_project(project: "Project", tracks: list["Track"]) -> ProjectAnalysis:
    """Analyze project state to infer musical context.

    Args:
        project: Project model
        tracks: List of tracks with clips, notes, chord events

    Returns:
        ProjectAnalysis with detected key/mode, harmonic rhythm, etc.
    """
    # Start with project's explicit key/mode
    detected_key = project.key_tonic
    detected_mode = project.mode

    # Analyze chord events to infer key if not set or verify
    chord_events = []
    for track in tracks:
        if track.role == "chords":
            for clip in track.clips:
                chord_events.extend(clip.chord_events)

    if chord_events:
        # Try to infer key from chord progression
        inferred = infer_key_from_chords(chord_events, project.key_tonic, project.mode)
        if inferred:
            detected_key, detected_mode = inferred

    # Calculate harmonic rhythm (chords per bar)
    harmonic_rhythm = calculate_harmonic_rhythm(chord_events, project.bars)

    # Analyze rhythmic density per lane/track
    rhythmic_density = {}
    for track in tracks:
        if track.role == "drums":
            note_count = sum(len(clip.notes) for clip in track.clips)
            total_bars = sum(clip.length_bars for clip in track.clips)
            if total_bars > 0:
                rhythmic_density[track.role] = note_count / total_bars

    # Extract chord functions
    chord_functions = []
    for ce in sorted(chord_events, key=lambda x: x.start_tick):
        chord_functions.append(
            {
                "roman_numeral": ce.roman_numeral,
                "chord_name": ce.chord_name,
                "start_tick": ce.start_tick,
            }
        )

    return ProjectAnalysis(
        detected_key=detected_key,
        detected_mode=detected_mode,
        harmonic_rhythm=harmonic_rhythm,
        rhythmic_density=rhythmic_density,
        chord_functions=chord_functions,
    )


def infer_key_from_chords(
    chord_events: list,
    default_key: str,
    default_mode: str,
) -> tuple[str, str] | None:
    """Infer key and mode from chord progression.

    Args:
        chord_events: List of chord events
        default_key: Default key if inference fails
        default_mode: Default mode if inference fails

    Returns:
        Tuple of (key, mode) or None to use defaults
    """
    if not chord_events:
        return None

    # Simple heuristic: look at first chord
    first_chord = chord_events[0]
    roman = first_chord.roman_numeral.upper()

    # If starts on I, likely major (ionian)
    # If starts on i or vi, likely minor (aeolian)
    if roman == "I":
        return (default_key, "ionian")
    if roman in ("I", "VI"):
        # Could be minor, but need more context
        return (default_key, default_mode)

    # For now, return None to use project defaults
    return None


def calculate_harmonic_rhythm(chord_events: list, total_bars: int) -> float:
    """Calculate average chords per bar.

    Args:
        chord_events: List of chord events
        total_bars: Total bars in project

    Returns:
        Average chords per bar
    """
    if not chord_events or total_bars == 0:
        return 1.0

    # Count unique chord positions (group by start_tick)
    unique_positions = len(set(ce.start_tick for ce in chord_events))
    return unique_positions / total_bars if total_bars > 0 else 1.0


def analyze_note_pitches(notes: list) -> dict:
    """Analyze note pitch distribution.

    Args:
        notes: List of note objects

    Returns:
        Dict with pitch_class_counts, range, etc.
    """
    if not notes:
        return {"pitch_class_counts": {}, "range": (0, 127), "center": 60}

    pitches = [n.pitch for n in notes]
    pitch_classes = [p % 12 for p in pitches]

    return {
        "pitch_class_counts": dict(Counter(pitch_classes)),
        "range": (min(pitches), max(pitches)),
        "center": sum(pitches) // len(pitches) if pitches else 60,
    }
