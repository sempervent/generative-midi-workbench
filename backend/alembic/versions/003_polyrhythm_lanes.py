"""Add polyrhythm lanes (multi-cycle support)

Revision ID: 003_polyrhythm_lanes
Revises: 002_polyrhythms
Create Date: 2024-01-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_polyrhythm_lanes'
down_revision: Union[str, None] = '002_polyrhythms'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create clip_polyrhythm_lanes table
    op.create_table(
        'clip_polyrhythm_lanes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('clip_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('polyrhythm_profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lane_name', sa.String(255), nullable=False, server_default='Lane 1'),
        sa.Column('instrument_role', sa.String(50), nullable=True),
        sa.Column('pitch', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('velocity', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('mute', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('solo', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('seed_offset', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['clip_id'], ['clips.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['polyrhythm_profile_id'], ['polyrhythm_profiles.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_clip_lanes_order', 'clip_polyrhythm_lanes', ['clip_id', 'order_index'])
    op.create_index('ix_clip_lanes_mute', 'clip_polyrhythm_lanes', ['clip_id', 'mute'])

    # Update clips.grid_mode to support 'polyrhythm_multi'
    # Note: We don't change the column type, just document the new value
    # The existing VARCHAR(20) can handle the new value

    # Data migration: Convert legacy single-profile clips to lanes
    # This runs in Python after table creation
    connection = op.get_bind()
    
    # Find clips with grid_mode='polyrhythm' and polyrhythm_profile_id set
    result = connection.execute(sa.text("""
        SELECT id, polyrhythm_profile_id 
        FROM clips 
        WHERE grid_mode = 'polyrhythm' 
        AND polyrhythm_profile_id IS NOT NULL
    """))
    
    for row in result:
        clip_id = row[0]
        profile_id = row[1]
        
        # Create a default lane for this legacy clip
        connection.execute(sa.text("""
            INSERT INTO clip_polyrhythm_lanes 
            (id, clip_id, polyrhythm_profile_id, lane_name, pitch, velocity, order_index, seed_offset, created_at)
            VALUES 
            (gen_random_uuid(), :clip_id, :profile_id, 'Default Lane', 60, 100, 0, 0, NOW())
        """), {"clip_id": clip_id, "profile_id": profile_id})


def downgrade() -> None:
    op.drop_index('ix_clip_lanes_mute', table_name='clip_polyrhythm_lanes')
    op.drop_index('ix_clip_lanes_order', table_name='clip_polyrhythm_lanes')
    op.drop_table('clip_polyrhythm_lanes')

