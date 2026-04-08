from __future__ import annotations

import uuid
from datetime import datetime, timezone
from math import atan2, cos, radians, sin, sqrt
from typing import Any, Optional

from sqlalchemy import Select, select, or_
from sqlalchemy.orm import Session

from colcommute.db.models import CommutePost, Trip, TripFeedback, TripPayment, User
from colcommute.db.session import session_scope


def _norm_place(s: str) -> str:
    return " ".join(s.lower().strip().split())


def _post_kind(vacant_seats: int, seats_needed: int) -> str:
    if vacant_seats > 0 and seats_needed == 0:
        return "offer"
    if seats_needed > 0 and vacant_seats == 0:
        return "need"
    return "invalid"


def _text_location_matches(query_text: Optional[str], *candidate_texts: Optional[str]) -> bool:
    if not query_text:
        return False
    query = _norm_place(query_text)
    if not query:
        return False

    for candidate in candidate_texts:
        if not candidate:
            continue
        normalized_candidate = _norm_place(candidate)
        if query in normalized_candidate or normalized_candidate in query:
            return True
    return False


def _distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    earth_radius_km = 6371.0
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    )
    return 2 * earth_radius_km * atan2(sqrt(a), sqrt(1 - a))


def _project_xy_km(lat: float, lng: float, ref_lat: float) -> tuple[float, float]:
    x = radians(lng) * 6371.0 * cos(radians(ref_lat))
    y = radians(lat) * 6371.0
    return x, y


def _distance_point_to_segment_km(
    point_lat: float,
    point_lng: float,
    start_lat: float,
    start_lng: float,
    end_lat: float,
    end_lng: float,
) -> tuple[float, float]:
    ref_lat = (point_lat + start_lat + end_lat) / 3
    px, py = _project_xy_km(point_lat, point_lng, ref_lat)
    sx, sy = _project_xy_km(start_lat, start_lng, ref_lat)
    ex, ey = _project_xy_km(end_lat, end_lng, ref_lat)

    dx = ex - sx
    dy = ey - sy
    segment_length_sq = dx * dx + dy * dy
    if segment_length_sq == 0:
        return sqrt((px - sx) ** 2 + (py - sy) ** 2), 0.0

    projection = ((px - sx) * dx + (py - sy) * dy) / segment_length_sq
    clamped = max(0.0, min(1.0, projection))
    closest_x = sx + clamped * dx
    closest_y = sy + clamped * dy
    distance = sqrt((px - closest_x) ** 2 + (py - closest_y) ** 2)
    return distance, clamped


def _destination_compatible(a: CommutePost, b: CommutePost, tolerance_km: float = 2.0) -> bool:
    if a.destination_place_id and b.destination_place_id:
        return a.destination_place_id == b.destination_place_id
    if (
        a.destination_lat is not None
        and a.destination_lng is not None
        and b.destination_lat is not None
        and b.destination_lng is not None
    ):
        return (
            _distance_km(
                a.destination_lat,
                a.destination_lng,
                b.destination_lat,
                b.destination_lng,
            )
            <= tolerance_km
        )
    return _norm_place(a.destination) == _norm_place(b.destination)


def _origin_on_offer_route(
    offer: CommutePost,
    need: CommutePost,
    corridor_km: float = 3.0,
) -> bool:
    if (
        offer.origin_lat is None
        or offer.origin_lng is None
        or offer.destination_lat is None
        or offer.destination_lng is None
        or need.origin_lat is None
        or need.origin_lng is None
    ):
        if offer.origin_place_id and need.origin_place_id:
            return offer.origin_place_id == need.origin_place_id
        return _norm_place(offer.origin) == _norm_place(need.origin)

    distance_to_route, projection = _distance_point_to_segment_km(
        need.origin_lat,
        need.origin_lng,
        offer.origin_lat,
        offer.origin_lng,
        offer.destination_lat,
        offer.destination_lng,
    )
    return 0.0 <= projection <= 1.0 and distance_to_route <= corridor_km


