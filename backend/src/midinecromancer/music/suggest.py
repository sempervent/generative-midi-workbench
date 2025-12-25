"""Suggestion generation engine for theory-aware musical suggestions."""

import hashlib
import math
import random
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from midinecromancer.music.analysis import ProjectAnalysis
from midinecromancer.music.progression import generate_chord_progression
from midinecromancer.music.theory import (
    CIRCLE_OF_FIFTHS,
    MODE_INTERVALS,
    get_chord_notes,
    get_scale_degrees,
    parse_tonic,
    roman_to_degree,
)
from midinecromancer.music.theory import PPQ


@dataclass
class Suggestion:
    """A musical suggestion with preview and commit plan."""

    kind: Literal["harmony", "rhythm", "melody"]
    title: str
    explanation: str
    score: float
    preview_events: list[dict]
    commit_plan: dict

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "kind": self.kind,
            "title": self.title,
            "explanation": self.explanation,
            "score": self.score,
            "payload_json": {
                "preview_events": self.preview_events,
                "commit_plan": self.commit_plan,
            },
        }


def deterministic_suggestion_seed(base_seed: int, project_id: UUID, kind: str, index: int) -> int:
    """Generate deterministic seed for a suggestion.

    Args:
        base_seed: Base project seed
        project_id: Project UUID
        kind: Suggestion kind (harmony/rhythm/melody)
        index: Suggestion index within kind

    Returns:
        Deterministic integer seed
    """
    combined = f"{base_seed}:{project_id}:{kind}:{index}".encode()
    hash_obj = hashlib.blake2b(combined, digest_size=8)
    hash_int = int.from_bytes(hash_obj.digest(), byteorder="big")
    return base_seed ^ hash_int ^ index


