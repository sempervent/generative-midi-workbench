"""Add intensity and params to clips for arrangement cards

Revision ID: 010_arrangement_cards
Revises: 009_add_track_solo
Create Date: 2024-01-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '010_arrangement_cards'
down_revision: Union[str, None] = '009_add_track_solo'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add intensity column (float, default 1.0)
    op.add_column('clips', sa.Column('intensity', sa.Float(), nullable=False, server_default='1.0'))
    
    # Add params column (jsonb, default empty object)
    op.add_column('clips', sa.Column('params', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'))
    
    # Add index on (track_id, start_bar) for efficient ordering
    op.create_index('ix_clips_track_start', 'clips', ['track_id', 'start_bar'])


def downgrade() -> None:
    op.drop_index('ix_clips_track_start', table_name='clips')
    op.drop_column('clips', 'params')
    op.drop_column('clips', 'intensity')

