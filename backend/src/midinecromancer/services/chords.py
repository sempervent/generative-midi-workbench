"""Service for chord rendering operations."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from midinecromancer.music.chords_render import NoteEvent, render_chord_progression_to_notes
from midinecromancer.models.chord_event import ChordEvent
from midinecromancer.models.clip import Clip
from midinecromancer.models.note import Note
from midinecromancer.models.project import Project
from midinecromancer.models.track import Track
from midinecromancer.schemas.chord_projections import (
    ChordCommitRequest,
    ChordCommitResponse,
    ChordPreviewRequest,
    ChordPreviewResponse,
    NoteEventResponse,
)


class ChordService:
    """Service for chord rendering operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def preview_chords(self, request: ChordPreviewRequest) -> ChordPreviewResponse:
        """Preview chord rendering without committing."""
        # Get project
        result = await self.session.execute(select(Project).where(Project.id == request.project_id))
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError(f"Project {request.project_id} not found")

        # Get chord events based on source
        chord_events = []
        if request.progression_source == "existing":
            # Get existing chord events from project
            result = await self.session.execute(
                select(Track)
                .where(Track.project_id == request.project_id)
                .where(Track.role == "chords")
                .options(selectinload(Track.clips).selectinload(Clip.chord_events))
            )
            tracks = list(result.scalars().all())
            for track in tracks:
                for clip in track.clips:
                    for ce in clip.chord_events:
                        chord_events.append(
                            {
                                "start_tick": ce.start_tick,
                                "duration_tick": ce.duration_tick,
                                "roman_numeral": ce.roman_numeral,
                                "chord_name": ce.chord_name,
                            }
                        )
        elif request.progression_source.startswith("suggestion:"):
            # Get from suggestion (would need to implement suggestion retrieval)
            # For now, use inline if provided
            if request.chord_events:
                chord_events = request.chord_events
        elif request.progression_source == "inline":
            if request.chord_events:
                chord_events = request.chord_events

        if not chord_events:
            return ChordPreviewResponse(note_events=[], summary={})

        # Get seed
        seed = request.seed if request.seed is not None else project.seed

        # Build timing context
        timing_ctx = {
            "tonic": project.key_tonic,
            "mode": project.mode,
            "bpm": project.bpm,
            "time_signature_num": project.time_signature_num,
            "time_signature_den": project.time_signature_den,
        }

        # Render
        note_events = render_chord_progression_to_notes(
            chord_events,
            request.settings,
            seed,
            timing_ctx,
        )

        # Convert to response
        note_responses = [
            NoteEventResponse(
                pitch=e.pitch,
                start_tick=e.start_tick,
                duration_tick=e.duration_tick,
                velocity=e.velocity,
            )
            for e in note_events
        ]

        # Calculate summary
        pitches = [e.pitch for e in note_events]
        summary = {
            "voicing_stats": {
                "min_pitch": min(pitches) if pitches else 0,
                "max_pitch": max(pitches) if pitches else 0,
                "note_count": len(note_events),
            }
        }

        return ChordPreviewResponse(note_events=note_responses, summary=summary)

    async def commit_chords(self, request: ChordCommitRequest) -> ChordCommitResponse:
        """Commit chord rendering to clip notes."""
        # Get clip
        result = await self.session.execute(
            select(Clip)
            .where(Clip.id == request.clip_id)
            .options(selectinload(Clip.chord_events), selectinload(Clip.track))
        )
        clip = result.scalar_one_or_none()
        if not clip:
            raise ValueError(f"Clip {request.clip_id} not found")

        # Get project
        result = await self.session.execute(
            select(Project).where(Project.id == request.project_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError(f"Project {request.project_id} not found")

        # Get chord events from clip
        chord_events = []
        for ce in clip.chord_events:
            chord_events.append(
                {
                    "start_tick": ce.start_tick,
                    "duration_tick": ce.duration_tick,
                    "roman_numeral": ce.roman_numeral,
                    "chord_name": ce.chord_name,
                }
            )

        if not chord_events:
            return ChordCommitResponse(clip_id=request.clip_id, notes_created=0, notes_updated=0)

        # Get seed
        seed = request.seed if request.seed is not None else project.seed

        # Build timing context
        timing_ctx = {
            "tonic": project.key_tonic,
            "mode": project.mode,
            "bpm": project.bpm,
            "time_signature_num": project.time_signature_num,
            "time_signature_den": project.time_signature_den,
        }

        # Render
        note_events = render_chord_progression_to_notes(
            chord_events,
            request.settings,
            seed,
            timing_ctx,
        )

        # Clear existing notes in clip (if commit_key matches, skip)
        # For now, always clear and recreate
        existing_notes = [n for n in clip.notes]
        for note in existing_notes:
            await self.session.delete(note)

        # Create new notes
        notes_created = 0
        for event in note_events:
            note = Note(
                clip_id=clip.id,
                pitch=event.pitch,
                velocity=event.velocity,
                start_tick=event.start_tick,
                duration_tick=event.duration_tick,
                probability=1.0,
            )
            self.session.add(note)
            notes_created += 1

        await self.session.commit()

        return ChordCommitResponse(
            clip_id=request.clip_id,
            notes_created=notes_created,
            notes_updated=0,
        )
