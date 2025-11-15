
import requests


USER_AGENT = "trucky-backend/1.0 (contact@example.com)"


class MapServiceError(Exception):
    """Raised when routing / geocoding fails."""



def _nominatim_geocode(query: str):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": query, "format": "json", "limit": 1}
    headers = {"User-Agent": USER_AGENT}

    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()

        if not data:
            raise MapServiceError(f"Nominatim: No result for '{query}'")

        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])
        return (lat, lon)

    except Exception as e:
        raise MapServiceError(f"Geocode error: {e}")



def _osrm_route(start_latlon, end_latlon):
    slat, slon = start_latlon
    dlat, dlon = end_latlon

    url = f"https://router.project-osrm.org/route/v1/driving/{slon},{slat};{dlon},{dlat}"
    params = {
        "overview": "full",
        "geometries": "geojson",
        "alternatives": "false"
    }

    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()

        routes = data.get("routes") or []
        if not routes:
            raise MapServiceError("OSRM: No route found")

        route = routes[0]

        # Convert distances/durations
        distance_miles = route["distance"] / 1609.34      # meters → miles
        duration_hours = route["duration"] / 3600.0       # seconds → hours

        # Convert coords → [lat, lon]
        coords = route["geometry"]["coordinates"]
        route_latlon = [[c[1], c[0]] for c in coords]

        return distance_miles, duration_hours, route_latlon

    except Exception as e:
        raise MapServiceError(f"OSRM error: {e}")


# 

def _assemble(distance_miles, duration_hours, route, pickup, dropoff):
    mid_index = len(route) // 2
    map_center = route[mid_index]

    stops = [
        {"pos": route[0], "label": f"Pickup: {pickup}"},
        {"pos": map_center, "label": "Midpoint"},
        {"pos": route[-1], "label": f"Dropoff: {dropoff}"}
    ]

    return {
        "distance_miles": round(distance_miles, 2),
        "duration_hours": round(duration_hours, 2),
        "mapInfo": {
            "route": route,
            "stops": stops,
            "mapCenter": map_center
        }
    }




def generate_route_map(pickup: str, dropoff: str):
    try:
        # 1) Geocode both points
        s_latlon = _nominatim_geocode(pickup)
        e_latlon = _nominatim_geocode(dropoff)

        # 2) Get route from OSRM
        distance, duration, route = _osrm_route(s_latlon, e_latlon)

        # 3) Create output for frontend
        return _assemble(distance, duration, route, pickup, dropoff)

    except Exception as exc:
        # Clear descriptive error for debugging
        raise MapServiceError(f"Route generation failed: {exc}")