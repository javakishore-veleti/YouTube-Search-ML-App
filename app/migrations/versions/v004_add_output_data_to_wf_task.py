"""Add output_data column to model_build_wf_task

Revision ID: v004
Revises: v003
Create Date: 2026-03-22
"""
from alembic import op
import sqlalchemy as sa

revision = 'v004'
down_revision = 'v003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'model_build_wf_task',
        sa.Column('output_data', sa.Text(), nullable=True, server_default='{}'),
    )


def downgrade() -> None:
    op.drop_column('model_build_wf_task', 'output_data')
