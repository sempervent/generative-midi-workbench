"""Generation request/response schemas."""

from typing import Any

from pydantic import BaseModel, Field


class GenerationRequest(BaseModel):
    """Generation request schema."""

    kind: str = Field(..., pattern="^(drums|chords|bass|melody|full)$")
    seed: int | None = None
    params: dict[str, Any] = Field(default_factory=dict)


class GenerationResponse(BaseModel):
    """Generation response schema."""

    success: bool
    message: str
    generation_run_id: str | None = None
