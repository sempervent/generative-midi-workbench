"""Generation service for creating musical content."""

import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from midinecromancer.music import (
    generate_bassline,
    generate_chord_progression,
    generate_drum_pattern,
    generate_melody,
)
from midinecromancer.music.drums import DrumMap, generate_drum_pattern_v2
from midinecromancer.music.theory import PPQ
from midinecromancer.models.chord_event import ChordEvent
from midinecromancer.models.clip import Clip
from midinecromancer.models.generation_run import GenerationRun
from midinecromancer.models.note import Note
from midinecromancer.models.project import Project
from midinecromancer.models.track import Track


class GenerationService:
    """Service for generating musical content."""

    def __init__(self, session: AsyncSession):
        """Initialize service with database session."""
        self.session = session

    async def generate_full(
        self,
        project_id: UUID,
        seed: int | None = None,
        params: dict | None = None,
    ) -> GenerationRun:
        """Generate full arrangement (drums, chords, bass, melody)."""
        project = await self.session.get(Project, project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        actual_seed = seed if seed is not None else project.seed
        params = params or {}

        # Create or get tracks
        tracks = await self._ensure_tracks(project_id)

        # Generate each part
        await self.generate_drums(project_id, actual_seed, params.get("drums", {}))
        await self.generate_chords(project_id, actual_seed, params.get("chords", {}))
        await self.generate_bass(project_id, actual_seed, params.get("bass", {}))
        await self.generate_melody(project_id, actual_seed, params.get("melody", {}))

        # Record generation run
        run = GenerationRun(
            project_id=project_id,
            kind="full",
            seed_used=actual_seed,
            params=params,
        )
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def generate_drums(
        self,
        project_id: UUID,
        seed: int | None = None,
        params: dict | None = None,
    ) -> GenerationRun:
        """Generate drum pattern."""
        project = await self.session.get(Project, project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        actual_seed = seed if seed is not None else project.seed
        params = params or {}

        # Get or create drums track
        track = await self._get_or_create_track(project_id, "drums", 9)  # Channel 9 = drums

        # Clear existing clips
        await self._clear_track_clips(track.id)

        # Get drum map profile if specified
        drum_map = DrumMap()  # Default GM mapping
        if params.get("drum_map_profile_id"):
            from midinecromancer.models.drum_map_profile import DrumMapProfile

            profile = await self.session.get(DrumMapProfile, params["drum_map_profile_id"])
            if profile:
                drum_map = DrumMap(
                    kick_note=profile.kick_note,
                    snare_note=profile.snare_note,
                    clap_note=profile.clap_note,
                    closed_hat_note=profile.closed_hat_note,
                    open_hat_note=profile.open_hat_note,
                    rim_note=profile.rim_note,
                    perc_notes=profile.perc_notes,
                )

        # Generate pattern using new engine
        events = generate_drum_pattern_v2(
            bars=project.bars,
            time_signature_num=project.time_signature_num,
            time_signature_den=project.time_signature_den,
            seed=actual_seed,
            drum_map=drum_map,
            style=params.get("style", "boom_bap"),
            swing=params.get("swing", 0.0),
            density=params.get("density", 0.7),
            hat_mode=params.get("hat_mode", "straight_16"),
            ghost_notes=params.get("ghost_notes", True),
            pause_probability=params.get("pause_probability", 0.0),
            pause_scope=params.get("pause_scope", "kick"),
            variation_intensity=params.get("variation_intensity", 0.3),
        )

        # Create clip and notes
        clip = Clip(
            track_id=track.id,
            start_bar=0,
            length_bars=project.bars,
            drum_map_profile_id=params.get("drum_map_profile_id"),
        )
        # Store drum params in clip.params
        clip.params = {
            "style": params.get("style", "boom_bap"),
            "swing": params.get("swing", 0.0),
            "density": params.get("density", 0.7),
            "hat_mode": params.get("hat_mode", "straight_16"),
            "ghost_notes": params.get("ghost_notes", True),
            "pause_probability": params.get("pause_probability", 0.0),
            "variation_intensity": params.get("variation_intensity", 0.3),
        }
        self.session.add(clip)
        await self.session.flush()

        for event in events:
            note = Note(
                clip_id=clip.id,
                pitch=event["pitch"],
                velocity=event["velocity"],
                start_tick=event["start_tick"],
                duration_tick=event["duration_tick"],
                probability=1.0,
            )
            self.session.add(note)

        # Record generation run
        run = GenerationRun(
            project_id=project_id,
            kind="drums",
            seed_used=actual_seed,
            params=params,
        )
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def generate_chords(
        self,
        project_id: UUID,
        seed: int | None = None,
        params: dict | None = None,
    ) -> GenerationRun:
        """Generate chord progression."""
        project = await self.session.get(Project, project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        actual_seed = seed if seed is not None else project.seed
        params = params or {}

        # Get or create chords track
        track = await self._get_or_create_track(project_id, "chords", 0)

        # Clear existing clips
        await self._clear_track_clips(track.id)

        # Generate progression
        progression = generate_chord_progression(
            tonic=project.key_tonic,
            mode=project.mode,
            bars=project.bars,
            seed=actual_seed,
            start_on=params.get("start_on", "I"),
            prefer_circle_motion=params.get("prefer_circle_motion", True),
            cadence_ending=params.get("cadence_ending", True),
        )

        # Calculate ticks per bar
        quarter_notes_per_bar = (project.time_signature_num * 4) / project.time_signature_den
        ticks_per_bar = int(quarter_notes_per_bar * PPQ)

        # Create clips and chord events
        for chord in progression:
            clip = Clip(
                track_id=track.id,
                start_bar=chord["start_bar"],
                length_bars=chord["length_bars"],
            )
            self.session.add(clip)
            await self.session.flush()

            duration_beats = (
                chord["length_bars"] * (project.time_signature_num * 4) / project.time_signature_den
            )
            chord_event = ChordEvent(
                clip_id=clip.id,
                start_tick=0,
                duration_tick=chord["length_bars"] * ticks_per_bar,
                duration_beats=duration_beats,
                roman_numeral=chord["roman_numeral"],
                chord_name=chord["chord_name"],
                intensity=0.85,
                voicing="root",
                inversion=0,
                strum_ms=0,
                humanize_ms=0,
                velocity_jitter=0,
                timing_jitter_ms=0,
                is_enabled=True,
                is_locked=False,
            )
            self.session.add(chord_event)

        # Record generation run
        run = GenerationRun(
            project_id=project_id,
            kind="chords",
            seed_used=actual_seed,
            params=params,
        )
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def generate_bass(
        self,
        project_id: UUID,
        seed: int | None = None,
        params: dict | None = None,
    ) -> GenerationRun:
        """Generate bassline."""
        project = await self.session.get(Project, project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        actual_seed = seed if seed is not None else project.seed
        params = params or {}

        # Get chord progression
        chords_track = await self._get_track_by_role(project_id, "chords")
        if not chords_track:
            raise ValueError("Chords track not found. Generate chords first.")

        # Get chord events
        result = await self.session.execute(
            select(Clip).where(Clip.track_id == chords_track.id).order_by(Clip.start_bar)
        )
        chord_clips = list(result.scalars().all())

        progression = []
        ticks_per_bar = int(((project.time_signature_num * 4) / project.time_signature_den) * 480)
        for clip in chord_clips:
            chord_events = await self.session.execute(
                select(ChordEvent).where(ChordEvent.clip_id == clip.id)
            )
            for ce in chord_events.scalars():
                progression.append(
                    {
                        "roman_numeral": ce.roman_numeral,
                        "start_bar": clip.start_bar,
                        "length_bars": clip.length_bars,
                    }
                )

        # Get or create bass track
        track = await self._get_or_create_track(project_id, "bass", 1)

        # Clear existing clips
        await self._clear_track_clips(track.id)

        # Generate bassline
        events = generate_bassline(
            tonic=project.key_tonic,
            mode=project.mode,
            bars=project.bars,
            time_signature_num=project.time_signature_num,
            time_signature_den=project.time_signature_den,
            chord_progression=progression,
            seed=actual_seed,
            octave=params.get("octave", 3),
            syncopation=params.get("syncopation", 0.3),
        )

        # Create clip and notes
        clip = Clip(track_id=track.id, start_bar=0, length_bars=project.bars)
        self.session.add(clip)
        await self.session.flush()

        for event in events:
            note = Note(
                clip_id=clip.id,
                pitch=event["pitch"],
                velocity=event["velocity"],
                start_tick=event["start_tick"],
                duration_tick=event["duration_tick"],
            )
            self.session.add(note)

        # Record generation run
        run = GenerationRun(
            project_id=project_id,
            kind="bass",
            seed_used=actual_seed,
            params=params,
        )
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def generate_melody(
        self,
        project_id: UUID,
        seed: int | None = None,
        params: dict | None = None,
    ) -> GenerationRun:
        """Generate melody."""
        project = await self.session.get(Project, project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        actual_seed = seed if seed is not None else project.seed
        params = params or {}

        # Get or create melody track
        track = await self._get_or_create_track(project_id, "melody", 2)

        # Clear existing clips
        await self._clear_track_clips(track.id)

        # Generate melody
        events = generate_melody(
            tonic=project.key_tonic,
            mode=project.mode,
            bars=project.bars,
            time_signature_num=project.time_signature_num,
            time_signature_den=project.time_signature_den,
            seed=actual_seed,
            octave=params.get("octave", 5),
            stepwise_bias=params.get("stepwise_bias", 0.7),
            leap_probability=params.get("leap_probability", 0.2),
        )

        # Create clip and notes
        clip = Clip(track_id=track.id, start_bar=0, length_bars=project.bars)
        self.session.add(clip)
        await self.session.flush()

        for event in events:
            note = Note(
                clip_id=clip.id,
                pitch=event["pitch"],
                velocity=event["velocity"],
                start_tick=event["start_tick"],
                duration_tick=event["duration_tick"],
            )
            self.session.add(note)

        # Record generation run
        run = GenerationRun(
            project_id=project_id,
            kind="melody",
            seed_used=actual_seed,
            params=params,
        )
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def _ensure_tracks(self, project_id: UUID) -> list[Track]:
        """Ensure all required tracks exist."""
        roles = ["drums", "chords", "bass", "melody"]
        channels = [9, 0, 1, 2]
        tracks = []

        for role, channel in zip(roles, channels):
            track = await self._get_or_create_track(project_id, role, channel)
            tracks.append(track)

        return tracks

    async def _get_or_create_track(
        self,
        project_id: UUID,
        role: str,
        channel: int,
    ) -> Track:
        """Get or create a track by role."""
        existing = await self._get_track_by_role(project_id, role)
        if existing:
            return existing

        track = Track(
            project_id=project_id,
            name=role.capitalize(),
            role=role,
            midi_channel=channel,
            midi_program=0,
        )
        self.session.add(track)
        await self.session.flush()
        return track

    async def _get_track_by_role(self, project_id: UUID, role: str) -> Track | None:
        """Get track by role."""
        result = await self.session.execute(
            select(Track).where(Track.project_id == project_id, Track.role == role)
        )
        return result.scalar_one_or_none()

    async def _clear_track_clips(self, track_id: UUID) -> None:
        """Clear all clips and notes for a track."""
        result = await self.session.execute(select(Clip).where(Clip.track_id == track_id))
        clips = list(result.scalars().all())
        for clip in clips:
            await self.session.delete(clip)
        await self.session.flush()
