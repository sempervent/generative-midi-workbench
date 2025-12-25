"""Service for suggestion operations."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from midinecromancer.music.analysis import analyze_project
from midinecromancer.music.suggest import generate_all_suggestions
from midinecromancer.models.chord_event import ChordEvent
from midinecromancer.models.clip import Clip
from midinecromancer.models.clip_polyrhythm_lane import ClipPolyrhythmLane
from midinecromancer.models.note import Note
from midinecromancer.models.project import Project
from midinecromancer.models.suggestion import Suggestion
from midinecromancer.models.suggestion_commit import SuggestionCommit
from midinecromancer.models.suggestion_run import SuggestionRun
from midinecromancer.models.track import Track


class SuggestionService:
    """Service for suggestion operations."""

    def __init__(self, session: AsyncSession):
        """Initialize service with database session."""
        self.session = session

    async def create_run_and_suggestions(
        self,
        project_id: UUID,
        seed: int | None = None,
        params: dict | None = None,
    ) -> SuggestionRun:
        """Create a suggestion run and generate suggestions.

        Args:
            project_id: Project ID
            seed: Optional seed (uses project seed if not provided)
            params: Optional parameters (complexity, tension, density)

        Returns:
            SuggestionRun with generated suggestions
        """
        # Get project with tracks
        result = await self.session.execute(
            select(Project)
            .where(Project.id == project_id)
            .options(
                selectinload(Project.tracks).selectinload(Track.clips).selectinload(Clip.notes)
            )
        )
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        actual_seed = seed if seed is not None else project.seed
        params = params or {}

        # Get tracks with all data
        result = await self.session.execute(
            select(Track)
            .where(Track.project_id == project_id)
            .options(
                selectinload(Track.clips).selectinload(Clip.notes),
                selectinload(Track.clips).selectinload(Clip.chord_events),
                selectinload(Track.clips).selectinload(Clip.polyrhythm_lanes),
            )
        )
        tracks = list(result.scalars().all())

        # Analyze project
        analysis = analyze_project(project, tracks)

        # Collect chord events and lanes
        chord_events = []
        lanes_data = []
        for track in tracks:
            if track.role == "chords":
                for clip in track.clips:
                    chord_events.extend(clip.chord_events)
            if track.role == "drums":
                for clip in track.clips:
                    if (
                        clip.grid_mode in ("polyrhythm", "polyrhythm_multi")
                        and clip.polyrhythm_lanes
                    ):
                        for lane in clip.polyrhythm_lanes:
                            lanes_data.append(
                                {
                                    "id": lane.id,
                                    "name": lane.lane_name,
                                    "steps": lane.polyrhythm_profile.steps
                                    if lane.polyrhythm_profile
                                    else 8,
                                    "pulses": lane.polyrhythm_profile.pulses
                                    if lane.polyrhythm_profile
                                    else 4,
                                    "rotation": lane.polyrhythm_profile.rotation
                                    if lane.polyrhythm_profile
                                    else 0,
                                }
                            )

        # Build context
        context = {
            "key": analysis.detected_key,
            "mode": analysis.detected_mode,
            "harmonic_rhythm": analysis.harmonic_rhythm,
            "rhythmic_density": analysis.rhythmic_density,
        }

        # Generate suggestions
        suggestions_data = generate_all_suggestions(
            analysis=analysis,
            project_id=project_id,
            project_seed=actual_seed,
            bars=project.bars,
            time_signature_num=project.time_signature_num,
            time_signature_den=project.time_signature_den,
            bpm=project.bpm,
            chord_events=chord_events,
            lanes=lanes_data if lanes_data else None,
            params=params,
        )

        # Create run
        run = SuggestionRun(
            project_id=project_id,
            seed=actual_seed,
            context_json=context,
            params_json=params,
        )
        self.session.add(run)
        await self.session.flush()

        # Create suggestions
        for sug_data in suggestions_data:
            suggestion = Suggestion(
                run_id=run.id,
                kind=sug_data.kind,
                title=sug_data.title,
                explanation=sug_data.explanation,
                score=sug_data.score,
                payload_json=sug_data.to_dict()["payload_json"],
            )
            self.session.add(suggestion)

        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def commit_suggestion(self, suggestion_id: UUID) -> SuggestionCommit:
        """Commit a suggestion to the project.

        Args:
            suggestion_id: Suggestion ID

        Returns:
            SuggestionCommit record
        """
        # Get suggestion
        suggestion = await self.session.get(Suggestion, suggestion_id)
        if not suggestion:
            raise ValueError(f"Suggestion {suggestion_id} not found")

        if suggestion.is_committed:
            raise ValueError("Suggestion already committed")

        commit_plan = suggestion.payload_json.get("commit_plan", {})
        action = commit_plan.get("action")

        created_ids = {"clips": [], "notes": [], "chord_events": []}

        # Get project and tracks
        run = await self.session.get(SuggestionRun, suggestion.run_id)
        project = await self.session.get(Project, run.project_id)

        result = await self.session.execute(select(Track).where(Track.project_id == run.project_id))
        tracks = list(result.scalars().all())

        if action == "create_chord_event":
            # Find or create chords track
            chords_track = next((t for t in tracks if t.role == "chords"), None)
            if not chords_track:
                from midinecromancer.models.track import Track

                chords_track = Track(
                    project_id=run.project_id,
                    name="Chords",
                    role="chords",
                    midi_channel=0,
                )
                self.session.add(chords_track)
                await self.session.flush()

            # Create clip and chord event
            clip = Clip(
                track_id=chords_track.id,
                start_bar=commit_plan["start_bar"],
                length_bars=commit_plan["length_bars"],
            )
            self.session.add(clip)
            await self.session.flush()
            created_ids["clips"].append(str(clip.id))

            from midinecromancer.models.chord_event import ChordEvent

            quarter_notes_per_bar = (project.time_signature_num * 4) / project.time_signature_den
            ticks_per_bar = int(quarter_notes_per_bar * 480)

            chord_event = ChordEvent(
                clip_id=clip.id,
                start_tick=0,
                duration_tick=commit_plan["length_bars"] * ticks_per_bar,
                roman_numeral=commit_plan["roman_numeral"],
                chord_name=commit_plan["chord_name"],
            )
            self.session.add(chord_event)
            await self.session.flush()
            created_ids["chord_events"].append(str(chord_event.id))

        elif action == "create_chord_events":
            # Similar to above but multiple events
            chords_track = next((t for t in tracks if t.role == "chords"), None)
            if not chords_track:
                from midinecromancer.models.track import Track

                chords_track = Track(
                    project_id=run.project_id,
                    name="Chords",
                    role="chords",
                    midi_channel=0,
                )
                self.session.add(chords_track)
                await self.session.flush()

            from midinecromancer.models.chord_event import ChordEvent

            quarter_notes_per_bar = (project.time_signature_num * 4) / project.time_signature_den
            ticks_per_bar = int(quarter_notes_per_bar * 480)

            for event_data in commit_plan["events"]:
                clip = Clip(
                    track_id=chords_track.id,
                    start_bar=event_data["start_bar"],
                    length_bars=event_data["length_bars"],
                )
                self.session.add(clip)
                await self.session.flush()
                created_ids["clips"].append(str(clip.id))

                chord_event = ChordEvent(
                    clip_id=clip.id,
                    start_tick=0,
                    duration_tick=event_data["length_bars"] * ticks_per_bar,
                    roman_numeral=event_data["roman_numeral"],
                    chord_name=event_data["chord_name"],
                )
                self.session.add(chord_event)
                await self.session.flush()
                created_ids["chord_events"].append(str(chord_event.id))

        elif action == "create_notes":
            # Find or create track
            track_role = commit_plan["track_role"]
            track = next((t for t in tracks if t.role == track_role), None)
            if not track:
                from midinecromancer.models.track import Track

                track = Track(
                    project_id=run.project_id,
                    name=track_role.capitalize(),
                    role=track_role,
                    midi_channel=0 if track_role != "drums" else 9,
                )
                self.session.add(track)
                await self.session.flush()

            # Create clip
            clip = Clip(
                track_id=track.id,
                start_bar=commit_plan.get("clip_start_bar", 0),
                length_bars=project.bars,
            )
            self.session.add(clip)
            await self.session.flush()
            created_ids["clips"].append(str(clip.id))

            # Create notes
            for note_data in commit_plan["notes"]:
                note = Note(
                    clip_id=clip.id,
                    pitch=note_data["pitch"],
                    velocity=note_data["velocity"],
                    start_tick=note_data["start_tick"],
                    duration_tick=note_data["duration_tick"],
                )
                self.session.add(note)
                await self.session.flush()
                created_ids["notes"].append(str(note.id))

        elif action == "append_notes":
            # Append to existing clip
            track_role = commit_plan["track_role"]
            track = next((t for t in tracks if t.role == track_role), None)
            if not track:
                raise ValueError(f"Track with role {track_role} not found")

            # Find or create clip
            clip_start_bar = commit_plan.get("clip_start_bar", 0)
            clip = next(
                (c for c in track.clips if c.start_bar == clip_start_bar),
                None,
            )
            if not clip:
                clip = Clip(
                    track_id=track.id,
                    start_bar=clip_start_bar,
                    length_bars=project.bars,
                )
                self.session.add(clip)
                await self.session.flush()
                created_ids["clips"].append(str(clip.id))

            # Add notes
            for note_data in commit_plan["notes"]:
                note = Note(
                    clip_id=clip.id,
                    pitch=note_data["pitch"],
                    velocity=note_data["velocity"],
                    start_tick=note_data["start_tick"],
                    duration_tick=note_data["duration_tick"],
                )
                self.session.add(note)
                await self.session.flush()
                created_ids["notes"].append(str(note.id))

        # Mark suggestion as committed
        from datetime import datetime

        suggestion.is_committed = True
        suggestion.committed_at = datetime.utcnow()

        # Create commit record
        commit = SuggestionCommit(
            suggestion_id=suggestion_id,
            commit_json=created_ids,
        )
        self.session.add(commit)

        await self.session.commit()
        await self.session.refresh(commit)
        return commit
