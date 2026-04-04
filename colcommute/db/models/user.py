"""User ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from .commute_post import CommutePost

from sqlalchemy import DateTime, Float, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_user_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    college_name: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    college_place_id: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    college_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    college_lng: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    commute_posts: Mapped[List["CommutePost"]] = relationship(
        "CommutePost",
        back_populates="user",
        cascade="all, delete-orphan",
    )
