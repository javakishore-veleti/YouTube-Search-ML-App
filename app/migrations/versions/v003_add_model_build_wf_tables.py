"""Add model_build_wf and model_build_wf_task tables

Revision ID: v003
Revises: v002
Create Date: 2026-03-22
"""
from alembic import op
import sqlalchemy as sa

revision = 'v003'
down_revision = 'v002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'model_build_wf',
        sa.Column('id',            sa.Integer(),     primary_key=True, autoincrement=True),
        sa.Column('model_id',      sa.Integer(),     sa.ForeignKey('models.id'),            nullable=True),
        sa.Column('queue_item_id', sa.Integer(),     sa.ForeignKey('model_build_queue.id'), nullable=True),
        sa.Column('approach_id',   sa.String(100),   nullable=False),
        sa.Column('status',        sa.String(20),    nullable=False, server_default='started'),
        sa.Column('started_at',    sa.DateTime(),    nullable=False),
        sa.Column('ended_at',      sa.DateTime(),    nullable=True),
        sa.Column('created_at',    sa.DateTime(),    nullable=False),
        sa.Column('error_message', sa.Text(),        nullable=True, server_default=''),
    )
    op.create_index('ix_model_build_wf_model_id',      'model_build_wf', ['model_id'])
    op.create_index('ix_model_build_wf_queue_item_id', 'model_build_wf', ['queue_item_id'])
    op.create_index('ix_model_build_wf_status',        'model_build_wf', ['status'])

    op.create_table(
        'model_build_wf_task',
        sa.Column('id',                sa.Integer(),    primary_key=True, autoincrement=True),
        sa.Column('wf_id',             sa.Integer(),    sa.ForeignKey('model_build_wf.id'), nullable=False),
        sa.Column('task_id',           sa.String(100),  nullable=False),
        sa.Column('task_file',         sa.String(200),  nullable=False, server_default=''),
        sa.Column('task_order',        sa.Integer(),    nullable=False, server_default='0'),
        sa.Column('status',            sa.String(20),   nullable=False, server_default='pending'),
        sa.Column('started_at',        sa.DateTime(),   nullable=True),
        sa.Column('ended_at',          sa.DateTime(),   nullable=True),
        sa.Column('status_updated_at', sa.DateTime(),   nullable=True),
        sa.Column('error_message',     sa.Text(),       nullable=True, server_default=''),
    )
    op.create_index('ix_model_build_wf_task_wf_id', 'model_build_wf_task', ['wf_id'])


def downgrade() -> None:
    op.drop_table('model_build_wf_task')
    op.drop_table('model_build_wf')
