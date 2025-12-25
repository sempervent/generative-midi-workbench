"""Suggestion endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from midinecromancer.db.base import get_session
from midinecromancer.music.analysis import analyze_project
from midinecromancer.music.suggest import generate_all_suggestions
from midinecromancer.models.project import Project
from midinecromancer.models.suggestion import Suggestion
from midinecromancer.models.suggestion_run import SuggestionRun
from midinecromancer.models.track import Track
from midinecromancer.schemas.suggestion import (
    PreviewRequest,
    PreviewResponse,
    SuggestionCommitRequest,
    SuggestionCommitResponse,
    SuggestionRunCreate,
    SuggestionRunResponse,
    SuggestionResponse,
)
from midinecromancer.services.suggestions import SuggestionService

router = APIRouter()


@router.post("/suggestions/run", response_model=SuggestionRunResponse, status_code=201)
async def create_suggestion_run(
    data: SuggestionRunCreate,
    session: AsyncSession = Depends(get_session),
) -> SuggestionRunResponse:
    """Create a suggestion run and generate suggestions."""
    service = SuggestionService(session)
    try:
        run = await service.create_run_and_suggestions(
            project_id=data.project_id,
            seed=data.seed,
            params=data.params,
        )
        # Reload with suggestions
        result = await session.execute(
            select(SuggestionRun)
            .where(SuggestionRun.id == run.id)
            .options(selectinload(SuggestionRun.suggestions))
        )
        run = result.scalar_one()
        return SuggestionRunResponse.model_validate(run)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/suggestions/runs/{run_id}", response_model=SuggestionRunResponse)
async def get_suggestion_run(
    run_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> SuggestionRunResponse:
    """Get suggestion run with suggestions."""
    result = await session.execute(
        select(SuggestionRun)
        .where(SuggestionRun.id == run_id)
        .options(selectinload(SuggestionRun.suggestions))
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Suggestion run not found")
    return SuggestionRunResponse.model_validate(run)


@router.post("/suggestions/{suggestion_id}/commit", response_model=SuggestionCommitResponse)
async def commit_suggestion(
    suggestion_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> SuggestionCommitResponse:
    """Commit a suggestion to the project."""
    service = SuggestionService(session)
    try:
        commit = await service.commit_suggestion(suggestion_id)
        return SuggestionCommitResponse.model_validate(commit)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/suggestions/preview", response_model=PreviewResponse)
async def preview_suggestion(
    request: PreviewRequest,
    session: AsyncSession = Depends(get_session),
) -> PreviewResponse:
    """Preview a suggestion without persisting."""
    # Get project
    result = await session.execute(
        select(Project)
        .where(Project.id == request.project_id)
        .options(selectinload(Project.tracks).selectinload(Track.clips))
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get tracks with clips
    from midinecromancer.models.clip import Clip

    result = await session.execute(
        select(Track)
        .where(Track.project_id == request.project_id)
        .options(
            selectinload(Track.clips).selectinload(Clip.chord_events),
            selectinload(Track.clips).selectinload(Clip.notes),
        )
    )
    tracks = list(result.scalars().all())

    # Analyze
    from midinecromancer.music.analysis import analyze_project

    analysis = analyze_project(project, tracks)

    # Collect data
    chord_events = []
    for track in tracks:
        if track.role == "chords":
            for clip in track.clips:
                chord_events.extend(clip.chord_events)

    # Generate single suggestion of requested kind
    seed = request.seed if request.seed is not None else project.seed

    if request.kind == "harmony":
        from midinecromancer.music.suggest import generate_harmony_suggestions

        suggestions = generate_harmony_suggestions(
            analysis,
            request.project_id,
            seed,
            project.bars,
            project.time_signature_num,
            project.time_signature_den,
            project.bpm,
            chord_events,
            request.params.get("complexity", 0.5),
            request.params.get("tension", 0.5),
        )
    elif request.kind == "rhythm":
        from midinecromancer.music.suggest import generate_rhythm_suggestions

        suggestions = generate_rhythm_suggestions(
            analysis,
            request.project_id,
            seed,
            project.bars,
            project.time_signature_num,
            project.time_signature_den,
            project.bpm,
            None,
            request.params.get("density", 0.5),
        )
    elif request.kind == "melody":
        from midinecromancer.music.suggest import generate_melody_suggestions

        suggestions = generate_melody_suggestions(
            analysis,
            request.project_id,
            seed,
            project.bars,
            project.time_signature_num,
            project.time_signature_den,
            project.bpm,
            chord_events,
            request.params.get("complexity", 0.5),
        )
    else:
        raise HTTPException(status_code=400, detail=f"Invalid kind: {request.kind}")

    if not suggestions:
        raise HTTPException(status_code=404, detail="No suggestions generated")

    # Return first suggestion
    sug = suggestions[0]
    return PreviewResponse(
        explanation=sug.explanation,
        preview_events=[
            {
                "pitch": e["pitch"],
                "velocity": e["velocity"],
                "start_tick": e["start_tick"],
                "duration_tick": e["duration_tick"],
                "channel": e.get("channel", 0),
            }
            for e in sug.preview_events
        ],
    )
