"""ZIP export with per-part MIDI files."""

import io
import re
import zipfile
from datetime import datetime
from typing import TYPE_CHECKING, Literal

import mido

from midinecromancer.music.offsets import apply_offsets_to_tick
from midinecromancer.music.theory import PPQ
from midinecromancer.services.playback_filter import (
    filter_clips_for_playback,
    filter_tracks_for_playback,
)

if TYPE_CHECKING:
    from midinecromancer.models.project import Project
    from midinecromancer.models.track import Track


def sanitize_filename(name: str) -> str:
    """Sanitize a string for use as a filename."""
    # Remove or replace invalid characters
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    # Remove leading/trailing spaces and dots
    name = name.strip(" .")
    # Limit length
    if len(name) > 100:
        name = name[:100]
    return name or "untitled"


def export_track_to_midi(project: "Project", track: "Track", ticks_per_bar: int) -> bytes:
    """Export a single track to MIDI file bytes.

    Args:
        project: Project model
        track: Track model with clips loaded
        ticks_per_bar: Pre-calculated ticks per bar

    Returns:
        MIDI file as bytes
    """
    mid = mido.MidiFile(ticks_per_beat=PPQ)

    # Create MIDI track
    midi_track = mido.MidiTrack()
    midi_track.name = track.name

    # Set program change
    midi_track.append(
        mido.Message(
            "program_change",
            channel=track.midi_channel,
            program=track.midi_program,
            time=0,
        )
    )

    # Filter clips based on mute/solo
    filtered_clips = filter_clips_for_playback(track.clips)

    # Collect all note events from clips
    note_events = []
    for clip in filtered_clips:
        clip_start_tick = clip.start_bar * ticks_per_bar
        # Apply offsets
        clip_offset = clip.start_offset_ticks
        track_offset = track.start_offset_ticks
        for note in clip.notes:
            # Calculate base tick position
            base_tick = clip_start_tick + note.start_tick
            # Apply offsets
            start_tick = int(round(apply_offsets_to_tick(base_tick, clip_offset, track_offset)))
            duration_tick = int(round(note.duration_tick))
            note_events.append(
                {
                    "tick": start_tick,
                    "pitch": note.pitch,
                    "velocity": note.velocity,
                    "duration": max(duration_tick, 1),
                }
            )

    # Sort by tick
    note_events.sort(key=lambda x: x["tick"])

    # Convert to MIDI messages
    all_events = []
    for event in note_events:
        all_events.append(
            {
                "tick": event["tick"],
                "type": "on",
                "pitch": event["pitch"],
                "velocity": event["velocity"],
            }
        )
        all_events.append(
            {
                "tick": event["tick"] + event["duration"],
                "type": "off",
                "pitch": event["pitch"],
                "velocity": 0,
            }
        )

    # Sort all events by tick
    all_events.sort(key=lambda x: x["tick"])

    # Convert to MIDI messages with delta times
    current_tick = 0
    for event in all_events:
        tick_delta = event["tick"] - current_tick
        if tick_delta < 0:
            tick_delta = 0

        if event["type"] == "on":
            midi_track.append(
                mido.Message(
                    "note_on",
                    channel=track.midi_channel,
                    note=event["pitch"],
                    velocity=event["velocity"],
                    time=tick_delta,
                )
            )
        else:
            midi_track.append(
                mido.Message(
                    "note_off",
                    channel=track.midi_channel,
                    note=event["pitch"],
                    velocity=0,
                    time=tick_delta,
                )
            )
        current_tick = event["tick"]

    mid.tracks.append(midi_track)

    # Export to bytes
    buffer = io.BytesIO()
    mid.save(file=buffer)
    return buffer.getvalue()


def export_project_to_zip(
    project: "Project",
    tracks: list["Track"],
    split_by: Literal["track", "clip"] = "track",
) -> bytes:
    """Export project as ZIP containing per-part MIDI files.

    Args:
        project: Project model
        tracks: List of tracks with clips, notes, and chord events loaded
        split_by: How to split parts ("track" or "clip")

    Returns:
        ZIP file as bytes
    """
    # Calculate ticks per bar
    quarter_notes_per_bar = (project.time_signature_num * 4) / project.time_signature_den
    ticks_per_bar = int(quarter_notes_per_bar * PPQ)

    # Filter tracks based on mute/solo
    filtered_tracks = filter_tracks_for_playback(tracks)

    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        part_index = 0

        if split_by == "track":
            # One MIDI file per track
            for track in filtered_tracks:
                part_index += 1
                midi_bytes = export_track_to_midi(project, track, ticks_per_bar)
                safe_name = sanitize_filename(track.name)
                filename = f"part_{part_index:02d}_{safe_name}.mid"
                zip_file.writestr(filename, midi_bytes)

        elif split_by == "clip":
            # One MIDI file per clip
            for track in filtered_tracks:
                for clip in filter_clips_for_playback(track.clips):
                    part_index += 1
                    # Create a temporary track with just this clip
                    from midinecromancer.models.track import Track

                    temp_track = Track(
                        id=track.id,
                        project_id=track.project_id,
                        name=track.name,
                        role=track.role,
                        midi_channel=track.midi_channel,
                        midi_program=track.midi_program,
                        is_muted=track.is_muted,
                        start_offset_ticks=track.start_offset_ticks,
                    )
                    temp_track.clips = [clip]

                    midi_bytes = export_track_to_midi(project, temp_track, ticks_per_bar)
                    safe_track_name = sanitize_filename(track.name)
                    safe_clip_name = sanitize_filename(f"bar_{clip.start_bar}")
                    filename = f"part_{part_index:02d}_{safe_track_name}_{safe_clip_name}.mid"
                    zip_file.writestr(filename, midi_bytes)

    zip_buffer.seek(0)
    return zip_buffer.getvalue()


def generate_zip_filename(project_name: str) -> str:
    """Generate ZIP filename with timestamp.

    Args:
        project_name: Project name

    Returns:
        Filename like "ProjectName_20240115_143022.zip"
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = sanitize_filename(project_name)
    return f"{safe_name}_{timestamp}.zip"
