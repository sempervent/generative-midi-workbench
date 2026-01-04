"""Producer-grade drum generation engine.

Pattern-based, swing-aware, variation-controlled drum generation
for hip-hop, trap, drill, and other producer workflows.
"""

import hashlib
import random
from dataclasses import dataclass
from typing import Literal

from midinecromancer.music.theory import PPQ


@dataclass
class DrumMap:
    """Drum note mappings."""

    kick_note: int = 36
    snare_note: int = 38
    clap_note: int = 39
    closed_hat_note: int = 42
    open_hat_note: int = 46
    rim_note: int = 37
    perc_notes: list[int] | None = None

    def get_note(self, role: str) -> int:
        """Get MIDI note for a drum role."""
        role_map = {
            "kick": self.kick_note,
            "snare": self.snare_note,
            "clap": self.clap_note,
            "closed_hat": self.closed_hat_note,
            "open_hat": self.open_hat_note,
            "rim": self.rim_note,
        }
        return role_map.get(role, 36)


@dataclass
class DrumPattern:
    """Base pattern for a drum role."""

    role: str
    grid: list[bool]  # True = hit, False = rest
    accents: list[int]  # Step indices with accents
    velocity_base: int = 100
    velocity_range: tuple[int, int] = (80, 127)


@dataclass
class GrooveTemplate:
    """Groove timing and velocity curves."""

    name: str
    timing_offsets: list[int]  # Per-step timing offsets in ticks
    velocity_curve: list[float]  # Per-step velocity multipliers (0-1)


def deterministic_seed(base_seed: int, bar_index: int, role: str, param: str) -> int:
    """Generate deterministic seed for variation."""
    hash_input = f"{base_seed}:{bar_index}:{role}:{param}".encode()
    hash_bytes = hashlib.blake2b(hash_input, digest_size=8).digest()
    return int.from_bytes(hash_bytes, byteorder="big")


def apply_swing(
    tick: int,
    step_index: int,
    swing_amt: float,
    step_ticks: int,
    basis: Literal["8th", "16th"] = "16th",
) -> int:
    """Apply swing to off-beat steps.

    Args:
        tick: Base tick position
        step_index: Step index (0-based)
        swing_amt: Swing amount (0.0-1.0, where 0.5 = triplet feel)
        step_ticks: Ticks per step
        basis: Swing basis (8th or 16th)

    Returns:
        Adjusted tick position
    """
    if swing_amt == 0.0:
        return tick

    # Swing applies to off-beats only
    if (basis == "16th" or basis == "8th") and step_index % 2 == 1:
        swing_offset = int(swing_amt * step_ticks * 0.5)
        return tick + swing_offset

    return tick


def generate_kick_pattern(
    bars: int,
    ticks_per_bar: int,
    style: str,
    seed: int,
    density: float = 0.7,
    pause_probability: float = 0.0,
    pause_scope: str = "kick",
) -> list[dict]:
    """Generate kick pattern with style-aware placement.

    Args:
        bars: Number of bars
        ticks_per_bar: Ticks per bar
        style: Style (boom_bap, trap, drill, lofi, minimal)
        seed: Base seed
        density: Hit density (0-1)
        pause_probability: Probability of pausing a bar
        pause_scope: What to pause (kick, all)

    Returns:
        List of kick events: {pitch, velocity, start_tick, duration_tick, role}
    """
    events = []
    step_ticks = ticks_per_bar // 4  # 16th note grid

    # Style-based base patterns
    style_patterns = {
        "boom_bap": [0, 6, 8, 14],  # 1, 2.5, 3, 4.5
        "trap": [0, 8, 12],  # 1, 3, 4
        "drill": [0, 4, 8, 12],  # 1, 2, 3, 4
        "lofi": [0, 8],  # 1, 3
        "minimal": [0],  # Just 1
    }

    base_steps = style_patterns.get(style, [0, 8])  # Default: 1 and 3

    for bar in range(bars):
        bar_seed = deterministic_seed(seed, bar, "kick", "pattern")
        bar_rng = random.Random(bar_seed)

        # Check for pause
        if pause_scope in ("kick", "all") and bar_rng.random() < pause_probability:
            continue

        # Generate hits for this bar
        for step in base_steps:
            # Apply density
            if bar_rng.random() > density:
                continue

            # Variation: sometimes shift ±1 step
            variation_seed = deterministic_seed(seed, bar, "kick", f"variation_{step}")
            var_rng = random.Random(variation_seed)
            if var_rng.random() < 0.2:  # 20% chance to shift
                step += var_rng.choice([-1, 1])
                step = max(0, min(15, step))  # Clamp to 0-15

            tick = bar * ticks_per_bar + step * step_ticks

            # Velocity: stronger on downbeats
            if step % 4 == 0:
                velocity = 110 + int(var_rng.random() * 17)  # 110-127
            else:
                velocity = 90 + int(var_rng.random() * 20)  # 90-110

            events.append(
                {
                    "pitch": 36,  # Will be mapped via DrumMap
                    "velocity": velocity,
                    "start_tick": tick,
                    "duration_tick": step_ticks // 2,
                    "role": "kick",
                }
            )

    return events


