from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class UserLocation(BaseModel):
    lat: float
    lng: float
    pin: str
    transport: str
    budget_inr: int

class EvalInput(BaseModel):
    probe_id: str
    kind: str
    query_text: str
    user_location: UserLocation
    time: str

class Citation(BaseModel):
    facility_name: str
    source_field: str
    span: str

class FacilityOutput(BaseModel):
    facility_name: str
    facility_pin: str
    verdict: str
    trust_score: float
    distance_km: float
    capabilities: List[str]
    citations: List[Citation]
    why: str
    why_not_runner_up: str

class EvalOutput(BaseModel):
    facilities: List[FacilityOutput]
    abstain: bool
    abstain_reason: Optional[str] = None
    desert_flags: List[str] = Field(default_factory=list)
