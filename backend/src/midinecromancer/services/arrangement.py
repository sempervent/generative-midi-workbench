"""Arrangement service for unified arrangement view model."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from midinecromancer.models.clip import Clip
from midinecromancer.models.project import Project
from midinecromancer.models.track import Track


class ArrangementService:
    """Service for building arrangement view models."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_project_arrangement(self, project_id: UUID) -> dict:
        """Get unified arrangement view model for a project.

        Returns a structure optimized for the Arrangement panel:
        - Project timing info
        - Track lanes (beats/chords/bass/melody) with ordered segments
        - Each segment includes minimal info for card rendering
        """
        # Load project
        result = await self.session.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Load tracks with clips in a single query (eager load)
        result = await self.session.execute(
            select(Track)
            .where(Track.project_id == project_id)
            .options(
                selectinload(Track.clips).selectinload(Clip.chord_events),
                selectinload(Track.clips).selectinload(Clip.polyrhythm_lanes),
                selectinload(Track.clips).selectinload(Clip.chord_settings),
            )
            .order_by(Track.created_at)
        )
        tracks = list(result.scalars().all())

        # Define track order: Beats, Chords, Bass, Melody (then others)
        role_order = {"drums": 0, "chords": 1, "bass": 2, "melody": 3}

        # Sort tracks by role order
        sorted_tracks = sorted(tracks, key=lambda t: role_order.get(t.role, 999))

        # Build lanes (one per track role)
        lanes = []
        for track in sorted_tracks:
            # Sort clips by start_bar then created_at
            sorted_clips = sorted(track.clips, key=lambda c: (c.start_bar, c.created_at))

            # Build segments (one per clip)
            segments = []
            for clip in sorted_clips:
                # Compute card payload
                segment = {
                    "id": str(clip.id),
                    "kind": track.role,  # beats/chords/bass/melody
                    "name": track.name,
                    "start_bar": clip.start_bar,
                    "length_bars": clip.length_bars,
                    "intensity": getattr(clip, "intensity", 1.0),
                    "mute": clip.is_muted or track.is_muted,  # clip-level override
                    "is_soloed": clip.is_soloed or track.is_soloed,  # clip-level override
                    "seed": project.seed,  # Use project seed by default
                    "params": getattr(clip, "params", {}),
                }

                # Add kind-specific info
                if track.role == "chords":
                    # Chord events summary
                    segment["chord_count"] = len(clip.chord_events)
                    if clip.chord_events:
                        # Get chord names for summary
                        chord_names = [ce.chord_name for ce in clip.chord_events]
                        segment["chord_summary"] = ", ".join(chord_names[:3])
                        if len(chord_names) > 3:
                            segment["chord_summary"] += "..."
                    else:
                        segment["chord_summary"] = "No chords"

                    # Voicing params if available
                    if clip.chord_settings:
                        segment["voicing_params"] = {
                            "gate_pct": clip.chord_settings.gate_pct,
                            "strum_ms": clip.chord_settings.strum_ms,
                            "humanize_ms": clip.chord_settings.humanize_ms,
                        }

                elif track.role == "drums" and clip.grid_mode in ("polyrhythm", "polyrhythm_multi"):
                    # Polyrhythm lanes summary
                    segment["lane_count"] = len(clip.polyrhythm_lanes)
                    if clip.polyrhythm_lanes:
                        # Get lane names for summary
                        lane_names = [lane.lane_name for lane in clip.polyrhythm_lanes]
                        segment["lane_summary"] = ", ".join(lane_names[:3])
                        if len(lane_names) > 3:
                            segment["lane_summary"] += "..."
                    else:
                        segment["lane_summary"] = "No lanes"

                segments.append(segment)

            lanes.append(
                {
                    "kind": track.role,
                    "name": track.name,
                    "track_id": str(track.id),
                    "segments": segments,
                }
            )

        return {
            "project_id": str(project.id),
            "project_name": project.name,
            "bpm": project.bpm,
            "bars": project.bars,
            "time_signature_num": project.time_signature_num,
            "time_signature_den": project.time_signature_den,
            "lanes": lanes,
        }
