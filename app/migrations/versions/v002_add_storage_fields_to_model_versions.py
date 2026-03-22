"""Add storage_type and storage_path to model_versions

Revision ID: v002
Revises: 41cb0596ce95
Create Date: 2026-03-22
"""
from alembic import op
import sqlalchemy as sa

revision = 'v002'
down_revision = '41cb0596ce95'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('model_versions') as batch_op:
        batch_op.add_column(sa.Column('storage_type', sa.String(50), nullable=True, server_default='local'))
        batch_op.add_column(sa.Column('storage_path', sa.String(1000), nullable=True, server_default=''))


def downgrade() -> None:
    with op.batch_alter_table('model_versions') as batch_op:
        batch_op.drop_column('storage_path')
        batch_op.drop_column('storage_type')
