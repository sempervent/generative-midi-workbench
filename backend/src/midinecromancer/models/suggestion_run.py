"""Suggestion run model."""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Index, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from midinecromancer.db.base import Base


class SuggestionRun(Base):
    """Suggestion run tracking a generation session."""

    __tablename__ = "suggestion_runs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    seed: Mapped[int] = mapped_column(BigInteger, nullable=False)
    context_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    params_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="suggestion_runs")
    suggestions: Mapped[list["Suggestion"]] = relationship(
        "Suggestion",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="Suggestion.score.desc()",
    )

    __table_args__ = (Index("ix_suggestion_runs_project", "project_id", "created_at"),)
