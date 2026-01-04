"""Add chord patterns and regeneration support

Revision ID: 013_chord_patterns
Revises: 012_chord_timing_beats
Create Date: 2024-01-23 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "013_chord_patterns"
down_revision: Union[str, None] = "012_chord_timing_beats"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add pattern fields to chord_events
    op.add_column(
        "chord_events",
        sa.Column("pattern_type", sa.String(20), nullable=False, server_default="block"),
    )
    op.add_column(
        "chord_events",
        sa.Column("duration_gate", sa.Numeric(5, 2), nullable=False, server_default="0.85"),
    )
    op.add_column(
        "chord_events",
        sa.Column("velocity_curve", sa.String(20), nullable=False, server_default="flat"),
    )
    op.add_column(
        "chord_events",
        sa.Column("comp_pattern", postgresql.JSONB, nullable=True),
    )
    op.add_column(
        "chord_events",
        sa.Column("strum_direction", sa.String(20), nullable=False, server_default="down"),
    )
    op.add_column(
        "chord_events",
        sa.Column("strum_spread", sa.Numeric(5, 2), nullable=False, server_default="1.0"),
    )
    op.add_column(
        "chord_events",
        sa.Column("retrigger", sa.Boolean, nullable=False, server_default="false"),
    )

    # Add constraints
    op.create_check_constraint(
        "ck_chord_events_pattern_type",
        "chord_events",
        "pattern_type IN ('block', 'strum', 'comp', 'arp')",
    )
    op.create_check_constraint(
        "ck_chord_events_duration_gate",
        "chord_events",
        "duration_gate >= 0.0 AND duration_gate <= 1.0",
    )
    op.create_check_constraint(
        "ck_chord_events_velocity_curve",
        "chord_events",
        "velocity_curve IN ('flat', 'down', 'up', 'swell', 'dip')",
    )
    op.create_check_constraint(
        "ck_chord_events_strum_direction",
        "chord_events",
        "strum_direction IN ('down', 'up', 'alternate', 'random')",
    )
    op.create_check_constraint(
        "ck_chord_events_strum_spread",
        "chord_events",
        "strum_spread >= 0.1 AND strum_spread <= 3.0",
    )

    # Create chord_gen_runs table
    op.create_table(
        "chord_gen_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clip_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("bar_start", sa.Integer, nullable=False),
        sa.Column("bar_end", sa.Integer, nullable=False),
        sa.Column("seed", sa.Integer, nullable=False),
        sa.Column("params", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["clip_id"], ["clips.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_chord_gen_runs_project", "chord_gen_runs", ["project_id"])
    op.create_index("ix_chord_gen_runs_clip", "chord_gen_runs", ["clip_id"])

    # Create chord_gen_suggestions table
    op.create_table(
        "chord_gen_suggestions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rank", sa.Integer, nullable=False),
        sa.Column("score", sa.Numeric(5, 2), nullable=False),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("explanation", sa.Text, nullable=True),
        sa.Column("progression", postgresql.JSONB, nullable=False),
        sa.Column("locks", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["run_id"], ["chord_gen_runs.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_chord_gen_suggestions_run", "chord_gen_suggestions", ["run_id"])
    op.create_index(
        "ix_chord_gen_suggestions_run_rank", "chord_gen_suggestions", ["run_id", "rank"]
    )


def downgrade() -> None:
    op.drop_table("chord_gen_suggestions")
    op.drop_table("chord_gen_runs")
    op.drop_constraint("ck_chord_events_strum_spread", "chord_events")
    op.drop_constraint("ck_chord_events_strum_direction", "chord_events")
    op.drop_constraint("ck_chord_events_velocity_curve", "chord_events")
    op.drop_constraint("ck_chord_events_duration_gate", "chord_events")
    op.drop_constraint("ck_chord_events_pattern_type", "chord_events")
    op.drop_column("chord_events", "retrigger")
    op.drop_column("chord_events", "strum_spread")
    op.drop_column("chord_events", "strum_direction")
    op.drop_column("chord_events", "comp_pattern")
    op.drop_column("chord_events", "velocity_curve")
    op.drop_column("chord_events", "duration_gate")
    op.drop_column("chord_events", "pattern_type")

