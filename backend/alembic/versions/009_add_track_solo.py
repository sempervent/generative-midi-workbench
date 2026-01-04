"""Add is_soloed field to tracks

Revision ID: 009_add_track_solo
Revises: 008_chords_expressive
Create Date: 2024-01-17 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "009_add_track_solo"
down_revision = "008_chords_expressive"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_soloed field to tracks
    op.add_column(
        "tracks",
        sa.Column("is_soloed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    # Drop is_soloed column
    op.drop_column("tracks", "is_soloed")

