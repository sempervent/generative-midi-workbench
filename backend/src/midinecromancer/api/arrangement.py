"""Arrangement endpoints for panel view."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from midinecromancer.db.base import get_session
from midinecromancer.services.arrangement import ArrangementService

router = APIRouter()


@router.get("/projects/{project_id}/arrangement/panel")
async def get_arrangement_panel(
    project_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get arrangement panel view model (lightweight, optimized for UI)."""
    service = ArrangementService(session)
    try:
        return await service.get_project_arrangement(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
