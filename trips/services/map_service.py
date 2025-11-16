import requests
import time

USER_AGENT = "TruckyApp/1.0 (contact: your-email@gmail.com)"
OSRM_URL = "https://router.project-osrm.org"


class MapServiceError(Exception):
    pass


def _nominatim_geocode(query):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": query, "format": "json", "limit": 1}
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "en",
    }

    # Retry logic for Render slow network
    for attempt in range(4):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=10)
            r.raise_for_status()
            data = r.json()

            if data:
                return (float(data[0]["lat"]), float(data[0]["lon"]))

        except Exception:
            time.sleep(1.5)  # wait & retry

    # Fallback to fixed geocode (never fail)
    fallback = {
        "dhaka": (23.8103, 90.4125),
        "chittagong": (22.3569, 91.7832),
        "new york": (40.7128, -74.0060),
        "brooklyn": (40.6782, -73.9442),
        "manhattan": (40.7831, -73.9712),
        "los angeles": (34.0522, -118.2437),
        "chicago": (41.8781, -87.6298),
    }

    key = query.lower().strip()
    if key in fallback:
        return fallback[key]

    raise MapServiceError(f"Geocode failed permanently for {query}")



def _osrm_route(start_latlon, end_latlon):
    slat, slon = start_latlon
    dlat, dlon = end_latlon

    url = f"{OSRM_URL}/route/v1/driving/{slon},{slat};{dlon},{dlat}"
    params = {"overview": "full", "geometries": "geojson"}

    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()

        routes = data.get("routes") or []
        if not routes:
            raise MapServiceError("OSRM returned no route")

        route = routes[0]

        distance_miles = route["distance"] / 1609.34
        duration_hours = route["duration"] / 3600.0

        coords = route["geometry"]["coordinates"]  # [lon,lat]
        route_latlon = [[c[1], c[0]] for c in coords]

        return distance_miles, duration_hours, route_latlon

    except Exception as e:
        raise MapServiceError(f"OSRM error: {e}")



def _assemble(distance_miles, duration_hours, route, pickup, dropoff):
    mid_index = len(route) // 2
    center = route[mid_index]

    stops = [
        {"pos": route[0], "label": f"Pickup: {pickup}"},
        {"pos": center, "label": "Midpoint"},
        {"pos": route[-1], "label": f"Dropoff: {dropoff}"},
    ]

    return {
        "distance_miles": round(distance_miles, 2),
        "duration_hours": round(duration_hours, 2),
        "mapInfo": {
            "route": route,
            "stops": stops,
            "mapCenter": center,
        },
    }



def generate_route_map(pickup, dropoff):
    try:
        start = _nominatim_geocode(pickup)
        end = _nominatim_geocode(dropoff)

        distance, duration, route = _osrm_route(start, end)

        return _assemble(distance, duration, route, pickup, dropoff)

    except Exception as exc:
        raise MapServiceError(f"Route generation failed: {exc}")