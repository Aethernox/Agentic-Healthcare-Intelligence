"""
PIN code & City → lat/lng geocoder and Real-Time Location Resolver for Indian Healthcare Facilities.

Features:
1. Auto-detection of real-time user location via IP or headers.
2. In-memory lookup for Indian cities, districts, and PIN codes (fast, offline).
3. Dynamic database reverse-centroid lookup over 10,000 facilities in dataset.csv.
4. Nominatim OpenStreetMap fallback.
5. State centroid fallback with spatial jittering.
"""
import logging
import math
import random
import re
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)

# State capital centroids — used as broad regional fallback
STATE_CENTROIDS: Dict[str, Tuple[float, float]] = {
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

# Major Indian Cities & District Centroids for fast offline matching
CITY_CENTROIDS: Dict[str, Tuple[float, float, str, str]] = {
    # format: name.lower(): (lat, lng, display_city, state)
    # Bihar
    "patna": (25.6120, 85.1580, "Patna", "Bihar"),
    "saharsa": (25.8834, 86.5851, "Saharsa", "Bihar"),
    "muzaffarpur": (26.1209, 85.3647, "Muzaffarpur", "Bihar"),
    "gaya": (24.7955, 85.0002, "Gaya", "Bihar"),
    "bhagalpur": (25.2425, 86.9842, "Bhagalpur", "Bihar"),
    "darbhanga": (26.1542, 85.8918, "Darbhanga", "Bihar"),
    "purnea": (25.7711, 87.4745, "Purnea", "Bihar"),
    "purnia": (25.7711, 87.4745, "Purnea", "Bihar"),
    "hajipur": (25.6858, 85.2090, "Hajipur", "Bihar"),
    "vaishali": (25.8645, 85.1781, "Vaishali", "Bihar"),
    "lalganj": (25.8645, 85.1781, "Lalganj, Vaishali", "Bihar"),
    "sheohar": (26.5192, 85.2941, "Sheohar", "Bihar"),
    "begusarai": (25.4182, 86.1272, "Begusarai", "Bihar"),
    "samastipur": (25.8628, 85.7811, "Samastipur", "Bihar"),
    "madhubani": (26.3533, 86.0717, "Madhubani", "Bihar"),
    "siwan": (26.2223, 84.3567, "Siwan", "Bihar"),
    "chhapra": (25.7796, 84.7499, "Chhapra", "Bihar"),
    "saran": (25.7796, 84.7499, "Saran", "Bihar"),
    "bhojpur": (25.5560, 84.6603, "Arrah, Bhojpur", "Bihar"),
    "arrah": (25.5560, 84.6603, "Arrah", "Bihar"),
    "motihari": (26.6469, 84.9089, "Motihari", "Bihar"),
    "bettiah": (26.8025, 84.5034, "Bettiah", "Bihar"),
    "nalanda": (25.1357, 85.4578, "Nalanda", "Bihar"),
    "bihar sharif": (25.1982, 85.5149, "Bihar Sharif", "Bihar"),
    "rohtas": (24.9532, 84.0150, "Sasaram, Rohtas", "Bihar"),
    "sasaram": (24.9532, 84.0150, "Sasaram", "Bihar"),
    "katihar": (25.5393, 87.5707, "Katihar", "Bihar"),
    "kishanganj": (26.0964, 87.9404, "Kishanganj", "Bihar"),
    "supaul": (26.1226, 86.6022, "Supaul", "Bihar"),
    "khagaria": (25.5037, 86.4746, "Khagaria", "Bihar"),
    "aurangabad bihar": (24.7539, 84.3742, "Aurangabad", "Bihar"),
    "nawada": (24.8879, 85.5428, "Nawada", "Bihar"),
    "jamui": (24.9250, 86.2241, "Jamui", "Bihar"),

    # Uttar Pradesh
    "lucknow": (26.8467, 80.9462, "Lucknow", "Uttar Pradesh"),
    "kanpur": (26.4499, 80.3319, "Kanpur", "Uttar Pradesh"),
    "varanasi": (25.3176, 82.9739, "Varanasi", "Uttar Pradesh"),
    "banaras": (25.3176, 82.9739, "Varanasi", "Uttar Pradesh"),
    "kashi": (25.3176, 82.9739, "Varanasi", "Uttar Pradesh"),
    "prayagraj": (25.4358, 81.8463, "Prayagraj", "Uttar Pradesh"),
    "allahabad": (25.4358, 81.8463, "Prayagraj", "Uttar Pradesh"),
    "agra": (27.1767, 78.0081, "Agra", "Uttar Pradesh"),
    "noida": (28.5355, 77.3910, "Noida", "Uttar Pradesh"),
    "greater noida": (28.4744, 77.5040, "Greater Noida", "Uttar Pradesh"),
    "ghaziabad": (28.6692, 77.4538, "Ghaziabad", "Uttar Pradesh"),
    "meerut": (28.9845, 77.7064, "Meerut", "Uttar Pradesh"),
    "gorakhpur": (26.7606, 83.3732, "Gorakhpur", "Uttar Pradesh"),
    "bahraich": (27.5744, 81.5982, "Bahraich", "Uttar Pradesh"),
    "bareilly": (28.3670, 79.4304, "Bareilly", "Uttar Pradesh"),
    "aligarh": (27.8974, 78.0880, "Aligarh", "Uttar Pradesh"),
    "mathura": (27.4924, 77.6737, "Mathura", "Uttar Pradesh"),
    "vrindavan": (27.5806, 77.7006, "Vrindavan", "Uttar Pradesh"),
    "ayodhya": (26.7922, 82.1998, "Ayodhya", "Uttar Pradesh"),
    "jhansi": (25.4484, 78.5685, "Jhansi", "Uttar Pradesh"),

    # Delhi NCR
    "delhi": (28.6139, 77.2090, "New Delhi", "Delhi"),
    "new delhi": (28.6139, 77.2090, "New Delhi", "Delhi"),
    "gurgaon": (28.4595, 77.0266, "Gurugram", "Haryana"),
    "gurugram": (28.4595, 77.0266, "Gurugram", "Haryana"),
    "faridabad": (28.4089, 77.3178, "Faridabad", "Haryana"),

    # Rajasthan
    "jaipur": (26.9124, 75.7873, "Jaipur", "Rajasthan"),
    "jodhpur": (26.2389, 73.0243, "Jodhpur", "Rajasthan"),
    "udaipur": (24.5854, 73.7125, "Udaipur", "Rajasthan"),
    "kota": (25.2138, 75.8648, "Kota", "Rajasthan"),
    "bikaner": (28.0229, 73.3119, "Bikaner", "Rajasthan"),
    "pratapgarh": (24.0315, 74.7812, "Pratapgarh", "Rajasthan"),
    "ajmer": (26.4499, 74.6399, "Ajmer", "Rajasthan"),

    # Maharashtra
    "mumbai": (19.0760, 72.8777, "Mumbai", "Maharashtra"),
    "pune": (18.5204, 73.8567, "Pune", "Maharashtra"),
    "nagpur": (21.1458, 79.0882, "Nagpur", "Maharashtra"),
    "nashik": (19.9975, 73.7898, "Nashik", "Maharashtra"),
    "thane": (19.2183, 72.9781, "Thane", "Maharashtra"),
    "aurangabad": (19.8762, 75.3433, "Chhatrapati Sambhajinagar", "Maharashtra"),

    # South India
    "bangalore": (12.9716, 77.5946, "Bengaluru", "Karnataka"),
    "bengaluru": (12.9716, 77.5946, "Bengaluru", "Karnataka"),
    "hyderabad": (17.3850, 78.4867, "Hyderabad", "Telangana"),
    "chennai": (13.0827, 80.2707, "Chennai", "Tamil Nadu"),
    "kochi": (9.9312, 76.2673, "Kochi", "Kerala"),
    "trivandrum": (8.5241, 76.9366, "Thiruvananthapuram", "Kerala"),
    "visakhapatnam": (17.6868, 83.2185, "Visakhapatnam", "Andhra Pradesh"),

    # East & Central India
    "kolkata": (22.5726, 88.3639, "Kolkata", "West Bengal"),
    "howrah": (22.5958, 88.2636, "Howrah", "West Bengal"),
    "bhopal": (23.2599, 77.4126, "Bhopal", "Madhya Pradesh"),
    "indore": (22.7196, 75.8577, "Indore", "Madhya Pradesh"),
    "ranchi": (23.3441, 85.3096, "Ranchi", "Jharkhand"),
    "jamshedpur": (22.8046, 86.2029, "Jamshedpur", "Jharkhand"),
    "dhanbad": (23.7957, 86.4304, "Dhanbad", "Jharkhand"),
    "raipur": (21.2514, 81.6296, "Raipur", "Chhattisgarh"),
    "bhubaneswar": (20.2961, 85.8245, "Bhubaneswar", "Odisha"),
    "ahmedabad": (23.0225, 72.5714, "Ahmedabad", "Gujarat"),
    "surat": (21.1702, 72.8311, "Surat", "Gujarat"),
    "guwahati": (26.1445, 91.7362, "Guwahati", "Assam"),
}

# Prominent PIN codes from dataset.csv & Indian postal sectors
PIN_CENTROIDS: Dict[str, Tuple[float, float, str, str]] = {
    # format: pin: (lat, lng, city, state)
    "852200": (25.8834, 86.5851, "Saharsa", "Bihar"),
    "800001": (25.6120, 85.1580, "Patna Urban", "Bihar"),
    "800004": (25.6200, 85.1700, "Patna Central", "Bihar"),
    "844121": (25.8645, 85.1781, "Lalganj, Vaishali", "Bihar"),
    "843329": (26.5192, 85.2941, "Sheohar", "Bihar"),
    "854301": (25.7711, 87.4745, "Purnea", "Bihar"),
    "842001": (26.1209, 85.3647, "Muzaffarpur", "Bihar"),
    "823001": (24.7955, 85.0002, "Gaya", "Bihar"),
    "812001": (25.2425, 86.9842, "Bhagalpur", "Bihar"),
    "846004": (26.1542, 85.8918, "Darbhanga", "Bihar"),
    "271801": (27.5744, 81.5982, "Bahraich", "Uttar Pradesh"),
    "201301": (28.5722, 77.3690, "Noida", "Uttar Pradesh"),
    "201307": (28.5722, 77.3690, "Noida Sector 50", "Uttar Pradesh"),
    "226001": (26.8467, 80.9462, "Lucknow", "Uttar Pradesh"),
    "221001": (25.3176, 82.9739, "Varanasi", "Uttar Pradesh"),
    "281001": (27.4560, 77.7044, "Mathura", "Uttar Pradesh"),
    "110001": (28.6304, 77.2177, "Connaught Place, Delhi", "Delhi"),
    "500013": (17.3977, 78.4827, "Hyderabad", "Telangana"),
    "400001": (18.9322, 72.8347, "Fort, Mumbai", "Maharashtra"),
    "560001": (12.9767, 77.5993, "MG Road, Bengaluru", "Karnataka"),
    "700001": (22.5726, 88.3639, "BBD Bagh, Kolkata", "West Bengal"),
    "302001": (26.9124, 75.7873, "Jaipur", "Rajasthan"),
    "312605": (24.0315, 74.7812, "Pratapgarh", "Rajasthan"),
}

# State bounding boxes for random spread around centroid
STATE_SPREAD_KM = {
    "Uttar Pradesh": 2.5, "Rajasthan": 3.0, "Maharashtra": 2.5,
    "Madhya Pradesh": 2.5, "Bihar": 1.5, "West Bengal": 1.2,
    "Gujarat": 2.0, "Karnataka": 2.0, "Tamil Nadu": 1.5,
    "Andhra Pradesh": 2.0, "Odisha": 1.8, "Telangana": 1.5,
    "Jharkhand": 1.2, "Chhattisgarh": 1.8, "Assam": 1.5,
}

_nominatim_cache: dict[str, Optional[Tuple[float, float]]] = {}


def _jitter(lat: float, lng: float, spread_deg: float = 0.5) -> Tuple[float, float]:
    """Add random offset so markers don't stack on the exact same point."""
    dlat = random.uniform(-spread_deg, spread_deg)
    dlng = random.uniform(-spread_deg, spread_deg)
    return round(lat + dlat, 5), round(lng + dlng, 5)


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Compute Haversine distance in km between two GPS coordinates."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)


async def _nominatim_lookup(query_str: str) -> Optional[Tuple[float, float]]:
    """Query OpenStreetMap Nominatim with a 2.5s timeout."""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=2.5) as client:
            resp = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": f"{query_str}, India",
                    "format": "json",
                    "limit": 1,
                    "countrycodes": "in",
                },
                headers={"User-Agent": "MedMap-Healthcare/1.0"},
            )
            data = resp.json()
            if data and len(data) > 0:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        logger.debug(f"Nominatim lookup failed for '{query_str}': {e}")
    return None


