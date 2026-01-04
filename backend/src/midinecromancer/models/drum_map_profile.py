"""Drum map profile model."""

import uuid
from datetime import datetime

from sqlalchemy import ARRAY, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from midinecromancer.db.base import Base


class DrumMapProfile(Base):
    """Drum map profile defining MIDI note mappings for drum sounds."""

    __tablename__ = "drum_map_profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    kick_note: Mapped[int] = mapped_column(Integer, nullable=False, default=36, server_default="36")
    snare_note: Mapped[int] = mapped_column(
        Integer, nullable=False, default=38, server_default="38"
    )
    clap_note: Mapped[int] = mapped_column(Integer, nullable=False, default=39, server_default="39")
    closed_hat_note: Mapped[int] = mapped_column(
        Integer, nullable=False, default=42, server_default="42"
    )
    open_hat_note: Mapped[int] = mapped_column(
        Integer, nullable=False, default=46, server_default="46"
    )
    rim_note: Mapped[int] = mapped_column(Integer, nullable=False, default=37, server_default="37")
    perc_notes: Mapped[list[int] | None] = mapped_column(ARRAY(Integer), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    clips: Mapped[list["Clip"]] = relationship("Clip", back_populates="drum_map_profile")
