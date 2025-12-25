"""Chord event model."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, String
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
    roman_numeral: Mapped[str] = mapped_column(String(20), nullable=False)  # "I", "vi", "V7", etc.
    chord_name: Mapped[str] = mapped_column(String(50), nullable=False)  # "Am", "G7", etc.
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    clip: Mapped["Clip"] = relationship("Clip", back_populates="chord_events")

    __table_args__ = (Index("ix_chord_events_clip_start", "clip_id", "start_tick"),)
