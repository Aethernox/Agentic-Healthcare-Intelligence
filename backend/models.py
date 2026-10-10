"""
SQLAlchemy ORM models for MedMap - Agentic Healthcare Intelligence.
Enhanced with dataset.csv row-level citations, functional capabilities, and medical standards validation.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Integer, String, Float, Boolean, Text, DateTime, JSON, Index, func
)
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class Hospital(Base):
    __tablename__ = "hospitals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_row_num: Mapped[Optional[int]] = mapped_column(Integer, index=True)

    # Identity
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    city: Mapped[Optional[str]] = mapped_column(String(100))
    district: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(100))
    pin_code: Mapped[Optional[str]] = mapped_column(String(10))
    address_line: Mapped[Optional[str]] = mapped_column(String(300))

    # Contact & Digital Footprint
    phone: Mapped[Optional[str]] = mapped_column(String(100))
    email: Mapped[Optional[str]] = mapped_column(String(150))
    website: Mapped[Optional[str]] = mapped_column(String(300))
    recency_date: Mapped[Optional[str]] = mapped_column(String(50))

    # Geography
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)

    # Facility details
    bed_count: Mapped[Optional[int]] = mapped_column(Integer)
    number_doctors: Mapped[Optional[int]] = mapped_column(Integer)
    icu_beds: Mapped[Optional[int]] = mapped_column(Integer)
    ventilator_count: Mapped[Optional[int]] = mapped_column(Integer)
    accreditation: Mapped[Optional[str]] = mapped_column(String(50))
    accreditation_date: Mapped[Optional[str]] = mapped_column(String(50))
    facility_type: Mapped[Optional[str]] = mapped_column(String(100))
    operator_type: Mapped[Optional[str]] = mapped_column(String(100))

    # Capabilities & Unstructured Records
    capabilities: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    functional_capabilities: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    staff_specialties: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    equipment_list: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    procedures: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    unstructured_capabilities: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    # Trust scoring & Contradictions
    trust_score: Mapped[int] = mapped_column(Integer, default=50)
    trust_tier: Mapped[str] = mapped_column(String(10), default="medium")
    trust_flags: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    # Agentic Traceability & Row-Level Citations
    citations: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    # Validator Agent (Medical Standards Cross-Check)
    validator_verdict: Mapped[Optional[str]] = mapped_column(String(50), default="PASSED")
    validator_notes: Mapped[Optional[str]] = mapped_column(Text)
    validator_adjustment: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    # Crisis / Desert Metrics
    desert_index: Mapped[Optional[float]] = mapped_column(Float, default=0.0)

    # Tavily verification
    tavily_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    tavily_summary: Mapped[Optional[str]] = mapped_column(Text)
    tavily_queried_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Source data
    raw_text: Mapped[Optional[str]] = mapped_column(Text)
    extraction_source: Mapped[Optional[str]] = mapped_column(Text)
    extraction_confidence: Mapped[Optional[float]] = mapped_column(Float)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_hospitals_state", "state"),
        Index("ix_hospitals_district", "district"),
        Index("ix_hospitals_trust_score", "trust_score"),
        Index("ix_hospitals_trust_tier", "trust_tier"),
        Index("ix_hospitals_pin_code", "pin_code"),
        Index("ix_hospitals_lat_lng", "latitude", "longitude"),
    )

    def capability_list(self) -> list[str]:
        """Return list of capability names that are True."""
        caps = self.capabilities or {}
        cap_labels = {
            "icu": "ICU",
            "surgery": "Surgery",
            "emergency_24h": "Emergency",
            "dialysis": "Dialysis",
            "nicu": "NICU",
            "oncology": "Oncology",
            "trauma": "Trauma",
            "blood_bank": "Blood Bank",
            "cardiac_surgery": "Cardiac Surgery",
            "neurosurgery": "Neurosurgery",
            "burn_unit": "Burn Unit",
            "psychiatric": "Psychiatric",
        }
        return [cap_labels[k] for k, v in caps.items() if v is True and k in cap_labels]

    def flag_descriptions(self) -> list[str]:
        """Return trust flag descriptions."""
        flags = self.trust_flags or []
        descriptions = []
        for f in flags:
            if isinstance(f, dict):
                descriptions.append(f.get("description", ""))
            elif isinstance(f, str):
                descriptions.append(f)
        return [d for d in descriptions if d]
