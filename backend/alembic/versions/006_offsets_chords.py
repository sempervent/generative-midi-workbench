"""Add arrangement offsets and fix chord visibility

Revision ID: 006_offsets_chords
Revises: 005_mute_solo_consistency
Create Date: 2024-01-15 10:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "006_offsets_chords"
down_revision = "005_mute_solo_consistency"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add offset columns to clips
    op.add_column(
        "clips",
        sa.Column("start_offset_ticks", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )

    # Add offset columns to tracks
    op.add_column(
        "tracks",
        sa.Column("start_offset_ticks", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )

    # Create indexes for efficient querying
    op.create_index(
        op.f("ix_clips_start_offset_ticks"), "clips", ["start_offset_ticks"], unique=False
    )
    op.create_index(
        op.f("ix_tracks_start_offset_ticks"), "tracks", ["start_offset_ticks"], unique=False
    )

    # Ensure chord_events are properly indexed for querying by project
    # (clip_id index already exists, but add composite for project queries if needed)
    # Note: We can query via clip -> track -> project, so existing indexes should suffice


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f("ix_tracks_start_offset_ticks"), table_name="tracks")
    op.drop_index(op.f("ix_clips_start_offset_ticks"), table_name="clips")

    # Drop columns
    op.drop_column("tracks", "start_offset_ticks")
    op.drop_column("clips", "start_offset_ticks")
