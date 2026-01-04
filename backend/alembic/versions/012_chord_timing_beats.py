"""Add beat-based timing fields to chord events

Revision ID: 012_chord_timing_beats
Revises: 011_drum_maps
Create Date: 2024-01-22 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "012_chord_timing_beats"
down_revision: Union[str, None] = "011_drum_maps"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add beat-based timing fields
    op.add_column(
        "chord_events",
        sa.Column("strum_beats", sa.Numeric(5, 3), nullable=True, server_default="0.0"),
    )
    op.add_column(
        "chord_events",
        sa.Column("humanize_beats", sa.Numeric(5, 3), nullable=True, server_default="0.0"),
    )

    # Set default values for existing rows (we can't convert ms to beats without BPM context)
    op.execute("UPDATE chord_events SET strum_beats = 0.0 WHERE strum_beats IS NULL")
    op.execute("UPDATE chord_events SET humanize_beats = 0.0 WHERE humanize_beats IS NULL")

    # Make columns non-nullable after backfill
    op.alter_column("chord_events", "strum_beats", nullable=False, server_default="0.0")
    op.alter_column("chord_events", "humanize_beats", nullable=False, server_default="0.0")

    # Add constraints
    op.create_check_constraint(
        "ck_chord_events_strum_beats_non_negative",
        "chord_events",
        "strum_beats >= 0",
    )
    op.create_check_constraint(
        "ck_chord_events_humanize_beats_non_negative",
        "chord_events",
        "humanize_beats >= 0",
    )
    op.create_check_constraint(
        "ck_chord_events_strum_beats_reasonable",
        "chord_events",
        "strum_beats <= 2.0",
    )
    op.create_check_constraint(
        "ck_chord_events_humanize_beats_reasonable",
        "chord_events",
        "humanize_beats <= 0.5",
    )


def downgrade() -> None:
    op.drop_constraint("ck_chord_events_humanize_beats_reasonable", "chord_events")
    op.drop_constraint("ck_chord_events_strum_beats_reasonable", "chord_events")
    op.drop_constraint("ck_chord_events_humanize_beats_non_negative", "chord_events")
    op.drop_constraint("ck_chord_events_strum_beats_non_negative", "chord_events")
    op.drop_column("chord_events", "humanize_beats")
    op.drop_column("chord_events", "strum_beats")

