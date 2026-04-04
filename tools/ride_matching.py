"""ADK function tools for ride matching — thin wrappers around ``services.ride_services``."""

from __future__ import annotations
from typing import Optional
from services import ride_services as rs


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
) -> dict:
    """Register one commute post with Places-backed destination; optional origin place fields."""
    return rs.register_commute_post(
        user_id=user_id,
        origin=origin,
        destination=destination,
        destination_place_id=destination_place_id,
        destination_lat=destination_lat,
        destination_lng=destination_lng,
        destination_label=destination_label,
        time_bucket=time_bucket,
        vacant_seats=vacant_seats,
        seats_needed=seats_needed,
        origin_place_id=origin_place_id,
        origin_lat=origin_lat,
        origin_lng=origin_lng,
        origin_label=origin_label,
    )


def find_matches_for_commute_post(commute_post_id: str) -> dict:
    """Find compatible commute posts for this commute_post_id (offer paired with need)."""
    return rs.find_matches_for_commute_post(commute_post_id)


def list_commute_posts(destination_substring: Optional[str] = None) -> dict:
    """List registered commute posts; filter by destination substring if provided."""
    return rs.list_commute_posts(destination_substring=destination_substring)


def confirm_trip(offer_commute_post_id: str, need_commute_post_id: str) -> dict:
    """
    Record a finalized trip after mutual agreement: offer post UUID, then need post UUID.

    Production should require verified consent from both users; this call only enforces
    data rules, not real-world agreement.
    """
    return rs.confirm_trip(offer_commute_post_id, need_commute_post_id)
