from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class TrustTier(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Capabilities(BaseModel):
    icu: Optional[bool] = None
    surgery: Optional[bool] = None
    emergency_24h: Optional[bool] = None
    dialysis: Optional[bool] = None
    nicu: Optional[bool] = None
    oncology: Optional[bool] = None
    trauma: Optional[bool] = None
    blood_bank: Optional[bool] = None
    cardiac_surgery: Optional[bool] = None
    neurosurgery: Optional[bool] = None
    burn_unit: Optional[bool] = None
    psychiatric: Optional[bool] = None


class Citation(BaseModel):
    row_num: Optional[int] = None
    source_field: str
    quote: str
    context: Optional[str] = None
    contradiction_flag: Optional[str] = None


class FunctionalCapabilityDetail(BaseModel):
    status: str  # "VERIFIED_FUNCTIONAL", "PHANTOM_CLAIM", "NOT_AVAILABLE"
    confidence: float
    evidence: str
    missing_requirements: List[str] = Field(default_factory=list)


class HospitalBase(BaseModel):
    name: str
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pin_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address_line: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    facility_type: Optional[str] = None
    operator_type: Optional[str] = None


class HospitalExtracted(HospitalBase):
    """Structured data extracted from raw India 10k dataset records."""
    dataset_row_num: Optional[int] = None
    bed_count: Optional[int] = None
    number_doctors: Optional[int] = None
    icu_beds: Optional[int] = None
    ventilator_count: Optional[int] = None
    staff_specialties: List[str] = Field(default_factory=list)
    equipment_list: List[str] = Field(default_factory=list)
    procedures: List[str] = Field(default_factory=list)
    unstructured_capabilities: List[str] = Field(default_factory=list)
    accreditation: Optional[str] = None
    accreditation_date: Optional[str] = None
    capabilities: Capabilities = Field(default_factory=Capabilities)
    functional_capabilities: Dict[str, Any] = Field(default_factory=dict)
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    raw_text: Optional[str] = None
    extraction_source: Optional[str] = None
    extraction_confidence: Optional[float] = None
    recency_date: Optional[str] = None


class TrustFlag(BaseModel):
    rule: str
    description: str
    score_impact: int
    citation: Optional[Dict[str, Any]] = None


class HospitalTrustScore(BaseModel):
    hospital_id: int
    base_score: int
    final_score: int
    tier: TrustTier
    flags: List[TrustFlag] = Field(default_factory=list)
    tavily_verified: bool = False
    tavily_query: Optional[str] = None
    tavily_summary: Optional[str] = None
    tavily_score_adjustment: int = 0


class HospitalResponse(HospitalExtracted):
    """Full hospital record returned to frontend."""
    id: int
    trust_score: int
    trust_tier: TrustTier
    trust_flags: List[str] = Field(default_factory=list)
    detailed_flags: List[TrustFlag] = Field(default_factory=list)
    tavily_verified: bool = False
    tavily_summary: Optional[str] = None
    distance_km: Optional[float] = None
    travel_time_min: Optional[int] = None
    fitness_score: Optional[float] = None
    clinical_match_reasons: List[str] = Field(default_factory=list)
    validator_verdict: Optional[str] = "PASSED"
    validator_notes: Optional[str] = None
    validator_adjustment: Optional[int] = 0
    desert_index: Optional[float] = 0.0

    class Config:
        from_attributes = True


class DiagnosticQuestion(BaseModel):
    id: str
    question: str
    options: List[str] = Field(default_factory=list)
    rationale: Optional[str] = None
    category: Optional[str] = "clinical_triage"


class ClinicalAnalysis(BaseModel):
    primary_complaint: str
    urgency_tier: str = "ROUTINE"  # "CRITICAL_EMERGENCY", "URGENT", "SEMI_URGENT", "ROUTINE"
    urgency_color: str = "emerald"  # "red", "amber", "emerald"
    differential_diagnosis: List[str] = Field(default_factory=list)
    confirmed_diagnosis: Optional[str] = None
    red_flags: List[str] = Field(default_factory=list)
    required_capabilities: List[str] = Field(default_factory=list)
    required_equipment: List[str] = Field(default_factory=list)
    patient_guidance: str = ""
    clarification_summary: Optional[str] = None
    questions: List[DiagnosticQuestion] = Field(default_factory=list)


class ResolvedLocation(BaseModel):
    lat: float
    lng: float
    address: str
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    source: str = "manual"  # "gps", "manual", "ip_auto", "fallback"


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    user_location: Optional[str] = None  # e.g. "Patna", "Saharsa, Bihar", "852200", "Lalganj"
    lat: Optional[float] = None
    lng: Optional[float] = None
    radius_km: Optional[float] = None
    auto_detect_location: Optional[bool] = False
    diagnostic_answers: Optional[Dict[str, str]] = None
    max_results: int = Field(default=10, ge=1, le=50)
    min_trust_score: Optional[int] = Field(default=None, ge=0, le=100)
    scenario: Optional[str] = None  # e.g., "ananya_emergency"


class AgentStep(BaseModel):
    type: str
    title: str
    message: Optional[str] = None
    count: Optional[int] = None
    agent: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    query: str
    user_location: Optional[ResolvedLocation] = None
    clinical_intent: Optional[Dict[str, Any]] = None
    clinical_analysis: Optional[ClinicalAnalysis] = None
    diagnostic_questions: List[DiagnosticQuestion] = Field(default_factory=list)
    results: List[HospitalResponse]
    total: int
    agent_steps: List[AgentStep] = Field(default_factory=list)
    validator_summary: Optional[Dict[str, Any]] = None
    mlflow_run_id: Optional[str] = None