def generate_snare_pattern(
    bars: int,
    ticks_per_bar: int,
    style: str,
    seed: int,
    density: float = 0.8,
    pause_probability: float = 0.0,
) -> list[dict]:
    """Generate snare pattern (typically on 2 and 4)."""
    events = []
    step_ticks = ticks_per_bar // 4  # 16th note grid

    # Snares typically on 2 and 4 (steps 4 and 12 in 16th grid)
    base_steps = [4, 12]

    for bar in range(bars):
        bar_seed = deterministic_seed(seed, bar, "snare", "pattern")
        bar_rng = random.Random(bar_seed)

        # Check for pause
        if bar_rng.random() < pause_probability:
            continue

        for step in base_steps:
            if bar_rng.random() > density:
                continue

            tick = bar * ticks_per_bar + step * step_ticks

            # Snare velocity: consistent backbeat
            velocity = 100 + int(bar_rng.random() * 20)  # 100-120

            events.append(
                {
                    "pitch": 38,
                    "velocity": velocity,
                    "start_tick": tick,
                    "duration_tick": step_ticks // 2,
                    "role": "snare",
                }
            )

    return events


def generate_hat_pattern(
    bars: int,
    ticks_per_bar: int,
    style: str,
    seed: int,
    mode: Literal["straight_8", "straight_16", "skip_step", "roll"] = "straight_16",
    density: float = 0.7,
    swing: float = 0.0,
    roll_probability: float = 0.1,
    roll_subdivision: str = "1/32",
) -> list[dict]:
    """Generate hi-hat pattern with various modes."""
    events = []
    step_ticks = ticks_per_bar // 4  # 16th note grid

    for bar in range(bars):
        bar_seed = deterministic_seed(seed, bar, "hats", "pattern")
        bar_rng = random.Random(bar_seed)

        if mode == "straight_8":
            # Every 8th note
            steps = [0, 2, 4, 6, 8, 10, 12, 14]
        elif mode == "straight_16":
            # Every 16th note
            steps = list(range(16))
        elif mode == "skip_step":
            # Skip-step pattern (every other)
            steps = [0, 2, 4, 6, 8, 10, 12, 14]
            # Randomly skip some
            steps = [s for s in steps if bar_rng.random() < density]
        elif mode == "roll":
            # Trap-style rolls
            steps = []
            # Base pattern
            for i in range(0, 16, 2):
                if bar_rng.random() < density:
                    steps.append(i)
            # Add rolls
            if bar_rng.random() < roll_probability:
                # Add rapid-fire hits
                roll_start = bar_rng.randint(8, 12)
                if roll_subdivision == "1/32":
                    roll_steps = [roll_start, roll_start + 1, roll_start + 2, roll_start + 3]
                else:  # 1/64
                    roll_steps = list(range(roll_start, roll_start + 6))
                steps.extend(roll_steps)
        else:
            steps = list(range(16))

        for step in steps:
            if bar_rng.random() > density:
                continue

            tick = bar * ticks_per_bar + step * step_ticks

            # Apply swing
            tick = apply_swing(tick, step, swing, step_ticks, "16th")

            # Hat velocity: varies the most
            velocity = 70 + int(bar_rng.random() * 40)  # 70-110

            events.append(
                {
                    "pitch": 42,  # Closed hat
                    "velocity": velocity,
                    "start_tick": tick,
                    "duration_tick": step_ticks // 2,
                    "role": "closed_hat",
                }
            )

    return events


def generate_ghost_notes(
    bars: int,
    ticks_per_bar: int,
    seed: int,
    snare_events: list[dict],
    density: float = 0.3,
) -> list[dict]:
    """Generate ghost notes (quiet snares between main snares)."""
    events = []
    step_ticks = ticks_per_bar // 4

    # Find gaps between snares
    snare_steps = set()
    for event in snare_events:
        step = (event["start_tick"] % ticks_per_bar) // step_ticks
        snare_steps.add(step)

    for bar in range(bars):
        bar_seed = deterministic_seed(seed, bar, "ghost", "pattern")
        bar_rng = random.Random(bar_seed)

        # Add ghost notes in gaps
        for step in range(16):
            if step in snare_steps:
                continue  # Don't overlap with main snare

            if bar_rng.random() < density:
                tick = bar * ticks_per_bar + step * step_ticks

                # Ghost notes: low velocity
                velocity = 40 + int(bar_rng.random() * 20)  # 40-60

                events.append(
                    {
                        "pitch": 38,  # Snare note
                        "velocity": velocity,
                        "start_tick": tick,
                        "duration_tick": step_ticks // 2,
                        "role": "ghost",
                    }
                )

    return events


