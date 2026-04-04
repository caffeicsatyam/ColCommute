"""
Ride matching backed by PostgreSQL (Cloud SQL).

Vacant seats = offers; seats_needed = requests. Matching uses ``destination_place_id``
when both sides have it, else normalized ``destination`` text.

**CommutePost** = open listing. **Trip** = confirmed ride (two posts linked) — insert via app flow when both agree.

ADK **tools** live under ``tools/`` (e.g. ``tools/ride_matching.py``); this module only exposes plain functions for those tools to call.
"""

from __future__ import annotations

import uuid
from typing import Any, Optional

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from colcommute.db.models import CommutePost, Trip, User
from colcommute.db.session import session_scope


def _norm_place(s: str) -> str:
    return " ".join(s.lower().strip().split())


def _commute_post_to_dict(post: CommutePost, external_user_id: str) -> dict[str, Any]:
    return {
        "commute_post_id": str(post.id),
        "user_id": external_user_id,
        "origin": post.origin,
        "destination": post.destination,
        "destination_place_id": post.destination_place_id,
        "destination_lat": post.destination_lat,
        "destination_lng": post.destination_lng,
        "destination_label": post.destination_label,
        "origin_place_id": post.origin_place_id,
        "origin_lat": post.origin_lat,
        "origin_lng": post.origin_lng,
        "origin_label": post.origin_label,
        "time_bucket": post.time_bucket,
        "vacant_seats": post.vacant_seats,
        "seats_needed": post.seats_needed,
    }


def _get_user_by_external_id(session: Session, external_user_id: str) -> Optional[User]:
    return session.scalar(
        select(User).where(User.external_user_id == external_user_id.strip())
    )


def _get_commute_post_with_user(
    session: Session, commute_post_id: str
) -> tuple[Optional[CommutePost], Optional[str]]:
    try:
        pid = uuid.UUID(commute_post_id.strip())
    except ValueError:
        return None, None
    post = session.get(CommutePost, pid)
    if post is None:
        return None, None
    user = session.get(User, post.user_id)
    ext = user.external_user_id if user else ""
    return post, ext


def register_commute_post(
    user_id: str,
    origin: str,
    destination: str,
    destination_place_id: str,
    destination_lat: float,
    destination_lng: float,
    destination_label: str,
    time_bucket: str,
    vacant_seats: int = 0,
    seats_needed: int = 0,
    origin_place_id: Optional[str] = None,
    origin_lat: Optional[float] = None,
    origin_lng: Optional[float] = None,
    origin_label: Optional[str] = None,
) -> dict[str, Any]:
    """
    Register a commute **post** (listing). ``user_id`` is ``users.external_user_id`` for an existing user row.

    Destination fields should come from Places (Details) or your UI; they are required for persistence.
    """
    if vacant_seats < 0 or seats_needed < 0:
        return {"status": "error", "error_message": "Seat counts cannot be negative."}
    if vacant_seats == 0 and seats_needed == 0:
        return {
            "status": "error",
            "error_message": "Set either vacant_seats (offering) or seats_needed (looking).",
        }
    if vacant_seats > 0 and seats_needed > 0:
        return {
            "status": "error",
            "error_message": "Set only one of vacant_seats or seats_needed for a single listing.",
        }

    dest_place = destination_place_id.strip()
    dest_lbl = destination_label.strip()
    if not dest_place or not dest_lbl:
        return {
            "status": "error",
            "error_message": "destination_place_id and destination_label are required.",
        }

    with session_scope() as session:
        user = _get_user_by_external_id(session, user_id)
        if user is None:
            return {
                "status": "error",
                "error_message": f"Unknown user_id {user_id!r}. Create a users row first.",
            }

        post = CommutePost(
            user_id=user.id,
            origin=origin.strip(),
            origin_place_id=origin_place_id.strip() if origin_place_id else None,
            origin_lat=origin_lat,
            origin_lng=origin_lng,
            origin_label=origin_label.strip() if origin_label else None,
            destination=_norm_place(destination),
            destination_place_id=dest_place,
            destination_lat=destination_lat,
            destination_lng=destination_lng,
            destination_label=dest_lbl,
            time_bucket=time_bucket.strip().lower() or "flex",
            vacant_seats=vacant_seats,
            seats_needed=seats_needed,
        )
        session.add(post)
        session.flush()
        return {
            "status": "success",
            "commute_post": _commute_post_to_dict(post, user.external_user_id),
        }


def _time_compatible(a: str, b: str) -> bool:
    if a == "flex" or b == "flex":
        return True
    return a == b


