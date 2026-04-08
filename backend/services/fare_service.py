"""Fare splitting business logic."""

from __future__ import annotations

from typing import Any


def calculate_fare_split(total_fare: float, co_rider_count: int) -> dict[str, Any]:
    """
    Split a total fare between the driver and the additional riders.

    ``co_rider_count`` excludes the driver.
    """
    if co_rider_count <= 0:
        return {
            "status": "error",
            "error_message": "co_rider_count must be at least 1.",
        }
    if total_fare <= 0:
        return {
            "status": "error",
            "error_message": "total_fare must be greater than 0.",
        }

    per_person_share = round(total_fare / (co_rider_count + 1), 2)
    driver_share = per_person_share
    driver_savings = round(per_person_share * co_rider_count, 2)

    return {
        "status": "success",
        "total_fare": round(total_fare, 2),
        "co_rider_count": co_rider_count,
        "per_person_share": per_person_share,
        "per_rider_share": per_person_share,
        "driver_share": driver_share,
        "driver_savings": driver_savings,
        "summary": (
            f"Total Rs.{round(total_fare, 2)} split across {co_rider_count + 1} people: "
            f"each person pays Rs.{per_person_share}. "
            f"Riders together cover Rs.{driver_savings}."
        ),
    }