def generate_fill_pattern(
    bar: int, ticks_per_bar: int, style: str, seed: int, drum_map: DrumMap
) -> list[dict]:
    """Generate a fill pattern for the last bar.

    Args:
        bar: Bar index (0-based, typically last bar)
        ticks_per_bar: Ticks per bar
        style: Style (boom_bap, trap, drill, lofi, minimal)
        seed: Random seed
        drum_map: Drum note mappings

    Returns:
        List of fill events
    """
    rng = random.Random(seed)
    events = []

    # Fill typically happens in last half-bar or last bar
    fill_start_tick = bar * ticks_per_bar + (ticks_per_bar // 2)
    fill_length_ticks = ticks_per_bar // 2

    # Generate rapid snare/kick hits
    num_hits = 4 + rng.randint(0, 4)  # 4-8 hits
    for i in range(num_hits):
        offset = int((i / num_hits) * fill_length_ticks)
        tick = fill_start_tick + offset

        # Alternate between snare and kick
        if i % 2 == 0:
            events.append(
                {
                    "pitch": drum_map.get_note("snare"),
                    "velocity": 100 + rng.randint(-10, 10),
                    "start_tick": tick,
                    "duration_tick": PPQ // 8,
                    "role": "snare",
                }
            )
        else:
            events.append(
                {
                    "pitch": drum_map.get_note("kick"),
                    "velocity": 110 + rng.randint(-10, 10),
                    "start_tick": tick,
                    "duration_tick": PPQ // 8,
                    "role": "kick",
                }
            )

    return events


def generate_drum_pattern_v2(
    bars: int,
    time_signature_num: int,
    time_signature_den: int,
    seed: int,
    drum_map: DrumMap,
    style: str = "boom_bap",
    swing: float = 0.0,
    density: float = 0.7,
    hat_mode: Literal["straight_8", "straight_16", "skip_step", "roll"] = "straight_16",
    ghost_notes: bool = True,
    pause_probability: float = 0.0,
    pause_scope: str = "kick",
    variation_intensity: float = 0.3,
    fill_probability: float = 0.0,
    syncopation: float = 0.0,
    ghost_note_probability: float = 0.3,
    hat_subdivision: Literal["1/8", "1/16", "1/32"] = "1/16",
) -> list[dict]:
    """Generate producer-grade drum pattern.

    Args:
        bars: Number of bars
        time_signature_num: Time signature numerator
        time_signature_den: Time signature denominator
        seed: Base seed for determinism
        drum_map: Drum note mappings
        style: Style (boom_bap, trap, drill, lofi, minimal)
        swing: Swing amount (0.0-1.0)
        density: Overall hit density (0-1)
        hat_mode: Hi-hat mode
        ghost_notes: Enable ghost notes
        pause_probability: Probability of pausing per bar
        pause_scope: What to pause (kick, snare, all)
        variation_intensity: Bar-to-bar variation (0-1)
        fill_probability: Probability of fill in last bar (0-1)
        syncopation: Syncopation amount (0-1), shifts off-beat hits
        ghost_note_probability: Probability of ghost notes (0-1)
        hat_subdivision: Hi-hat subdivision (1/8, 1/16, 1/32)

    Returns:
        List of drum events with proper MIDI mapping
    """
    # Calculate timing
    quarter_notes_per_bar = (time_signature_num * 4) / time_signature_den
    ticks_per_bar = int(quarter_notes_per_bar * PPQ)

    all_events = []

    # Generate each role
    kick_events = generate_kick_pattern(
        bars, ticks_per_bar, style, seed, density, pause_probability, pause_scope
    )
    snare_events = generate_snare_pattern(
        bars, ticks_per_bar, style, seed, density, pause_probability
    )
    hat_events = generate_hat_pattern(
        bars, ticks_per_bar, style, seed, hat_mode, density, swing, roll_probability=0.1
    )

    # Apply drum map
    for event in kick_events:
        event["pitch"] = drum_map.get_note("kick")
    for event in snare_events:
        event["pitch"] = drum_map.get_note("snare")
    for event in hat_events:
        event["pitch"] = drum_map.get_note("closed_hat")

    all_events.extend(kick_events)
    all_events.extend(snare_events)
    all_events.extend(hat_events)

    # Add ghost notes if enabled
    if ghost_notes and ghost_note_probability > 0:
        ghost_events = generate_ghost_notes(
            bars, ticks_per_bar, seed, snare_events, density=ghost_note_probability
        )
        for event in ghost_events:
            event["pitch"] = drum_map.get_note("snare")
        all_events.extend(ghost_events)

    # Add fills if enabled (last bar or last half-bar)
    if fill_probability > 0:
        fill_seed = deterministic_seed(seed, bars - 1, "fill", "pattern")
        rng = random.Random(fill_seed)
        if rng.random() < fill_probability:
            fill_events = generate_fill_pattern(bars - 1, ticks_per_bar, style, fill_seed, drum_map)
            all_events.extend(fill_events)

    # Apply syncopation (shift off-beat hits)
    if syncopation > 0:
        syncopation_offset = int(syncopation * PPQ / 8)  # Max 1/8 note shift
        for event in all_events:
            # Only shift off-beat hits (not on 1, 2, 3, 4)
            beat_position = (event["start_tick"] % ticks_per_bar) / (ticks_per_bar / 4)
            if beat_position % 1.0 > 0.1:  # Off-beat
                event["start_tick"] += syncopation_offset

    # Sort by start_tick
    all_events.sort(key=lambda e: e["start_tick"])

    return all_events
