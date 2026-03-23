"""Add settings_json column to user_conversation

Revision ID: v007
Revises: v006
Create Date: 2026-03-23
"""
from alembic import op
import sqlalchemy as sa

revision = 'v007'
down_revision = 'v006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'user_conversation',
        sa.Column('settings_json', sa.Text(), nullable=True, server_default='{}'),
    )


def downgrade() -> None:
    op.drop_column('user_conversation', 'settings_json')
