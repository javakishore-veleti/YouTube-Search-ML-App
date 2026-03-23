"""Add uuid to user_conversation and create user_conversation_message table

Revision ID: v006
Revises: v005
Create Date: 2026-03-23
"""
from alembic import op
import sqlalchemy as sa

revision = 'v006'
down_revision = 'v005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add uuid column to user_conversation
    op.add_column(
        'user_conversation',
        sa.Column('uuid', sa.String(36), nullable=True),
    )
    op.create_index('ix_user_conversation_uuid', 'user_conversation', ['uuid'], unique=True)

    # Backfill existing rows with UUIDs
    from uuid import uuid4
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id FROM user_conversation WHERE uuid IS NULL")).fetchall()
    for row in rows:
        conn.execute(
            sa.text("UPDATE user_conversation SET uuid = :uuid WHERE id = :id"),
            {"uuid": str(uuid4()), "id": row[0]},
        )

    # Create messages table
    op.create_table(
        'user_conversation_message',
        sa.Column('id',              sa.Integer(),  primary_key=True, autoincrement=True),
        sa.Column('conversation_id', sa.Integer(),  sa.ForeignKey('user_conversation.id'), nullable=False),
        sa.Column('query',           sa.Text(),     nullable=False),
        sa.Column('results_json',    sa.Text(),     nullable=False, server_default='[]'),
        sa.Column('created_at',      sa.DateTime(), nullable=False),
    )
    op.create_index('ix_user_conversation_message_conv_id', 'user_conversation_message', ['conversation_id'])


def downgrade() -> None:
    op.drop_table('user_conversation_message')
    op.drop_index('ix_user_conversation_uuid', table_name='user_conversation')
    op.drop_column('user_conversation', 'uuid')
