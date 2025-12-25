"""Project schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """Project creation schema."""

    name: str = Field(..., min_length=1, max_length=255)
    bpm: int = Field(default=120, ge=20, le=300)
    time_signature_num: int = Field(default=4, ge=1, le=32)
    time_signature_den: int = Field(default=4, ge=1, le=32)
    bars: int = Field(default=8, ge=1, le=256)
    key_tonic: str = Field(default="C", max_length=10)
    mode: str = Field(default="ionian", max_length=20)
    seed: int = Field(default=0)


class ProjectUpdate(BaseModel):
    """Project update schema."""

    name: str | None = Field(None, min_length=1, max_length=255)
    bpm: int | None = Field(None, ge=20, le=300)
    time_signature_num: int | None = Field(None, ge=1, le=32)
    time_signature_den: int | None = Field(None, ge=1, le=32)
    bars: int | None = Field(None, ge=1, le=256)
    key_tonic: str | None = Field(None, max_length=10)
    mode: str | None = Field(None, max_length=20)
    seed: int | None = None


class ProjectResponse(BaseModel):
    """Project response schema."""

    id: UUID
    name: str
    bpm: int
    time_signature_num: int
    time_signature_den: int
    bars: int
    key_tonic: str
    mode: str
    seed: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
