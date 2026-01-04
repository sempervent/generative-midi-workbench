"""Add expressive fields to chord events

Revision ID: 008_chords_expressive
Revises: 007_chord_projections
Create Date: 2024-01-17 10:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "008_chords_expressive"
down_revision = "007_chord_projections"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add expressive fields to chord_events
    op.add_column(
        "chord_events",
        sa.Column("duration_beats", sa.Numeric(precision=10, scale=2), nullable=False, server_default=sa.text("4.0")),
    )
    op.add_column(
        "chord_events",
        sa.Column("intensity", sa.Numeric(precision=5, scale=2), nullable=False, server_default=sa.text("0.85")),
    )
    op.add_column(
        "chord_events",
        sa.Column("voicing", sa.String(20), nullable=False, server_default="root"),
    )
    op.add_column(
        "chord_events",
        sa.Column("inversion", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "chord_events",
        sa.Column("strum_ms", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "chord_events",
        sa.Column("humanize_ms", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "chord_events",
        sa.Column("velocity_jitter", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "chord_events",
        sa.Column("timing_jitter_ms", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "chord_events",
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "chord_events",
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "chord_events",
        sa.Column("grid_quantum", sa.Numeric(precision=5, scale=2), nullable=True),
    )

    # Data migration: infer duration_beats from existing duration_tick if needed
    # Calculate beats from ticks: beats = ticks / (PPQ * 4) for 4/4 time
    # For simplicity, assume 4/4 and PPQ=480, so 1 beat = 480 ticks
    op.execute("""
        UPDATE chord_events
        SET duration_beats = ROUND((duration_tick::numeric / 480.0)::numeric, 2)
        WHERE duration_beats IS NULL OR duration_beats = 4.0
    """)

    # Add indexes for efficient querying
    # Note: ix_chord_events_clip_start already exists from initial migration
    op.create_index(
        "ix_chord_events_enabled",
        "chord_events",
        ["is_enabled"],
    )


def downgrade() -> None:
    # Drop indexes
    # Note: ix_chord_events_clip_start was created in initial migration, don't drop it here
    op.drop_index("ix_chord_events_enabled", table_name="chord_events")

    # Drop columns
    op.drop_column("chord_events", "grid_quantum")
    op.drop_column("chord_events", "is_locked")
    op.drop_column("chord_events", "is_enabled")
    op.drop_column("chord_events", "timing_jitter_ms")
    op.drop_column("chord_events", "velocity_jitter")
    op.drop_column("chord_events", "humanize_ms")
    op.drop_column("chord_events", "strum_ms")
    op.drop_column("chord_events", "inversion")
    op.drop_column("chord_events", "voicing")
    op.drop_column("chord_events", "intensity")
    op.drop_column("chord_events", "duration_beats")

