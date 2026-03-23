"""Add user_conversation and user_conversation_history tables

Revision ID: v005
Revises: v004
Create Date: 2026-03-22
"""
from alembic import op
import sqlalchemy as sa

revision = 'v005'
down_revision = 'v004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'user_conversation',
        sa.Column('id',                sa.Integer(),    primary_key=True, autoincrement=True),
        sa.Column('user_id',           sa.String(100),  nullable=False),
        sa.Column('conversation_name', sa.String(300),  nullable=False),
        sa.Column('model_id',          sa.Integer(),    sa.ForeignKey('models.id'), nullable=True),
        sa.Column('is_active',         sa.Boolean(),    nullable=False, server_default='0'),
        sa.Column('created_at',        sa.DateTime(),   nullable=False),
        sa.Column('updated_at',        sa.DateTime(),   nullable=False),
    )
    op.create_index('ix_user_conversation_user_id', 'user_conversation', ['user_id'])

    op.create_table(
        'user_conversation_history',
        sa.Column('id',                sa.Integer(),    primary_key=True, autoincrement=True),
        sa.Column('conversation_id',   sa.Integer(),    sa.ForeignKey('user_conversation.id'), nullable=False),
        sa.Column('user_id',           sa.String(100),  nullable=False),
        sa.Column('conversation_name', sa.String(300),  nullable=False),
        sa.Column('model_id',          sa.Integer(),    nullable=True),
        sa.Column('is_active',         sa.Boolean(),    nullable=False, server_default='0'),
        sa.Column('snapshot_at',       sa.DateTime(),   nullable=False),
    )
    op.create_index('ix_user_conversation_history_conv_id', 'user_conversation_history', ['conversation_id'])


def downgrade() -> None:
    op.drop_table('user_conversation_history')
    op.drop_table('user_conversation')
