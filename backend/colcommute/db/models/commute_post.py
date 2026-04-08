"""Commute post ORM model — an open listing (offer or need), not a confirmed ride."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:
    from .user import User


class CommutePost(Base):
    __tablename__ = "commute_posts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    origin: Mapped[str] = mapped_column(Text, nullable=False)
    origin_place_id: Mapped[Optional[str]] = mapped_column(String(256), nullable=True, index=True)
    origin_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    origin_lng: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    origin_label: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    destination: Mapped[str] = mapped_column(Text, nullable=False)
    destination_place_id: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    destination_lat: Mapped[float] = mapped_column(Float, nullable=False)
    destination_lng: Mapped[float] = mapped_column(Float, nullable=False)
    destination_label: Mapped[str] = mapped_column(String(512), nullable=False)
    time_bucket: Mapped[str] = mapped_column(String(64), nullable=False)
    vacant_seats: Mapped[int] = mapped_column(Integer, nullable=False)
    seats_needed: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="commute_posts")

    __table_args__ = (
        Index("ix_commute_posts_destination_time", "destination_place_id", "time_bucket"),
    )
