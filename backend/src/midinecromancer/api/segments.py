"""Segment generation endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from midinecromancer.db.base import get_session
from midinecromancer.schemas.segment import SegmentCreateRequest, SegmentGenerateResponse
from midinecromancer.services.segments import SegmentService

router = APIRouter()


@router.post("/segments/generate", response_model=SegmentGenerateResponse)
async def generate_segments(
    request: SegmentCreateRequest,
    session: AsyncSession = Depends(get_session),
) -> SegmentGenerateResponse:
    """Generate segments (clips with content).

    If preview=true, returns preview data without DB writes.
    If preview=false, creates clips and persists to DB.
    """
    service = SegmentService(session)
    try:
        result = await service.generate_segments(request)
        if not request.preview:
            await session.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
