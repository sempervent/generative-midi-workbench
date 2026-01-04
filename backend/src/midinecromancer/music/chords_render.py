"""Chord rendering engine: converts chord progressions to note events."""

import random

from midinecromancer.music.theory import (
    PPQ,
    get_chord_notes,
    roman_to_degree,
)


class NoteEvent:
    """A note event for chord rendering."""

    def __init__(
        self,
        pitch: int,
        start_tick: int,
        duration_tick: int,
        velocity: int = 100,
    ):
        self.pitch = pitch
        self.start_tick = start_tick
        self.duration_tick = duration_tick
        self.velocity = velocity


def parse_subdivision(subdivision: str) -> int:
    """Parse subdivision string (e.g., '1/4', '1/8', '1/16') to ticks per subdivision.

    Args:
        subdivision: Subdivision string

    Returns:
        Ticks per subdivision
    """
    parts = subdivision.split("/")
    if len(parts) != 2:
        return PPQ  # Default to quarter notes
    try:
        num, den = int(parts[0]), int(parts[1])
        # PPQ ticks per quarter note, so 1/4 = PPQ, 1/8 = PPQ/2, 1/16 = PPQ/4
        return int(PPQ * num / den)
    except ValueError:
        return PPQ


def voice_chord(
    chord_tones: list[int],
    voicing_low: int,
    voicing_high: int,
    previous_voicing: list[int] | None = None,
    inversion_policy: str = "smooth",
) -> list[int]:
    """Voice a chord within a range with smooth voice leading.

    Args:
        chord_tones: List of MIDI pitches (can be in any octave)
        voicing_low: Lowest allowed MIDI pitch
        voicing_high: Highest allowed MIDI pitch
        previous_voicing: Previous chord voicing for smooth voice leading
        inversion_policy: "root", "smooth", or "drop2"

    Returns:
        List of MIDI pitches within range
    """
    if not chord_tones:
        return []

    # Normalize chord tones to single octave (0-11)
    pitch_classes = sorted({p % 12 for p in chord_tones})

    # Find octave range that fits
    min_octave = (voicing_low - max(pitch_classes)) // 12
    max_octave = (voicing_high - min(pitch_classes)) // 12

    if min_octave > max_octave:
        # Range too small, use middle
        octave = (voicing_low + voicing_high) // 24
        return [
            p + octave * 12 for p in pitch_classes if voicing_low <= p + octave * 12 <= voicing_high
        ]

    # Try different octaves
    best_voicing = None
    best_score = float("inf")

    for octave in range(min_octave, max_octave + 1):
        candidate = sorted([p + octave * 12 for p in pitch_classes])
        # Filter to range
        candidate = [p for p in candidate if voicing_low <= p <= voicing_high]

        if not candidate:
            continue

        # Score based on voice leading (if previous exists)
        if previous_voicing:
            # Minimize total movement
            score = sum(min(abs(p - prev) for prev in previous_voicing) for p in candidate)
        else:
            # Prefer middle of range
            mid = (voicing_low + voicing_high) // 2
            score = sum(abs(p - mid) for p in candidate)

        if score < best_score:
            best_score = score
            best_voicing = candidate

    if best_voicing:
        return best_voicing

    # Fallback: use middle octave
    octave = (voicing_low + voicing_high) // 24
    return [
        p + octave * 12 for p in pitch_classes if voicing_low <= p + octave * 12 <= voicing_high
    ]