def _same_destination(a: CommutePost, b: CommutePost) -> bool:
    if a.destination_place_id and b.destination_place_id:
        return a.destination_place_id == b.destination_place_id
    return _norm_place(a.destination) == _norm_place(b.destination)


def _pair_compatible(
    offer: CommutePost, offer_user: str, need: CommutePost, need_user: str
) -> bool:
    if offer_user == need_user:
        return False
    if offer.vacant_seats <= 0 or need.seats_needed <= 0:
        return False
    if not _same_destination(offer, need):
        return False
    if not _time_compatible(offer.time_bucket, need.time_bucket):
        return False
    return offer.vacant_seats >= need.seats_needed


def confirm_trip(offer_commute_post_id: str, need_commute_post_id: str) -> dict[str, Any]:
    """
    Insert a finalized ``Trip`` row linking the offer post to the need post.

    Production note: real deployments should only call this after **verified mutual
    agreement** (in-app confirm from both users, signed intents, etc.). For now this
    only checks posts exist, roles match (offer vs need), users differ, and the same
    matching rules as ``find_matches_for_commute_post`` hold.
    """
    try:
        offer_id = uuid.UUID(offer_commute_post_id.strip())
        need_id = uuid.UUID(need_commute_post_id.strip())
    except ValueError:
        return {"status": "error", "error_message": "Invalid commute post UUID."}

    if offer_id == need_id:
        return {"status": "error", "error_message": "Offer and need must be two different posts."}

    with session_scope() as session:
        offer = session.get(CommutePost, offer_id)
        need = session.get(CommutePost, need_id)
        if offer is None or need is None:
            return {
                "status": "error",
                "error_message": "One or both commute posts were not found.",
            }

        offer_user = session.get(User, offer.user_id)
        need_user = session.get(User, need.user_id)
        offer_ext = offer_user.external_user_id if offer_user else ""
        need_ext = need_user.external_user_id if need_user else ""

        if not _pair_compatible(offer, offer_ext, need, need_ext):
            return {
                "status": "error",
                "error_message": (
                    "Posts are not a valid offer/need pair (same rules as matching: "
                    "different users, offer has seats, need wants seats, destination and time align)."
                ),
            }

        trip = Trip(offer_commute_post_id=offer_id, need_commute_post_id=need_id)
        session.add(trip)
        session.flush()
        return {
            "status": "success",
            "trip": {
                "trip_id": str(trip.id),
                "offer_commute_post_id": str(offer_id),
                "need_commute_post_id": str(need_id),
            },
        }


def find_matches_for_commute_post(commute_post_id: str) -> dict[str, Any]:
    """Return commute posts that can pair with the given post (offer<->request)."""
    with session_scope() as session:
        base, base_ext = _get_commute_post_with_user(session, commute_post_id)
        if base is None:
            return {
                "status": "error",
                "error_message": f"Unknown commute_post_id {commute_post_id!r}.",
            }

        others = session.scalars(select(CommutePost).where(CommutePost.id != base.id)).all()
        matches: list[dict[str, Any]] = []

        for other in others:
            other_user_row = session.get(User, other.user_id)
            other_ext = other_user_row.external_user_id if other_user_row else ""

            if base.vacant_seats > 0 and other.seats_needed > 0 and _pair_compatible(
                base, base_ext, other, other_ext
            ):
                matches.append(
                    {
                        "relationship": "your_offer_their_need",
                        "their_commute_post": _commute_post_to_dict(other, other_ext),
                    }
                )
            elif base.seats_needed > 0 and other.vacant_seats > 0 and _pair_compatible(
                other, other_ext, base, base_ext
            ):
                matches.append(
                    {
                        "relationship": "their_offer_your_need",
                        "their_commute_post": _commute_post_to_dict(other, other_ext),
                    }
                )

        return {
            "status": "success",
            "your_commute_post": _commute_post_to_dict(base, base_ext),
            "match_count": len(matches),
            "matches": matches,
        }


def list_commute_posts(destination_substring: Optional[str] = None) -> dict[str, Any]:
    """List registered commute posts; optional filter on destination text or label."""
    with session_scope() as session:
        q: Select[tuple[CommutePost]] = select(CommutePost).order_by(CommutePost.created_at.desc())
        posts = list(session.scalars(q).all())

        if destination_substring:
            sub = _norm_place(destination_substring)
            posts = [
                p
                for p in posts
                if sub in _norm_place(p.destination)
                or sub in _norm_place(p.destination_label)
            ]

        rows: list[dict[str, Any]] = []
        for p in posts:
            u = session.get(User, p.user_id)
            ext = u.external_user_id if u else ""
            rows.append(_commute_post_to_dict(p, ext))

        return {"status": "success", "count": len(rows), "commute_posts": rows}
