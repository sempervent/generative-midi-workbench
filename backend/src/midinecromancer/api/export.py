"""Export endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from midinecromancer.db.base import get_session
from midinecromancer.midi.export import export_project_to_midi
from midinecromancer.midi.export_zip import export_project_to_zip, generate_zip_filename
from midinecromancer.models.clip import Clip
from midinecromancer.models.project import Project
from midinecromancer.models.track import Track
from midinecromancer.schemas.arrangement import ArrangementResponse
from midinecromancer.services.polyrhythm import render_clip_lanes_to_notes

router = APIRouter()


@router.get("/{project_id}/export/midi")
async def export_midi(
    project_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Export project as Standard MIDI File."""
    # Get project
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get tracks with all data
    result = await session.execute(
        select(Track)
        .where(Track.project_id == project_id)
        .options(
            selectinload(Track.clips).selectinload(Clip.notes),
            selectinload(Track.clips).selectinload(Clip.chord_events),
            selectinload(Track.clips).selectinload(Clip.polyrhythm_lanes),
        )
        .order_by(Track.created_at)
    )
    tracks = list(result.scalars().all())

    # Render polyrhythm lanes to notes for clips that use lanes
    for track in tracks:
        for clip in track.clips:
            if clip.grid_mode in ("polyrhythm", "polyrhythm_multi"):
                # Render lanes to notes (temporary, for export only)
                lane_notes = await render_clip_lanes_to_notes(clip, project, session)
                # Add to clip's notes list for export
                clip.notes.extend(lane_notes)

    # Export to MIDI
    midi_bytes = export_project_to_midi(project, tracks)

    return Response(
        content=midi_bytes,
        media_type="audio/midi",
        headers={"Content-Disposition": f'attachment; filename="{project.name}.mid"'},
    )


@router.get("/{project_id}/export/zip")
async def export_zip(
    project_id: UUID,
    split_by: str = Query(default="track", pattern="^(track|clip)$"),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Export project as ZIP containing per-part MIDI files.

    Args:
        project_id: Project ID
        split_by: How to split parts ("track" or "clip")
        session: Database session

    Returns:
        ZIP file response
    """
    # Get project
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get tracks with all data
    result = await session.execute(
        select(Track)
        .where(Track.project_id == project_id)
        .options(
            selectinload(Track.clips).selectinload(Clip.notes),
            selectinload(Track.clips).selectinload(Clip.chord_events),
            selectinload(Track.clips).selectinload(Clip.polyrhythm_lanes),
        )
        .order_by(Track.created_at)
    )
    tracks = list(result.scalars().all())

    # Render polyrhythm lanes to notes for clips that use lanes
    for track in tracks:
        for clip in track.clips:
            if clip.grid_mode in ("polyrhythm", "polyrhythm_multi"):
                # Render lanes to notes (temporary, for export only)
                lane_notes = await render_clip_lanes_to_notes(clip, project, session)
                # Add to clip's notes list for export
                clip.notes.extend(lane_notes)

    # Export to ZIP
    zip_bytes = export_project_to_zip(project, tracks, split_by=split_by)  # type: ignore
    zip_filename = generate_zip_filename(project.name)

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{zip_filename}"'},
    )


@router.get("/{project_id}/export/json", response_model=ArrangementResponse)
async def export_json(
    project_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> ArrangementResponse:
    """Export project as JSON arrangement."""
    from midinecromancer.api.projects import get_arrangement

    return await get_arrangement(project_id, session)
