from services import ride_services as rs


def register_user(user_id: str) -> dict:
    """Register a new user in the system if they don't exist."""
    return rs.register_user(user_id=user_id)
