"""Initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('bpm', sa.Integer(), nullable=False),
        sa.Column('time_signature_num', sa.Integer(), nullable=False),
        sa.Column('time_signature_den', sa.Integer(), nullable=False),
        sa.Column('bars', sa.Integer(), nullable=False),
        sa.Column('key_tonic', sa.String(10), nullable=False),
        sa.Column('mode', sa.String(20), nullable=False),
        sa.Column('seed', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # Create tracks table
    op.create_table(
        'tracks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('midi_channel', sa.Integer(), nullable=False),
        sa.Column('midi_program', sa.Integer(), nullable=False),
        sa.Column('is_muted', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    )

    # Create clips table
    op.create_table(
        'clips',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('track_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('start_bar', sa.Integer(), nullable=False),
        sa.Column('length_bars', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['track_id'], ['tracks.id'], ondelete='CASCADE'),
    )

    # Create notes table
    op.create_table(
        'notes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('clip_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('pitch', sa.Integer(), nullable=False),
        sa.Column('velocity', sa.Integer(), nullable=False),
        sa.Column('start_tick', sa.Integer(), nullable=False),
        sa.Column('duration_tick', sa.Integer(), nullable=False),
        sa.Column('probability', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['clip_id'], ['clips.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_notes_clip_start', 'notes', ['clip_id', 'start_tick'])

    # Create chord_events table
    op.create_table(
        'chord_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('clip_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('start_tick', sa.Integer(), nullable=False),
        sa.Column('duration_tick', sa.Integer(), nullable=False),
        sa.Column('roman_numeral', sa.String(20), nullable=False),
        sa.Column('chord_name', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['clip_id'], ['clips.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_chord_events_clip_start', 'chord_events', ['clip_id', 'start_tick'])

    # Create generation_runs table
    op.create_table(
        'generation_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('kind', sa.String(20), nullable=False),
        sa.Column('seed_used', sa.BigInteger(), nullable=False),
        sa.Column('params', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    )


def downgrade() -> None:
    op.drop_table('generation_runs')
    op.drop_index('ix_chord_events_clip_start', table_name='chord_events')
    op.drop_table('chord_events')
    op.drop_index('ix_notes_clip_start', table_name='notes')
    op.drop_table('notes')
    op.drop_table('clips')
    op.drop_table('tracks')
    op.drop_table('projects')

