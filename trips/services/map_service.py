# trips/services/map_service.py
import os, requests

MAP_PROVIDER = os.getenv("MAP_PROVIDER", "auto")  
MAP_API_KEY  = os.getenv("MAP_API_KEY", "")

class MapServiceError(Exception):
    """Raised when map / routing API fails."""


def _ors_geocode(text: str):
    url = "https://api.openrouteservice.org/geocode/search"
    params = {"api_key": MAP_API_KEY, "text": text, "size": 1}
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    feats = data.get("features") or []
    if not feats:
        raise MapServiceError(f"ORS geocode: no result for {text!r}")
    return feats[0]["geometry"]["coordinates"]  # [lon, lat]

def _ors_route(start_lonlat, end_lonlat):
    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {"Authorization": MAP_API_KEY, "Content-Type": "application/json"}
    body = {"coordinates": [start_lonlat, end_lonlat]}
    r = requests.post(url, json=body, headers=headers, timeout=30)
    r.raise_for_status()
    data = r.json()
    feat = data["features"][0]
    props, geom = feat["properties"], feat["geometry"]
    distance_km    = props["summary"]["distance"] / 1000.0
    duration_hours = props["summary"]["duration"] / 3600.0
    # ORS coords are [lon,lat]; UI usually wants [lat,lon]
    route_latlon   = [[c[1], c[0]] for c in geom["coordinates"]]
    distance_miles = distance_km * 0.621371
    return distance_miles, duration_hours, route_latlon


def _nominatim_geocode(text: str):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": text, "format": "json", "limit": 1}
    headers = {"User-Agent": "trucky-backend/1.0 (support@example.com)"}  # required by Nominatim
    r = requests.get(url, params=params, headers=headers, timeout=15)
    r.raise_for_status()
    data = r.json()
    if not data:
        raise MapServiceError(f"Nominatim: no result for {text!r}")
    return float(data[0]["lat"]), float(data[0]["lon"])  # [lat, lon]

def _osrm_route(s_latlon, e_latlon):
    url = "https://router.project-osrm.org/route/v1/driving/{},{};{},{}".format(
        s_latlon[1], s_latlon[0], e_latlon[1], e_latlon[0]
    )
    params = {"overview": "full", "geometries": "geojson", "alternatives": "false"}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    routes = data.get("routes") or []
    if not routes:
        raise MapServiceError("OSRM: no route")
    route = routes[0]
    distance_miles = route["distance"] / 1609.344   # meters -> miles
    duration_hours = route["duration"] / 3600.0     # seconds -> hours
    route_latlon   = [[c[1], c[0]] for c in route["geometry"]["coordinates"]]
    return distance_miles, duration_hours, route_latlon


def _assemble(distance_miles, duration_hours, route, pickup, dropoff):
    mid = route[len(route)//2] if route else [0, 0]
    stops = [
        {"pos": route[0],  "label": f"Pickup: {pickup}"},
        {"pos": mid,       "label": "Midpoint"},
        {"pos": route[-1], "label": f"Dropoff: {dropoff}"},
    ]
    return {
        "distance_miles": round(distance_miles, 2),
        "duration_hours": round(duration_hours, 2),
        "mapInfo": {"route": route, "stops": stops, "mapCenter": mid},
    }

def generate_route_map(pickup: str, dropoff: str):
    try:
        use_ors = (MAP_PROVIDER == "openrouteservice") or (MAP_PROVIDER == "auto" and MAP_API_KEY)
        if use_ors:
            s = _ors_geocode(pickup)
            e = _ors_geocode(dropoff)
            dmi, hrs, route = _ors_route(s, e)
            return _assemble(dmi, hrs, route, pickup, dropoff)

        # OSRM fallback (or MAP_PROVIDER=osrm)
        s_latlon = _nominatim_geocode(pickup)
        e_latlon = _nominatim_geocode(dropoff)
        dmi, hrs, route = _osrm_route(s_latlon, e_latlon)
        return _assemble(dmi, hrs, route, pickup, dropoff)

    except Exception as exc:
        # ❌ No demo route fallback anymore—surface a clear error
        raise MapServiceError(str(exc))
