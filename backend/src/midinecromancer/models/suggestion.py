"""Suggestion model."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Float, ForeignKey, Index, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from midinecromancer.db.base import Base


class Suggestion(Base):
    """Individual suggestion with preview and commit plan."""

    __tablename__ = "suggestions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("suggestion_runs.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(20), nullable=False)  # harmony|rhythm|melody
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    explanation: Mapped[str] = mapped_column(String(1000), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    is_committed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    committed_at: Mapped[datetime | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    run: Mapped["SuggestionRun"] = relationship("SuggestionRun", back_populates="suggestions")
    commits: Mapped[list["SuggestionCommit"]] = relationship(
        "SuggestionCommit",
        back_populates="suggestion",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_suggestions_run_kind", "run_id", "kind"),
        Index("ix_suggestions_committed", "is_committed", "committed_at"),
    )
