"""Chord projection profile model."""

import uuid
from datetime import datetime

from sqlalchemy import Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from midinecromancer.db.base import Base


class ChordProjectionProfile(Base):
    """Chord projection profile defining how chords are realized."""

    __tablename__ = "chord_projection_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # block, arpeggio, broken, rhythm_pattern
    settings: Mapped[dict | None] = mapped_column(JSONB(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    clip_settings: Mapped[list["ClipChordSettings"]] = relationship(
        "ClipChordSettings", back_populates="projection_profile"
    )

    __table_args__ = (Index("ix_chord_projection_profiles_kind", "kind"),)

