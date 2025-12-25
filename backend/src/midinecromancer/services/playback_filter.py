"""Playback filtering logic for mute and solo."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from midinecromancer.models.clip import Clip
    from midinecromancer.models.clip_polyrhythm_lane import ClipPolyrhythmLane
    from midinecromancer.models.track import Track


def should_play_track(track: "Track", all_tracks: list["Track"]) -> bool:
    """Determine if a track should play based on mute/solo logic.

    Args:
        track: Track to check
        all_tracks: All tracks in the project

    Returns:
        True if track should play, False otherwise
    """
    # If muted, never play
    if track.is_muted:
        return False

    # Check if any track is soloed
    has_any_solo = any(t.is_soloed for t in all_tracks)

    # If any track is soloed, only soloed tracks play
    if has_any_solo:
        return track.is_soloed

    # Otherwise, play if not muted
    return True


def should_play_clip(clip: "Clip", all_clips_in_track: list["Clip"]) -> bool:
    """Determine if a clip should play based on mute/solo logic.

    Args:
        clip: Clip to check
        all_clips_in_track: All clips in the same track

    Returns:
        True if clip should play, False otherwise
    """
    # If muted, never play
    if clip.is_muted:
        return False

    # Check if any clip in track is soloed
    has_any_solo = any(c.is_soloed for c in all_clips_in_track)

    # If any clip is soloed, only soloed clips play
    if has_any_solo:
        return clip.is_soloed

    # Otherwise, play if not muted
    return True


def should_play_lane(
    lane: "ClipPolyrhythmLane", all_lanes_in_clip: list["ClipPolyrhythmLane"]
) -> bool:
    """Determine if a polyrhythm lane should play based on mute/solo logic.

    Args:
        lane: Lane to check
        all_lanes_in_clip: All lanes in the same clip

    Returns:
        True if lane should play, False otherwise
    """
    # If muted, never play
    if lane.mute:
        return False

    # Check if any lane is soloed
    has_any_solo = any(l.solo for l in all_lanes_in_clip)

    # If any lane is soloed, only soloed lanes play
    if has_any_solo:
        return lane.solo

    # Otherwise, play if not muted
    return True


def filter_tracks_for_playback(tracks: list["Track"]) -> list["Track"]:
    """Filter tracks based on mute/solo logic.

    Args:
        tracks: List of tracks

    Returns:
        Filtered list of tracks that should play
    """
    return [t for t in tracks if should_play_track(t, tracks)]


def filter_clips_for_playback(clips: list["Clip"]) -> list["Clip"]:
    """Filter clips based on mute/solo logic.

    Args:
        clips: List of clips (should be from same track)

    Returns:
        Filtered list of clips that should play
    """
    return [c for c in clips if should_play_clip(c, clips)]


def filter_lanes_for_playback(lanes: list["ClipPolyrhythmLane"]) -> list["ClipPolyrhythmLane"]:
    """Filter lanes based on mute/solo logic.

    Args:
        lanes: List of lanes (should be from same clip)

    Returns:
        Filtered list of lanes that should play
    """
    return [l for l in lanes if should_play_lane(l, lanes)]
