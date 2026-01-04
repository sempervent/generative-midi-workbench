"""Service for rendering chord events to notes with expressive parameters."""

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


def render_chord_event_to_notes(
    chord_event: "ChordEvent",
    project_context: dict,
    seed: int,
) -> list[dict]:
    """Render a single chord event to note events with expressive parameters.

    Args:
        chord_event: ChordEvent model with expressive fields
        project_context: Dict with tonic, mode, bpm, time_signature_num, time_signature_den
        seed: Base seed for determinism

    Returns:
        List of note dicts: {pitch, start_tick, duration_tick, velocity}
    """
    tonic = project_context["tonic"]
    mode = project_context["mode"]
    bpm = project_context["bpm"]

    # Get chord tones
    roman = chord_event.roman_numeral
    degree = roman_to_degree(roman)
    quality = "7th" if "7" in roman else "triad"
    chord_tones = get_chord_notes(tonic, mode, degree, quality, octave=4)

    # Apply voicing and inversion
    voicing_pitches = apply_voicing(
        chord_tones,
        chord_event.voicing,
        chord_event.inversion,
        voicing_low=48,
        voicing_high=72,
    )

    # Calculate timing
    base_start_tick = chord_event.start_tick
    duration_ticks = int(chord_event.duration_tick)
    intensity = float(chord_event.intensity)

    # Convert strum/humanize from beats to ticks
    # Use beats fields if available, otherwise fall back to ms (for backward compatibility)
    quarter_notes_per_bar = (project_context["time_signature_num"] * 4) / project_context["time_signature_den"]
    ticks_per_beat = PPQ  # 1 beat = 1 quarter note = PPQ ticks
    
    if hasattr(chord_event, "strum_beats") and chord_event.strum_beats is not None:
        strum_beats = float(chord_event.strum_beats)
    else:
        # Fallback: convert ms to beats (approximate, requires BPM)
        strum_beats = (chord_event.strum_ms / 1000.0) * (bpm / 60.0) if chord_event.strum_ms > 0 else 0.0
    
    if hasattr(chord_event, "humanize_beats") and chord_event.humanize_beats is not None:
        humanize_beats = float(chord_event.humanize_beats)
    else:
        # Fallback: convert ms to beats
        humanize_beats = (chord_event.humanize_ms / 1000.0) * (bpm / 60.0) if chord_event.humanize_ms > 0 else 0.0
    
    strum_ticks = int(strum_beats * ticks_per_beat)
    humanize_ticks = int(humanize_beats * ticks_per_beat)

    # Generate deterministic seeds for each parameter
    strum_seed = deterministic_seed(seed, str(chord_event.id), "strum")
    humanize_seed = deterministic_seed(seed, str(chord_event.id), "humanize")
    velocity_seed = deterministic_seed(seed, str(chord_event.id), "velocity")

    notes = []
    rng_strum = random.Random(strum_seed)
    rng_humanize = random.Random(humanize_seed)
    rng_velocity = random.Random(velocity_seed)

    # Determine strum order (deterministic)
    strum_order = list(range(len(voicing_pitches)))
    if strum_beats > 0:
        # Random but deterministic order
        rng_strum.shuffle(strum_order)

    for i, pitch_idx in enumerate(strum_order):
        pitch = voicing_pitches[pitch_idx]

        # Calculate start time with strum
        # Distribute notes evenly across strum duration
        if len(strum_order) > 1 and strum_beats > 0:
            strum_position = i / (len(strum_order) - 1) if len(strum_order) > 1 else 0
            note_start = base_start_tick + int(strum_position * strum_ticks)
        else:
            note_start = base_start_tick

        # Apply humanization (clamp to not exceed chord bounds)
        if humanize_beats > 0:
            humanize_offset = rng_humanize.randint(-humanize_ticks, humanize_ticks)
            note_start += humanize_offset
            # Clamp to chord bounds
            note_start = max(base_start_tick, min(base_start_tick + duration_ticks, note_start))

        # Calculate velocity with intensity and jitter
        base_velocity = int(100 * intensity)
        if chord_event.velocity_jitter > 0:
            velocity_jitter = rng_velocity.randint(
                -chord_event.velocity_jitter, chord_event.velocity_jitter
            )
            base_velocity += velocity_jitter
        velocity = max(1, min(127, base_velocity))

        notes.append({
            "pitch": pitch,
            "start_tick": note_start,
            "duration_tick": duration_ticks,
            "velocity": velocity,
        })

    return notes


def apply_voicing(
    chord_tones: list[int],
    voicing: str,
    inversion: int,
    voicing_low: int = 48,
    voicing_high: int = 72,
) -> list[int]:
    """Apply voicing preset and inversion to chord tones.

    Args:
        chord_tones: List of MIDI pitches (can be in any octave)
        voicing: Voicing preset ("root", "open", "drop2", "smooth")
        inversion: Inversion number (0=root, 1=first, 2=second)
        voicing_low: Lowest allowed MIDI pitch
        voicing_high: Highest allowed MIDI pitch

    Returns:
        List of MIDI pitches within range
    """
    if not chord_tones:
        return []

    # Normalize to pitch classes
    pitch_classes = sorted({p % 12 for p in chord_tones})

    # Apply inversion (rotate pitch classes)
    for _ in range(inversion):
        if pitch_classes:
            pitch_classes = pitch_classes[1:] + [pitch_classes[0] + 12]

    # Find octave range
    min_octave = (voicing_low - max(pitch_classes)) // 12
    max_octave = (voicing_high - min(pitch_classes)) // 12

    if min_octave > max_octave:
        octave = (voicing_low + voicing_high) // 24
        return [p + octave * 12 for p in pitch_classes if voicing_low <= p + octave * 12 <= voicing_high]

    # Apply voicing preset
    if voicing == "open":
        # Spread across wider range
        if len(pitch_classes) >= 3:
            # Root, 5th, 3rd spread
            octave_root = min_octave
            octave_third = min_octave + 1
            octave_fifth = min_octave + 1
            result = []
            if len(pitch_classes) > 0:
                result.append(pitch_classes[0] + octave_root * 12)
            if len(pitch_classes) > 1:
                result.append(pitch_classes[1] + octave_third * 12)
            if len(pitch_classes) > 2:
                result.append(pitch_classes[2] + octave_fifth * 12)
            return [p for p in result if voicing_low <= p <= voicing_high]

    elif voicing == "drop2":
        # Drop 2nd voice down an octave
        if len(pitch_classes) >= 2:
            result = []
            for i, pc in enumerate(pitch_classes):
                if i == 1:  # 2nd voice
                    octave = min_octave
                else:
                    octave = min_octave + 1
                pitch = pc + octave * 12
                if voicing_low <= pitch <= voicing_high:
                    result.append(pitch)
            return result

    # Default: root position in middle octave
    octave = (min_octave + max_octave) // 2
    return [p + octave * 12 for p in pitch_classes if voicing_low <= p + octave * 12 <= voicing_high]