def generate_harmony_suggestions(
    analysis: ProjectAnalysis,
    project_id: UUID,
    project_seed: int,
    bars: int,
    time_signature_num: int,
    time_signature_den: int,
    bpm: int,
    chord_events: list,
    complexity: float = 0.5,
    tension: float = 0.5,
) -> list[Suggestion]:
    """Generate harmony suggestions.

    Args:
        analysis: Project analysis
        project_id: Project UUID
        project_seed: Base seed
        bars: Number of bars
        time_signature_num: Time signature numerator
        time_signature_den: Time signature denominator
        bpm: BPM
        chord_events: Existing chord events
        complexity: Complexity parameter (0.0-1.0)
        tension: Tension parameter (0.0-1.0)

    Returns:
        List of harmony suggestions
    """
    suggestions = []
    tonic = analysis.detected_key or "C"
    mode = analysis.detected_mode or "ionian"

    # Calculate timing
    quarter_notes_per_bar = (time_signature_num * 4) / time_signature_den
    ticks_per_bar = int(quarter_notes_per_bar * PPQ)

    # Get current chord progression
    current_chords = [ce.roman_numeral for ce in sorted(chord_events, key=lambda x: x.start_tick)]
    last_chord = current_chords[-1] if current_chords else "I"

    # Suggestion 1: Next chord (circle-of-fifths motion)
    seed1 = deterministic_suggestion_seed(project_seed, project_id, "harmony", 0)
    rng1 = random.Random(seed1)

    next_chord_options = []
    last_degree = roman_to_degree(last_chord)

    # Dominant motion (up a fifth)
    dominant_degree = ((last_degree + 3) % 7) + 1
    next_chord_options.append(("V", dominant_degree, "Dominant motion creates forward momentum"))

    # Subdominant motion (up a fourth)
    subdominant_degree = ((last_degree - 3) % 7) + 1
    next_chord_options.append(("IV", subdominant_degree, "Subdominant motion provides stability"))

    if rng1.random() < 0.7:
        chosen = rng1.choice(next_chord_options)
        roman, degree, reason = chosen
        chord_notes = get_chord_notes(tonic, mode, degree, "triad", 4)

        preview_events = []
        start_bar = bars  # Append after current bars
        start_tick = start_bar * ticks_per_bar

        for note in chord_notes:
            preview_events.append(
                {
                    "pitch": note,
                    "velocity": 100,
                    "start_tick": start_tick,
                    "duration_tick": ticks_per_bar,
                    "channel": 0,
                }
            )

        suggestions.append(
            Suggestion(
                kind="harmony",
                title=f"Next Chord: {roman}",
                explanation=f"{reason}. Adds {roman} chord after current progression.",
                score=0.8,
                preview_events=preview_events,
                commit_plan={
                    "action": "create_chord_event",
                    "track_role": "chords",
                    "start_bar": start_bar,
                    "length_bars": 1,
                    "roman_numeral": roman,
                    "chord_name": _roman_to_chord_name(roman, tonic, mode),
                },
            )
        )

    # Suggestion 2: Cadence ending
    seed2 = deterministic_suggestion_seed(project_seed, project_id, "harmony", 1)
    rng2 = random.Random(seed2)

    if rng2.random() < 0.6:
        cadence = ["V", "I"] if mode == "ionian" else ["V", "i"]
        cadence_notes = []
        for i, roman in enumerate(cadence):
            degree = roman_to_degree(roman)
            chord_notes = get_chord_notes(tonic, mode, degree, "triad", 4)
            start_tick = (bars - 2 + i) * ticks_per_bar
            for note in chord_notes:
                cadence_notes.append(
                    {
                        "pitch": note,
                        "velocity": 100,
                        "start_tick": start_tick,
                        "duration_tick": ticks_per_bar,
                        "channel": 0,
                    }
                )

        suggestions.append(
            Suggestion(
                kind="harmony",
                title="Cadence Ending",
                explanation=f"Classic {cadence[0]} → {cadence[1]} cadence provides strong resolution.",
                score=0.9,
                preview_events=cadence_notes,
                commit_plan={
                    "action": "create_chord_events",
                    "track_role": "chords",
                    "events": [
                        {
                            "start_bar": bars - 2,
                            "length_bars": 1,
                            "roman_numeral": cadence[0],
                            "chord_name": _roman_to_chord_name(cadence[0], tonic, mode),
                        },
                        {
                            "start_bar": bars - 1,
                            "length_bars": 1,
                            "roman_numeral": cadence[1],
                            "chord_name": _roman_to_chord_name(cadence[1], tonic, mode),
                        },
                    ],
                },
            )
        )

    # Suggestion 3: Borrowed chord (modal interchange)
    if mode == "ionian" and tension > 0.4:
        seed3 = deterministic_suggestion_seed(project_seed, project_id, "harmony", 2)
        rng3 = random.Random(seed3)

        if rng3.random() < 0.5:
            # Borrow iv from minor
            borrowed_notes = get_chord_notes(tonic, "aeolian", 4, "triad", 4)
            start_tick = (bars // 2) * ticks_per_bar

            preview_events = []
            for note in borrowed_notes:
                preview_events.append(
                    {
                        "pitch": note,
                        "velocity": 90,
                        "start_tick": start_tick,
                        "duration_tick": ticks_per_bar,
                        "channel": 0,
                    }
                )

            suggestions.append(
                Suggestion(
                    kind="harmony",
                    title="Borrowed Chord: iv",
                    explanation="Modal interchange adds color by borrowing iv from parallel minor.",
                    score=0.7,
                    preview_events=preview_events,
                    commit_plan={
                        "action": "create_chord_event",
                        "track_role": "chords",
                        "start_bar": bars // 2,
                        "length_bars": 1,
                        "roman_numeral": "iv",
                        "chord_name": _roman_to_chord_name("iv", tonic, "aeolian"),
                    },
                )
            )

    return suggestions


def generate_rhythm_suggestions(
    analysis: ProjectAnalysis,
    project_id: UUID,
    project_seed: int,
    bars: int,
    time_signature_num: int,
    time_signature_den: int,
    bpm: int,
    lanes: list | None = None,
    density: float = 0.5,
) -> list[Suggestion]:
    """Generate rhythm suggestions.

    Args:
        analysis: Project analysis
        project_id: Project UUID
        project_seed: Base seed
        bars: Number of bars
        time_signature_num: Time signature numerator
        time_signature_den: Time signature denominator
        bpm: BPM
        lanes: Existing polyrhythm lanes (if any)
        density: Density parameter (0.0-1.0)

    Returns:
        List of rhythm suggestions
    """
    suggestions = []
    quarter_notes_per_bar = (time_signature_num * 4) / time_signature_den
    ticks_per_bar = int(quarter_notes_per_bar * PPQ)

    # Suggestion 1: Add ghost notes
    seed1 = deterministic_suggestion_seed(project_seed, project_id, "rhythm", 0)
    rng1 = random.Random(seed1)

    if rng1.random() < 0.7:
        # Add subtle ghost notes on off-beats
        preview_events = []
        for bar in range(bars):
            for offset in [ticks_per_bar // 4, 3 * ticks_per_bar // 4]:
                tick = bar * ticks_per_bar + offset
                preview_events.append(
                    {
                        "pitch": 42,  # Hi-hat
                        "velocity": 40,  # Quiet
                        "start_tick": tick,
                        "duration_tick": PPQ // 8,
                        "channel": 9,
                    }
                )

        suggestions.append(
            Suggestion(
                kind="rhythm",
                title="Add Ghost Notes",
                explanation="Subtle off-beat accents add groove and texture without overwhelming.",
                score=0.75,
                preview_events=preview_events,
                commit_plan={
                    "action": "append_notes",
                    "track_role": "drums",
                    "clip_start_bar": 0,
                    "notes": preview_events,
                },
            )
        )

    # Suggestion 2: Rotate polyrhythm lane
    if lanes:
        seed2 = deterministic_suggestion_seed(project_seed, project_id, "rhythm", 1)
        rng2 = random.Random(seed2)

        if rng2.random() < 0.6:
            lane = rng2.choice(lanes)
            new_rotation = (lane.get("rotation", 0) + 1) % lane.get("steps", 8)

            suggestions.append(
                Suggestion(
                    kind="rhythm",
                    title=f"Rotate Lane: {lane.get('name', 'Lane')}",
                    explanation=f"Rotating pattern by 1 step shifts the feel while maintaining the same rhythm.",
                    score=0.7,
                    preview_events=[],  # Would need to re-render lane
                    commit_plan={
                        "action": "update_lane_rotation",
                        "lane_id": lane.get("id"),
                        "rotation": new_rotation,
                    },
                )
            )

    return suggestions


def generate_melody_suggestions(
    analysis: ProjectAnalysis,
    project_id: UUID,
    project_seed: int,
    bars: int,
    time_signature_num: int,
    time_signature_den: int,
    bpm: int,
    chord_events: list,
    complexity: float = 0.5,
) -> list[Suggestion]:
    """Generate melody suggestions.

    Args:
        analysis: Project analysis
        project_id: Project UUID
        project_seed: Base seed
        bars: Number of bars
        time_signature_num: Time signature numerator
        time_signature_den: Time signature denominator
        bpm: BPM
        chord_events: Existing chord events
        complexity: Complexity parameter (0.0-1.0)

    Returns:
        List of melody suggestions
    """
    suggestions = []
    tonic = analysis.detected_key or "C"
    mode = analysis.detected_mode or "ionian"

    quarter_notes_per_bar = (time_signature_num * 4) / time_signature_den
    ticks_per_bar = int(quarter_notes_per_bar * PPQ)
    scale = get_scale_degrees(tonic, mode, 5)

    # Suggestion 1: Arpeggiate chord tones
    seed1 = deterministic_suggestion_seed(project_seed, project_id, "melody", 0)
    rng1 = random.Random(seed1)

    if chord_events and rng1.random() < 0.7:
        chord = rng1.choice(chord_events)
        degree = roman_to_degree(chord.roman_numeral)
        chord_notes = get_chord_notes(tonic, mode, degree, "triad", 5)

        preview_events = []
        start_tick = chord.start_tick
        step_ticks = chord.duration_tick // len(chord_notes)

        for i, note in enumerate(chord_notes):
            preview_events.append(
                {
                    "pitch": note,
                    "velocity": 80,
                    "start_tick": start_tick + i * step_ticks,
                    "duration_tick": step_ticks // 2,
                    "channel": 2,
                }
            )

        suggestions.append(
            Suggestion(
                kind="melody",
                title="Arpeggiate Chord Tones",
                explanation=f"Arpeggiating {chord.chord_name} highlights the harmonic structure.",
                score=0.8,
                preview_events=preview_events,
                commit_plan={
                    "action": "create_notes",
                    "track_role": "melody",
                    "clip_start_bar": 0,
                    "notes": preview_events,
                },
            )
        )

    # Suggestion 2: Approach notes
    seed2 = deterministic_suggestion_seed(project_seed, project_id, "melody", 1)
    rng2 = random.Random(seed2)

    if rng2.random() < 0.6:
        target_note = rng2.choice(scale)
        approach_note = target_note - 1  # Half step below

        preview_events = [
            {
                "pitch": approach_note,
                "velocity": 70,
                "start_tick": ticks_per_bar,
                "duration_tick": PPQ // 4,
                "channel": 2,
            },
            {
                "pitch": target_note,
                "velocity": 90,
                "start_tick": ticks_per_bar + PPQ // 4,
                "duration_tick": PPQ // 2,
                "channel": 2,
            },
        ]

        suggestions.append(
            Suggestion(
                kind="melody",
                title="Approach Note",
                explanation="Approach notes create smooth melodic motion and add interest.",
                score=0.75,
                preview_events=preview_events,
                commit_plan={
                    "action": "create_notes",
                    "track_role": "melody",
                    "clip_start_bar": 0,
                    "notes": preview_events,
                },
            )
        )

    return suggestions


def generate_all_suggestions(
    analysis: ProjectAnalysis,
    project_id: UUID,
    project_seed: int,
    bars: int,
    time_signature_num: int,
    time_signature_den: int,
    bpm: int,
    chord_events: list,
    lanes: list | None = None,
    params: dict | None = None,
) -> list[Suggestion]:
    """Generate all suggestion types.

    Args:
        analysis: Project analysis
        project_id: Project UUID
        project_seed: Base seed
        bars: Number of bars
        time_signature_num: Time signature numerator
        time_signature_den: Time signature denominator
        bpm: BPM
        chord_events: Existing chord events
        lanes: Existing polyrhythm lanes
        params: Suggestion parameters (complexity, tension, density)

    Returns:
        Combined list of all suggestions, sorted by score
    """
    params = params or {}
    complexity = params.get("complexity", 0.5)
    tension = params.get("tension", 0.5)
    density = params.get("density", 0.5)

    all_suggestions = []

    # Generate by kind
    all_suggestions.extend(
        generate_harmony_suggestions(
            analysis,
            project_id,
            project_seed,
            bars,
            time_signature_num,
            time_signature_den,
            bpm,
            chord_events,
            complexity,
            tension,
        )
    )
    all_suggestions.extend(
        generate_rhythm_suggestions(
            analysis,
            project_id,
            project_seed,
            bars,
            time_signature_num,
            time_signature_den,
            bpm,
            lanes,
            density,
        )
    )
    all_suggestions.extend(
        generate_melody_suggestions(
            analysis,
            project_id,
            project_seed,
            bars,
            time_signature_num,
            time_signature_den,
            bpm,
            chord_events,
            complexity,
        )
    )

    # Sort by score (descending), then by title
    all_suggestions.sort(key=lambda s: (-s.score, s.title))

    return all_suggestions


def _roman_to_chord_name(roman: str, tonic: str, mode: str) -> str:
    """Convert roman numeral to chord name."""
    degree = roman_to_degree(roman)
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
    intervals = MODE_INTERVALS.get(mode, MODE_INTERVALS["ionian"])
    root_pc = (tonic_pc + intervals[degree - 1]) % 12

    pc_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    root_name = pc_names[root_pc]

    if mode == "ionian":
        qualities = {1: "", 2: "m", 3: "m", 4: "", 5: "", 6: "m", 7: "dim"}
    else:
        qualities = {1: "m", 2: "dim", 3: "", 4: "m", 5: "m", 6: "", 7: ""}

    quality = qualities.get(degree, "")
    if "7" in roman:
        quality += "7"

    return root_name + quality
