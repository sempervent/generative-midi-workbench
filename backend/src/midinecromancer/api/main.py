"""Main API router."""

from fastapi import APIRouter

from .projects import router as projects_router
from .tracks import router as tracks_router
from .clips import router as clips_router
from .generation import router as generation_router
from .export import router as export_router
from .polyrhythms import router as polyrhythms_router
from .polyrhythm_lanes import router as polyrhythm_lanes_router
from .suggestions import router as suggestions_router

router = APIRouter()

router.include_router(projects_router, prefix="/projects", tags=["projects"])
router.include_router(tracks_router, prefix="/tracks", tags=["tracks"])
router.include_router(clips_router, prefix="/clips", tags=["clips"])
router.include_router(generation_router, prefix="/projects", tags=["generation"])
router.include_router(export_router, prefix="/projects", tags=["export"])
router.include_router(polyrhythms_router, prefix="/polyrhythms", tags=["polyrhythms"])
router.include_router(polyrhythm_lanes_router, prefix="/api/v1", tags=["polyrhythm-lanes"])
router.include_router(suggestions_router, prefix="", tags=["suggestions"])
