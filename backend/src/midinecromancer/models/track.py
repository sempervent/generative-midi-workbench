"""Track model."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from midinecromancer.db.base import Base


class Track(Base):
    """Track model representing a MIDI track."""

    __tablename__ = "tracks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # drums/chords/bass/melody
    midi_channel: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    midi_program: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 0-127
    is_muted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_soloed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    start_offset_ticks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="tracks")
    clips: Mapped[list["Clip"]] = relationship(
        "Clip", back_populates="track", cascade="all, delete-orphan"
    )
