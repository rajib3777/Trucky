import time
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any, Optional

import requests


# ========= CONFIG =========
# IMPORTANT: Nominatim requires a real contact in User-Agent (email or website).
USER_AGENT = "TruckyApp/1.0 (contact: you@example.com)"
OSRM_URL = "https://router.project-osrm.org"

# Nominatim usage guideline: be polite (rate-limit yourself)
MIN_SECONDS_BETWEEN_NOMINATIM_CALLS = 1.1

# Retry settings
HTTP_TIMEOUT = 12
MAX_RETRIES = 4
BACKOFF_SECONDS = 1.2


# ========= ERRORS =========
class MapServiceError(Exception):
    """Raised when route generation fails due to geocoding or routing issues."""


# ========= INTERNAL STATE =========
_last_nominatim_call_ts = 0.0


def _sleep_backoff(attempt: int) -> None:
    # simple exponential-ish backoff
    time.sleep(BACKOFF_SECONDS * (attempt + 1))


def _polite_nominatim_wait() -> None:
    global _last_nominatim_call_ts
    now = time.time()
    elapsed = now - _last_nominatim_call_ts
    if elapsed < MIN_SECONDS_BETWEEN_NOMINATIM_CALLS:
        time.sleep(MIN_SECONDS_BETWEEN_NOMINATIM_CALLS - elapsed)
    _last_nominatim_call_ts = time.time()


def _get_json(session: requests.Session, url: str, *, params: Optional[dict] = None, headers: Optional[dict] = None) -> Any:
    # Centralized HTTP GET with retries + clear errors
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            r = session.get(url, params=params, headers=headers, timeout=HTTP_TIMEOUT)
            # Many services return useful body even on non-200; keep it simple:
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            last_exc = exc
            _sleep_backoff(attempt)
    raise MapServiceError(f"HTTP request failed after {MAX_RETRIES} retries: {url} | last error: {last_exc}")


def _nominatim_geocode(session: requests.Session, query: str) -> Tuple[float, float]:
    """
    Tries 3 geocoders in order:
      1) Nominatim (OSM)
      2) geocode.maps.co
      3) Open-Meteo geocoding
    If all fail, raises MapServiceError (NO random fallback).
    """
    if not query or not query.strip():
        raise MapServiceError("Geocoding query is empty.")

    # ---- 1) Nominatim ----
    nominatim_url = "https://nominatim.openstreetmap.org/search"
    nominatim_params = {"q": query, "format": "json", "limit": 1}
    nominatim_headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "en",
    }

    for attempt in range(MAX_RETRIES):
        try:
            _polite_nominatim_wait()
            data = _get_json(session, nominatim_url, params=nominatim_params, headers=nominatim_headers)
            if isinstance(data, list) and data:
                return float(data[0]["lat"]), float(data[0]["lon"])
        except Exception:
            _sleep_backoff(attempt)

    # ---- 2) geocode.maps.co ----
    try:
        url = "https://geocode.maps.co/search"
        data = _get_json(session, url, params={"q": query})
        if isinstance(data, list) and data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass

    # ---- 3) Open-Meteo ----
    try:
        url = "https://geocoding-api.open-meteo.com/v1/search"
        data = _get_json(session, url, params={"name": query, "count": 1})
        if isinstance(data, dict) and data.get("results"):
            d = data["results"][0]
            return float(d["latitude"]), float(d["longitude"])
    except Exception:
        pass

    raise MapServiceError(f"Geocoding failed for: {query}")


def _osrm_route(session: requests.Session, start_latlon: Tuple[float, float], end_latlon: Tuple[float, float]) -> Tuple[float, float, List[List[float]]]:
    """
    Returns (distance_miles, duration_hours, route_latlon_points)
    Raises MapServiceError if OSRM returns no route.
    """
    slat, slon = start_latlon
    dlat, dlon = end_latlon

    url = f"{OSRM_URL}/route/v1/driving/{slon},{slat};{dlon},{dlat}"
    params = {"overview": "full", "geometries": "geojson"}

    data = _get_json(session, url, params=params)

    routes = (data or {}).get("routes") or []
    if not routes:
        code = (data or {}).get("code")
        msg = (data or {}).get("message")
        raise MapServiceError(f"OSRM: no route found. code={code} message={msg}")

    route = routes[0]
    distance_miles = float(route["distance"]) / 1609.34
    duration_hours = float(route["duration"]) / 3600.0

    coords = route.get("geometry", {}).get("coordinates") or []
    if not coords:
        raise MapServiceError("OSRM returned empty route geometry.")

    # OSRM returns [lon, lat]; convert to [lat, lon]
    latlon = [[float(c[1]), float(c[0])] for c in coords]
    return distance_miles, duration_hours, latlon


def _assemble(distance_miles: float, duration_hours: float, route: List[List[float]], pickup: str, dropoff: str) -> Dict[str, Any]:
    if not route:
        raise MapServiceError("Cannot assemble map info: route is empty.")

    mid = route[len(route) // 2]
    stops = [
        {"pos": route[0], "label": f"Pickup: {pickup}"},
        {"pos": mid, "label": "Midpoint"},
        {"pos": route[-1], "label": f"Dropoff: {dropoff}"},
    ]

    return {
        "distance_miles": round(distance_miles, 2),
        "duration_hours": round(duration_hours, 2),
        "mapInfo": {
            "route": route,
            "stops": stops,
            "mapCenter": mid,
        },
    }


def generate_route_map(pickup: str, dropoff: str) -> Dict[str, Any]:
    """
    Main function you call.
    Raises MapServiceError with a clean message if anything fails.
    """
    if not pickup or not pickup.strip():
        raise MapServiceError("Pickup is empty.")
    if not dropoff or not dropoff.strip():
        raise MapServiceError("Dropoff is empty.")

    with requests.Session() as session:
        try:
            start = _nominatim_geocode(session, pickup)
            end = _nominatim_geocode(session, dropoff)
            distance, duration, route = _osrm_route(session, start, end)
            return _assemble(distance, duration, route, pickup, dropoff)
        except MapServiceError:
            # already clean, just re-raise
            raise
        except Exception as exc:
            # anything unexpected
            raise MapServiceError(f"Route generation failed: {exc}") from exc


# ---------- OPTIONAL: quick test ----------
if __name__ == "__main__":
    # Change these to your real locations
    pickup = "Dhaka, Bangladesh"
    dropoff = "Chittagong, Bangladesh"
    try:
        result = generate_route_map(pickup, dropoff)
        print(result)
    except MapServiceError as e:
        print("ERROR:", e)