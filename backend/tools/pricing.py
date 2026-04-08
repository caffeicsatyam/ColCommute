from __future__ import annotations

from typing import Any

from services.fare_service import calculate_fare_split as service_calculate_fare_split


def calculate_fare_split(
    total_fare: float,
    seats_needed: int = 0,
    vacant_seats: int = 0,
    co_rider_count: int = 0,
) -> dict[str, Any]:
    """
    Split a fare for a ride.

    Accepted rider-count inputs:
    - ``co_rider_count``: explicit number of additional riders
    - ``seats_needed``: rider count in a request or offer pairing
    - ``vacant_seats``: rider count when the user phrases it as filled vacant seats
    """
    positive_inputs = {
        "co_rider_count": co_rider_count,
        "seats_needed": seats_needed,
        "vacant_seats": vacant_seats,
    }
    provided = {key: value for key, value in positive_inputs.items() if value > 0}

    if not provided:
        return {
            "status": "error",
            "error_message": (
                "Provide at least one of co_rider_count, seats_needed, or vacant_seats."
            ),
        }

    if len(set(provided.values())) > 1:
        return {
            "status": "error",
            "error_message": (
                "Provide only one rider count, or make all provided counts equal."
            ),
        }

    riders = next(iter(provided.values()))
    result = service_calculate_fare_split(total_fare=total_fare, co_rider_count=riders)
    if result.get("status") != "success":
        return result

    result["seats_needed"] = riders
    result["vacant_seats"] = riders
    return result
