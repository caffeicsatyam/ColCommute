from __future__ import annotations

from typing import Any

from services import ride_services as rs


def log_feedback(
    ride_id: str,
    user_id: str,
    feedback_score: int,
    feedback_text: str,
) -> dict[str, Any]:
    """Persist feedback for a trip."""
    return rs.log_trip_feedback(ride_id, user_id, feedback_score, feedback_text)


log_feedback_tool = log_feedback
