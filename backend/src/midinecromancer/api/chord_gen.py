"""Chord generation API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from midinecromancer.db.base import get_session
from midinecromancer.models.chord_event import ChordEvent
from midinecromancer.models.chord_gen_run import ChordGenRun, ChordGenSuggestion
from midinecromancer.models.clip import Clip
from midinecromancer.models.project import Project
from midinecromancer.music.chords_generate import generate_progression_candidates
from midinecromancer.music.chord_patterns import render_chord_event_to_notes
from midinecromancer.music.theory import PPQ

router = APIRouter()


class ChordGenRequest(BaseModel):
    """Request to generate chord progression candidates."""

    project_id: UUID
    clip_id: UUID | None = None
    bar_start: int = Field(..., ge=0)
    bar_end: int = Field(..., ge=1)
    seed: int = Field(default=0)
    params: dict = Field(default_factory=dict)
    locks: dict | None = None


class ChordGenResponse(BaseModel):
    """Response with run and suggestions."""

    run_id: UUID
    suggestions: list[dict]


class ChordSuggestionPreviewRequest(BaseModel):
    """Request to preview a suggestion."""

    bpm: int = Field(..., ge=1, le=300)
    time_signature_num: int = Field(default=4, ge=1, le=32)
    time_signature_den: int = Field(default=4, ge=1, le=32)


class ChordSuggestionApplyRequest(BaseModel):
    """Request to apply a suggestion."""

    clip_id: UUID
    replace_existing: bool = Field(default=True)


@router.post("/chords/generate/run", response_model=ChordGenResponse)
async def create_chord_gen_run(
    request: ChordGenRequest,
    session: AsyncSession = Depends(get_session),
) -> ChordGenResponse:
    """Generate chord progression candidates."""
    # Get project
    project = await session.get(Project, request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get clip if specified
    clip = None
    if request.clip_id:
        clip = await session.get(Clip, request.clip_id)
        if not clip:
            raise HTTPException(status_code=404, detail="Clip not found")

    # Create run
    run = ChordGenRun(
        project_id=request.project_id,
        clip_id=request.clip_id,
        bar_start=request.bar_start,
        bar_end=request.bar_end,
        seed=request.seed,
        params=request.params,
    )
    session.add(run)
    await session.flush()

    # Generate candidates
    context = {
        "tonic": project.key_tonic,
        "mode": project.mode,
        "bars": request.bar_end - request.bar_start,
        "time_signature_num": project.time_signature_num,
        "time_signature_den": project.time_signature_den,
    }

    candidates = generate_progression_candidates(
        context=context,
        params=request.params,
        locks=request.locks,
        seed=request.seed,
        run_id=run.id,
        num_candidates=5,
    )

    # Create suggestions
    suggestions_data = []
    for rank, candidate in enumerate(candidates):
        suggestion = ChordGenSuggestion(
            run_id=run.id,
            rank=rank,
            score=float(candidate.score),
            title=candidate.title,
            explanation=candidate.explanation,
            progression=candidate.progression,
            locks=request.locks,
        )
        session.add(suggestion)
        await session.flush()

        suggestions_data.append({
            "id": str(suggestion.id),
            "rank": rank,
            "score": float(candidate.score),
            "title": candidate.title,
            "explanation": candidate.explanation,
            "progression": candidate.progression,
        })

    await session.commit()

    return ChordGenResponse(run_id=run.id, suggestions=suggestions_data)


@router.get("/chords/generate/runs/{run_id}")
async def get_chord_gen_run(
    run_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get a chord generation run with suggestions."""
    run = await session.get(ChordGenRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    result = await session.execute(
        select(ChordGenSuggestion)
        .where(ChordGenSuggestion.run_id == run_id)
        .order_by(ChordGenSuggestion.rank)
    )
    suggestions = result.scalars().all()

    return {
        "id": str(run.id),
        "project_id": str(run.project_id),
        "clip_id": str(run.clip_id) if run.clip_id else None,
        "bar_start": run.bar_start,
        "bar_end": run.bar_end,
        "seed": run.seed,
        "params": run.params,
        "suggestions": [
            {
                "id": str(s.id),
                "rank": s.rank,
                "score": float(s.score),
                "title": s.title,
                "explanation": s.explanation,
                "progression": s.progression,
                "locks": s.locks,
            }
            for s in suggestions
        ],
    }


@router.post("/chords/generate/suggestions/{suggestion_id}/preview")
async def preview_chord_suggestion(
    suggestion_id: UUID,
    request: ChordSuggestionPreviewRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Preview a chord suggestion (returns rendered notes, no DB write)."""
    suggestion = await session.get(ChordGenSuggestion, suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    run = await session.get(ChordGenRun, suggestion.run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    project = await session.get(Project, run.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Calculate ticks per bar
    quarter_notes_per_bar = (request.time_signature_num * 4) / request.time_signature_den
    ticks_per_bar = int(quarter_notes_per_bar * PPQ)

    # Render progression to notes
    all_notes = []
    project_context = {
        "tonic": project.key_tonic,
        "mode": project.mode,
        "bpm": request.bpm,
        "time_signature_num": request.time_signature_num,
        "time_signature_den": request.time_signature_den,
    }

    for chord_data in suggestion.progression:
        # Create a temporary chord event for rendering
        from midinecromancer.models.chord_event import ChordEvent

        temp_chord = ChordEvent(
            id=UUID("00000000-0000-0000-0000-000000000000"),  # Dummy ID
            clip_id=run.clip_id or UUID("00000000-0000-0000-0000-000000000000"),
            start_tick=int(chord_data["start_bar"] * ticks_per_bar),
            duration_tick=int(chord_data["length_bars"] * ticks_per_bar),
            duration_beats=chord_data.get("duration_beats", chord_data["length_bars"] * 4),
            roman_numeral=chord_data["roman_numeral"],
            chord_name=chord_data["chord_name"],
            intensity=chord_data.get("intensity", 0.85),
            voicing=chord_data.get("voicing", "root"),
            inversion=chord_data.get("inversion", 0),
            pattern_type=chord_data.get("pattern_type", "block"),
            duration_gate=chord_data.get("duration_gate", 0.85),
            velocity_curve=chord_data.get("velocity_curve", "flat"),
            comp_pattern=chord_data.get("comp_pattern"),
            strum_direction=chord_data.get("strum_direction", "down"),
            strum_spread=chord_data.get("strum_spread", 1.0),
            retrigger=chord_data.get("retrigger", False),
            strum_beats=chord_data.get("strum_beats", 0.0),
            humanize_beats=chord_data.get("humanize_beats", 0.0),
            is_enabled=True,
            is_locked=False,
        )

        rendered_notes = render_chord_event_to_notes(
            temp_chord,
            project_context,
            run.seed,
        )

        all_notes.extend(rendered_notes)

    return {
        "suggestion_id": str(suggestion_id),
        "notes": all_notes,
        "chord_count": len(suggestion.progression),
    }


@router.post("/chords/generate/suggestions/{suggestion_id}/apply")
async def apply_chord_suggestion(
    suggestion_id: UUID,
    request: ChordSuggestionApplyRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Apply a chord suggestion to the project."""
    suggestion = await session.get(ChordGenSuggestion, suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    run = await session.get(ChordGenRun, suggestion.run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Get or create clip
    clip = await session.get(Clip, request.clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    project = await session.get(Project, run.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Calculate ticks per bar
    quarter_notes_per_bar = (project.time_signature_num * 4) / project.time_signature_den
    ticks_per_bar = int(quarter_notes_per_bar * PPQ)

    # Delete existing chord events in range if requested
    if request.replace_existing:
        result = await session.execute(
            select(ChordEvent)
            .where(ChordEvent.clip_id == request.clip_id)
            .where(ChordEvent.start_tick >= run.bar_start * ticks_per_bar)
            .where(ChordEvent.start_tick < run.bar_end * ticks_per_bar)
        )
        existing_chords = result.scalars().all()
        for chord in existing_chords:
            await session.delete(chord)

    # Create chord events from progression
    created_chords = []
    for chord_data in suggestion.progression:
        chord_event = ChordEvent(
            clip_id=request.clip_id,
            start_tick=int((run.bar_start + chord_data["start_bar"]) * ticks_per_bar),
            duration_tick=int(chord_data["length_bars"] * ticks_per_bar),
            duration_beats=chord_data.get("duration_beats", chord_data["length_bars"] * 4),
            roman_numeral=chord_data["roman_numeral"],
            chord_name=chord_data["chord_name"],
            intensity=chord_data.get("intensity", 0.85),
            voicing=chord_data.get("voicing", "root"),
            inversion=chord_data.get("inversion", 0),
            pattern_type=chord_data.get("pattern_type", "block"),
            duration_gate=chord_data.get("duration_gate", 0.85),
            velocity_curve=chord_data.get("velocity_curve", "flat"),
            comp_pattern=chord_data.get("comp_pattern"),
            strum_direction=chord_data.get("strum_direction", "down"),
            strum_spread=chord_data.get("strum_spread", 1.0),
            retrigger=chord_data.get("retrigger", False),
            strum_beats=chord_data.get("strum_beats", 0.0),
            humanize_beats=chord_data.get("humanize_beats", 0.0),
            is_enabled=True,
            is_locked=False,
        )
        session.add(chord_event)
        await session.flush()
        created_chords.append(str(chord_event.id))

    await session.commit()

    return {
        "suggestion_id": str(suggestion_id),
        "chords_created": len(created_chords),
        "chord_ids": created_chords,
    }

