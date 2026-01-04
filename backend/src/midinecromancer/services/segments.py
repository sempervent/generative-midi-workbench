"""Segment generation service for creating clips with configurable models."""

import hashlib
import random
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from midinecromancer.music import generate_bassline, generate_chord_progression, generate_melody
from midinecromancer.music.drums import DrumMap, generate_drum_pattern_v2
from midinecromancer.music.theory import PPQ
from midinecromancer.models.chord_event import ChordEvent
from midinecromancer.models.clip import Clip
from midinecromancer.models.note import Note
from midinecromancer.models.project import Project
from midinecromancer.models.track import Track
from midinecromancer.schemas.segment import (
    BassModel,
    BeatsModel,
    ChordsModel,
    MelodyModel,
    SegmentCreateRequest,
    SegmentGenerateResponse,
    SegmentKind,
)


def deterministic_seed(base_seed: int, project_id: UUID, start_bar: int, kind: str) -> int:
    """Generate deterministic seed for a segment."""
    seed_str = f"{base_seed}_{project_id}_{start_bar}_{kind}"
    hash_bytes = hashlib.blake2b(seed_str.encode(), digest_size=8).digest()
    return int.from_bytes(hash_bytes, byteorder="big", signed=True)


class SegmentService:
    """Service for generating segments (clips with content)."""

    def __init__(self, session: AsyncSession):
        """Initialize service with database session."""
        self.session = session

    async def generate_segments(self, request: SegmentCreateRequest) -> SegmentGenerateResponse:
        """Generate segments based on request.

        If preview=True, returns preview data without DB writes.
        If preview=False, creates clips and persists to DB.
        """
        project = await self.session.get(Project, request.project_id)
        if not project:
            raise ValueError(f"Project {request.project_id} not found")

        bpm = request.bpm if request.bpm is not None else project.bpm
        ticks_per_bar = int((project.time_signature_num * 4) / project.time_signature_den * PPQ)

        clips_data = []
        events_by_clip: dict[str, list[dict]] = {}
        chords_by_clip: dict[str, list[dict]] = {}
        lanes_by_clip: dict[str, list[dict]] = {}

        for kind in request.kinds:
            model = request.models.get(kind)
            segment_seed = deterministic_seed(
                request.seed, request.project_id, request.start_bar, kind
            )

            if kind == "beats":
                clip_data, events = await self._generate_beats(
                    project,
                    request.start_bar,
                    request.length_bars,
                    segment_seed,
                    model if isinstance(model, BeatsModel) else BeatsModel(),
                    request.preview,
                )
            elif kind == "chords":
                clip_data, events, chord_events = await self._generate_chords(
                    project,
                    request.start_bar,
                    request.length_bars,
                    segment_seed,
                    model if isinstance(model, ChordsModel) else ChordsModel(),
                    request.preview,
                )
                chords_by_clip[clip_data["id"]] = chord_events
            elif kind == "bass":
                clip_data, events = await self._generate_bass(
                    project,
                    request.start_bar,
                    request.length_bars,
                    segment_seed,
                    model if isinstance(model, BassModel) else BassModel(),
                    request.preview,
                )
            elif kind == "melody":
                clip_data, events = await self._generate_melody(
                    project,
                    request.start_bar,
                    request.length_bars,
                    segment_seed,
                    model if isinstance(model, MelodyModel) else MelodyModel(),
                    request.preview,
                )
            else:
                continue

            clips_data.append(clip_data)
            events_by_clip[clip_data["id"]] = events

        return SegmentGenerateResponse(
            clips=clips_data,
            events_by_clip=events_by_clip,
            chords_by_clip=chords_by_clip,
            lanes_by_clip=lanes_by_clip,
            preview=request.preview,
        )

    async def _get_or_create_track(self, project_id: UUID, role: str, midi_channel: int) -> Track:
        """Get or create a track for a role."""
        result = await self.session.execute(
            select(Track).where(Track.project_id == project_id, Track.role == role)
        )
        track = result.scalar_one_or_none()
        if not track:
            track = Track(
                project_id=project_id,
                name=role.capitalize(),
                role=role,
                midi_channel=midi_channel,
                midi_program=0,
            )
            self.session.add(track)
            await self.session.flush()
        return track

    async def _generate_beats(
        self,
        project: Project,
        start_bar: int,
        length_bars: int,
        seed: int,
        model: BeatsModel,
        preview: bool,
    ) -> tuple[dict, list[dict]]:
        """Generate beats segment."""
        track = await self._get_or_create_track(project.id, "drums", 9)

        # Map kit to style
        style_map = {
            "gm_hiphop": "boom_bap",
            "gm_trap": "trap",
            "gm_boom_bap": "boom_bap",
            "gm_blank": "minimal",
        }
        style = style_map.get(model.kit, "boom_bap")

        # Map pattern to hat_mode
        hat_mode_map = {
            "straight": "straight_16",
            "syncopated": "skip_step",
            "euclidean": "straight_8",
            "polyrhythm": "roll",
        }
        hat_mode = hat_mode_map.get(model.pattern, "straight_16")

        drum_map = DrumMap()  # Default GM mapping
        events = generate_drum_pattern_v2(
            bars=length_bars,
            time_signature_num=project.time_signature_num,
            time_signature_den=project.time_signature_den,
            seed=seed,
            drum_map=drum_map,
            style=style,
            swing=model.swing,
            density=model.density,
            hat_mode=hat_mode,
            ghost_notes=model.ghost_notes,
            pause_probability=model.mute_probability,
            pause_scope="kick",
            variation_intensity=model.kick_variation,
        )

        # Adjust start_tick to account for start_bar
        ticks_per_bar = int((project.time_signature_num * 4) / project.time_signature_den * PPQ)
        for event in events:
            event["start_tick"] += start_bar * ticks_per_bar

        if preview:
            clip_data = {
                "id": f"preview_beats_{seed}",
                "kind": "beats",
                "start_bar": start_bar,
                "length_bars": length_bars,
                "track_id": str(track.id),
            }
        else:
            clip = Clip(
                track_id=track.id,
                start_bar=start_bar,
                length_bars=length_bars,
                params={
                    "kit": model.kit,
                    "density": model.density,
                    "swing": model.swing,
                    "pattern": model.pattern,
                    "ghost_notes": model.ghost_notes,
                    "fills": model.fills,
                },
            )
            self.session.add(clip)
            await self.session.flush()

            for event in events:
                note = Note(
                    clip_id=clip.id,
                    pitch=event["pitch"],
                    velocity=event["velocity"],
                    start_tick=event["start_tick"] - start_bar * ticks_per_bar,  # Relative to clip
                    duration_tick=event["duration_tick"],
                    probability=1.0,
                )
                self.session.add(note)

            await self.session.flush()
            clip_data = {
                "id": str(clip.id),
                "kind": "beats",
                "start_bar": clip.start_bar,
                "length_bars": clip.length_bars,
                "track_id": str(clip.track_id),
            }

        return clip_data, events

    async def _generate_chords(
        self,
        project: Project,
        start_bar: int,
        length_bars: int,
        seed: int,
        model: ChordsModel,
        preview: bool,
    ) -> tuple[dict, list[dict], list[dict]]:
        """Generate chords segment."""
        track = await self._get_or_create_track(project.id, "chords", 0)

        # Generate progression
        progression = generate_chord_progression(
            tonic=model.key,
            mode=model.mode,
            bars=length_bars,
            seed=seed,
            start_on="I",
            prefer_circle_motion=model.progression_style == "circle_fifths",
            cadence_ending=model.cadence_strength > 0.5,
        )

        ticks_per_bar = int((project.time_signature_num * 4) / project.time_signature_den * PPQ)

        chord_events = []
        note_events = []

        if preview:
            clip_data = {
                "id": f"preview_chords_{seed}",
                "kind": "chords",
                "start_bar": start_bar,
                "length_bars": length_bars,
                "track_id": str(track.id),
            }
        else:
            clip = Clip(
                track_id=track.id,
                start_bar=start_bar,
                length_bars=length_bars,
                params={
                    "key": model.key,
                    "mode": model.mode,
                    "progression_style": model.progression_style,
                    "harmonic_rhythm": model.harmonic_rhythm,
                },
            )
            self.session.add(clip)
            await self.session.flush()

        for chord in progression:
            duration_beats = (
                chord["length_bars"] * (project.time_signature_num * 4) / project.time_signature_den
            )
            duration_ticks = int(chord["length_bars"] * ticks_per_bar)
            # Start tick relative to clip start (chord["start_bar"] is relative to segment start)
            relative_start_bar = chord["start_bar"]  # Already relative to segment start
            chord_start_tick = int(relative_start_bar * ticks_per_bar)

            chord_event_data = {
                "start_tick": chord_start_tick,
                "duration_tick": duration_ticks,
                "duration_beats": duration_beats,
                "roman_numeral": chord["roman_numeral"],
                "chord_name": chord["chord_name"],
                "intensity": model.intensity,
                "voicing": model.voicing,
                "inversion": int(model.inversion_bias * 2) - 1,  # -1 to 1
                "strum_ms": model.strum_ms,
                "humanize_ms": 0,  # Can be enhanced
                "velocity_jitter": 0,
                "timing_jitter_ms": 0,
                "is_enabled": True,
                "is_locked": False,
            }

            if preview:
                chord_events.append(chord_event_data)
            else:
                chord_event = ChordEvent(
                    clip_id=clip.id,
                    start_tick=chord_event_data["start_tick"],
                    duration_tick=chord_event_data["duration_tick"],
                    duration_beats=chord_event_data["duration_beats"],
                    roman_numeral=chord_event_data["roman_numeral"],
                    chord_name=chord_event_data["chord_name"],
                    intensity=chord_event_data["intensity"],
                    voicing=chord_event_data["voicing"],
                    inversion=chord_event_data["inversion"],
                    strum_ms=chord_event_data["strum_ms"],
                    humanize_ms=chord_event_data["humanize_ms"],
                    velocity_jitter=chord_event_data["velocity_jitter"],
                    timing_jitter_ms=chord_event_data["timing_jitter_ms"],
                    is_enabled=chord_event_data["is_enabled"],
                    is_locked=chord_event_data["is_locked"],
                )
                self.session.add(chord_event)
                await self.session.flush()

                # Render chord to notes for playback
                from midinecromancer.services.chord_render import render_chord_event_to_notes

                project_context = {
                    "tonic": model.key,
                    "mode": model.mode,
                    "bpm": project.bpm,
                    "time_signature_num": project.time_signature_num,
                    "time_signature_den": project.time_signature_den,
                }
                rendered_notes = render_chord_event_to_notes(chord_event, project_context, seed)

                for note_data in rendered_notes:
                    note = Note(
                        clip_id=clip.id,
                        pitch=note_data["pitch"],
                        velocity=note_data["velocity"],
                        start_tick=note_data["start_tick"],
                        duration_tick=note_data["duration_tick"],
                        probability=1.0,
                    )
                    self.session.add(note)
                    note_events.append(note_data)

                chord_events.append(
                    {
                        "id": str(chord_event.id),
                        **chord_event_data,
                    }
                )

        if not preview:
            await self.session.flush()
            clip_data = {
                "id": str(clip.id),
                "kind": "chords",
                "start_bar": clip.start_bar,
                "length_bars": clip.length_bars,
                "track_id": str(clip.track_id),
            }

        return clip_data, note_events, chord_events

    async def _generate_bass(
        self,
        project: Project,
        start_bar: int,
        length_bars: int,
        seed: int,
        model: BassModel,
        preview: bool,
    ) -> tuple[dict, list[dict]]:
        """Generate bass segment."""
        track = await self._get_or_create_track(project.id, "bass", 1)

        # Get chord progression for bass to follow
        chord_progression = generate_chord_progression(
            tonic=project.key_tonic,
            mode=project.mode,
            bars=length_bars,
            seed=seed,
        )

        from midinecromancer.music.theory import Mode

        events = generate_bassline(
            tonic=project.key_tonic,
            mode=project.mode,  # type: ignore[arg-type]
            bars=length_bars,
            time_signature_num=project.time_signature_num,
            time_signature_den=project.time_signature_den,
            chord_progression=chord_progression,
            seed=seed,
            octave=model.octave,
            syncopation=model.rhythmic_density,
        )

        # Adjust start_tick
        ticks_per_bar = int((project.time_signature_num * 4) / project.time_signature_den * PPQ)
        for event in events:
            event["start_tick"] += start_bar * ticks_per_bar
            event["velocity"] = int(event["velocity"] * model.intensity)

        if preview:
            clip_data = {
                "id": f"preview_bass_{seed}",
                "kind": "bass",
                "start_bar": start_bar,
                "length_bars": length_bars,
                "track_id": str(track.id),
            }
        else:
            clip = Clip(
                track_id=track.id,
                start_bar=start_bar,
                length_bars=length_bars,
                params={
                    "style": model.style,
                    "octave": model.octave,
                    "follow_kicks": model.follow_kicks,
                },
            )
            self.session.add(clip)
            await self.session.flush()

            for event in events:
                note = Note(
                    clip_id=clip.id,
                    pitch=event["pitch"],
                    velocity=event["velocity"],
                    start_tick=event["start_tick"] - start_bar * ticks_per_bar,
                    duration_tick=event["duration_tick"],
                    probability=1.0,
                )
                self.session.add(note)

            await self.session.flush()
            clip_data = {
                "id": str(clip.id),
                "kind": "bass",
                "start_bar": clip.start_bar,
                "length_bars": clip.length_bars,
                "track_id": str(clip.track_id),
            }

        return clip_data, events

    async def _generate_melody(
        self,
        project: Project,
        start_bar: int,
        length_bars: int,
        seed: int,
        model: MelodyModel,
        preview: bool,
    ) -> tuple[dict, list[dict]]:
        """Generate melody segment."""
        track = await self._get_or_create_track(project.id, "melody", 2)

        # Map range to octave
        octave_map = {"narrow": 5, "medium": 5, "wide": 6}
        octave = octave_map.get(model.range, 5)

        # Map leapiness to stepwise_bias
        stepwise_bias = 1.0 - model.leapiness

        from midinecromancer.music.theory import Mode

        events = generate_melody(
            tonic=project.key_tonic,
            mode=project.mode,  # type: ignore[arg-type]
            bars=length_bars,
            time_signature_num=project.time_signature_num,
            time_signature_den=project.time_signature_den,
            seed=seed,
            octave=octave,
            stepwise_bias=stepwise_bias,
            leap_probability=model.leapiness,
        )

        # Adjust start_tick and velocity
        ticks_per_bar = int((project.time_signature_num * 4) / project.time_signature_den * PPQ)
        for event in events:
            event["start_tick"] += start_bar * ticks_per_bar
            event["velocity"] = int(event["velocity"] * model.intensity)

        if preview:
            clip_data = {
                "id": f"preview_melody_{seed}",
                "kind": "melody",
                "start_bar": start_bar,
                "length_bars": length_bars,
                "track_id": str(track.id),
            }
        else:
            clip = Clip(
                track_id=track.id,
                start_bar=start_bar,
                length_bars=length_bars,
                params={
                    "range": model.range,
                    "motif_repetition": model.motif_repetition,
                    "leapiness": model.leapiness,
                },
            )
            self.session.add(clip)
            await self.session.flush()

            for event in events:
                note = Note(
                    clip_id=clip.id,
                    pitch=event["pitch"],
                    velocity=event["velocity"],
                    start_tick=event["start_tick"] - start_bar * ticks_per_bar,
                    duration_tick=event["duration_tick"],
                    probability=1.0,
                )
                self.session.add(note)

            await self.session.flush()
            clip_data = {
                "id": str(clip.id),
                "kind": "melody",
                "start_bar": clip.start_bar,
                "length_bars": clip.length_bars,
                "track_id": str(clip.track_id),
            }

        return clip_data, events