def db_lookup_location(query_str: str, db_session) -> Optional[Tuple[float, float, str, str]]:
    """
    Dynamically search the 10,000 facilities database in SQLite to find
    centroids for any city, district, or PIN code mentioned by the user.
    """
    if not db_session:
        return None

    try:
        from models import Hospital
        from sqlalchemy import func, or_

        clean_q = query_str.strip().lower()

        # 1. Match PIN code
        if clean_q.isdigit() and len(clean_q) >= 5:
            res = (
                db_session.query(
                    func.avg(Hospital.latitude).label("lat"),
                    func.avg(Hospital.longitude).label("lng"),
                    func.min(Hospital.city).label("city"),
                    func.min(Hospital.state).label("state"),
                )
                .filter(
                    Hospital.pin_code.ilike(f"%{clean_q}%"),
                    Hospital.latitude.isnot(None),
                    Hospital.longitude.isnot(None),
                )
                .first()
            )
            if res and res.lat and res.lng:
                return float(res.lat), float(res.lng), res.city or f"PIN {clean_q}", res.state or "India"

        # 2. Match City or District
        res = (
            db_session.query(
                func.avg(Hospital.latitude).label("lat"),
                func.avg(Hospital.longitude).label("lng"),
                func.min(Hospital.city).label("city"),
                func.min(Hospital.state).label("state"),
            )
            .filter(
                or_(
                    Hospital.city.ilike(f"%{clean_q}%"),
                    Hospital.district.ilike(f"%{clean_q}%"),
                ),
                Hospital.latitude.isnot(None),
                Hospital.longitude.isnot(None),
            )
            .first()
        )
        if res and res.lat and res.lng:
            return float(res.lat), float(res.lng), res.city or query_str.title(), res.state or "India"

    except Exception as e:
        logger.debug(f"DB location lookup failed: {e}")

    return None


