"""
Synthetic data seeder — generates realistic Indian hospital data for development.

Usage:
  python -m pipelines.seed_data              # seeds 500 records (fast)
  python -m pipelines.seed_data --count 2000
  python -m pipelines.seed_data --clear      # clears existing records first

Runs without any API keys or Excel file — good for local dev and demo.
"""
import logging
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database import SessionLocal, init_db
from models import Hospital
from agents.trust_scorer import compute_trust_score, get_trust_tier
from schemas.hospital import HospitalExtracted as HospitalSchema, Capabilities
from tools.geocoder import batch_geocode_sync

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger("medmap.seed")

STATES_WEIGHTED = [
    ("Uttar Pradesh", 22), ("Maharashtra", 14), ("Bihar", 11),
    ("Rajasthan", 9), ("Madhya Pradesh", 8), ("West Bengal", 7),
    ("Karnataka", 6), ("Tamil Nadu", 6), ("Gujarat", 5),
    ("Andhra Pradesh", 4), ("Odisha", 3), ("Telangana", 3),
    ("Jharkhand", 2), ("Chhattisgarh", 2), ("Assam", 2),
    ("Punjab", 2), ("Haryana", 2), ("Kerala", 2), ("Delhi", 2),
]

STATE_CITIES = {
    "Uttar Pradesh": ["Lucknow", "Varanasi", "Agra", "Kanpur", "Allahabad", "Meerut", "Gorakhpur", "Bahraich", "Shrawasti", "Balrampur"],
    "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad", "Solapur", "Thane"],
    "Bihar": ["Patna", "Gaya", "Muzaffarpur", "Bhagalpur", "Araria", "Sheohar", "Khagaria", "Supaul", "Arwal", "Kaimur"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Bikaner", "Ajmer", "Pratapgarh"],
    "Madhya Pradesh": ["Bhopal", "Indore", "Gwalior", "Jabalpur", "Ujjain", "Sagar"],
    "West Bengal": ["Kolkata", "Howrah", "Durgapur", "Asansol", "Siliguri"],
    "Karnataka": ["Bengaluru", "Mysuru", "Hubli", "Mangaluru", "Belagavi"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Bhavnagar"],
    "Andhra Pradesh": ["Visakhapatnam", "Vijayawada", "Guntur", "Nellore", "Tirupati"],
    "Odisha": ["Bhubaneswar", "Cuttack", "Rourkela", "Berhampur"],
    "Telangana": ["Hyderabad", "Warangal", "Nizamabad", "Karimnagar"],
    "Jharkhand": ["Ranchi", "Jamshedpur", "Dhanbad", "Bokaro"],
    "Chhattisgarh": ["Raipur", "Bhilai", "Durg", "Bilaspur"],
    "Assam": ["Guwahati", "Silchar", "Dibrugarh", "Jorhat"],
    "Punjab": ["Amritsar", "Ludhiana", "Jalandhar", "Patiala"],
    "Haryana": ["Faridabad", "Gurugram", "Hisar", "Ambala"],
    "Kerala": ["Thiruvananthapuram", "Kochi", "Kozhikode", "Thrissur"],
    "Delhi": ["New Delhi", "North Delhi", "South Delhi", "East Delhi", "West Delhi"],
}

HOSPITAL_PREFIXES = [
    "District Hospital", "Government Medical College & Hospital", "Primary Health Centre",
    "Community Health Centre", "Sub-District Hospital", "Civil Hospital",
    "General Hospital", "Taluka Hospital", "Rural Hospital",
    "Apollo Hospital", "Fortis Hospital", "Max Healthcare", "Manipal Hospital",
    "Narayana Health", "Medanta", "HCG Hospital", "Care Hospital",
    "AIIMS", "PGIMER", "NIMHANS",
    "Mission Hospital", "Christian Medical College", "St. Joseph Hospital",
]

SPECIALTY_STAFF = {
    "surgery": ["Surgeon", "Anesthesiologist", "Surgical Assistant", "OT Nurse"],
    "icu": ["Intensivist", "Critical Care Nurse", "Respiratory Therapist"],
    "nicu": ["Neonatologist", "Pediatric Nurse", "NICU Specialist"],
    "oncology": ["Oncologist", "Radiation Therapist", "Chemotherapy Nurse"],
    "cardiac_surgery": ["Cardiologist", "Cardiac Surgeon", "Perfusionist"],
    "dialysis": ["Nephrologist", "Dialysis Technician"],
    "neurosurgery": ["Neurosurgeon", "Neurologist"],
    "trauma": ["Trauma Surgeon", "Emergency Physician", "Orthopedic Surgeon"],
}

EQUIPMENT_BY_CAP = {
    "icu": ["Ventilator", "Cardiac Monitor", "Defibrillator", "Pulse Oximeter"],
    "surgery": ["Operation Theatre", "Laparoscopic Equipment", "Surgical Instruments"],
    "nicu": ["Incubator", "NICU Warmer", "Neonatal Monitor"],
    "oncology": ["Linear Accelerator", "CT Scanner", "Chemotherapy Infusion Pump"],
    "dialysis": ["Hemodialysis Machine", "Water Purification Plant"],
    "cardiac_surgery": ["Cath Lab", "Cardiac ICU", "Bypass Machine"],
    "neurosurgery": ["Surgical Microscope", "Neuro Navigation"],
    "blood_bank": ["Blood Refrigerator", "Blood Component Separator"],
}

ACCREDITATIONS = ["NABH", "NABL", None, None, None, "NABH", None, None, "NABH", "JCI"]

PIN_RANGES = {
    "Uttar Pradesh": (200000, 285999), "Maharashtra": (400000, 445999),
    "Bihar": (800000, 855999), "Rajasthan": (300000, 345999),
    "Madhya Pradesh": (450000, 490999), "West Bengal": (700000, 743999),
    "Karnataka": (560000, 591999), "Tamil Nadu": (600000, 643999),
    "Gujarat": (360000, 396999), "Andhra Pradesh": (500000, 535999),
    "Odisha": (750000, 770999), "Telangana": (500000, 509999),
    "Jharkhand": (813000, 835999), "Chhattisgarh": (490000, 499999),
    "Assam": (781000, 788999), "Punjab": (140000, 152999),
    "Haryana": (121000, 136999), "Kerala": (670000, 695999),
    "Delhi": (110000, 110099),
}


def _make_hospital(i: int) -> dict:
    state = random.choices([s for s, _ in STATES_WEIGHTED], weights=[w for _, w in STATES_WEIGHTED])[0]
    cities = STATE_CITIES.get(state, ["Unknown"])
    city = random.choice(cities)

    prefix = random.choice(HOSPITAL_PREFIXES)
    name = f"{prefix} {city}"

    is_private = any(p in prefix for p in ["Apollo", "Fortis", "Max", "Manipal", "Narayana", "Medanta", "HCG", "Care"])
    is_teaching = any(p in prefix for p in ["Medical College", "AIIMS", "PGIMER", "NIMHANS", "Christian"])
    is_primary = any(p in prefix for p in ["Primary", "Sub-District", "Rural"])

    if is_primary:
        beds = random.randint(10, 50)
    elif is_private:
        beds = random.randint(50, 800)
    elif is_teaching:
        beds = random.randint(400, 1500)
    else:
        beds = random.randint(30, 300)

    base_prob = 0.7 if is_teaching else (0.6 if is_private else 0.3 if is_primary else 0.45)
    introduce_contradiction = random.random() < 0.18

    caps = {
        "icu": beds >= 50 and random.random() < (base_prob + 0.1),
        "surgery": beds >= 30 and random.random() < base_prob,
        "emergency_24h": random.random() < (base_prob + 0.2),
        "dialysis": random.random() < (base_prob - 0.2),
        "nicu": beds >= 50 and random.random() < (base_prob - 0.1),
        "oncology": (is_teaching or is_private) and random.random() < (base_prob - 0.3),
        "trauma": random.random() < (base_prob - 0.1),
        "blood_bank": beds >= 50 and random.random() < base_prob,
        "cardiac_surgery": (is_teaching or is_private) and beds >= 200 and random.random() < (base_prob - 0.35),
        "neurosurgery": (is_teaching or is_private) and beds >= 200 and random.random() < (base_prob - 0.4),
        "burn_unit": beds >= 100 and random.random() < 0.1,
        "psychiatric": random.random() < 0.15,
    }

    staff, equipment = [], []
    for cap_key, has_cap in caps.items():
        if has_cap:
            if cap_key in SPECIALTY_STAFF and not (introduce_contradiction and random.random() < 0.3):
                staff.extend(SPECIALTY_STAFF[cap_key])
            if cap_key in EQUIPMENT_BY_CAP and not (introduce_contradiction and random.random() < 0.25):
                equipment.extend(EQUIPMENT_BY_CAP[cap_key])

    general = ["General Physician", "Radiologist", "Pathologist", "Pharmacist", "Nurse"]
    staff.extend(random.sample(general, k=random.randint(1, 3)))

    accreditation = random.choice(ACCREDITATIONS)
    accreditation_date = None
    if accreditation:
        year = random.randint(2018, 2024)
        month = random.randint(1, 12)
        accreditation_date = f"{year}-{month:02d}-01"
        if random.random() < 0.2:
            accreditation_date = None  # no date — creates trust flag

    icu_beds = None
    ventilator_count = None
    if caps.get("icu"):
        icu_beds = random.randint(2, max(2, beds // 10))
        ventilator_count = 0 if random.random() < 0.15 else random.randint(1, icu_beds)

    lo, hi = PIN_RANGES.get(state, (100000, 999999))
    pin = str(random.randint(lo, hi))

    raw_text = (
        f"{name} — {city}, {state}. Beds: {beds}. "
        + ("ICU available. " if caps.get("icu") else "")
        + ("Surgery dept active. " if caps.get("surgery") else "")
        + ("24/7 Emergency. " if caps.get("emergency_24h") else "")
        + ("Dialysis available. " if caps.get("dialysis") else "")
        + ("NICU facility. " if caps.get("nicu") else "")
        + ("Oncology dept. " if caps.get("oncology") else "")
        + ("Trauma care. " if caps.get("trauma") else "")
        + ("Blood bank. " if caps.get("blood_bank") else "")
        + (f"Accreditation: {accreditation}. " if accreditation else "")
        + f"Staff: {', '.join(list(set(staff))[:6])}."
    )

    return {
        "name": name,
        "city": city,
        "district": city,
        "state": state,
        "pin_code": pin,
        "bed_count": beds,
        "icu_beds": icu_beds,
        "ventilator_count": ventilator_count if ventilator_count else None,
        "accreditation": accreditation,
        "accreditation_date": accreditation_date,
        "facility_type": "Private" if is_private else "Teaching" if is_teaching else "Government",
        "capabilities": caps,
        "staff_specialties": list(set(staff)),
        "equipment_list": list(set(equipment)),
        "raw_text": raw_text,
        "extraction_source": f"Row {i + 1}: {raw_text[:200]}…",
        "extraction_confidence": round(random.uniform(0.55, 0.98), 2),
    }


def seed(count: int = 500, clear: bool = False):
    logger.info(f"Seeding {count} synthetic hospital records…")
    init_db()

    db = SessionLocal()
    try:
        if clear:
            db.query(Hospital).delete()
            db.commit()
            logger.info("Cleared existing records")

        raw_records = [_make_hospital(i) for i in range(count)]
        geo_inputs = [{"state": r["state"], "city": r["city"]} for r in raw_records]
        coords = batch_geocode_sync(geo_inputs)

        hospitals = []
        for i, (data, (lat, lng)) in enumerate(zip(raw_records, coords)):
            caps = data["capabilities"]
            schema_obj = HospitalSchema(
                name=data["name"],
                capabilities=Capabilities(**caps),
                bed_count=data["bed_count"],
                ventilator_count=data.get("ventilator_count"),
                staff_specialties=data["staff_specialties"],
                equipment_list=data["equipment_list"],
                accreditation=data.get("accreditation"),
                accreditation_date=data.get("accreditation_date"),
                extraction_confidence=data.get("extraction_confidence"),
            )
            trust_score, trust_flags = compute_trust_score(schema_obj)
            trust_tier = get_trust_tier(trust_score)

            hospitals.append(Hospital(
                name=data["name"],
                city=data["city"],
                district=data["district"],
                state=data["state"],
                pin_code=data["pin_code"],
                latitude=lat,
                longitude=lng,
                bed_count=data["bed_count"],
                icu_beds=data.get("icu_beds"),
                ventilator_count=data.get("ventilator_count"),
                accreditation=data.get("accreditation"),
                accreditation_date=data.get("accreditation_date"),
                facility_type=data.get("facility_type"),
                capabilities=caps,
                staff_specialties=data["staff_specialties"],
                equipment_list=data["equipment_list"],
                trust_score=trust_score,
                trust_tier=trust_tier.value,
                trust_flags=[
                    {"rule": f.rule, "description": f.description, "score_impact": f.score_impact}
                    for f in trust_flags
                ],
                raw_text=data["raw_text"],
                extraction_source=data["extraction_source"],
                extraction_confidence=data.get("extraction_confidence"),
            ))

            if (i + 1) % 100 == 0:
                db.add_all(hospitals)
                db.commit()
                logger.info(f"  Saved {i + 1}/{count}")
                hospitals = []

        if hospitals:
            db.add_all(hospitals)
            db.commit()

        total = db.query(Hospital).count()
        logger.info(f"Seeding complete. Total records in DB: {total}")

        from collections import Counter
        tiers = Counter(db.query(Hospital.trust_tier).all())
        logger.info(f"Trust distribution: {dict(tiers)}")

    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=500)
    parser.add_argument("--clear", action="store_true")
    args = parser.parse_args()
    seed(count=args.count, clear=args.clear)
