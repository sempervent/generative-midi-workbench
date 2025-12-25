"""Add mute field to clips for consistency

Revision ID: 005_mute_solo_consistency
Revises: 004_theory_overlay
Create Date: 2024-01-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '005_mute_solo_consistency'
down_revision: Union[str, None] = '004_theory_overlay'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add mute field to clips
    op.add_column('clips', sa.Column('is_muted', sa.Boolean(), nullable=False, server_default='false'))
    
    # Add solo field to clips (for consistency, though solo is primarily per-lane)
    op.add_column('clips', sa.Column('is_soloed', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('clips', 'is_soloed')
    op.drop_column('clips', 'is_muted')