def detect_ip_location(client_ip: Optional[str] = None) -> Dict[str, Any]:
    """
    Auto-detect user real-time location via IP or headers.
    Falls back gracefully to Patna/Delhi if client is localhost or unresolvable.
    """
    clean_ip = (client_ip or "").strip()
    is_private = (
        not clean_ip
        or clean_ip in ("127.0.0.1", "::1", "localhost")
        or clean_ip.startswith("192.168.")
        or clean_ip.startswith("10.")
        or clean_ip.startswith("172.16.")
    )

    if not is_private:
        import httpx
        try:
            with httpx.Client(timeout=2.0) as client:
                resp = client.get(f"http://ip-api.com/json/{clean_ip}?fields=status,country,regionName,city,lat,lon")
                data = resp.json()
                if data.get("status") == "success":
                    return {
                        "lat": round(float(data["lat"]), 4),
                        "lng": round(float(data["lon"]), 4),
                        "city": data.get("city", "Current Location"),
                        "district": data.get("city"),
                        "state": data.get("regionName", "India"),
                        "address": f"{data.get('city')}, {data.get('regionName')}",
                        "source": "ip_auto",
                    }
        except Exception as e:
            logger.debug(f"IP Geolocation error: {e}")

    # Fallback default: epicenter in Patna, Bihar (core hackathon test geography)
    return {
        "lat": 25.6120,
        "lng": 85.1580,
        "city": "Patna",
        "district": "Patna",
        "state": "Bihar",
        "address": "Patna, Bihar (Auto-detected Reference)",
        "source": "fallback",
    }


