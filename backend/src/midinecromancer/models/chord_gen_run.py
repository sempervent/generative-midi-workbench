"""Chord generation run model."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, Index, String, Text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from midinecromancer.db.base import Base


class ChordGenRun(Base):
    """Chord generation run model."""

    __tablename__ = "chord_gen_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    clip_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clips.id", ondelete="CASCADE"), nullable=True
    )
    bar_start: Mapped[int] = mapped_column(Integer, nullable=False)
    bar_end: Mapped[int] = mapped_column(Integer, nullable=False)
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    params: Mapped[dict] = mapped_column(postgresql.JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    suggestions: Mapped[list["ChordGenSuggestion"]] = relationship(
        "ChordGenSuggestion", back_populates="run", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_chord_gen_runs_project", "project_id"),
        Index("ix_chord_gen_runs_clip", "clip_id"),
    )


class ChordGenSuggestion(Base):
    """Chord generation suggestion model."""

    __tablename__ = "chord_gen_suggestions"

    id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chord_gen_runs.id", ondelete="CASCADE"), nullable=False
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(postgresql.NUMERIC(5, 2), nullable=False)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    explanation: Mapped[str | None] = mapped_column(String, nullable=True)
    progression: Mapped[list[dict]] = mapped_column(postgresql.JSONB, nullable=False)
    locks: Mapped[dict | None] = mapped_column(postgresql.JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    run: Mapped["ChordGenRun"] = relationship("ChordGenRun", back_populates="suggestions")

    __table_args__ = (
        Index("ix_chord_gen_suggestions_run", "run_id"),
        Index("ix_chord_gen_suggestions_run_rank", "run_id", "rank"),
    )

