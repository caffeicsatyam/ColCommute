"""add trip lifecycle, payments, and feedback

Revision ID: 20260406_trip_lifecycle
Revises: 20260406_auth_users
Create Date: 2026-04-06

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260406_trip_lifecycle"
down_revision: Union[str, None] = "20260406_auth_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("trips", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("trips", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "trip_payments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("trip_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trip_payments_trip_id", "trip_payments", ["trip_id"], unique=False)

    op.create_table(
        "trip_feedback",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("trip_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("feedback_score", sa.Integer(), nullable=False),
        sa.Column("feedback_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trip_feedback_trip_id", "trip_feedback", ["trip_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_trip_feedback_trip_id", table_name="trip_feedback")
    op.drop_table("trip_feedback")
    op.drop_index("ix_trip_payments_trip_id", table_name="trip_payments")
    op.drop_table("trip_payments")
    op.drop_column("trips", "completed_at")
    op.drop_column("trips", "started_at")
