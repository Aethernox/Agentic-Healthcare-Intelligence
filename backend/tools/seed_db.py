"""
Seed the database from the VF_Hackathon_Dataset_India_Large JSON extract.
Run: python -m tools.seed_db  (from backend/ directory)
"""
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database import SessionLocal, init_db
from models import Hospital

# Import trust_scorer directly to avoid pulling in anthropic / langchain deps
import importlib.util as _ilu, os as _os

_ts_path = _os.path.join(_os.path.dirname(__file__), "..", "agents", "trust_scorer.py")
_spec = _ilu.spec_from_file_location("trust_scorer", _ts_path)
_ts_mod = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_ts_mod)
compute_trust_score = _ts_mod.compute_trust_score
get_trust_tier = _ts_mod.get_trust_tier

# Import schemas directly without triggering the agents __init__
_schemas_path = _os.path.join(_os.path.dirname(__file__), "..", "schemas", "hospital.py")
_sspec = _ilu.spec_from_file_location("schemas_hospital", _schemas_path)
_smod = _ilu.module_from_spec(_sspec)
_sspec.loader.exec_module(_smod)
HospitalExtracted = _smod.HospitalExtracted
Capabilities = _smod.Capabilities

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_db")

DATA_FILE = Path(__file__).parent.parent.parent / "data" / "seed_hospitals.json"

# ── Keyword-based capability inference ──────────────────────────────────────

def _any_match(texts: list, *keywords: str) -> bool:
    combined = " ".join(str(t).lower() for t in texts if t)
    return any(kw.lower() in combined for kw in keywords)


def infer_capabilities(record: dict) -> dict:
    specs = record.get("specialties") or []
    procs = record.get("procedure") or []
    caps_raw = record.get("capability") or []
    desc = str(record.get("description") or "")
    all_text = [*specs, *procs, *caps_raw, desc]

    result = {}

    def cap(key, *kws):
        val = _any_match(all_text, *kws)
        result[key] = True if val else None

    cap("icu", "icu", "intensive care", "critical care")
    cap("surgery", "surg", "operation theatre", "laparoscop", "laparo")
    cap("emergency_24h", "emergency", "24/7", "24x7", "casualty")
    cap("dialysis", "dialysis", "hemodialy", "nephrology")
    cap("nicu", "nicu", "neonatal", "newborn icu")
    cap("oncology", "oncol", "cancer", "chemotherapy", "radiation therapy")
    cap("trauma", "trauma", "accident", "injury")
    cap("blood_bank", "blood bank", "transfusion")
    cap("cardiac_surgery", "cardiac surg", "heart surg", "bypass", "cath lab", "cardiothoracic")
    cap("neurosurgery", "neurosurg", "brain surg", "spine surg")
    cap("burn_unit", "burn unit", "plastic surg")
    cap("psychiatric", "psychiatr", "mental health", "psychology")

    return result


def record_to_extracted(record: dict, caps: dict) -> HospitalExtracted:
    return HospitalExtracted(
        name=record.get("name", "Unknown"),
        city=record.get("address_city"),
        state=record.get("address_stateOrRegion"),
        pin_code=str(record.get("address_zipOrPostcode") or ""),
        latitude=record.get("latitude"),
        longitude=record.get("longitude"),
        bed_count=record.get("capacity") if isinstance(record.get("capacity"), int) else None,
        staff_specialties=[s for s in (record.get("specialties") or []) if isinstance(s, str)],
        equipment_list=[e for e in (record.get("equipment") or []) if isinstance(e, str)],
        capabilities=Capabilities(**{k: v for k, v in caps.items() if v is not None}),
        extraction_confidence=0.7,
    )


def seed():
    if not DATA_FILE.exists():
        logger.error(f"Data file not found: {DATA_FILE}")
        sys.exit(1)

    with open(DATA_FILE) as f:
        records = json.load(f)

    logger.info(f"Loaded {len(records)} records from {DATA_FILE}")

    init_db()
    db = SessionLocal()

    existing = db.query(Hospital).count()
    if existing > 0:
        logger.info(f"DB already has {existing} records — clearing before re-seed.")
        db.query(Hospital).delete()
        db.commit()

    inserted = 0
    for rec in records:
        name = rec.get("name")
        if not name or not isinstance(name, str):
            continue

        caps = infer_capabilities(rec)
        extracted = record_to_extracted(rec, caps)
        trust_score_val, flags = compute_trust_score(extracted)
        tier = get_trust_tier(trust_score_val)

        # Build raw text for extraction_source
        parts = [rec.get("description") or ""]
        if rec.get("capability"):
            parts.extend(rec["capability"])
        if rec.get("procedure"):
            parts.extend(rec["procedure"])
        raw_text = " | ".join(str(p) for p in parts if p)

        h = Hospital(
            name=name,
            city=rec.get("address_city"),
            district=None,
            state=rec.get("address_stateOrRegion"),
            pin_code=str(rec.get("address_zipOrPostcode") or "")[:6],
            latitude=rec.get("latitude"),
            longitude=rec.get("longitude"),
            bed_count=rec.get("capacity") if isinstance(rec.get("capacity"), int) else None,
            icu_beds=None,
            ventilator_count=None,
            accreditation=None,
            accreditation_date=None,
            facility_type=rec.get("facilityTypeId"),
            capabilities={k: v for k, v in caps.items() if v is not None},
            staff_specialties=[s for s in (rec.get("specialties") or []) if isinstance(s, str)],
            equipment_list=[e for e in (rec.get("equipment") or []) if isinstance(e, str)],
            trust_score=trust_score_val,
            trust_tier=tier.value,
            trust_flags=[{"rule": f.rule, "description": f.description, "score_impact": f.score_impact} for f in flags],
            tavily_verified=False,
            tavily_summary=None,
            raw_text=raw_text[:2000],
            extraction_source=f"VF Dataset row {rec.get('row_num', '?')}: {name}, {rec.get('address_city')}",
            extraction_confidence=0.7,
        )
        db.add(h)
        inserted += 1

    db.commit()
    db.close()
    logger.info(f"Seeded {inserted} hospitals into database.")


if __name__ == "__main__":
    seed()