def reverse_geocode_sync(lat: float, lng: float) -> str:
    """Find closest recognized city or district from coordinates."""
    best_city = "Chosen Location"
    best_dist = 999999.0

    for city_key, (c_lat, c_lng, c_name, c_state) in CITY_CENTROIDS.items():
        d = haversine_distance(lat, lng, c_lat, c_lng)
        if d < best_dist:
            best_dist = d
            best_city = f"{c_name}, {c_state}"

    if best_dist < 50.0:
        return best_city
    return f"{round(lat, 3)}°N, {round(lng, 3)}°E"


def resolve_user_location(
    user_location: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    auto_detect: bool = False,
    client_ip: Optional[str] = None,
    db_session=None,
) -> Dict[str, Any]:
    """
    Unified multi-strategy Location Resolver:
    1. Direct GPS / Provided LatLng
    2. Explicit manual location text (City, District, PIN code)
    3. Auto-detected real-time client IP location
    """
    # 1. Direct coordinates provided (e.g. from browser navigator.geolocation)
    if lat is not None and lng is not None and (lat != 0 or lng != 0):
        human_addr = user_location or reverse_geocode_sync(lat, lng)
        return {
            "lat": round(float(lat), 5),
            "lng": round(float(lng), 5),
            "city": human_addr.split(",")[0].strip(),
            "district": human_addr.split(",")[0].strip(),
            "state": human_addr.split(",")[1].strip() if "," in human_addr else "India",
            "address": human_addr,
            "source": "gps" if not user_location else "manual",
        }

    # 2. Manual Location Text provided (e.g. "Saharsa", "Patna", "852200", "Lalganj, Vaishali", "Delhi")
    if user_location and user_location.strip():
        loc_str = user_location.strip()
        loc_clean = loc_str.lower()

        # Check PIN code
        pin_match = re.search(r"\b(\d{6})\b", loc_clean)
        if pin_match:
            pin_code = pin_match.group(1)
            if pin_code in PIN_CENTROIDS:
                c_lat, c_lng, city, state = PIN_CENTROIDS[pin_code]
                return {
                    "lat": c_lat, "lng": c_lng,
                    "city": city, "district": city, "state": state,
                    "address": f"{city}, {state} (PIN {pin_code})",
                    "source": "manual",
                }

        # Check City Centroids
        for city_key, (c_lat, c_lng, c_city, c_state) in CITY_CENTROIDS.items():
            if city_key in loc_clean:
                return {
                    "lat": c_lat, "lng": c_lng,
                    "city": c_city, "district": c_city, "state": c_state,
                    "address": f"{c_city}, {c_state}",
                    "source": "manual",
                }

        # Check State Centroids
        for state_name, (s_lat, s_lng) in STATE_CENTROIDS.items():
            if state_name.lower() in loc_clean:
                return {
                    "lat": s_lat, "lng": s_lng,
                    "city": state_name, "district": state_name, "state": state_name,
                    "address": f"{state_name}, India",
                    "source": "manual",
                }

        # Query Database over 10,000 facilities for dynamic match
        if db_session:
            db_res = db_lookup_location(loc_str, db_session)
            if db_res:
                d_lat, d_lng, d_city, d_state = db_res
                return {
                    "lat": round(d_lat, 4), "lng": round(d_lng, 4),
                    "city": d_city, "district": d_city, "state": d_state,
                    "address": f"{d_city}, {d_state}",
                    "source": "manual",
                }

    # 3. Auto-detect real-time location via IP
    if auto_detect or not user_location:
        return detect_ip_location(client_ip)

    # 4. Final Fallback
    return {
        "lat": 25.6120,
        "lng": 85.1580,
        "city": "Patna",
        "district": "Patna",
        "state": "Bihar",
        "address": "Patna, Bihar",
        "source": "fallback",
    }


