"""MIDI file export using mido.

This module handles export of projects to Standard MIDI Files, including support
for polyrhythms with fractional beat positions. All fractional beat times are
rounded to the nearest tick using standard rounding (round half to even).
"""

import io
from typing import TYPE_CHECKING

import mido

from midinecromancer.music.theory import PPQ
from midinecromancer.services.playback_filter import (
    filter_tracks_for_playback,
    filter_clips_for_playback,
)

if TYPE_CHECKING:
    from midinecromancer.models.project import Project
    from midinecromancer.models.track import Track


def export_project_to_midi(project: "Project", tracks: list["Track"]) -> bytes:
    """Export project to Standard MIDI File format.

    Args:
        project: Project model
        tracks: List of tracks with clips, notes, and chord events

    Returns:
        MIDI file as bytes
    """
    mid = mido.MidiFile(ticks_per_beat=PPQ)

    # Calculate total length in ticks
    quarter_notes_per_bar = (project.time_signature_num * 4) / project.time_signature_den
    ticks_per_bar = int(quarter_notes_per_bar * PPQ)
    total_ticks = project.bars * ticks_per_bar

    # Filter tracks based on mute/solo
    filtered_tracks = filter_tracks_for_playback(tracks)

    # Create a track for each track in the project
    for track_model in filtered_tracks:
        midi_track = mido.MidiTrack()
        midi_track.name = track_model.name

        # Set program change
        midi_track.append(
            mido.Message(
                "program_change",
                channel=track_model.midi_channel,
                program=track_model.midi_program,
                time=0,
            )
        )

        # Filter clips based on mute/solo
        filtered_clips = filter_clips_for_playback(track_model.clips)

        # Collect all note events from clips
        # Note: start_tick and duration_tick are already in integer ticks.
        # For polyrhythms, fractional beats are converted to ticks during generation
        # using deterministic rounding (nearest tick, round half to even).
        note_events = []
        for clip in filtered_clips:
            clip_start_tick = clip.start_bar * ticks_per_bar
            for note in clip.notes:
                # Ensure tick values are integers (should already be, but validate)
                start_tick = int(round(clip_start_tick + note.start_tick))
                duration_tick = int(round(note.duration_tick))
                note_events.append(
                    {
                        "tick": start_tick,
                        "pitch": note.pitch,
                        "velocity": note.velocity,
                        "duration": max(duration_tick, 1),  # Minimum 1 tick
                    }
                )

        # Sort by tick
        note_events.sort(key=lambda x: x["tick"])

        # Convert to MIDI messages - create note on/off events
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
                        channel=track_model.midi_channel,
                        note=event["pitch"],
                        velocity=event["velocity"],
                        time=tick_delta,
                    )
                )
            else:
                midi_track.append(
                    mido.Message(
                        "note_off",
                        channel=track_model.midi_channel,
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
