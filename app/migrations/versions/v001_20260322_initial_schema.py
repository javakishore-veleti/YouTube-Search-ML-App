"""Initial schema — all tables for YouTube-Search-ML-App.

Tables created
--------------
  activity_logs           – background activity / audit log
  model_build_queue       – async build job queue
  models                  – top-level model records
  model_versions          – versioned snapshots of each model
  model_requests          – build requests tied to a model
  model_request_resources – YouTube video resources per request

Revision ID : 41cb0596ce95
Revises     : (none – first migration)
Create Date : 2026-03-22
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# ---------------------------------------------------------------------------
# Alembic revision identifiers
# ---------------------------------------------------------------------------
revision: str = "41cb0596ce95"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------------------------------------------------------------------------
# upgrade
# ---------------------------------------------------------------------------

def upgrade() -> None:
    # ── activity_logs ──────────────────────────────────────────────────────
    op.create_table(
        "activity_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_dt", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("activity_logs") as batch_op:
        batch_op.create_index("ix_activity_logs_created_dt", ["created_dt"], unique=False)

    # ── model_build_queue ──────────────────────────────────────────────────
    op.create_table(
        "model_build_queue",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("model_name", sa.String(length=200), nullable=False),
        sa.Column("approach_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("context_data", sa.Text(), nullable=True),
        sa.Column("selected_videos", sa.Text(), nullable=True),
        sa.Column("selected_sub_models", sa.Text(), nullable=True),
        sa.Column("publish_as_latest", sa.Boolean(), nullable=True),
        sa.Column("user_id", sa.String(length=100), nullable=False),
        sa.Column("created_dt", sa.DateTime(), nullable=False),
        sa.Column("updated_dt", sa.DateTime(), nullable=True),
        sa.Column("started_dt", sa.DateTime(), nullable=True),
        sa.Column("completed_dt", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("model_build_queue") as batch_op:
        batch_op.create_index("ix_model_build_queue_created_dt", ["created_dt"], unique=False)
        batch_op.create_index("ix_model_build_queue_status", ["status"], unique=False)

    # ── models ─────────────────────────────────────────────────────────────
    op.create_table(
        "models",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=100), nullable=False),
        sa.Column("model_name", sa.String(length=200), nullable=False),
        sa.Column("model_approach_type", sa.String(length=50), nullable=False),
        sa.Column("created_dt", sa.DateTime(), nullable=True),
        sa.Column("updated_dt", sa.DateTime(), nullable=True),
        sa.Column("input_criteria", sa.Text(), nullable=True),
        sa.Column("output_results", sa.Text(), nullable=True),
        sa.Column("latest_version", sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── model_versions ─────────────────────────────────────────────────────
    op.create_table(
        "model_versions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("model_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("input_criteria", sa.Text(), nullable=True),
        sa.Column("output_criteria", sa.Text(), nullable=True),
        sa.Column("model_location", sa.String(length=500), nullable=True),
        sa.Column("created_dt", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["model_id"], ["models.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── model_requests ─────────────────────────────────────────────────────
    op.create_table(
        "model_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("model_id", sa.Integer(), nullable=False),
        sa.Column("request_date", sa.DateTime(), nullable=True),
        sa.Column("model_approach_status", sa.String(length=30), nullable=True),
        sa.Column("created_dt", sa.DateTime(), nullable=True),
        sa.Column("updated_dt", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["model_id"], ["models.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── model_request_resources ────────────────────────────────────────────
    op.create_table(
        "model_request_resources",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("model_request_id", sa.Integer(), nullable=False),
        sa.Column("resource_type", sa.String(length=50), nullable=False),
        sa.Column("resource_type_id", sa.String(length=200), nullable=False),
        sa.Column("resource_metadata_json", sa.Text(), nullable=True),
        sa.Column("created_dt", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["model_request_id"], ["model_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


# ---------------------------------------------------------------------------
# downgrade
# ---------------------------------------------------------------------------

def downgrade() -> None:
    op.drop_table("model_request_resources")
    op.drop_table("model_requests")
    op.drop_table("model_versions")
    op.drop_table("models")
    with op.batch_alter_table("model_build_queue") as batch_op:
        batch_op.drop_index("ix_model_build_queue_status")
        batch_op.drop_index("ix_model_build_queue_created_dt")
    op.drop_table("model_build_queue")
    with op.batch_alter_table("activity_logs") as batch_op:
        batch_op.drop_index("ix_activity_logs_created_dt")
    op.drop_table("activity_logs")
