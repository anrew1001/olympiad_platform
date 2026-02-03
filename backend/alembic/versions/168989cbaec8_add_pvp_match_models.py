"""Add PvP match models

Revision ID: 168989cbaec8
Revises:
Create Date: 2026-02-02 20:23:23.439635

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '168989cbaec8'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Create Matches Table ---
    op.create_table('matches',
        sa.Column('player1_id', sa.Integer(), nullable=False),
        sa.Column('player2_id', sa.Integer(), nullable=False),
        # Enum values now lowercase to match model definition
        sa.Column('status', sa.Enum('waiting', 'active', 'finished', 'cancelled', 'error', name='matchstatus', native_enum=False), server_default='waiting', nullable=False),
        sa.Column('player1_score', sa.Integer(), server_default='0', nullable=False),
        sa.Column('player2_score', sa.Integer(), server_default='0', nullable=False),
        sa.Column('winner_id', sa.Integer(), nullable=True),
        # Split rating change columns
        sa.Column('player1_rating_change', sa.Integer(), nullable=True, comment='Изменение рейтинга игрока 1 (может быть отрицательным)'),
        sa.Column('player2_rating_change', sa.Integer(), nullable=True, comment='Изменение рейтинга игрока 2 (может быть отрицательным)'),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['player1_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['player2_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['winner_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        # Self-match protection
        sa.CheckConstraint('player1_id != player2_id', name='check_not_self_match')
    )
    op.create_index(op.f('ix_matches_player1_id'), 'matches', ['player1_id'], unique=False)
    op.create_index(op.f('ix_matches_player2_id'), 'matches', ['player2_id'], unique=False)
    op.create_index(op.f('ix_matches_status'), 'matches', ['status'], unique=False)

    # --- Create MatchTasks Table ---
    op.create_table('match_tasks',
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_match_tasks_match_id'), 'match_tasks', ['match_id'], unique=False)
    op.create_index('ix_match_tasks_match_order', 'match_tasks', ['match_id', 'order'], unique=False) # Used for sorting
    op.create_index(op.f('ix_match_tasks_task_id'), 'match_tasks', ['task_id'], unique=False)
    # Unique constraints
    op.create_index('ix_match_tasks_unique_task', 'match_tasks', ['match_id', 'task_id'], unique=True)
    op.create_index('ix_match_tasks_unique_order', 'match_tasks', ['match_id', 'order'], unique=True)

    # --- Create MatchAnswers Table ---
    op.create_table('match_answers',
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        # Changed to Text
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        # Added submitted_at with timezone=True and server default
        sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_match_answers_match_id'), 'match_answers', ['match_id'], unique=False)
    op.create_index(op.f('ix_match_answers_task_id'), 'match_answers', ['task_id'], unique=False)
    op.create_index('ix_match_answers_unique_submission', 'match_answers', ['match_id', 'user_id', 'task_id'], unique=True)
    op.create_index(op.f('ix_match_answers_user_id'), 'match_answers', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop MatchAnswers
    op.drop_index(op.f('ix_match_answers_user_id'), table_name='match_answers')
    op.drop_index('ix_match_answers_unique_submission', table_name='match_answers')
    op.drop_index(op.f('ix_match_answers_task_id'), table_name='match_answers')
    op.drop_index(op.f('ix_match_answers_match_id'), table_name='match_answers')
    op.drop_table('match_answers')

    # Drop MatchTasks
    op.drop_index('ix_match_tasks_unique_order', table_name='match_tasks')
    op.drop_index('ix_match_tasks_unique_task', table_name='match_tasks')
    op.drop_index(op.f('ix_match_tasks_task_id'), table_name='match_tasks')
    op.drop_index('ix_match_tasks_match_order', table_name='match_tasks')
    op.drop_index(op.f('ix_match_tasks_match_id'), table_name='match_tasks')
    op.drop_table('match_tasks')

    # Drop Matches
    op.drop_index(op.f('ix_matches_status'), table_name='matches')
    op.drop_index(op.f('ix_matches_player2_id'), table_name='matches')
    op.drop_index(op.f('ix_matches_player1_id'), table_name='matches')
    op.drop_table('matches')
