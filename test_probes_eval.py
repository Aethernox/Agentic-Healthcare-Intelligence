import csv
import json
import math
from pathlib import Path

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

csv_path = Path("dataset.csv")
with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"Total rows: {len(rows)}")

probes = [
    {"id": "ps03_g1_ananya", "lat": 26.24, "lng": 84.4, "desc": "appendicitis emergency surgery"},
    {"id": "ps03_g2_contradiction", "lat": 25.42, "lng": 86.1, "desc": "cardiac bypass in Begusarai"},
    {"id": "ps03_g3_abstain", "lat": 25.0, "lng": 84.75, "desc": "emergency appendicitis night Makhdumpur"},
]

for p in probes:
    matches = []
    for idx, r in enumerate(rows):
        if not r.get("latitude") or not r.get("longitude"):
            continue
        try:
            lat = float(r["latitude"])
            lng = float(r["longitude"])
        except ValueError:
            continue
        d = haversine(p["lat"], p["lng"], lat, lng)
        if d <= 30.0:
            matches.append((d, idx, r))
    matches.sort(key=lambda x: x[0])
    print(f"\n=================== {p['id']} ({p['desc']}) within 30km: {len(matches)} matches ===================")
    for d, idx, r in matches[:5]:
        print(f"  {d:.2f}km | Row {idx+2} | {r.get('name')} | PIN: {r.get('address_zipOrPostcode')}")
        print(f"    Specialties: {r.get('specialties')}")
        print(f"    Procedures: {r.get('procedure')}")
        print(f"    Capabilities: {r.get('capability')}")
