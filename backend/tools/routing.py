import os
import httpx
from typing import Dict, Any

def get_route(origin: str, destination: str) -> Dict[str, Any]:
    """
    Gets the real route between origin and destination using Google Maps Directions API.
    Returns distance, duration, and step-by-step directions.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY") or os.getenv("GOOGLE_MAP_API_KEY")
    url = "https://maps.googleapis.com/maps/api/directions/json"
    if not api_key:
        return {"status": "error", "error_message": "Google Maps API key is not configured."}

    try:
        resp = httpx.get(
            url,
            params={
                "origin": origin,
                "destination": destination,
                "region": "IN",
                "key": api_key,
            },
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPError as exc:
        return {"status": "error", "error_message": f"Could not get route: {exc}"}

    if data["status"] != "OK":
        return {"status": "error", "error_message": f"Could not get route: {data['status']}"}

    leg = data["routes"][0]["legs"][0]
    steps = [step["html_instructions"] for step in leg["steps"]]

    return {
        "status": "success",
        "origin": leg["start_address"],
        "destination": leg["end_address"],
        "distance": leg["distance"]["text"],
        "duration": leg["duration"]["text"],
        "steps": steps
    }
