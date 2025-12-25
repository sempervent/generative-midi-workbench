"""Project model."""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from midinecromancer.db.base import Base


class Project(Base):
    """Project model representing a composition project."""

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    bpm: Mapped[int] = mapped_column(Integer, nullable=False, default=120)
    time_signature_num: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    time_signature_den: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    bars: Mapped[int] = mapped_column(Integer, nullable=False, default=8)
    key_tonic: Mapped[str] = mapped_column(String(10), nullable=False, default="C")
    mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ionian",
    )  # ionian/dorian/phrygian/lydian/mixolydian/aeolian/locrian
    seed: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tracks: Mapped[list["Track"]] = relationship(
        "Track", back_populates="project", cascade="all, delete-orphan"
    )
    generation_runs: Mapped[list["GenerationRun"]] = relationship(
        "GenerationRun",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    suggestion_runs: Mapped[list["SuggestionRun"]] = relationship(
        "SuggestionRun",
        back_populates="project",
        cascade="all, delete-orphan",
    )
