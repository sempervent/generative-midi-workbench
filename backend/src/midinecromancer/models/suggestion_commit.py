"""Suggestion commit model."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from midinecromancer.db.base import Base


class SuggestionCommit(Base):
    """Commit record tracking what was created from a suggestion."""

    __tablename__ = "suggestion_commits"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    suggestion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("suggestions.id", ondelete="CASCADE"), nullable=False
    )
    commit_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    suggestion: Mapped["Suggestion"] = relationship("Suggestion", back_populates="commits")

    __table_args__ = (Index("ix_suggestion_commits_suggestion", "suggestion_id", "created_at"),)
