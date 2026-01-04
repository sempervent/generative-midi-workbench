"""Clip model."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from midinecromancer.db.base import Base


class Clip(Base):
    """Clip model representing a sequence of notes/chords."""

    __tablename__ = "clips"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    track_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False
    )
    start_bar: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    length_bars: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    grid_mode: Mapped[str] = mapped_column(
        String(20), nullable=False, default="standard"
    )  # standard|euclidean|polyrhythm|polyrhythm_multi
    polyrhythm_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("polyrhythm_profiles.id", ondelete="SET NULL"), nullable=True
    )  # Legacy: deprecated in favor of lanes, kept for backward compatibility
    drum_map_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("drum_map_profiles.id", ondelete="SET NULL"), nullable=True
    )
    is_muted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_soloed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    start_offset_ticks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    intensity: Mapped[float] = mapped_column(
        Float, nullable=False, default=1.0, server_default="1.0"
    )
    params: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    track: Mapped["Track"] = relationship("Track", back_populates="clips")
    notes: Mapped[list["Note"]] = relationship(
        "Note", back_populates="clip", cascade="all, delete-orphan"
    )
    chord_events: Mapped[list["ChordEvent"]] = relationship(
        "ChordEvent",
        back_populates="clip",
        cascade="all, delete-orphan",
    )
    polyrhythm_profile: Mapped["PolyrhythmProfile | None"] = relationship(
        "PolyrhythmProfile", back_populates="clips"
    )
    polyrhythm_lanes: Mapped[list["ClipPolyrhythmLane"]] = relationship(
        "ClipPolyrhythmLane",
        back_populates="clip",
        cascade="all, delete-orphan",
        order_by="ClipPolyrhythmLane.order_index",
    )
    chord_settings: Mapped["ClipChordSettings | None"] = relationship(
        "ClipChordSettings", back_populates="clip", uselist=False, cascade="all, delete-orphan"
    )
    drum_map_profile: Mapped["DrumMapProfile | None"] = relationship(
        "DrumMapProfile", back_populates="clips"
    )
