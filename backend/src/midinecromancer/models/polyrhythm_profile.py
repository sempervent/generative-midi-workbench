"""Polyrhythm profile model."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from midinecromancer.db.base import Base


class PolyrhythmProfile(Base):
    """Polyrhythm profile defining a rhythmic cycle."""

    __tablename__ = "polyrhythm_profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    steps: Mapped[int] = mapped_column(Integer, nullable=False)  # Grid steps in cycle
    pulses: Mapped[int] = mapped_column(Integer, nullable=False)  # Number of onsets
    rotation: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # Rotation offset
    cycle_beats: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )  # Cycle length in beats
    swing: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 3), nullable=True
    )  # Swing amount (0.0-1.0)
    humanize_ms: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # Humanization in milliseconds
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    clips: Mapped[list["Clip"]] = relationship("Clip", back_populates="polyrhythm_profile")
