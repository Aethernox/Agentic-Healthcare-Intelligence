import csv
import json
import math
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "dataset.csv"
PROBES_FILE = Path(__file__).parent.parent / "participant_eval_kit" / "samples" / "ps03_practice_probes.jsonl"
SAMPLE_FILE = Path(__file__).parent.parent / "participant_eval_kit" / "samples" / "ps03_sample.jsonl"

def haversine(lat1, lng1, lat2, lng2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))

def inspect_dataset():
    print(f"Loading {DATA_FILE}...")
    facilities = []
    with open(DATA_FILE, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            lat_str = row.get("latitude")
            lng_str = row.get("longitude")
            try:
                lat = float(lat_str) if lat_str else None
                lng = float(lng_str) if lng_str else None
            except ValueError:
                lat, lng = None, None
            
            facilities.append({
                "row_num": i + 2,
                "name": (row.get("name") or "").strip(),
                "city": (row.get("address_city") or "").strip(),
                "state": (row.get("address_stateOrRegion") or "").strip(),
                "pin": (row.get("address_zipOrPostcode") or "").strip()[:6],
                "lat": lat,
                "lng": lng,
                "specialties": row.get("specialties") or "",
                "procedure": row.get("procedure") or "",
                "equipment": row.get("equipment") or "",
                "capability": row.get("capability") or "",
                "description": row.get("description") or "",
            })
    print(f"Total facilities in dataset.csv: {len(facilities)}")
    
    # 1. Inspect Probe 1 location (26.24, 84.4)
    print("\n--- Facilities near Probe 1 (26.24, 84.4, Siwan/Gopalganj) within 30km ---")
    p1_matches = []
    for f in facilities:
        if f["lat"] and f["lng"]:
            d = haversine(26.24, 84.4, f["lat"], f["lng"])
            if d <= 30.0:
                p1_matches.append((d, f))
    p1_matches.sort(key=lambda x: x[0])
    for d, f in p1_matches[:10]:
        print(f"[{d:.1f} km] {f['name']} (PIN {f['pin']}, {f['city']}) - row {f['row_num']}")
        if "thakur" in f["name"].lower():
            print(f"  FOUND THAKUR: procedure={f['procedure'][:100]}")

    # 2. Inspect Probe 2 location (25.42, 86.1, Begusarai)
    print("\n--- Facilities near Probe 2 (25.42, 86.1, Begusarai) within 35km ---")
    p2_matches = []
    for f in facilities:
        if f["lat"] and f["lng"]:
            d = haversine(25.42, 86.1, f["lat"], f["lng"])
            if d <= 35.0:
                p2_matches.append((d, f))
    p2_matches.sort(key=lambda x: x[0])
    for d, f in p2_matches[:10]:
        print(f"[{d:.1f} km] {f['name']} (PIN {f['pin']}, {f['city']}) - row {f['row_num']}")

    # 3. Inspect Probe 3 location (25.0, 84.75, Jehanabad/Gaya)
    print("\n--- Facilities near Probe 3 (25.0, 84.75) within 35km ---")
    p3_matches = []
    for f in facilities:
        if f["lat"] and f["lng"]:
            d = haversine(25.0, 84.75, f["lat"], f["lng"])
            if d <= 35.0:
                p3_matches.append((d, f))
    p3_matches.sort(key=lambda x: x[0])
    for d, f in p3_matches[:10]:
        print(f"[{d:.1f} km] {f['name']} (PIN {f['pin']}, {f['city']}) - row {f['row_num']}")

if __name__ == "__main__":
    inspect_dataset()
