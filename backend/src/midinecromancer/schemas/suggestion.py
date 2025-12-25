"""Suggestion schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class SuggestionRunCreate(BaseModel):
    """Suggestion run creation schema."""

    project_id: UUID
    seed: int | None = None
    params: dict = Field(default_factory=dict)


class SuggestionParams(BaseModel):
    """Suggestion parameters."""

    complexity: float = Field(default=0.5, ge=0.0, le=1.0)
    tension: float = Field(default=0.5, ge=0.0, le=1.0)
    density: float = Field(default=0.5, ge=0.0, le=1.0)


class PreviewEventResponse(BaseModel):
    """Preview event in response."""

    pitch: int
    velocity: int
    start_tick: int
    duration_tick: int
    channel: int


class SuggestionResponse(BaseModel):
    """Suggestion response schema."""

    id: UUID
    run_id: UUID
    kind: str
    title: str
    explanation: str
    score: float
    payload_json: dict
    is_committed: bool
    committed_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class SuggestionRunResponse(BaseModel):
    """Suggestion run response schema."""

    id: UUID
    project_id: UUID
    seed: int
    context_json: dict
    params_json: dict
    created_at: datetime
    suggestions: list[SuggestionResponse]

    class Config:
        from_attributes = True


class SuggestionCommitRequest(BaseModel):
    """Suggestion commit request schema."""

    suggestion_id: UUID


class SuggestionCommitResponse(BaseModel):
    """Suggestion commit response schema."""

    id: UUID
    suggestion_id: UUID
    commit_json: dict
    created_at: datetime

    class Config:
        from_attributes = True


class PreviewRequest(BaseModel):
    """Preview request schema."""

    project_id: UUID
    kind: str = Field(..., pattern="^(harmony|rhythm|melody)$")
    seed: int | None = None
    params: dict = Field(default_factory=dict)


class PreviewResponse(BaseModel):
    """Preview response schema."""

    explanation: str
    preview_events: list[PreviewEventResponse]
