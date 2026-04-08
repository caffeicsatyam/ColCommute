"""rename trips table to commute_posts; add finalized trips table

Revision ID: 20260406_commute_posts
Revises: 20260405_origin
Create Date: 2026-04-06

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260406_commute_posts"
down_revision: Union[str, None] = "20260405_origin"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("trips", "commute_posts")
    op.execute(sa.text("ALTER INDEX ix_trips_user_id RENAME TO ix_commute_posts_user_id"))
    op.execute(
        sa.text(
            "ALTER INDEX ix_trips_destination_place_id RENAME TO ix_commute_posts_destination_place_id"
        )
    )
    op.execute(sa.text("ALTER INDEX ix_trips_destination_time RENAME TO ix_commute_posts_destination_time"))
    op.execute(sa.text("ALTER INDEX ix_trips_origin_place_id RENAME TO ix_commute_posts_origin_place_id"))
    op.execute(
        sa.text(
            "ALTER TABLE commute_posts RENAME CONSTRAINT trips_user_id_fkey TO commute_posts_user_id_fkey"
        )
    )

    op.create_table(
        "trips",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("offer_commute_post_id", sa.Uuid(), nullable=False),
        sa.Column("need_commute_post_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "offer_commute_post_id <> need_commute_post_id",
            name="ck_trips_distinct_posts",
        ),
        sa.ForeignKeyConstraint(
            ["need_commute_post_id"],
            ["commute_posts.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["offer_commute_post_id"],
            ["commute_posts.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_trips_offer_commute_post_id",
        "trips",
        ["offer_commute_post_id"],
        unique=False,
    )
    op.create_index(
        "ix_trips_need_commute_post_id",
        "trips",
        ["need_commute_post_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_trips_need_commute_post_id", table_name="trips")
    op.drop_index("ix_trips_offer_commute_post_id", table_name="trips")
    op.drop_table("trips")

    op.execute(
        sa.text(
            "ALTER TABLE commute_posts RENAME CONSTRAINT commute_posts_user_id_fkey TO trips_user_id_fkey"
        )
    )
    op.execute(sa.text("ALTER INDEX ix_commute_posts_origin_place_id RENAME TO ix_trips_origin_place_id"))
    op.execute(sa.text("ALTER INDEX ix_commute_posts_destination_time RENAME TO ix_trips_destination_time"))
    op.execute(
        sa.text("ALTER INDEX ix_commute_posts_destination_place_id RENAME TO ix_trips_destination_place_id")
    )
    op.execute(sa.text("ALTER INDEX ix_commute_posts_user_id RENAME TO ix_trips_user_id"))
    op.rename_table("commute_posts", "trips")