def _origin_search_matches(
    post: CommutePost,
    requested: CommutePost,
    origin_query_text: Optional[str] = None,
) -> bool:
    if _text_location_matches(origin_query_text, post.origin, post.origin_label):
        return True
    if (
        _text_location_matches(origin_query_text, requested.origin, requested.origin_label)
        and _text_location_matches(post.origin, requested.origin, requested.origin_label)
    ):
        return True

    kind = _post_kind(post.vacant_seats, post.seats_needed)
    if kind == "offer":
        return _origin_on_offer_route(post, requested)

    if post.origin_place_id and requested.origin_place_id:
        return post.origin_place_id == requested.origin_place_id
    return _text_location_matches(post.origin, requested.origin, requested.origin_label)


def _commute_post_to_dict(post: CommutePost, external_user_id: str) -> dict[str, Any]:
    return {
        "commute_post_id": str(post.id),
        "user_id": external_user_id,
        "origin": post.origin_label or post.origin,
        "destination": post.destination_label or post.destination,
        "origin_normalized": post.origin,
        "destination_normalized": post.destination,
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
        "post_kind": _post_kind(post.vacant_seats, post.seats_needed),
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
    Register a commute post (listing). user_id is users.external_user_id for an existing user row.
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

    normalized_origin = _norm_place(origin)
    normalized_destination = _norm_place(destination)
    origin_text = origin.strip()
    destination_text = destination.strip()
    normalized_time_bucket = time_bucket.strip().lower() or "flex"
    post_kind = _post_kind(vacant_seats, seats_needed)

    with session_scope() as session:
        user = _get_user_by_external_id(session, user_id)
        if user is None:
            return {
                "status": "error",
                "error_message": f"Unknown user_id {user_id!r}. Create a users row first.",
            }

        # Prevent duplicate posts for same user, destination and time
        candidates = session.scalars(
            select(CommutePost).where(
                CommutePost.user_id == user.id,
                CommutePost.destination_place_id == dest_place,
                CommutePost.time_bucket == normalized_time_bucket,
            )
        ).all()
        existing = next(
            (
                post
                for post in candidates
                if (
                    (post_kind == "offer" and post.vacant_seats > 0)
                    or (post_kind == "need" and post.seats_needed > 0)
                )
                and (
                    (origin_place_id and post.origin_place_id == origin_place_id)
                    or (not origin_place_id and _norm_place(post.origin) == normalized_origin)
                )
            ),
            None,
        )
        if existing:
            return {
                "status": "error",
                "error_message": (
                    f"You already have a {post_kind} post for this route and time. "
                    f"Use your existing post ID: {str(existing.id)}"
                ),
            }

        post = CommutePost(
            user_id=user.id,
            origin=origin_text,
            origin_place_id=origin_place_id.strip() if origin_place_id else None,
            origin_lat=origin_lat,
            origin_lng=origin_lng,
            origin_label=origin_label.strip() if origin_label else None,
            destination=destination_text,
            destination_place_id=dest_place,
            destination_lat=destination_lat,
            destination_lng=destination_lng,
            destination_label=dest_lbl,
            time_bucket=normalized_time_bucket,
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
    return _destination_compatible(a, b)


def _pair_compatible(
    offer: CommutePost, offer_user: str, need: CommutePost, need_user: str
) -> bool:
    if offer_user == need_user:
        return False
    if offer.vacant_seats <= 0 or need.seats_needed <= 0:
        return False
    if not _same_destination(offer, need):
        return False
    if not _origin_on_offer_route(offer, need):
        return False
    if not _time_compatible(offer.time_bucket, need.time_bucket):
        return False
    return offer.vacant_seats >= need.seats_needed


def confirm_trip(offer_commute_post_id: str, need_commute_post_id: str) -> dict[str, Any]:
    """
    Insert a finalized Trip row linking the offer post to the need post.
    Production note: real deployments should only call this after verified mutual
    agreement (in-app confirm from both users, signed intents, etc.).
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

        trip = Trip(
            offer_commute_post_id=offer_id,
            need_commute_post_id=need_id,
            status="confirmed",
        )
        offer.vacant_seats -= need.seats_needed  # decrease available seats
        session.add(trip)
        session.flush()
        return {
            "status": "success",
            "trip": {
                "trip_id": str(trip.id),
                "offer_commute_post_id": str(offer_id),
                "need_commute_post_id": str(need_id),
                "remaining_seats": offer.vacant_seats,
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

        others = session.scalars(
            select(CommutePost)
            .where(CommutePost.id != base.id)
            .limit(50)  
        ).all()

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


def list_commute_posts(
    destination_substring: Optional[str] = None,
    origin_substring: Optional[str] = None,
    post_kind: Optional[str] = None,
) -> dict[str, Any]:
    """List active commute posts; optional filters on origin, destination, and post kind."""
    with session_scope() as session:
        q: Select[tuple[CommutePost]] = select(CommutePost).where(
            or_(
                CommutePost.vacant_seats > 0,   # active offers
                CommutePost.seats_needed > 0,   # active requests
            )
        ).order_by(CommutePost.created_at.desc())

        posts = list(session.scalars(q).all())

        if post_kind in {"offer", "need"}:
            posts = [
                p for p in posts if _post_kind(p.vacant_seats, p.seats_needed) == post_kind
            ]

        if origin_substring:
            sub = _norm_place(origin_substring)
            posts = [
                p
                for p in posts
                if sub in _norm_place(p.origin)
                or (p.origin_label and sub in _norm_place(p.origin_label))
            ]

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


def search_commute_posts_for_route(
    origin_text: Optional[str],
    origin_place_id: Optional[str],
    origin_lat: float,
    origin_lng: float,
    destination_text: Optional[str],
    destination_place_id: Optional[str],
    destination_lat: float,
    destination_lng: float,
    time_bucket: Optional[str] = None,
    post_kind: Optional[str] = None,
) -> dict[str, Any]:
    """Search commute posts whose route is compatible with the requested origin and destination."""
    requested = CommutePost(
        user_id=uuid.uuid4(),
        origin=origin_text or "query-origin",
        origin_place_id=origin_place_id,
        origin_lat=origin_lat,
        origin_lng=origin_lng,
        origin_label=origin_text or "query-origin",
        destination=destination_text or "query-destination",
        destination_place_id=destination_place_id or "",
        destination_lat=destination_lat,
        destination_lng=destination_lng,
        destination_label=destination_text or "query-destination",
        time_bucket=(time_bucket or "flex").strip().lower() or "flex",
        vacant_seats=0,
        seats_needed=1 if post_kind == "offer" else 0,
    )

    with session_scope() as session:
        posts = session.scalars(select(CommutePost).limit(100)).all()
        def _collect(kind_filter: Optional[str]) -> list[dict[str, Any]]:
            rows: list[dict[str, Any]] = []
            for post in posts:
                kind = _post_kind(post.vacant_seats, post.seats_needed)
                if kind_filter in {"offer", "need"} and kind != kind_filter:
                    continue
                if time_bucket and not _time_compatible(post.time_bucket, requested.time_bucket):
                    continue
                if not _destination_compatible(post, requested):
                    continue
                if not _origin_search_matches(post, requested, origin_text):
                    continue

                user = session.get(User, post.user_id)
                ext = user.external_user_id if user else ""
                rows.append(_commute_post_to_dict(post, ext))
            return rows

        primary_rows = _collect(post_kind)
        alternate_kind = None
        alternate_rows: list[dict[str, Any]] = []
        if post_kind == "offer":
            alternate_kind = "need"
            alternate_rows = _collect(alternate_kind)
        elif post_kind == "need":
            alternate_kind = "offer"
            alternate_rows = _collect(alternate_kind)

        return {
            "status": "success",
            "post_kind": post_kind,
            "count": len(primary_rows),
            "commute_posts": primary_rows,
            "alternate_post_kind": alternate_kind,
            "alternate_count": len(alternate_rows),
            "alternate_commute_posts": alternate_rows,
            "message": (
                "No matching ride offers found right now."
                if post_kind == "offer" and not primary_rows
                else "Search completed."
            ),
        }


def register_user(user_id: str) -> dict:
    """Register a new user if they don't already exist."""
    with session_scope() as session:
        existing = _get_user_by_external_id(session, user_id)
        if existing:
            return {"status": "already_exists", "user_id": user_id}

        user = User(
            external_user_id=user_id.strip()
        )
        session.add(user)
        session.flush()
        return {"status": "success", "user_id": user_id}


def start_trip(trip_id: str) -> dict[str, Any]:
    try:
        parsed_id = uuid.UUID(trip_id.strip())
    except ValueError:
        return {"status": "error", "error_message": "Invalid trip UUID."}

    with session_scope() as session:
        trip = session.get(Trip, parsed_id)
        if trip is None:
            return {"status": "error", "error_message": "Trip not found."}
        if trip.status not in {"confirmed", "paid"}:
            return {"status": "error", "error_message": f"Trip cannot be started from status '{trip.status}'."}

        trip.status = "in_progress"
        trip.started_at = trip.started_at or datetime.now(timezone.utc)
        session.flush()
        return {"status": "success", "trip_id": str(trip.id), "trip_status": trip.status}


def complete_trip(trip_id: str) -> dict[str, Any]:
    try:
        parsed_id = uuid.UUID(trip_id.strip())
    except ValueError:
        return {"status": "error", "error_message": "Invalid trip UUID."}

    with session_scope() as session:
        trip = session.get(Trip, parsed_id)
        if trip is None:
            return {"status": "error", "error_message": "Trip not found."}
        if trip.status not in {"confirmed", "in_progress", "paid"}:
            return {"status": "error", "error_message": f"Trip cannot be completed from status '{trip.status}'."}

        trip.started_at = trip.started_at or datetime.now(timezone.utc)
        trip.completed_at = datetime.now(timezone.utc)
        trip.status = "completed"
        session.flush()
        return {"status": "success", "trip_id": str(trip.id), "trip_status": trip.status}


def process_trip_payment(trip_id: str, users: list[str], total_fare: float) -> dict[str, Any]:
    try:
        parsed_id = uuid.UUID(trip_id.strip())
    except ValueError:
        return {"status": "error", "error_message": "Invalid trip UUID."}
    if not users:
        return {"status": "error", "error_message": "No users provided for payment splitting."}
    if total_fare <= 0:
        return {"status": "error", "error_message": "total_fare must be greater than 0."}

    with session_scope() as session:
        trip = session.get(Trip, parsed_id)
        if trip is None:
            return {"status": "error", "error_message": "Trip not found."}
        if trip.status not in {"completed", "paid"}:
            return {"status": "error", "error_message": "Complete the trip before processing payment."}

        share = round(total_fare / len(users), 2)
        payments: list[dict[str, Any]] = []
        for user_id in users:
            payment = TripPayment(
                trip_id=trip.id,
                user_id=user_id,
                amount=share,
                status="paid",
            )
            session.add(payment)
            payments.append({"user_id": user_id, "amount": share, "status": "paid"})

        trip.status = "paid"
        session.flush()
        return {
            "status": "success",
            "ride_id": str(trip.id),
            "trip_status": trip.status,
            "total_fare": round(total_fare, 2),
            "split_share": share,
            "payment_reports": payments,
        }


def log_trip_feedback(
    ride_id: str, user_id: str, feedback_score: int, feedback_text: str
) -> dict[str, Any]:
    try:
        parsed_id = uuid.UUID(ride_id.strip())
    except ValueError:
        return {"status": "error", "error_message": "Invalid trip UUID."}
    if not 1 <= feedback_score <= 5:
        return {"status": "error", "error_message": "feedback_score must be between 1 and 5."}

    with session_scope() as session:
        trip = session.get(Trip, parsed_id)
        if trip is None:
            return {"status": "error", "error_message": "Trip not found."}

        feedback = TripFeedback(
            trip_id=trip.id,
            user_id=user_id,
            feedback_score=feedback_score,
            feedback_text=feedback_text.strip(),
        )
        session.add(feedback)
        session.flush()
        return {
            "status": "success",
            "message": f"Feedback for ride {ride_id} has been logged successfully.",
            "feedback_id": str(feedback.id),
        }
