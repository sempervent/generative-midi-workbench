"""Add drum map profiles

Revision ID: 011_drum_maps
Revises: 010_arrangement_cards
Create Date: 2024-01-21 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "011_drum_maps"
down_revision: Union[str, None] = "010_arrangement_cards"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create drum_map_profiles table
    op.create_table(
        "drum_map_profiles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False, unique=True),
        sa.Column("kick_note", sa.Integer(), nullable=False, server_default="36"),
        sa.Column("snare_note", sa.Integer(), nullable=False, server_default="38"),
        sa.Column("clap_note", sa.Integer(), nullable=False, server_default="39"),
        sa.Column("closed_hat_note", sa.Integer(), nullable=False, server_default="42"),
        sa.Column("open_hat_note", sa.Integer(), nullable=False, server_default="46"),
        sa.Column("rim_note", sa.Integer(), nullable=False, server_default="37"),
        sa.Column("perc_notes", postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_drum_map_profiles")),
    )

    # Add drum_map_profile_id to clips
    op.add_column(
        "clips",
        sa.Column("drum_map_profile_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        op.f("fk_clips_drum_map_profile_id_drum_map_profiles"),
        "clips",
        "drum_map_profiles",
        ["drum_map_profile_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_clips_drum_map_profile_id"),
        "clips",
        ["drum_map_profile_id"],
        unique=False,
    )

    # Insert default drum map profiles
    op.execute("""
        INSERT INTO drum_map_profiles (id, name, kick_note, snare_note, clap_note, closed_hat_note, open_hat_note, rim_note, perc_notes, created_at, updated_at)
        VALUES
        (gen_random_uuid(), 'Ableton GM', 36, 38, 39, 42, 46, 37, ARRAY[49, 51, 45, 48], NOW(), NOW()),
        (gen_random_uuid(), 'Ableton Trap', 36, 38, 39, 42, 46, 37, ARRAY[49, 51, 45, 48], NOW(), NOW()),
        (gen_random_uuid(), 'Minimal', 36, 38, 39, 42, 46, 37, NULL, NOW(), NOW())
    """)


def downgrade() -> None:
    op.drop_index(op.f("ix_clips_drum_map_profile_id"), table_name="clips")
    op.drop_constraint(
        op.f("fk_clips_drum_map_profile_id_drum_map_profiles"),
        table_name="clips",
        type_="foreignkey",
    )
    op.drop_column("clips", "drum_map_profile_id")
    op.drop_table("drum_map_profiles")
