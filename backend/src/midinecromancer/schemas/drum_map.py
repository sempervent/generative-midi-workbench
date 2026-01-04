"""Drum map profile schemas."""

from uuid import UUID

from pydantic import BaseModel, Field


class DrumMapProfileBase(BaseModel):
    """Base drum map profile schema."""

    name: str = Field(..., description="Profile name")
    kick_note: int = Field(36, ge=0, le=127, description="MIDI note for kick")
    snare_note: int = Field(38, ge=0, le=127, description="MIDI note for snare")
    clap_note: int = Field(39, ge=0, le=127, description="MIDI note for clap")
    closed_hat_note: int = Field(42, ge=0, le=127, description="MIDI note for closed hi-hat")
    open_hat_note: int = Field(46, ge=0, le=127, description="MIDI note for open hi-hat")
    rim_note: int = Field(37, ge=0, le=127, description="MIDI note for rim shot")
    perc_notes: list[int] | None = Field(None, description="Additional percussion notes")


class DrumMapProfileCreate(DrumMapProfileBase):
    """Drum map profile creation schema."""

    pass


class DrumMapProfileResponse(DrumMapProfileBase):
    """Drum map profile response schema."""

    id: UUID

    class Config:
        from_attributes = True
