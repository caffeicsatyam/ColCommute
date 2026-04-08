from __future__ import annotations

from tools.pricing import calculate_fare_split


def test_pricing_with_co_rider_count() -> None:
    result = calculate_fare_split(total_fare=300, co_rider_count=2)

    assert result["status"] == "success"
    assert result["per_person_share"] == 100.0
    assert result["driver_share"] == 100.0
    assert result["driver_savings"] == 200.0


def test_pricing_accepts_seats_needed() -> None:
    result = calculate_fare_split(total_fare=450, seats_needed=2)

    assert result["status"] == "success"
    assert result["per_rider_share"] == 150.0
    assert result["seats_needed"] == 2


def test_pricing_accepts_vacant_seats() -> None:
    result = calculate_fare_split(total_fare=600, vacant_seats=3)

    assert result["status"] == "success"
    assert result["per_person_share"] == 150.0
    assert result["vacant_seats"] == 3


def test_pricing_rejects_conflicting_counts() -> None:
    result = calculate_fare_split(total_fare=300, seats_needed=1, vacant_seats=2)

    assert result["status"] == "error"
    assert "Provide only one rider count" in result["error_message"]
