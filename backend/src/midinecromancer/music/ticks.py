"""Tick conversion utilities for consistent timing across the application.

All timing conversions use PPQ (pulses per quarter note) = 480 ticks per quarter note.
"""

from midinecromancer.music.theory import PPQ


def ticks_per_bar(time_signature_num: int, time_signature_den: int) -> int:
    """Calculate ticks per bar.

    Args:
        time_signature_num: Time signature numerator (e.g., 4)
        time_signature_den: Time signature denominator (e.g., 4)

    Returns:
        Number of ticks per bar
    """
    quarter_notes_per_bar = (time_signature_num * 4) / time_signature_den
    return int(quarter_notes_per_bar * PPQ)


def ticks_to_seconds(ticks: int, bpm: int) -> float:
    """Convert ticks to seconds.

    Args:
        ticks: Number of ticks
        bpm: Beats per minute

    Returns:
        Time in seconds
    """
    seconds_per_tick = 60.0 / (bpm * PPQ)
    return ticks * seconds_per_tick


def seconds_to_ticks(seconds: float, bpm: int) -> int:
    """Convert seconds to ticks.

    Args:
        seconds: Time in seconds
        bpm: Beats per minute

    Returns:
        Number of ticks (rounded)
    """
    ticks_per_second = (bpm * PPQ) / 60.0
    return int(round(seconds * ticks_per_second))


def beats_to_ticks(beats: float, bpm: int) -> int:
    """Convert beats to ticks.

    Args:
        beats: Number of beats
        bpm: Beats per minute

    Returns:
        Number of ticks (rounded)
    """
    ticks_per_beat = PPQ
    return int(round(beats * ticks_per_beat))


def ticks_to_beats(ticks: int) -> float:
    """Convert ticks to beats.

    Args:
        ticks: Number of ticks

    Returns:
        Number of beats
    """
    return ticks / PPQ


def clip_start_tick(clip_start_bar: int, time_signature_num: int, time_signature_den: int) -> int:
    """Calculate absolute start tick for a clip.

    Args:
        clip_start_bar: Starting bar of clip (0-indexed)
        time_signature_num: Time signature numerator
        time_signature_den: Time signature denominator

    Returns:
        Absolute start tick
    """
    ticks_per_bar_value = ticks_per_bar(time_signature_num, time_signature_den)
    return clip_start_bar * ticks_per_bar_value


def absolute_tick(
    clip_start_bar: int,
    relative_tick: int,
    time_signature_num: int,
    time_signature_den: int,
) -> int:
    """Calculate absolute tick from clip start and relative tick.

    Args:
        clip_start_bar: Starting bar of clip
        relative_tick: Tick relative to clip start
        time_signature_num: Time signature numerator
        time_signature_den: Time signature denominator

    Returns:
        Absolute tick position
    """
    clip_start = clip_start_tick(clip_start_bar, time_signature_num, time_signature_den)
    return clip_start + relative_tick
