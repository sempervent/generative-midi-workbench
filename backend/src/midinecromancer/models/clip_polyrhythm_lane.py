"""Clip polyrhythm lane model."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from midinecromancer.db.base import Base


class ClipPolyrhythmLane(Base):
    """Polyrhythm lane linking a clip to a polyrhythm profile with lane-specific settings."""

    __tablename__ = "clip_polyrhythm_lanes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    clip_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clips.id", ondelete="CASCADE"), nullable=False
    )
    polyrhythm_profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("polyrhythm_profiles.id", ondelete="CASCADE"), nullable=False
    )
    lane_name: Mapped[str] = mapped_column(String(255), nullable=False, default="Lane 1")
    instrument_role: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # kick/snare/hat/etc
    pitch: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    velocity: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    mute: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    solo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    seed_offset: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    clip: Mapped["Clip"] = relationship("Clip", back_populates="polyrhythm_lanes")
    polyrhythm_profile: Mapped["PolyrhythmProfile"] = relationship("PolyrhythmProfile")

    __table_args__ = (
        Index("ix_clip_lanes_order", "clip_id", "order_index"),
        Index("ix_clip_lanes_mute", "clip_id", "mute"),
    )