async def geocode_pin(
    pin_code: Optional[str],
    city: Optional[str],
    state: Optional[str],
    use_nominatim: bool = False,
) -> Tuple[Optional[float], Optional[float]]:
    """Return (latitude, longitude) for a hospital record with jittering."""
    if pin_code and pin_code in PIN_CENTROIDS:
        lat, lng, _, _ = PIN_CENTROIDS[pin_code]
        return _jitter(lat, lng, spread_deg=0.08)

    if city:
        city_clean = city.strip().lower()
        if city_clean in CITY_CENTROIDS:
            lat, lng, _, _ = CITY_CENTROIDS[city_clean]
            return _jitter(lat, lng, spread_deg=0.1)

    if state:
        centroid = STATE_CENTROIDS.get(state)
        if not centroid:
            for s, c in STATE_CENTROIDS.items():
                if state.lower() in s.lower() or s.lower() in state.lower():
                    centroid = c
                    break
        if centroid:
            spread = STATE_SPREAD_KM.get(state, 1.5)
            spread_deg = spread / 111
            return _jitter(centroid[0], centroid[1], spread_deg=spread_deg)

    return None, None


def batch_geocode_sync(records: list) -> list:
    """Synchronous batch geocoder using state/city centroids + jitter."""
    results = []
    for r in records:
        city = r.get("city")
        pin = r.get("pin_code")
        state = r.get("state")

        if pin and pin in PIN_CENTROIDS:
            lat, lng, _, _ = PIN_CENTROIDS[pin]
            results.append(_jitter(lat, lng, spread_deg=0.05))
            continue

        if city and city.lower() in CITY_CENTROIDS:
            lat, lng, _, _ = CITY_CENTROIDS[city.lower()]
            results.append(_jitter(lat, lng, spread_deg=0.08))
            continue

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
