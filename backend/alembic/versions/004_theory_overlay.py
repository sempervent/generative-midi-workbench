"""Add theory overlay and suggestion engine

Revision ID: 004_theory_overlay
Revises: 003_polyrhythm_lanes
Create Date: 2024-01-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004_theory_overlay'
down_revision: Union[str, None] = '003_polyrhythm_lanes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create suggestion_runs table
    op.create_table(
        'suggestion_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('seed', sa.BigInteger(), nullable=False),
        sa.Column('context_json', postgresql.JSONB(), nullable=False),
        sa.Column('params_json', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_suggestion_runs_project', 'suggestion_runs', ['project_id', 'created_at'])

    # Create suggestions table
    op.create_table(
        'suggestions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('kind', sa.String(20), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('explanation', sa.String(1000), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('payload_json', postgresql.JSONB(), nullable=False),
        sa.Column('is_committed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('committed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['run_id'], ['suggestion_runs.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_suggestions_run_kind', 'suggestions', ['run_id', 'kind'])
    op.create_index('ix_suggestions_committed', 'suggestions', ['is_committed', 'committed_at'])

    # Create suggestion_commits table
    op.create_table(
        'suggestion_commits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('suggestion_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('commit_json', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['suggestion_id'], ['suggestions.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_suggestion_commits_suggestion', 'suggestion_commits', ['suggestion_id', 'created_at'])


def downgrade() -> None:
    op.drop_index('ix_suggestion_commits_suggestion', table_name='suggestion_commits')
    op.drop_table('suggestion_commits')
    op.drop_index('ix_suggestions_committed', table_name='suggestions')
    op.drop_index('ix_suggestions_run_kind', table_name='suggestions')
    op.drop_table('suggestions')
    op.drop_index('ix_suggestion_runs_project', table_name='suggestion_runs')
    op.drop_table('suggestion_runs')

