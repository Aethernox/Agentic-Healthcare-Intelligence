"""
PostgreSQL structured query tool for filtering hospitals by attributes.
"""
import logging
from typing import List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from config import settings

logger = logging.getLogger(__name__)

engine = None


def get_engine():
    global engine
    if engine is None:
        engine = create_engine(settings.database_url, pool_pre_ping=True)
    return engine


def query_hospitals(
    state: Optional[str] = None,
    district: Optional[str] = None,
    min_beds: Optional[int] = None,
    has_icu: Optional[bool] = None,
    has_emergency: Optional[bool] = None,
    specialty: Optional[str] = None,
    min_trust_score: Optional[int] = None,
    max_results: int = 50,
) -> List[dict]:
    """
    Execute structured SQL query over extracted hospital data.
    """
    conditions = ["1=1"]
    params = {}

    if state:
        conditions.append("LOWER(state) = LOWER(:state)")
        params["state"] = state
    if district:
        conditions.append("LOWER(district) LIKE LOWER(:district)")
        params["district"] = f"%{district}%"
    if min_beds:
        conditions.append("bed_count >= :min_beds")
        params["min_beds"] = min_beds
    if has_icu is not None:
        conditions.append("icu = :has_icu")
        params["has_icu"] = has_icu
    if has_emergency is not None:
        conditions.append("emergency_24h = :has_emergency")
        params["has_emergency"] = has_emergency
    if min_trust_score:
        conditions.append("trust_score >= :min_trust_score")
        params["min_trust_score"] = min_trust_score

    where_clause = " AND ".join(conditions)
    sql = f"""
        SELECT id, name, city, district, state, pin_code, latitude, longitude,
               bed_count, trust_score, trust_tier, accreditation
        FROM hospitals
        WHERE {where_clause}
        ORDER BY trust_score DESC
        LIMIT :max_results
    """
    params["max_results"] = max_results

    try:
        with Session(get_engine()) as session:
            result = session.execute(text(sql), params)
            return [dict(row._mapping) for row in result]
    except Exception as e:
        logger.error(f"DB query failed: {e}")
        return []


def get_hospital_by_id(hospital_id: int) -> Optional[dict]:
    try:
        with Session(get_engine()) as session:
            result = session.execute(
                text("SELECT * FROM hospitals WHERE id = :id"),
                {"id": hospital_id},
            )
            row = result.fetchone()
            return dict(row._mapping) if row else None
    except Exception as e:
        logger.error(f"Failed to fetch hospital {hospital_id}: {e}")
        return None
