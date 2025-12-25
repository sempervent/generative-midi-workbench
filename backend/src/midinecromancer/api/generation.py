"""Generation endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from midinecromancer.db.base import get_session
from midinecromancer.schemas.generation import GenerationRequest, GenerationResponse
from midinecromancer.services.generation import GenerationService

router = APIRouter()


@router.post("/{project_id}/generate/full", response_model=GenerationResponse)
async def generate_full(
    project_id: UUID,
    request: GenerationRequest,
    session: AsyncSession = Depends(get_session),
) -> GenerationResponse:
    """Generate full arrangement."""
    if request.kind != "full":
        raise HTTPException(
            status_code=400, detail="Use /generate/full endpoint for full generation"
        )

    service = GenerationService(session)
    try:
        run = await service.generate_full(project_id, request.seed, request.params)
        return GenerationResponse(
            success=True,
            message="Full arrangement generated successfully",
            generation_run_id=str(run.id),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{project_id}/generate/drums", response_model=GenerationResponse)
async def generate_drums(
    project_id: UUID,
    request: GenerationRequest,
    session: AsyncSession = Depends(get_session),
) -> GenerationResponse:
    """Generate drum pattern."""
    if request.kind != "drums":
        raise HTTPException(
            status_code=400, detail="Use /generate/drums endpoint for drums generation"
        )

    service = GenerationService(session)
    try:
        run = await service.generate_drums(project_id, request.seed, request.params)
        return GenerationResponse(
            success=True,
            message="Drum pattern generated successfully",
            generation_run_id=str(run.id),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{project_id}/generate/chords", response_model=GenerationResponse)
async def generate_chords(
    project_id: UUID,
    request: GenerationRequest,
    session: AsyncSession = Depends(get_session),
) -> GenerationResponse:
    """Generate chord progression."""
    if request.kind != "chords":
        raise HTTPException(
            status_code=400, detail="Use /generate/chords endpoint for chords generation"
        )

    service = GenerationService(session)
    try:
        run = await service.generate_chords(project_id, request.seed, request.params)
        return GenerationResponse(
            success=True,
            message="Chord progression generated successfully",
            generation_run_id=str(run.id),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{project_id}/generate/bass", response_model=GenerationResponse)
async def generate_bass(
    project_id: UUID,
    request: GenerationRequest,
    session: AsyncSession = Depends(get_session),
) -> GenerationResponse:
    """Generate bassline."""
    if request.kind != "bass":
        raise HTTPException(
            status_code=400, detail="Use /generate/bass endpoint for bass generation"
        )

    service = GenerationService(session)
    try:
        run = await service.generate_bass(project_id, request.seed, request.params)
        return GenerationResponse(
            success=True,
            message="Bassline generated successfully",
            generation_run_id=str(run.id),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{project_id}/generate/melody", response_model=GenerationResponse)
async def generate_melody(
    project_id: UUID,
    request: GenerationRequest,
    session: AsyncSession = Depends(get_session),
) -> GenerationResponse:
    """Generate melody."""
    if request.kind != "melody":
        raise HTTPException(
            status_code=400, detail="Use /generate/melody endpoint for melody generation"
        )

    service = GenerationService(session)
    try:
        run = await service.generate_melody(project_id, request.seed, request.params)
        return GenerationResponse(
            success=True,
            message="Melody generated successfully",
            generation_run_id=str(run.id),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
