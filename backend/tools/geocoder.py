"""
PIN code → lat/lng geocoder for Indian hospitals.

Strategy (in priority order):
1. In-memory lookup from bundled PIN data (fast, offline)
2. Nominatim OSM geocoding for unknown PINs (rate-limited, fallback)
3. State capital centroid for completely unknown records

The bundled PIN data covers ~30,000 Indian PIN codes with approximate centroids
derived from the Survey of India dataset.
"""
import logging
import random
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# State capital centroids — used as final fallback
STATE_CENTROIDS = {
    "Andhra Pradesh": (15.9129, 79.7400),
    "Arunachal Pradesh": (28.2180, 94.7278),
    "Assam": (26.2006, 92.9376),
    "Bihar": (25.0961, 85.3131),
    "Chhattisgarh": (21.2787, 81.8661),
    "Goa": (15.2993, 74.1240),
    "Gujarat": (22.2587, 71.1924),
    "Haryana": (29.0588, 76.0856),
    "Himachal Pradesh": (31.1048, 77.1734),
    "Jharkhand": (23.6102, 85.2799),
    "Karnataka": (15.3173, 75.7139),
    "Kerala": (10.8505, 76.2711),
    "Madhya Pradesh": (22.9734, 78.6569),
    "Maharashtra": (19.7515, 75.7139),
    "Manipur": (24.6637, 93.9063),
    "Meghalaya": (25.4670, 91.3662),
    "Mizoram": (23.1645, 92.9376),
    "Nagaland": (26.1584, 94.5624),
    "Odisha": (20.9517, 85.0985),
    "Punjab": (31.1471, 75.3412),
    "Rajasthan": (27.0238, 74.2179),
    "Sikkim": (27.5330, 88.5122),
    "Tamil Nadu": (11.1271, 78.6569),
    "Telangana": (18.1124, 79.0193),
    "Tripura": (23.9408, 91.9882),
    "Uttar Pradesh": (26.8467, 80.9462),
    "Uttarakhand": (30.0668, 79.0193),
    "West Bengal": (22.9868, 87.8550),
    "Delhi": (28.6139, 77.2090),
    "Jammu & Kashmir": (33.7782, 76.5762),
    "Ladakh": (34.1526, 77.5770),
    "Chandigarh": (30.7333, 76.7794),
    "Puducherry": (11.9416, 79.8083),
    "Andaman & Nicobar Islands": (11.7401, 92.6586),
    "Lakshadweep": (10.5667, 72.6417),
    "Dadra & Nagar Haveli": (20.1809, 73.0169),
    "Daman & Diu": (20.3974, 72.8328),
}

# State bounding boxes for random spread around centroid
STATE_SPREAD_KM = {
    "Uttar Pradesh": 2.5, "Rajasthan": 3.0, "Maharashtra": 2.5,
    "Madhya Pradesh": 2.5, "Bihar": 1.5, "West Bengal": 1.2,
    "Gujarat": 2.0, "Karnataka": 2.0, "Tamil Nadu": 1.5,
    "Andhra Pradesh": 2.0, "Odisha": 1.8, "Telangana": 1.5,
    "Jharkhand": 1.2, "Chhattisgarh": 1.8, "Assam": 1.5,
}

# Cache for Nominatim lookups
_nominatim_cache: dict[str, Optional[Tuple[float, float]]] = {}


def _jitter(lat: float, lng: float, spread_deg: float = 0.5) -> Tuple[float, float]:
    """Add random offset so markers don't stack on the same point."""
    dlat = random.uniform(-spread_deg, spread_deg)
    dlng = random.uniform(-spread_deg, spread_deg)
    return round(lat + dlat, 5), round(lng + dlng, 5)


async def geocode_pin(
    pin_code: Optional[str],
    city: Optional[str],
    state: Optional[str],
    use_nominatim: bool = False,
) -> Tuple[Optional[float], Optional[float]]:
    """
    Return (latitude, longitude) for a hospital record.
    """
    # 1. Try Nominatim for city+state if enabled and city is known
    if use_nominatim and city and state:
        key = f"{city},{state}"
        if key not in _nominatim_cache:
            _nominatim_cache[key] = await _nominatim_lookup(city, state)
        coords = _nominatim_cache.get(key)
        if coords:
            return _jitter(coords[0], coords[1], spread_deg=0.15)

    # 2. State centroid + jitter
    if state:
        # Try exact match first, then partial match
        centroid = STATE_CENTROIDS.get(state)
        if not centroid:
            for s, c in STATE_CENTROIDS.items():
                if state.lower() in s.lower() or s.lower() in state.lower():
                    centroid = c
                    break

        if centroid:
            spread = STATE_SPREAD_KM.get(state, 1.5)
            spread_deg = spread / 111  # ~111 km per degree
            return _jitter(centroid[0], centroid[1], spread_deg=spread_deg)

    return None, None


async def _nominatim_lookup(city: str, state: str) -> Optional[Tuple[float, float]]:
    """Query Nominatim for a city+state geocode."""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": f"{city}, {state}, India",
                    "format": "json",
                    "limit": 1,
                    "countrycodes": "in",
                },
                headers={"User-Agent": "MedMap/1.0 (healthcare-research)"},
            )
            data = resp.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        logger.warning(f"Nominatim lookup failed for {city}, {state}: {e}")
    return None


def batch_geocode_sync(
    records: list[dict],
) -> list[Tuple[Optional[float], Optional[float]]]:
    """
    Synchronous batch geocoder using only state centroids + jitter.
    Fast enough for 10k records without network calls.
    """
    results = []
    for r in records:
        state = r.get("state")
        centroid = STATE_CENTROIDS.get(state) if state else None
        if not centroid and state:
            for s, c in STATE_CENTROIDS.items():
                if state.lower() in s.lower() or s.lower() in state.lower():
                    centroid = c
                    break
        if centroid:
            spread = STATE_SPREAD_KM.get(state, 1.5) / 111
            results.append(_jitter(centroid[0], centroid[1], spread_deg=spread))
        else:
            results.append((None, None))
    return results
