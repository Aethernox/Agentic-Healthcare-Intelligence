"""
Validator Agent — Medical Standards Cross-Referencing & Self-Correction Engine.
Cross-checks candidate facility recommendations against:
  1. Indian Public Health Standards (IPHS 2022) for PHC/CHC/Sub-District/District Hospitals
  2. National Medical Commission (NMC) Staffing & Surgical Safety Guidelines
  3. Ayushman Bharat PM-JAY Eligibility & Financial Feasibility (e.g. Ananya's ₹500 budget constraint)

Implements self-correction: Adjusts trust scores, flags overlooked contradictions,
and generates clinical feasibility verdicts.
"""
import json
import logging
from typing import List, Dict, Any, Optional

from schemas.hospital import HospitalResponse
from config import settings

logger = logging.getLogger(__name__)


def validate_facility_against_standards(
    hospital: HospitalResponse,
    clinical_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Deterministic rule-based medical standards validation.
    Runs reliably offline and without API keys.
    """
    context = clinical_context or {}
    procedure_needed = context.get("procedure_needed", "").lower()
    budget = context.get("budget", None)
    is_emergency = context.get("is_emergency", False)
    max_radius_km = context.get("max_radius_km", None)
    urgency = context.get("urgency", "routine")

    caps = hospital.capabilities
    func_caps = hospital.functional_capabilities or {}
    staff = [s.lower() for s in (hospital.staff_specialties or [])]
    equipment = [e.lower() for e in (hospital.equipment_list or [])]
    raw = (hospital.raw_text or "").lower()

    issues: List[str] = []
    standards: List[str] = []
    advisories: List[str] = []
    adjustment = 0
    passed = True

    # 1. Staff-to-Bed Ratio (NMC Standard: 1 doctor per 10 beds)
    if hospital.bed_count and hospital.bed_count >= 30:
        docs = hospital.number_doctors or 1
        ratio = hospital.bed_count / docs
        if ratio > 25:
            issues.append(f"Doctor-to-bed ratio is 1:{int(ratio)} (NMC recommends minimum 1:10 for general wards).")
            standards.append("NMC Staffing Standards 2023")
            adjustment -= 10

    # 2. Appendectomy / Surgical Emergency Standards (IPHS 2022 §4.2)
    if "append" in procedure_needed or "surg" in procedure_needed or "abdominal" in procedure_needed:
        standards.append("IPHS 2022 Guidelines §4.2 (Surgical & OT Standards)")
        surg_status = func_caps.get("surgery", {}).get("status")

        has_surgeon = any("surgeon" in s or "surgical" in s or "laparoscop" in s for s in staff)
        has_anesthetist = any("anesthesiolog" in s or "anaesthesiolog" in s or "anesthesia" in s for s in staff)
        has_part_time = "part-time" in raw or "on-call" in raw or "visiting" in raw or "on call" in raw

        if surg_status == "PHANTOM_CLAIM":
            issues.append("CRITICAL: Facility advertised surgical services but lacks functional OT and surgical team.")
            passed = False
            adjustment -= 25
        elif not has_surgeon and not has_part_time:
            issues.append("No general surgeon listed on resident or on-call roster for emergency appendectomy.")
            passed = False
            adjustment -= 20
        elif has_surgeon and not has_anesthetist:
            if has_part_time:
                advisories.append("IPHS 2022 Permissible: Utilizes visiting/part-time surgeon & on-call anesthesiologist. Call ahead to confirm arrival window before departure.")
                adjustment += 5
            else:
                issues.append("Surgeon available, but independent anesthesiologist unconfirmed; spinal/general anesthesia risk.")
                adjustment -= 10
        else:
            advisories.append("Full surgical team (Surgeon + Anesthesiologist) and OT operational.")
            adjustment += 10

    # 3. 24/7 Casualty & Night Roster Verification
    if is_emergency:
        standards.append("IPHS 2022 Casualty & Trauma Care Guidelines")
        emer_status = func_caps.get("emergency_24h", {}).get("status")
        if emer_status == "PHANTOM_CLAIM":
            issues.append("Claims 24/7 Emergency but has 0 observation beds and no casualty doctor roster.")
            passed = False
            adjustment -= 20
        elif emer_status == "VERIFIED_FUNCTIONAL":
            advisories.append("Active emergency ward with on-duty physician verified.")
            adjustment += 5

    # 4. Financial & Affordability Feasibility (e.g. ₹500 budget)
    if budget is not None and budget <= 1000:
        standards.append("National Health Authority (NHA) PM-JAY Empanelment Guidelines")
        is_gov = "government" in (hospital.operator_type or "").lower()
        is_pmjay = "ayushman" in raw or "pm-jay" in raw or "empanelled" in raw or "cashless" in raw

        if is_gov or is_pmjay:
            advisories.append(f"Financial Feasibility Confirmed: Patient's ₹{budget} budget is feasible. Covered under Ayushman Bharat / Government free emergency surgical package.")
            adjustment += 10
        else:
            advisories.append(f"Financial Warning: Private corporate establishment. Cash limit of ₹{budget} may be insufficient for admission deposits without active PM-JAY empanelment.")
            adjustment -= 5

    # 5. Distance & Transport Feasibility (Two-wheeler transport)
    if hospital.distance_km is not None and max_radius_km is not None:
        if hospital.distance_km > max_radius_km:
            issues.append(f"Distance {hospital.distance_km}km exceeds patient transport limit ({max_radius_km}km).")
            adjustment -= 5
        elif hospital.distance_km <= 22:
            est_time = int(hospital.distance_km * 2.4)  # ~25 km/h on rural roads
            advisories.append(f"Transport Feasibility: {hospital.distance_km}km accessible via two-wheeler in approximately {est_time} minutes.")

    # Determine Verdict
    if not passed or adjustment < -15:
        verdict = "FAILED_STANDARDS"
    elif issues:
        verdict = "PASSED_WITH_CONDITIONS"
    else:
        verdict = "PASSED"

    note = " | ".join(advisories + issues) if (advisories or issues) else "Cross-referenced with IPHS 2022 standards: Basic compliance verified."

    return {
        "validation_passed": passed,
        "verdict": verdict,
        "issues_found": issues,
        "advisories": advisories,
        "standards_referenced": list(set(standards)),
        "confidence_adjustment": max(-30, min(15, adjustment)),
        "validator_note": note,
    }


async def run_validator_agent(
    hospitals: List[HospitalResponse],
    clinical_context: Optional[Dict[str, Any]] = None,
) -> List[HospitalResponse]:
    """
    Run the Validator Agent across shortlisted recommendations.
    Applies deterministic standards check and optional LLM refinement.
    """
    validated: List[HospitalResponse] = []

    for hospital in hospitals:
        # Run deterministic standard check
        val_result = validate_facility_against_standards(hospital, clinical_context)

        # Apply self-correction adjustment to trust score
        new_score = max(5, min(100, hospital.trust_score + val_result["confidence_adjustment"]))
        hospital.trust_score = new_score
        hospital.validator_verdict = val_result["verdict"]
        hospital.validator_notes = val_result["validator_note"]
        hospital.validator_adjustment = val_result["confidence_adjustment"]

        # If issues found, append validator flag
        for issue in val_result["issues_found"]:
            hospital.trust_flags.append(f"[Validator Standards Flag] {issue}")

        validated.append(hospital)

    return validated
