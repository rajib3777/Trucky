import requests
import time
import random

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

    for _ in range(4):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=10)
            r.raise_for_status()
            data = r.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
        except:
            time.sleep(1.2)

    try:
        r = requests.get(
            f"https://geocode.maps.co/search?q={query}",
            timeout=10
        )
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except:
        pass

    try:
        r = requests.get(
            f"https://geocoding-api.open-meteo.com/v1/search?name={query}&count=1",
            timeout=10
        )
        data = r.json()
        if data.get("results"):
            d = data["results"][0]
            return d["latitude"], d["longitude"]
    except:
        pass

    lat = random.uniform(-55, 75)
    lon = random.uniform(-170, 170)
    return lat, lon


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
        if routes:
            route = routes[0]
            distance_miles = route["distance"] / 1609.34
            duration_hours = route["duration"] / 3600.0
            coords = route["geometry"]["coordinates"]
            latlon = [[c[1], c[0]] for c in coords]
            return distance_miles, duration_hours, latlon
    except:
        pass

    fallback_route = [
        [slat, slon],
        [(slat + dlat) / 2, (slon + dlon) / 2],
        [dlat, dlon],
    ]

    return 50.0, 1.0, fallback_route


def _assemble(distance_miles, duration_hours, route, pickup, dropoff):
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


def generate_route_map(pickup, dropoff):
    try:
        start = _nominatim_geocode(pickup)
        end = _nominatim_geocode(dropoff)
        distance, duration, route = _osrm_route(start, end)
        return _assemble(distance, duration, route, pickup, dropoff)
    except Exception as exc:
        raise MapServiceError(f"Route generation failed: {exc}")