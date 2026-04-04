"""Trip ORM model — a confirmed ride after both sides agree (links offer + need posts)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:
    from .commute_post import CommutePost


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    offer_commute_post_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("commute_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    need_commute_post_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("commute_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    offer_post: Mapped["CommutePost"] = relationship(
        "CommutePost",
        foreign_keys=[offer_commute_post_id],
    )
    need_post: Mapped["CommutePost"] = relationship(
        "CommutePost",
        foreign_keys=[need_commute_post_id],
    )

    __table_args__ = (
        CheckConstraint(
            "offer_commute_post_id <> need_commute_post_id",
            name="ck_trips_distinct_posts",
        ),
    )
