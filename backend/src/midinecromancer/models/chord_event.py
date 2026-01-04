"""Chord event model."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from midinecromancer.db.base import Base


class ChordEvent(Base):
    """Chord event model representing a chord in a clip."""

    __tablename__ = "chord_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    clip_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clips.id", ondelete="CASCADE"), nullable=False
    )
    start_tick: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_tick: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_beats: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("4.0")
    )
    roman_numeral: Mapped[str] = mapped_column(String(20), nullable=False)  # "I", "vi", "V7", etc.
    chord_name: Mapped[str] = mapped_column(String(50), nullable=False)  # "Am", "G7", etc.
    intensity: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0.85")
    )
    voicing: Mapped[str] = mapped_column(String(20), nullable=False, default="root")
    inversion: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    strum_ms: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )  # Deprecated, use strum_beats
    humanize_ms: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )  # Deprecated, use humanize_beats
    strum_beats: Mapped[Decimal] = mapped_column(
        Numeric(5, 3), nullable=False, default=Decimal("0.0")
    )
    humanize_beats: Mapped[Decimal] = mapped_column(
        Numeric(5, 3), nullable=False, default=Decimal("0.0")
    )
    pattern_type: Mapped[str] = mapped_column(String(20), nullable=False, default="block")
    duration_gate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0.85")
    )
    velocity_curve: Mapped[str] = mapped_column(String(20), nullable=False, default="flat")
    comp_pattern: Mapped[dict | None] = mapped_column(postgresql.JSONB, nullable=True)
    strum_direction: Mapped[str] = mapped_column(String(20), nullable=False, default="down")
    strum_spread: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("1.0")
    )
    retrigger: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    offset_beats: Mapped[Decimal] = mapped_column(
        Numeric(5, 3), nullable=False, default=Decimal("0.0")
    )
    strum_curve: Mapped[str] = mapped_column(String(20), nullable=False, default="linear")
    hit_params: Mapped[dict | None] = mapped_column(postgresql.JSONB, nullable=True)
    velocity_jitter: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    timing_jitter_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    grid_quantum: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    clip: Mapped["Clip"] = relationship("Clip", back_populates="chord_events")

    __table_args__ = (
        Index("ix_chord_events_clip_start", "clip_id", "start_tick"),
        Index("ix_chord_events_enabled", "is_enabled"),
    )
