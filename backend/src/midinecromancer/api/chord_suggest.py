"""Chord suggestion endpoint for getting contextual chord suggestions."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from midinecromancer.db.base import get_session
from midinecromancer.models.project import Project
from midinecromancer.music.chords_generate import generate_progression_candidates

router = APIRouter()


class ChordSuggestRequest(BaseModel):
    """Request for chord suggestions."""

    project_id: UUID
    context_bar: int = Field(default=0, ge=0)  # Bar position for context
    num_suggestions: int = Field(default=8, ge=1, le=20)
    seed: int | None = None
    style: str = Field(default="rap_dark")  # rap_dark, rap_bright, neo_soul, trap_minimal, boom_bap, cinematic, ambient
    tension: float = Field(default=0.5, ge=0, le=1)
    cadence_bias: float = Field(default=0.5, ge=0, le=1)
    include_borrowed: bool = Field(default=False)
    include_secondary_dominants: bool = Field(default=False)
    include_chromatic: bool = Field(default=False)


class ChordSuggestion(BaseModel):
    """A single chord suggestion."""

    roman_numeral: str
    chord_name: str
    reason: str  # "next_chord", "cadence", "borrowed_color", "tritone_spice", etc.
    score: float
    explanation: str | None = None


class ChordSuggestResponse(BaseModel):
    """Response with chord suggestions."""

    suggestions: list[ChordSuggestion]
    context_key: str
    context_mode: str


@router.post("/chords/suggest", response_model=ChordSuggestResponse)
async def suggest_chords(
    request: ChordSuggestRequest,
    session: AsyncSession = Depends(get_session),
) -> ChordSuggestResponse:
    """Get contextual chord suggestions for a project."""
    # Get project
    project = await session.get(Project, request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Use project seed if not provided
    seed = request.seed if request.seed is not None else project.seed

    # Generate suggestions based on context
    context = {
        "tonic": project.key_tonic,
        "mode": project.mode,
        "bars": 1,  # Single bar context
        "time_signature_num": project.time_signature_num,
        "time_signature_den": project.time_signature_den,
    }

    params = {
        "style": request.style,
        "tension": request.tension,
        "cadence_bias": request.cadence_bias,
        "include_borrowed": request.include_borrowed,
        "include_secondary_dominants": request.include_secondary_dominants,
        "include_chromatic": request.include_chromatic,
    }

    # Generate candidates
    candidates = generate_progression_candidates(
        context=context,
        params=params,
        locks=None,
        seed=seed,
        run_id=None,  # No run needed for suggestions
        num_candidates=request.num_suggestions,
    )

    # Convert to suggestion format
    suggestions = []
    for i, candidate in enumerate(candidates):
        # Get first chord from progression as the suggestion
        if candidate.progression:
            first_chord = candidate.progression[0]
            suggestions.append(
                ChordSuggestion(
                    roman_numeral=first_chord.get("roman_numeral", "I"),
                    chord_name=first_chord.get("chord_name", "C"),
                    reason=candidate.title or "next_chord",
                    score=float(candidate.score),
                    explanation=candidate.explanation,
                )
            )

    return ChordSuggestResponse(
        suggestions=suggestions,
        context_key=project.key_tonic,
        context_mode=project.mode,
    )

