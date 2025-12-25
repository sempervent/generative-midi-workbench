"""Note model."""

import uuid
from datetime import datetime

from sqlalchemy import Float, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from midinecromancer.db.base import Base


class Note(Base):
    """Note model representing a MIDI note event."""

    __tablename__ = "notes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    clip_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clips.id", ondelete="CASCADE"), nullable=False
    )
    pitch: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-127
    velocity: Mapped[int] = mapped_column(Integer, nullable=False, default=100)  # 1-127
    start_tick: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_tick: Mapped[int] = mapped_column(Integer, nullable=False)
    probability: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    clip: Mapped["Clip"] = relationship("Clip", back_populates="notes")

    __table_args__ = (Index("ix_notes_clip_start", "clip_id", "start_tick"),)
