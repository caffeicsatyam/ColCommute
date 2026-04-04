"""add optional origin place id and coordinates to trips

Revision ID: 20260405_origin
Revises: aca1bd348b9d
Create Date: 2026-04-05

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260405_origin"
down_revision: Union[str, None] = "aca1bd348b9d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("trips", sa.Column("origin_place_id", sa.String(length=256), nullable=True))
    op.add_column("trips", sa.Column("origin_lat", sa.Float(), nullable=True))
    op.add_column("trips", sa.Column("origin_lng", sa.Float(), nullable=True))
    op.add_column("trips", sa.Column("origin_label", sa.String(length=512), nullable=True))
    op.create_index("ix_trips_origin_place_id", "trips", ["origin_place_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_trips_origin_place_id", table_name="trips")
    op.drop_column("trips", "origin_label")
    op.drop_column("trips", "origin_lng")
    op.drop_column("trips", "origin_lat")
    op.drop_column("trips", "origin_place_id")
