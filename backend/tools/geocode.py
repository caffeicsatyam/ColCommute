import os
import httpx
from dotenv import load_dotenv

load_dotenv()


def _is_expected_country(result: dict, region: str) -> bool:
    if region.upper() != "IN":
        return True

    components = result.get("address_components", [])
    for component in components:
        if "country" in component.get("types", []):
            short_name = (component.get("short_name") or "").upper()
            return short_name == "IN"

    formatted_address = (result.get("formatted_address") or "").lower()
    return "india" in formatted_address


def resolve_place(place_name: str, region: str = "IN") -> dict:
    """Resolve a place name to place_id, lat, lng, and label using Google Maps."""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY") or os.getenv("GOOGLE_MAP_API_KEY")
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    if not api_key:
        return {"status": "error", "error_message": "Google Maps API key is not configured."}
    try:
        resp = httpx.get(
            url,
            params={
                "address": place_name,
                "region": region,
                "components": f"country:{region}",
                "key": api_key,
            },
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPError as exc:
        return {"status": "error", "error_message": f"Could not resolve place: {place_name} ({exc})"}

    if data["status"] != "OK" or not data["results"]:
        return {"status": "error", "error_message": f"Could not resolve place: {place_name}"}

    result = data["results"][0]
    if not _is_expected_country(result, region):
        return {
            "status": "error",
            "error_message": f"Resolved place is outside the expected region for: {place_name}",
        }
    return {
        "status": "success",
        "place_id": result["place_id"],
        "label": result["formatted_address"],
        "lat": result["geometry"]["location"]["lat"],
        "lng": result["geometry"]["location"]["lng"],
    }