def render_chord_progression_to_notes(
    chords: list[dict],
    settings: dict,
    seed: int,
    timing_ctx: dict,
) -> list[NoteEvent]:
    """Render a chord progression to note events.

    Args:
        chords: List of chord dicts with keys:
            - start_tick: Start position in ticks
            - duration_tick: Duration in ticks
            - roman_numeral: Roman numeral (e.g., "I", "vi")
            - chord_name: Chord name (e.g., "Am", "G7")
        settings: Settings dict with keys:
            - projection_kind: "block", "arpeggio", "broken", "rhythm_pattern"
            - gate_pct: 0-100, percentage of duration to hold
            - strum_ms: Milliseconds between chord tones
            - humanize_ms: Humanization range in ms
            - offset_ticks: Offset in ticks
            - subdivision: Subdivision string (e.g., "1/4", "1/8")
            - pattern: Optional pattern dict for rhythm_pattern
            - voicing_low_midi: Lowest MIDI pitch
            - voicing_high_midi: Highest MIDI pitch
            - inversion_policy: "root", "smooth", "drop2"
        seed: Random seed for determinism
        timing_ctx: Context dict with:
            - tonic: Key tonic
            - mode: Mode
            - bpm: BPM
            - time_signature_num: Time signature numerator
            - time_signature_den: Time signature denominator

    Returns:
        List of NoteEvent objects
    """
    rng = random.Random(seed)
    events = []

    projection_kind = settings.get("projection_kind", "block")
    gate_pct = settings.get("gate_pct", 90)
    strum_ms = settings.get("strum_ms", 0)
    humanize_ms = settings.get("humanize_ms", 0)
    offset_ticks = settings.get("offset_ticks", 0)
    subdivision = settings.get("subdivision", "1/4")
    voicing_low = settings.get("voicing_low_midi", 48)
    voicing_high = settings.get("voicing_high_midi", 72)
    inversion_policy = settings.get("inversion_policy", "smooth")

    tonic = timing_ctx["tonic"]
    mode = timing_ctx["mode"]
    bpm = timing_ctx["bpm"]

    # Convert strum/humanize from ms to ticks
    ticks_per_ms = (PPQ * bpm) / (60 * 1000)
    strum_ticks = int(strum_ms * ticks_per_ms)
    humanize_ticks = int(humanize_ms * ticks_per_ms)

    subdivision_ticks = parse_subdivision(subdivision)

    previous_voicing = None

    for chord in chords:
        start_tick = chord["start_tick"] + offset_ticks
        duration_tick = chord["duration_tick"]
        gate_duration = int(duration_tick * gate_pct / 100)

        # Get chord tones
        roman = chord["roman_numeral"]
        degree = roman_to_degree(roman)
        quality = "7th" if "7" in roman else "triad"
        chord_tones = get_chord_notes(tonic, mode, degree, quality, octave=4)

        # Voice chord
        voiced = voice_chord(
            chord_tones,
            voicing_low,
            voicing_high,
            previous_voicing,
            inversion_policy,
        )
        previous_voicing = voiced

        if not voiced:
            continue

        # Apply projection
        if projection_kind == "block":
            # All notes start together (with strum)
            for i, pitch in enumerate(voiced):
                note_start = start_tick + (i * strum_ticks)
                # Apply humanization
                if humanize_ticks > 0:
                    humanize_offset = rng.randint(-humanize_ticks, humanize_ticks)
                    note_start += humanize_offset

                events.append(
                    NoteEvent(
                        pitch=pitch,
                        start_tick=note_start,
                        duration_tick=gate_duration,
                        velocity=100,
                    )
                )

        elif projection_kind == "arpeggio":
            # Arpeggiate up or down
            direction = settings.get("arpeggio_direction", "up")
            if direction == "down":
                voiced = list(reversed(voiced))

            arp_duration = subdivision_ticks
            for i, pitch in enumerate(voiced):
                note_start = start_tick + (i * arp_duration)
                if humanize_ticks > 0:
                    humanize_offset = rng.randint(-humanize_ticks, humanize_ticks)
                    note_start += humanize_offset

                # Each note lasts until next or gate duration
                note_duration = min(arp_duration, gate_duration - (i * arp_duration))
                if note_duration <= 0:
                    continue

                events.append(
                    NoteEvent(
                        pitch=pitch,
                        start_tick=note_start,
                        duration_tick=note_duration,
                        velocity=100,
                    )
                )

        elif projection_kind == "broken":
            # Broken chord pattern (e.g., low-high-middle)
            pattern = settings.get("broken_pattern", [0, 2, 1])  # Default: root, 5th, 3rd
            pattern_ticks = subdivision_ticks

            for i, pattern_idx in enumerate(pattern):
                if pattern_idx >= len(voiced):
                    continue
                pitch = voiced[pattern_idx]
                note_start = start_tick + (i * pattern_ticks)

                if humanize_ticks > 0:
                    humanize_offset = rng.randint(-humanize_ticks, humanize_ticks)
                    note_start += humanize_offset

                note_duration = min(pattern_ticks, gate_duration - (i * pattern_ticks))
                if note_duration <= 0:
                    continue

                events.append(
                    NoteEvent(
                        pitch=pitch,
                        start_tick=note_start,
                        duration_tick=note_duration,
                        velocity=100,
                    )
                )

        elif projection_kind == "rhythm_pattern":
            # Use explicit pattern
            pattern = settings.get("pattern", {})
            if not pattern:
                # Default: on every subdivision
                pattern = {str(i): True for i in range(int(duration_tick / subdivision_ticks))}

            pattern_idx = 0
            for step_str, is_on in sorted(pattern.items(), key=lambda x: int(x[0])):
                if not is_on:
                    pattern_idx += 1
                    continue

                step = int(step_str)
                note_start = start_tick + (step * subdivision_ticks)

                if humanize_ticks > 0:
                    humanize_offset = rng.randint(-humanize_ticks, humanize_ticks)
                    note_start += humanize_offset

                # Play all chord tones at this step
                for pitch in voiced:
                    note_duration = min(
                        subdivision_ticks, gate_duration - (step * subdivision_ticks)
                    )
                    if note_duration <= 0:
                        continue

                    events.append(
                        NoteEvent(
                            pitch=pitch,
                            start_tick=note_start,
                            duration_tick=note_duration,
                            velocity=100,
                        )
                    )
                pattern_idx += 1

    # Sort by start_tick
    events.sort(key=lambda e: e.start_tick)
    return events
