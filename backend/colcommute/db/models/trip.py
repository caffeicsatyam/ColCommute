"""Trip ORM model — a confirmed ride after both sides agree (links offer + need posts)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

import enum

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:
    from .commute_post import CommutePost
    from .trip_feedback import TripFeedback
    from .trip_payment import TripPayment


class TripStatus(str, enum.Enum):
    PENDING = "pending"
    PROGRESSING = "progressing"
    COMPLETED = "completed"


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
    status: Mapped[str] = mapped_column(
        String(20), default=TripStatus.PENDING.value, nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="confirmed")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    offer_post: Mapped["CommutePost"] = relationship(
        "CommutePost",
        foreign_keys=[offer_commute_post_id],
    )
    need_post: Mapped["CommutePost"] = relationship(
        "CommutePost",
        foreign_keys=[need_commute_post_id],
    )
    payments: Mapped[List["TripPayment"]] = relationship(
        "TripPayment",
        cascade="all, delete-orphan",
    )
    feedback_entries: Mapped[List["TripFeedback"]] = relationship(
        "TripFeedback",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "offer_commute_post_id <> need_commute_post_id",
            name="ck_trips_distinct_posts",
        ),
    )
