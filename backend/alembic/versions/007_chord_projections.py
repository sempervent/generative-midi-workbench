"""Add chord projection profiles and clip chord settings

Revision ID: 007_chord_projections
Revises: 006_offsets_chords
Create Date: 2024-01-16 10:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "007_chord_projections"
down_revision = "006_offsets_chords"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create chord_projection_profiles table
    op.create_table(
        "chord_projection_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("kind", sa.String(50), nullable=False),  # block, arpeggio, broken, rhythm_pattern
        sa.Column("settings", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Create clip_chord_settings table
    op.create_table(
        "clip_chord_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("clip_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("projection_profile_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("gate_pct", sa.Integer(), nullable=False, server_default=sa.text("90")),
        sa.Column("strum_ms", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("humanize_ms", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("offset_ticks", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("subdivision", sa.String(10), nullable=False, server_default="1/4"),
        sa.Column("pattern", postgresql.JSONB(), nullable=True),
        sa.Column("voicing_low_midi", sa.Integer(), nullable=False, server_default=sa.text("48")),
        sa.Column("voicing_high_midi", sa.Integer(), nullable=False, server_default=sa.text("72")),
        sa.Column("inversion_policy", sa.String(20), nullable=False, server_default="smooth"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Add foreign keys
    op.create_foreign_key(
        "fk_clip_chord_settings_clip_id",
        "clip_chord_settings",
        "clips",
        ["clip_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_clip_chord_settings_profile_id",
        "clip_chord_settings",
        "chord_projection_profiles",
        ["projection_profile_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Add unique constraint on clip_id
    op.create_unique_constraint("uq_clip_chord_settings_clip_id", "clip_chord_settings", ["clip_id"])

    # Add indexes
    op.create_index(
        "ix_chord_projection_profiles_kind",
        "chord_projection_profiles",
        ["kind"],
    )
    op.create_index(
        "ix_clip_chord_settings_clip_id",
        "clip_chord_settings",
        ["clip_id"],
    )
    op.create_index(
        "ix_clip_chord_settings_profile_id",
        "clip_chord_settings",
        ["projection_profile_id"],
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_clip_chord_settings_profile_id", table_name="clip_chord_settings")
    op.drop_index("ix_clip_chord_settings_clip_id", table_name="clip_chord_settings")
    op.drop_index("ix_chord_projection_profiles_kind", table_name="chord_projection_profiles")

    # Drop tables
    op.drop_table("clip_chord_settings")
    op.drop_table("chord_projection_profiles")

