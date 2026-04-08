"""add trip status

Revision ID: d29c2833e9cc
Revises: 20260406_commute_posts
Create Date: 2026-04-06

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d29c2833e9cc"
down_revision: Union[str, None] = "20260406_commute_posts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "trips",
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="confirmed",
        ),
    )
    op.alter_column("trips", "status", server_default=None)


def downgrade() -> None:
    op.drop_column("trips", "status")
