"""Project endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from midinecromancer.db.base import get_session
from midinecromancer.schemas.arrangement import ArrangementResponse
from midinecromancer.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from midinecromancer.services.project import ProjectService

router = APIRouter()


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreate,
    session: AsyncSession = Depends(get_session),
) -> ProjectResponse:
    """Create a new project."""
    service = ProjectService(session)
    project = await service.create(data)
    return ProjectResponse.model_validate(project)


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    session: AsyncSession = Depends(get_session),
) -> list[ProjectResponse]:
    """List all projects."""
    service = ProjectService(session)
    projects = await service.list()
    return [ProjectResponse.model_validate(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> ProjectResponse:
    """Get project by ID."""
    service = ProjectService(session)
    project = await service.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    session: AsyncSession = Depends(get_session),
) -> ProjectResponse:
    """Update project."""
    service = ProjectService(session)
    project = await service.update(project_id, data)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse.model_validate(project)


@router.get("/{project_id}/arrangement", response_model=ArrangementResponse)
async def get_arrangement(
    project_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> ArrangementResponse:
    """Get full arrangement (project + tracks + clips + notes + chords)."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from midinecromancer.models.clip import Clip
    from midinecromancer.models.chord_event import ChordEvent
    from midinecromancer.models.note import Note
    from midinecromancer.models.project import Project
    from midinecromancer.models.track import Track

    # Get project
    result = await session.execute(
        select(Project).where(Project.id == project_id).options(selectinload(Project.tracks))
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get tracks with clips
    result = await session.execute(
        select(Track)
        .where(Track.project_id == project_id)
        .options(
            selectinload(Track.clips).selectinload(Clip.notes),
            selectinload(Track.clips).selectinload(Clip.chord_events),
        )
        .order_by(Track.created_at)
    )
    tracks = list(result.scalars().all())

    # Build response
    from midinecromancer.schemas.arrangement import (
        ChordEventInArrangement,
        ClipInArrangement,
        NoteInArrangement,
        TrackInArrangement,
    )

    track_responses = []
    for track in tracks:
        clip_responses = []
        for clip in track.clips:
            note_responses = [
                NoteInArrangement.model_validate(note)
                for note in sorted(clip.notes, key=lambda n: n.start_tick)
            ]
            chord_responses = [
                ChordEventInArrangement.model_validate(ce)
                for ce in sorted(clip.chord_events, key=lambda ce: ce.start_tick)
            ]
            clip_responses.append(
                ClipInArrangement(
                    id=clip.id,
                    start_bar=clip.start_bar,
                    length_bars=clip.length_bars,
                    is_muted=clip.is_muted,
                    is_soloed=clip.is_soloed,
                    start_offset_ticks=clip.start_offset_ticks,
                    notes=note_responses,
                    chord_events=chord_responses,
                )
            )
        track_responses.append(
            TrackInArrangement(
                id=track.id,
                name=track.name,
                role=track.role,
                midi_channel=track.midi_channel,
                midi_program=track.midi_program,
                is_muted=track.is_muted,
                is_soloed=track.is_soloed,
                start_offset_ticks=track.start_offset_ticks,
                clips=clip_responses,
            )
        )

    return ArrangementResponse(
        project_id=project.id,
        project_name=project.name,
        bpm=project.bpm,
        time_signature_num=project.time_signature_num,
        time_signature_den=project.time_signature_den,
        bars=project.bars,
        key_tonic=project.key_tonic,
        mode=project.mode,
        seed=project.seed,
        tracks=track_responses,
    )
