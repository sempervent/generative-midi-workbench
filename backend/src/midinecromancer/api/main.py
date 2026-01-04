"""Main API router."""

from fastapi import APIRouter

from .arrangement import router as arrangement_router
from .drum_maps import router as drum_maps_router
from .chord_events import router as chord_events_router
from .chord_gen import router as chord_gen_router
from .chord_projections import router as chord_projections_router
from .chords import router as chords_router
from .clips import router as clips_router
from .export import router as export_router
from .generation import router as generation_router
from .polyrhythm_lanes import router as polyrhythm_lanes_router
from .polyrhythms import router as polyrhythms_router
from .projects import router as projects_router
from .segments import router as segments_router
from .suggestions import router as suggestions_router
from .theory import router as theory_router
from .tracks import router as tracks_router
from .chord_insert import router as chord_insert_router
from .chord_suggest import router as chord_suggest_router

router = APIRouter()

router.include_router(arrangement_router, prefix="", tags=["arrangement"])
router.include_router(projects_router, prefix="/projects", tags=["projects"])
router.include_router(tracks_router, prefix="/tracks", tags=["tracks"])
router.include_router(clips_router, prefix="/clips", tags=["clips"])
router.include_router(generation_router, prefix="/projects", tags=["generation"])
router.include_router(export_router, prefix="/projects", tags=["export"])
router.include_router(polyrhythms_router, prefix="/polyrhythms", tags=["polyrhythms"])
router.include_router(polyrhythm_lanes_router, prefix="/api/v1", tags=["polyrhythm-lanes"])
router.include_router(suggestions_router, prefix="", tags=["suggestions"])
router.include_router(
    chord_projections_router, prefix="/chord-projections", tags=["chord-projections"]
)
router.include_router(chords_router, prefix="/chords", tags=["chords"])
router.include_router(chord_gen_router, prefix="", tags=["chord-generation"])
router.include_router(chord_events_router, prefix="", tags=["chord-events"])
router.include_router(drum_maps_router, prefix="/drum-maps", tags=["drum-maps"])
router.include_router(segments_router, prefix="", tags=["segments"])
router.include_router(theory_router, prefix="", tags=["theory"])
router.include_router(chord_insert_router, prefix="", tags=["chord-insert"])
router.include_router(chord_suggest_router, prefix="", tags=["chord-suggest"])
