"""Add polyrhythm support

Revision ID: 002_polyrhythms
Revises: 001_initial
Create Date: 2024-01-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_polyrhythms'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create polyrhythm_profiles table
    op.create_table(
        'polyrhythm_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('steps', sa.Integer(), nullable=False),
        sa.Column('pulses', sa.Integer(), nullable=False),
        sa.Column('rotation', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cycle_beats', sa.Numeric(10, 2), nullable=False),
        sa.Column('swing', sa.Numeric(5, 3), nullable=True),
        sa.Column('humanize_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_polyrhythm_profiles_name', 'polyrhythm_profiles', ['name'])

    # Add columns to clips table
    op.add_column('clips', sa.Column('grid_mode', sa.String(20), nullable=False, server_default='standard'))
    op.add_column('clips', sa.Column('polyrhythm_profile_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_clips_polyrhythm_profile',
        'clips',
        'polyrhythm_profiles',
        ['polyrhythm_profile_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_index('ix_clips_polyrhythm_profile', 'clips', ['polyrhythm_profile_id'])


def downgrade() -> None:
    op.drop_index('ix_clips_polyrhythm_profile', table_name='clips')
    op.drop_constraint('fk_clips_polyrhythm_profile', 'clips', type_='foreignkey')
    op.drop_column('clips', 'polyrhythm_profile_id')
    op.drop_column('clips', 'grid_mode')
    op.drop_index('ix_polyrhythm_profiles_name', table_name='polyrhythm_profiles')
    op.drop_table('polyrhythm_profiles')

