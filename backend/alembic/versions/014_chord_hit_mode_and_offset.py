"""Add hit_mode, offset_beats, and strum_curve to chord_events.

Revision ID: 014_chord_hit_mode_and_offset
Revises: 013_chord_patterns
Create Date: 2024-01-XX XX:XX:XX.XXXXXX
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "014_chord_hit_mode_and_offset"
down_revision: Union[str, None] = "013_chord_patterns"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add offset_beats for push/pull timing
    op.add_column(
        "chord_events",
        sa.Column(
            "offset_beats",
            sa.Numeric(5, 3),
            nullable=False,
            server_default="0.0",
        ),
    )

    # Add strum_curve for strum timing curve
    op.add_column(
        "chord_events",
        sa.Column(
            "strum_curve",
            sa.String(20),
            nullable=False,
            server_default="linear",
        ),
    )

    # Add hit_params JSONB for mode-specific parameters
    # (stabs: hits, spacing, skip_prob, vel_curve)
    # (comp: source, euclid steps/pulses/rot OR polyrhythm_profile_id, swing, humanize)
    # (arp: dir, rate, octaves)
    # (strum: duration_beats, dir, curve, tightness)
    op.add_column(
        "chord_events",
        sa.Column(
            "hit_params",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )

    # Note: pattern_type already exists and serves as hit_mode
    # Update pattern_type to support new values: sustain, piano_stabs, guitar_strum, syncopated_pump
    # Existing values: block, strum, comp, arp, stabs
    # We'll allow both old and new values for backward compatibility


def downgrade() -> None:
    op.drop_column("chord_events", "hit_params")
    op.drop_column("chord_events", "strum_curve")
    op.drop_column("chord_events", "offset_beats")

