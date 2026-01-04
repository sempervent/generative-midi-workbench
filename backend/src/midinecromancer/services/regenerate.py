"""Service for regenerating clip content with preview support."""

import hashlib
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


def deterministic_seed_for_regenerate(
    project_id: UUID, clip_id: UUID, kind: str, base_seed: int, variation: float
) -> int:
    """Generate deterministic seed for regeneration."""
    seed_str = f"{project_id}_{clip_id}_{kind}_{base_seed}_{variation}"
    hash_bytes = hashlib.blake2b(seed_str.encode(), digest_size=8).digest()
    return int.from_bytes(hash_bytes, byteorder="big", signed=True)


class RegenerateService:
    """Service for regenerating clip content."""

    def __init__(self, session: AsyncSession):
        """Initialize service with database session."""
        self.session = session

    async def regenerate_clip(
        self,
        clip_id: UUID,
        kind: str,
        seed: int | None = None,
        variation: float = 0.3,
        params: dict | None = None,
        preview: bool = False,
    ) -> dict:
        """Regenerate clip content.

        Args:
            clip_id: Clip to regenerate
            kind: Segment kind (beats, chords, bass, melody)
            seed: Base seed (uses project seed if None)
            variation: Variation amount (0-1)
            params: Type-specific parameters
            preview: If True, return preview without DB writes

        Returns:
            Dict with generated events and metadata
        """
        # Get clip and project context
        clip = await self.session.get(Clip, clip_id)
        if not clip:
            raise ValueError(f"Clip {clip_id} not found")

        track = await self.session.get(Track, clip.track_id)
        if not track:
            raise ValueError(f"Track {clip.track_id} not found")

        project = await self.session.get(Project, track.project_id)
        if not project:
            raise ValueError(f"Project {track.project_id} not found")

        base_seed = seed if seed is not None else project.seed
        actual_seed = deterministic_seed_for_regenerate(
            project.id, clip.id, kind, base_seed, variation
        )
        params = params or {}

        ticks_per_bar = int(
            (project.time_signature_num * 4) / project.time_signature_den * PPQ
        )

        if kind == "beats" or kind == "drums":
            return await self._regenerate_beats(
                clip, project, track, actual_seed, variation, params, preview, ticks_per_bar
            )
        elif kind == "chords":
            return await self._regenerate_chords(
                clip, project, track, actual_seed, variation, params, preview, ticks_per_bar
            )
        elif kind == "bass":
            return await self._regenerate_bass(
                clip, project, track, actual_seed, variation, params, preview, ticks_per_bar
            )
        elif kind == "melody":
            return await self._regenerate_melody(
                clip, project, track, actual_seed, variation, params, preview, ticks_per_bar
            )
        else:
            raise ValueError(f"Unknown kind: {kind}")

    async def _regenerate_beats(
        self,
        clip: Clip,
        project: Project,
        track: Track,
        seed: int,
        variation: float,
        params: dict,
        preview: bool,
        ticks_per_bar: int,
    ) -> dict:
        """Regenerate beats/drums."""
        style_map = {
            "gm_hiphop": "boom_bap",
            "gm_trap": "trap",
            "gm_boom_bap": "boom_bap",
            "gm_blank": "minimal",
        }
        style = style_map.get(params.get("kit", "gm_hiphop"), "boom_bap")

        hat_mode_map = {
            "straight": "straight_16",
            "syncopated": "skip_step",
            "euclidean": "straight_8",
            "polyrhythm": "roll",
        }
        hat_mode = hat_mode_map.get(params.get("pattern", "straight"), "straight_16")

        drum_map = DrumMap()
        events = generate_drum_pattern_v2(
            bars=clip.length_bars,
            time_signature_num=project.time_signature_num,
            time_signature_den=project.time_signature_den,
            seed=seed,
            drum_map=drum_map,
            style=style,
            swing=params.get("swing", 0.0),
            density=params.get("density", 0.7),
            hat_mode=hat_mode,
            ghost_notes=params.get("ghost_notes", True),
            pause_probability=params.get("pause_probability", 0.0),
            pause_scope="kick",
            variation_intensity=variation,
        )

        # Adjust start_tick to clip start
        for event in events:
            event["start_tick"] += clip.start_bar * ticks_per_bar

        if preview:
            return {
                "kind": "beats",
                "events": events,
                "clip_id": str(clip.id),
            }

        # Clear existing notes
        result = await self.session.execute(
            select(Note).where(Note.clip_id == clip.id)
        )
        existing_notes = result.scalars().all()
        for note in existing_notes:
            await self.session.delete(note)

        # Create new notes (relative to clip start)
        for event in events:
            note = Note(
                clip_id=clip.id,
                pitch=event["pitch"],
                velocity=event["velocity"],
                start_tick=event["start_tick"] - clip.start_bar * ticks_per_bar,
                duration_tick=event["duration_tick"],
                probability=1.0,
            )
            self.session.add(note)

        await self.session.flush()
        return {
            "kind": "beats",
            "events": events,
            "clip_id": str(clip.id),
        }

    async def _regenerate_chords(
        self,
        clip: Clip,
        project: Project,
        track: Track,
        seed: int,
        variation: float,
        params: dict,
        preview: bool,
        ticks_per_bar: int,
    ) -> dict:
        """Regenerate chords."""
        key = params.get("key", project.key_tonic)
        mode = params.get("mode", project.mode)

        progression = generate_chord_progression(
            tonic=key,
            mode=mode,
            bars=clip.length_bars,
            seed=seed,
            start_on="I",
            prefer_circle_motion=params.get("progression_style") == "circle_fifths",
            cadence_ending=params.get("cadence_strength", 0.7) > 0.5,
        )

        chord_events = []
        note_events = []

        if not preview:
            # Clear existing chord events and notes
            result = await self.session.execute(
                select(ChordEvent).where(ChordEvent.clip_id == clip.id)
            )
            existing_chords = result.scalars().all()
            for chord in existing_chords:
                await self.session.delete(chord)

            result = await self.session.execute(
                select(Note).where(Note.clip_id == clip.id)
            )
            existing_notes = result.scalars().all()
            for note in existing_notes:
                await self.session.delete(note)

        for chord in progression:
            duration_beats = (
                chord["length_bars"]
                * (project.time_signature_num * 4)
                / project.time_signature_den
            )
            duration_ticks = int(chord["length_bars"] * ticks_per_bar)

            chord_event_data = {
                "start_tick": int(chord["start_bar"] * ticks_per_bar),
                "duration_tick": duration_ticks,
                "duration_beats": duration_beats,
                "roman_numeral": chord["roman_numeral"],
                "chord_name": chord["chord_name"],
                "intensity": params.get("intensity", 0.85),
                "voicing": params.get("voicing", "root"),
                "inversion": int(params.get("inversion_bias", 0.2) * 2) - 1,
                "strum_beats": params.get("strum_beats", 0.0),
                "humanize_beats": params.get("humanize_beats", 0.0),
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
                    strum_beats=chord_event_data["strum_beats"],
                    humanize_beats=chord_event_data["humanize_beats"],
                    is_enabled=chord_event_data["is_enabled"],
                    is_locked=chord_event_data["is_locked"],
                )
                self.session.add(chord_event)
                await self.session.flush()

                # Render to notes
                from midinecromancer.services.chord_render import render_chord_event_to_notes

                project_context = {
                    "tonic": key,
                    "mode": mode,
                    "bpm": project.bpm,
                    "time_signature_num": project.time_signature_num,
                    "time_signature_den": project.time_signature_den,
                }
                rendered_notes = render_chord_event_to_notes(
                    chord_event, project_context, seed
                )

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

                chord_events.append({
                    "id": str(chord_event.id),
                    **chord_event_data,
                })

        if not preview:
            await self.session.flush()

        return {
            "kind": "chords",
            "chord_events": chord_events,
            "note_events": note_events,
            "clip_id": str(clip.id),
        }

    async def _regenerate_bass(
        self,
        clip: Clip,
        project: Project,
        track: Track,
        seed: int,
        variation: float,
        params: dict,
        preview: bool,
        ticks_per_bar: int,
    ) -> dict:
        """Regenerate bass."""
        # Get chord progression for bass to follow
        chord_progression = generate_chord_progression(
            tonic=project.key_tonic,
            mode=project.mode,
            bars=clip.length_bars,
            seed=seed,
        )

        events = generate_bassline(
            tonic=project.key_tonic,
            mode=project.mode,
            bars=clip.length_bars,
            time_signature_num=project.time_signature_num,
            time_signature_den=project.time_signature_den,
            chord_progression=chord_progression,
            seed=seed,
            octave=params.get("octave", 2),
            syncopation=params.get("rhythmic_density", 0.6),
        )

        # Adjust start_tick and velocity
        for event in events:
            event["start_tick"] += clip.start_bar * ticks_per_bar
            event["velocity"] = int(event["velocity"] * params.get("intensity", 0.85))

        if preview:
            return {
                "kind": "bass",
                "events": events,
                "clip_id": str(clip.id),
            }

        # Clear existing notes
        result = await self.session.execute(
            select(Note).where(Note.clip_id == clip.id)
        )
        existing_notes = result.scalars().all()
        for note in existing_notes:
            await self.session.delete(note)

        # Create new notes
        for event in events:
            note = Note(
                clip_id=clip.id,
                pitch=event["pitch"],
                velocity=event["velocity"],
                start_tick=event["start_tick"] - clip.start_bar * ticks_per_bar,
                duration_tick=event["duration_tick"],
                probability=1.0,
            )
            self.session.add(note)

        await self.session.flush()
        return {
            "kind": "bass",
            "events": events,
            "clip_id": str(clip.id),
        }

    async def _regenerate_melody(
        self,
        clip: Clip,
        project: Project,
        track: Track,
        seed: int,
        variation: float,
        params: dict,
        preview: bool,
        ticks_per_bar: int,
    ) -> dict:
        """Regenerate melody."""
        octave_map = {"narrow": 5, "medium": 5, "wide": 6}
        octave = octave_map.get(params.get("range", "medium"), 5)

        stepwise_bias = 1.0 - params.get("leapiness", 0.3)

        events = generate_melody(
            tonic=project.key_tonic,
            mode=project.mode,
            bars=clip.length_bars,
            time_signature_num=project.time_signature_num,
            time_signature_den=project.time_signature_den,
            seed=seed,
            octave=octave,
            stepwise_bias=stepwise_bias,
            leap_probability=params.get("leapiness", 0.3),
        )

        # Adjust start_tick and velocity
        for event in events:
            event["start_tick"] += clip.start_bar * ticks_per_bar
            event["velocity"] = int(event["velocity"] * params.get("intensity", 0.85))

        if preview:
            return {
                "kind": "melody",
                "events": events,
                "clip_id": str(clip.id),
            }

        # Clear existing notes
        result = await self.session.execute(
            select(Note).where(Note.clip_id == clip.id)
        )
        existing_notes = result.scalars().all()
        for note in existing_notes:
            await self.session.delete(note)

        # Create new notes
        for event in events:
            note = Note(
                clip_id=clip.id,
                pitch=event["pitch"],
                velocity=event["velocity"],
                start_tick=event["start_tick"] - clip.start_bar * ticks_per_bar,
                duration_tick=event["duration_tick"],
                probability=1.0,
            )
            self.session.add(note)

        await self.session.flush()
        return {
            "kind": "melody",
            "events": events,
            "clip_id": str(clip.id),
        }

