"""Pydantic schemas for API requests and responses."""

from .project import ProjectCreate, ProjectUpdate, ProjectResponse
from .track import TrackCreate, TrackResponse
from .clip import ClipCreate, ClipResponse
from .note import NoteCreate, NoteResponse
from .chord_event import ChordEventResponse
from .generation import GenerationRequest, GenerationResponse
from .arrangement import ArrangementResponse

__all__ = [
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "TrackCreate",
    "TrackResponse",
    "ClipCreate",
    "ClipResponse",
    "NoteCreate",
    "NoteResponse",
    "ChordEventResponse",
    "GenerationRequest",
    "GenerationResponse",
    "ArrangementResponse",
]
