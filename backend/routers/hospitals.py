"""
Hospital list and detail endpoints.
GET /api/hospitals          — filtered list (for map & directory)
GET /api/hospitals/{id}     — single record with row-level citations & IPHS validation details
"""
import math
from typing import Optional, Generator

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Hospital

router = APIRouter()


def _distance_km(lat1, lng1, lat2, lng2) -> Optional[float]:
    if not all([lat1, lng1, lat2, lng2]):
        return None
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return round(6371 * 2 * math.asin(math.sqrt(a)), 1)


def _to_response(h: Hospital, user_lat=None, user_lng=None) -> dict:
    return {
        "id": h.id,
        "dataset_row_num": h.dataset_row_num,
        "name": h.name,
        "city": h.city,
        "district": h.district,
        "state": h.state,
        "pin_code": h.pin_code,
        "address_line": h.address_line,
        "phone": h.phone,
        "email": h.email,
        "website": h.website,
        "recency_date": h.recency_date,
        "latitude": h.latitude,
        "longitude": h.longitude,
        "lat": h.latitude,
        "lng": h.longitude,
        "bed_count": h.bed_count,
        "number_doctors": h.number_doctors,
        "icu_beds": h.icu_beds,
        "ventilator_count": h.ventilator_count,
        "accreditation": h.accreditation,
        "accreditation_date": h.accreditation_date,
        "facility_type": h.facility_type,
        "operator_type": h.operator_type,
        "trust_score": h.trust_score,
        "trust_tier": h.trust_tier,
        "trust_flags": h.flag_descriptions(),
        "detailed_flags": h.trust_flags or [],
        "citations": h.citations or [],
        "tavily_verified": h.tavily_verified,
        "tavily_summary": h.tavily_summary,
        "capabilities": h.capability_list(),
        "capabilities_map": h.capabilities or {},
        "functional_capabilities": h.functional_capabilities or {},
        "staff_specialties": h.staff_specialties or [],
        "equipment_list": h.equipment_list or [],
        "procedures": h.procedures or [],
        "unstructured_capabilities": h.unstructured_capabilities or [],
        "validator_verdict": h.validator_verdict or "PASSED",
        "validator_notes": h.validator_notes,
        "validator_adjustment": h.validator_adjustment or 0,
        "desert_index": h.desert_index or 0.0,
        "raw_text": h.raw_text,
        "extraction_source": h.extraction_source or f"dataset.csv Row #{h.dataset_row_num}",
        "distance_km": _distance_km(user_lat, user_lng, h.latitude, h.longitude),
    }


@router.get("")
def list_hospitals(
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    trust_tier: Optional[str] = Query(None),
    min_trust: Optional[int] = Query(None, ge=0, le=100),
    specialty: Optional[str] = Query(None),
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    limit: int = Query(500, ge=1, le=2000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(Hospital)
    if state:
        q = q.filter(Hospital.state.ilike(f"%{state}%"))
    if district:
        q = q.filter(Hospital.district.ilike(f"%{district}%"))
    if trust_tier:
        q = q.filter(Hospital.trust_tier == trust_tier)
    if min_trust is not None:
        q = q.filter(Hospital.trust_score >= min_trust)

    hospitals_list = q.offset(offset).limit(limit).all()

    # Specialty filter (JSON field — done in Python)
    if specialty and specialty not in ("All Specialties", "All"):
        specialty_map = {
            "ICU": "icu", "Surgery": "surgery", "Emergency": "emergency_24h",
            "Dialysis": "dialysis", "NICU": "nicu", "Oncology": "oncology",
            "Trauma": "trauma", "Blood Bank": "blood_bank",
        }
        cap_key = specialty_map.get(specialty)
        if cap_key:
            hospitals_list = [h for h in hospitals_list if (h.capabilities or {}).get(cap_key) is True]

    return {
        "hospitals": [_to_response(h, lat, lng) for h in hospitals_list],
        "total": len(hospitals_list),
    }


@router.get("/{hospital_id}")
def get_hospital(
    hospital_id: int,
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    db: Session = Depends(get_db),
):
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return _to_response(hospital, lat, lng)
