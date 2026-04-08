from __future__ import annotations

from typing import Any

from services import ride_services as rs


def process_payment(ride_id: str, users: list[str], total_fare: float) -> dict[str, Any]:
    """Persist payment records for a completed trip."""
    return rs.process_trip_payment(ride_id, users, total_fare)


def start_trip(ride_id: str) -> dict[str, Any]:
    """Mark a confirmed trip as in progress."""
    return rs.start_trip(ride_id)


def complete_trip(ride_id: str) -> dict[str, Any]:
    """Mark a trip as completed."""
    return rs.complete_trip(ride_id)


process_payment_tool = process_payment
