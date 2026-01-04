"""Clip chord settings model."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from midinecromancer.db.base import Base


class ClipChordSettings(Base):
    """Settings for how chords in a clip are rendered/realized."""

    __tablename__ = "clip_chord_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clips.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    projection_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chord_projection_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    gate_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=90)  # 0-100
    strum_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    humanize_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    offset_ticks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    subdivision: Mapped[str] = mapped_column(String(10), nullable=False, default="1/4")
    pattern: Mapped[dict | None] = mapped_column(JSONB(), nullable=True)  # For rhythm_pattern
    voicing_low_midi: Mapped[int] = mapped_column(Integer, nullable=False, default=48)
    voicing_high_midi: Mapped[int] = mapped_column(Integer, nullable=False, default=72)
    inversion_policy: Mapped[str] = mapped_column(String(20), nullable=False, default="smooth")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    clip: Mapped["Clip"] = relationship("Clip", back_populates="chord_settings")
    projection_profile: Mapped["ChordProjectionProfile | None"] = relationship(
        "ChordProjectionProfile", back_populates="clip_settings"
    )

    __table_args__ = (
        UniqueConstraint("clip_id", name="uq_clip_chord_settings_clip_id"),
        Index("ix_clip_chord_settings_clip_id", "clip_id"),
        Index("ix_clip_chord_settings_profile_id", "projection_profile_id"),
    )

