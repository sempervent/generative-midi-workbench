"""Chord progression generation with candidate scoring and locking support."""

import hashlib
from typing import TYPE_CHECKING

from midinecromancer.music.progression import generate_chord_progression
from midinecromancer.music.theory import Mode

if TYPE_CHECKING:
    from uuid import UUID


class ChordProgressionCandidate:
    """A candidate chord progression with metadata."""

    def __init__(
        self,
        progression: list[dict],
        score: float,
        title: str | None = None,
        explanation: str | None = None,
    ):
        self.progression = progression
        self.score = score
        self.title = title
        self.explanation = explanation


def deterministic_seed_for_candidate(
    run_id: "UUID", candidate_index: int, base_seed: int
) -> int:
    """Generate deterministic seed for a candidate."""
    hash_input = f"{run_id}:{candidate_index}:{base_seed}".encode()
    hash_bytes = hashlib.blake2b(hash_input, digest_size=8).digest()
    return int.from_bytes(hash_bytes, byteorder="big", signed=True)


def score_progression(
    progression: list[dict],
    locks: dict | None = None,
    harmonic_rhythm_target: str = "1chord/bar",
    tension: float = 0.5,
    complexity: float = 0.5,
) -> float:
    """Score a chord progression.

    Args:
        progression: List of chord dicts with roman_numeral, start_bar, length_bars
        locks: Dict mapping bar indices or chord indices to required chords
        harmonic_rhythm_target: Target rhythm ("1chord/bar", "2chords/bar", etc.)
        tension: Tension level (0-1)
        complexity: Complexity level (0-1)

    Returns:
        Score (higher is better)
    """
    if not progression:
        return 0.0

    score = 1.0

    # Check locks
    if locks:
        for lock_key, lock_value in locks.items():
            # Lock key could be bar index or chord index
            if isinstance(lock_key, int):
                if lock_key < len(progression):
                    if progression[lock_key].get("roman_numeral") != lock_value:
                        score -= 10.0  # Heavy penalty for violating locks

    # Voice-leading smoothness (prefer small pitch-class movements)
    for i in range(1, len(progression)):
        prev_roman = progression[i - 1].get("roman_numeral", "")
        curr_roman = progression[i].get("roman_numeral", "")
        # Simple heuristic: same root or stepwise motion is smoother
        if prev_roman == curr_roman:
            score -= 0.1  # Slight penalty for immediate repetition
        # Could add more sophisticated voice-leading analysis here

    # Cadence quality (check if progression ends with strong cadence)
    if len(progression) >= 2:
        last_two = [p.get("roman_numeral", "") for p in progression[-2:]]
        # V->I or ii->V->I are strong cadences
        if "V" in last_two[-1] and "I" in last_two[-1]:
            score += 0.5
        elif len(progression) >= 3:
            last_three = [p.get("roman_numeral", "") for p in progression[-3:]]
            if "ii" in last_three[0] and "V" in last_three[1] and "I" in last_three[2]:
                score += 0.7

    # Harmonic rhythm alignment
    avg_chords_per_bar = len(progression) / max(1, progression[-1].get("start_bar", 1) + progression[-1].get("length_bars", 1))
    if harmonic_rhythm_target == "1chord/bar":
        target = 1.0
    elif harmonic_rhythm_target == "2chords/bar":
        target = 2.0
    else:
        target = 0.5

    rhythm_score = 1.0 - abs(avg_chords_per_bar - target) * 0.2
    score += rhythm_score

    # Tension and complexity (simplified)
    # More complex progressions (more chord changes) get higher complexity score
    unique_chords = len(set(p.get("roman_numeral", "") for p in progression))
    complexity_score = min(1.0, unique_chords / max(1, len(progression))) * complexity
    score += complexity_score

    return max(0.0, score)


def generate_progression_candidates(
    context: dict,
    params: dict,
    locks: dict | None = None,
    seed: int = 0,
    run_id: "UUID | None" = None,
    num_candidates: int = 5,
) -> list[ChordProgressionCandidate]:
    """Generate multiple chord progression candidates with scoring.

    Args:
        context: Dict with tonic, mode, bars, time_signature_num, time_signature_den
        params: Generation parameters (complexity, tension, harmonic_rhythm, etc.)
        locks: Dict mapping positions to locked chords
        seed: Base seed
        run_id: Run ID for deterministic candidate generation
        num_candidates: Number of candidates to generate

    Returns:
        List of ChordProgressionCandidate, sorted by score (highest first)
    """
    tonic = context["tonic"]
    mode = Mode(context["mode"]) if isinstance(context["mode"], str) else context["mode"]
    bars = context["bars"]
    time_signature_num = context.get("time_signature_num", 4)
    time_signature_den = context.get("time_signature_den", 4)

    harmonic_rhythm = params.get("harmonic_rhythm", "1chord/bar")
    complexity = params.get("complexity", 0.5)
    tension = params.get("tension", 0.5)
    progression_style = params.get("progression_style", "pop")
    cadence_ending = params.get("cadence_ending", True)

    candidates = []

    for candidate_idx in range(num_candidates):
        # Generate deterministic seed for this candidate
        if run_id:
            candidate_seed = deterministic_seed_for_candidate(run_id, candidate_idx, seed)
        else:
            candidate_seed = seed + candidate_idx * 1000

        # Generate progression
        progression = generate_chord_progression(
            tonic=tonic,
            mode=mode,
            bars=bars,
            seed=candidate_seed,
            progression_style=progression_style,
            harmonic_rhythm=harmonic_rhythm,
            cadence_ending=cadence_ending,
        )

        # Apply pattern defaults based on style
        style = params.get("style", "pads")
        for chord in progression:
            if style == "guitar":
                chord["pattern_type"] = "strum"
                chord["strum_beats"] = 0.125  # 1/8 beat strum
                chord["strum_direction"] = "down"
            elif style == "piano":
                chord["pattern_type"] = "comp"
                chord["comp_pattern"] = {
                    "grid": "1/8",
                    "steps": [1, 0, 1, 0, 1, 0, 1, 0],
                    "accent": [1.0, 0.8, 1.0, 0.8, 1.0, 0.8, 1.0, 0.8],
                    "swing": 0.0,
                }
                chord["retrigger"] = True
            else:  # pads
                chord["pattern_type"] = "block"
                chord["duration_gate"] = 0.95

            # Set defaults if not present
            chord.setdefault("intensity", 0.85)
            chord.setdefault("voicing", "root")
            chord.setdefault("inversion", 0)
            chord.setdefault("duration_gate", 0.85)
            chord.setdefault("velocity_curve", "flat")

        # Score progression
        score = score_progression(
            progression,
            locks=locks,
            harmonic_rhythm_target=harmonic_rhythm,
            tension=tension,
            complexity=complexity,
        )

        # Generate title and explanation
        title = f"Candidate {candidate_idx + 1}"
        if candidate_idx == 0:
            title = "Primary"
        elif score > 1.5:
            title = "Strong"
        elif score < 0.5:
            title = "Experimental"

        explanation = f"Score: {score:.2f}"
        if locks:
            explanation += f", {len(locks)} locked positions"

        candidates.append(
            ChordProgressionCandidate(
                progression=progression,
                score=score,
                title=title,
                explanation=explanation,
            )
        )

    # Sort by score (highest first)
    candidates.sort(key=lambda c: c.score, reverse=True)

    return candidates

