"""
Rule-based trust scoring and functional capability verification engine for Indian Healthcare Facilities.
Scores each facility record 0-100 based on internal consistency, medical plausibility, and equipment-staff alignment.
Produces row-level citations for agentic traceability.
"""
from typing import List, Tuple, Dict, Any, Optional
import logging
import re

from schemas.hospital import HospitalExtracted, TrustFlag, TrustTier, Citation

logger = logging.getLogger(__name__)

STARTING_SCORE = 100

# (rule_id, description, score_penalty, standard_reference)
CONTRADICTION_RULES: List[Tuple[str, str, int, str]] = [
    (
        "surgery_no_anesthesiologist",
        "Claims Advanced Surgery / Appendectomy but no Anesthesiologist listed in staff roster or on-call roster",
        30,
        "NMC Minimum Standard Requirements & IPHS 2022 Guidelines §4.2",
    ),
    (
        "icu_no_ventilators",
        "Claims Functional ICU / Critical Care but has 0 ventilators and no multipara monitors listed",
        25,
        "IPHS 2022 ICU Standards & NABH Critical Care Guidelines",
    ),
    (
        "emergency_no_resident_doctor",
        "Claims 24/7 Emergency Care but no resident doctor, casualty medical officer, or night staff listed",
        20,
        "IPHS 2022 Casualty & Emergency Standards",
    ),
    (
        "cosmetic_dental_claiming_hospital_icu",
        "Outpatient dental, cosmetic, or wellness clinic claiming full hospital ICU/OT capabilities without hospital infrastructure",
        35,
        "Clinical Establishments Act (Registration and Regulation)",
    ),
    (
        "dialysis_no_nephrologist_or_machine",
        "Claims Dialysis Centre but no nephrologist or hemodialysis equipment listed",
        25,
        "Pradhan Mantri National Dialysis Programme Guidelines",
    ),
    (
        "oncology_no_oncologist",
        "Claims Oncology / Cancer Care but no oncologist or chemo/radiation facilities listed",
        30,
        "National Cancer Grid (NCG) Standards",
    ),
    (
        "cardiac_no_cath_lab",
        "Claims Cardiac Surgery but no Cath Lab, cardiac OT, or perfusionist listed",
        25,
        "IPHS Tertiary Care Benchmarks",
    ),
    (
        "high_capacity_low_doctor",
        "Claims 50+ inpatient bed capacity but lists fewer than 2 doctors (severe staffing deficit)",
        20,
        "NMC Staff-to-Bed Ratio Mandate (min 1 doctor per 10 beds)",
    ),
    (
        "stale_survey_penalty",
        "Digital footprint originates from an unverified survey/dump older than 2 years with no active operational update",
        15,
        "Healthcare Directory Recency Protocol",
    ),
    (
        "nabh_no_date",
        "Claims NABH Accreditation but provides no accreditation validity date or registry reference",
        15,
        "National Accreditation Board for Hospitals & Healthcare Providers",
    ),
]


def _match_keywords(text_items: List[str], keywords: List[str]) -> bool:
    """Check if any keyword appears in the lowercase list of strings."""
    for item in text_items:
        low = item.lower()
        if any(kw in low for kw in keywords):
            return True
    return False


def verify_functional_capabilities(
    hospital: HospitalExtracted,
) -> Tuple[Dict[str, Any], List[Citation]]:
    """
    Evaluate claimed vs. functional capabilities.
    Distinguishes functional capabilities from phantom claims (e.g. unplugged concentrators).
    """
    caps = hospital.capabilities
    staff = [s.lower() for s in hospital.staff_specialties]
    equipment = [e.lower() for e in hospital.equipment_list]
    procedures = [p.lower() for p in hospital.procedures]
    claims = [c.lower() for c in hospital.unstructured_capabilities]
    raw_desc = (hospital.raw_text or "").lower()

    all_text = staff + equipment + procedures + claims + [raw_desc]
    citations: List[Citation] = []
    row_num = hospital.dataset_row_num

    functional_map: Dict[str, Any] = {}

    # 1. ICU Verification
    icu_claimed = (
        caps.icu is True
        or any("icu" in t or "intensive care" in t or "critical care" in t for t in all_text)
    )
    has_vent = (
        (hospital.ventilator_count or 0) > 0
        or _match_keywords(equipment, ["ventilator", "respirator", "bipap", "cpap", "multipara"])
    )
    has_icu_staff = _match_keywords(
        staff, ["intensivist", "critical care", "anesthesiolog", "anaesthesiolog", "resident", "physician"]
    )
    if icu_claimed:
        if has_vent and (has_icu_staff or (hospital.number_doctors or 0) >= 3):
            functional_map["icu"] = {
                "status": "VERIFIED_FUNCTIONAL",
                "confidence": 0.90,
                "evidence": "Functional ICU verified with ventilator/critical monitoring equipment and intensivist/resident coverage.",
                "missing_requirements": [],
            }
        else:
            missing = []
            if not has_vent:
                missing.append("No ventilator or multipara monitor in equipment log")
            if not has_icu_staff:
                missing.append("No intensivist or critical care physician listed")
            functional_map["icu"] = {
                "status": "PHANTOM_CLAIM",
                "confidence": 0.20,
                "evidence": "Advertised ICU lacks essential life-support apparatus or critical care physician on duty.",
                "missing_requirements": missing,
            }
            citations.append(Citation(
                row_num=row_num,
                source_field="equipment / numberDoctors",
                quote=f"Claims ICU, but ventilators={hospital.ventilator_count or 0}, equipment={hospital.equipment_list[:2]}",
                contradiction_flag="icu_no_ventilators",
            ))
    else:
        functional_map["icu"] = {
            "status": "NOT_AVAILABLE",
            "confidence": 1.0,
            "evidence": "No ICU service advertised or equipped.",
            "missing_requirements": [],
        }

    # 2. Surgery & Emergency Appendectomy Verification
    surgery_claimed = (
        caps.surgery is True
        or any("surgery" in t or "surgical" in t or "appendectomy" in t or "laparoscop" in t or "ot " in t for t in all_text)
    )
    has_ot = _match_keywords(equipment, ["operation theatre", "ot ", "operating room", "laparoscope", "anaesthetic equipment", "c-arm"])
    has_surgeon = _match_keywords(staff, ["surgeon", "general surgery", "laparoscopic", "surgical"])
    has_anesthetist = _match_keywords(staff, ["anesthesiolog", "anaesthesiolog", "anesthesia", "anaesthesia"])

    if surgery_claimed:
        if (has_ot or has_surgeon) and (has_anesthetist or "on-call" in raw_desc or "anesthesiologist on call" in raw_desc):
            functional_map["surgery"] = {
                "status": "VERIFIED_FUNCTIONAL",
                "confidence": 0.88,
                "evidence": "Functional surgical suite verified: equipped OT/laparoscopic instruments and surgeon + anesthesia coverage.",
                "missing_requirements": [],
            }
        elif has_surgeon and not has_anesthetist:
            functional_map["surgery"] = {
                "status": "CONDITIONAL_CAPABILITY",
                "confidence": 0.45,
                "evidence": "Surgeon present but no dedicated Anesthesiologist listed; depends on visiting part-time doctor.",
                "missing_requirements": ["Anesthesiologist not permanently rostered"],
            }
            citations.append(Citation(
                row_num=row_num,
                source_field="staff_specialties",
                quote=f"Surgeon listed but anesthesiologist absent in staff: {hospital.staff_specialties}",
                contradiction_flag="surgery_no_anesthesiologist",
            ))
        else:
            functional_map["surgery"] = {
                "status": "PHANTOM_CLAIM",
                "confidence": 0.15,
                "evidence": "Surgery claimed without operational Operation Theatre or surgical team.",
                "missing_requirements": ["Operation Theatre", "Surgeon", "Anesthesiologist"],
            }
    else:
        functional_map["surgery"] = {
            "status": "NOT_AVAILABLE",
            "confidence": 1.0,
            "evidence": "No surgical capabilities available.",
            "missing_requirements": [],
        }

    # 3. 24/7 Emergency Verification
    emer_claimed = (
        caps.emergency_24h is True
        or any("24/7" in t or "24x7" in t or "emergency" in t or "casualty" in t or "round the clock" in t for t in all_text)
    )
    has_emer_staff = _match_keywords(
        staff, ["emergency", "casualty", "resident", "night", "medical officer", "general physician", "cmo"]
    ) or (hospital.number_doctors or 0) >= 2

    is_outpatient_only = any(
        "outpatient" in c or "clinic" in (hospital.facility_type or "").lower() for c in claims
    ) and (hospital.bed_count or 0) == 0

    if emer_claimed:
        if has_emer_staff and not is_outpatient_only:
            functional_map["emergency_24h"] = {
                "status": "VERIFIED_FUNCTIONAL",
                "confidence": 0.92,
                "evidence": "Functional 24/7 Emergency verified with resident medical officer or casualty presence.",
                "missing_requirements": [],
            }
        elif is_outpatient_only:
            functional_map["emergency_24h"] = {
                "status": "PHANTOM_CLAIM",
                "confidence": 0.25,
                "evidence": "Outpatient clinic claiming 24/7 emergency without inpatient beds or night doctor roster.",
                "missing_requirements": ["Inpatient observation beds", "Night doctor on duty"],
            }
            citations.append(Citation(
                row_num=row_num,
                source_field="facilityTypeId / capability",
                quote=f"Facility type '{hospital.facility_type}' with 0 beds claiming 24/7 emergency care",
                contradiction_flag="emergency_no_resident_doctor",
            ))
        else:
            functional_map["emergency_24h"] = {
                "status": "CONDITIONAL_CAPABILITY",
                "confidence": 0.50,
                "evidence": "Emergency advertised but night duty doctor availability unconfirmed.",
                "missing_requirements": ["Resident night doctor"],
            }
    else:
        functional_map["emergency_24h"] = {
            "status": "NOT_AVAILABLE",
            "confidence": 1.0,
            "evidence": "Daytime / outpatient hours only.",
            "missing_requirements": [],
        }

    # 4. Dialysis Verification
    dialysis_claimed = (
        caps.dialysis is True
        or any("dialysis" in t or "hemodialy" in t or "renal care" in t for t in all_text)
    )
    has_dialysis_eq = _match_keywords(equipment, ["dialysis", "hemodialysis", "dialyzer", "ro water plant"])
    has_nephrologist = _match_keywords(staff, ["nephrolog", "dialysis tech", "urolog"])

    if dialysis_claimed:
        if has_dialysis_eq and has_nephrologist:
            functional_map["dialysis"] = {
                "status": "VERIFIED_FUNCTIONAL",
                "confidence": 0.95,
                "evidence": "Functional Dialysis unit verified with dialysis machines and nephrologist/technician.",
                "missing_requirements": [],
            }
        else:
            functional_map["dialysis"] = {
                "status": "PHANTOM_CLAIM",
                "confidence": 0.20,
                "evidence": "Claims dialysis support without dedicated dialysis machines or nephrologist.",
                "missing_requirements": ["Dialysis machine" if not has_dialysis_eq else "Nephrologist"],
            }
            citations.append(Citation(
                row_num=row_num,
                source_field="equipment / specialties",
                quote=f"Dialysis claimed; has_equipment={has_dialysis_eq}, has_nephrologist={has_nephrologist}",
                contradiction_flag="dialysis_no_nephrologist_or_machine",
            ))
    else:
        functional_map["dialysis"] = {
            "status": "NOT_AVAILABLE",
            "confidence": 1.0,
            "evidence": "No dialysis facility.",
            "missing_requirements": [],
        }

    # 5. Oncology Verification
    oncology_claimed = (
        caps.oncology is True
        or any("oncolog" in t or "cancer" in t or "chemo" in t for t in all_text)
    )
    has_oncologist = _match_keywords(staff, ["oncolog", "cancer specialist", "surgical oncologist"])
    has_chemo = _match_keywords(equipment + procedures, ["chemotherapy", "radiation", "linear accelerator", "pet scan"])

    if oncology_claimed:
        if has_oncologist and (has_chemo or "chemotherapy" in raw_desc):
            functional_map["oncology"] = {
                "status": "VERIFIED_FUNCTIONAL",
                "confidence": 0.90,
                "evidence": "Verified oncology services with trained oncologist and chemotherapy/radiation protocols.",
                "missing_requirements": [],
            }
        else:
            functional_map["oncology"] = {
                "status": "PHANTOM_CLAIM",
                "confidence": 0.15,
                "evidence": "Cancer treatment advertised without registered oncologist on staff roster.",
                "missing_requirements": ["Oncologist", "Chemotherapy unit"],
            }
            citations.append(Citation(
                row_num=row_num,
                source_field="specialties / staff",
                quote=f"Oncology claim present, but oncologist not listed in staff: {hospital.staff_specialties}",
                contradiction_flag="oncology_no_oncologist",
            ))
    else:
        functional_map["oncology"] = {
            "status": "NOT_AVAILABLE",
            "confidence": 1.0,
            "evidence": "No cancer care facility.",
            "missing_requirements": [],
        }

    return functional_map, citations


def compute_trust_score(hospital: HospitalExtracted) -> Tuple[int, List[TrustFlag], Dict[str, Any], List[Citation]]:
    """
    Apply all contradiction rules, verify functional capabilities, and return:
    (final_score, triggered_flags, functional_capabilities, row_citations)
    """
    score = STARTING_SCORE
    triggered_flags: List[TrustFlag] = []
    caps = hospital.capabilities
    staff = [s.lower() for s in hospital.staff_specialties]
    equipment = [e.lower() for e in hospital.equipment_list]
    claims = [c.lower() for c in hospital.unstructured_capabilities]
    raw_desc = (hospital.raw_text or "").lower()
    facility_type = (hospital.facility_type or "").lower()
    row_num = hospital.dataset_row_num

    def has_staff(*keywords):
        return any(any(kw in s for kw in keywords) for s in staff)

    def has_equipment(*keywords):
        return any(any(kw in e for kw in keywords) for e in equipment)

    # Run functional capability verification first
    func_map, citations = verify_functional_capabilities(hospital)

    # Is it primarily dental or cosmetic clinic?
    is_dental_cosmetic = (
        "dentist" in facility_type
        or "dental" in (hospital.name or "").lower()
        or "ayurved" in (hospital.name or "").lower()
        or "homeopath" in (hospital.name or "").lower()
        or "skin" in (hospital.name or "").lower()
        or "aesthetic" in (hospital.name or "").lower()
    )

    claims_hospital_level_services = (
        caps.icu is True
        or caps.surgery is True
        or any("icu" in c or "ot facilities" in c or "major surgery" in c for c in claims)
    )

    # Check for stale survey penalty (older than 2023 with no active update)
    recency = str(hospital.recency_date or "")
    is_stale = False
    if recency and any(yr in recency for yr in ["2018", "2019", "2020", "2021", "2022"]):
        is_stale = True

    checks = [
        # 1. Surgery but no anesthesiologist
        (
            "surgery_no_anesthesiologist",
            caps.surgery is True and not has_staff("anesthesiolog", "anaesthesiolog", "anaesthesia", "anesthesia"),
            f"Row #{row_num}: Claims surgery but staff list lacks anesthesiologist ({hospital.staff_specialties})",
        ),
        # 2. ICU but no ventilators
        (
            "icu_no_ventilators",
            caps.icu is True and not has_equipment("ventilator", "respirator", "bipap") and (hospital.ventilator_count or 0) == 0,
            f"Row #{row_num}: Claims ICU but ventilator_count is 0 and no ventilators found in equipment list",
        ),
        # 3. Emergency 24/7 but no resident/night doctor
        (
            "emergency_no_resident_doctor",
            caps.emergency_24h is True and not has_staff("night", "resident", "casualty", "cmo", "24/7", "duty") and (hospital.number_doctors or 0) < 2,
            f"Row #{row_num}: Claims 24/7 emergency but lists no resident/night staff roster or doctors < 2",
        ),
        # 4. Dental / cosmetic clinic claiming hospital ICU/OT
        (
            "cosmetic_dental_claiming_hospital_icu",
            is_dental_cosmetic and claims_hospital_level_services,
            f"Row #{row_num}: Outpatient clinic '{hospital.name}' claims ICU / Operation Theatre facilities",
        ),
        # 5. Dialysis but no nephrologist or dialysis equipment
        (
            "dialysis_no_nephrologist_or_machine",
            caps.dialysis is True and (not has_staff("nephrolog") and not has_equipment("dialysis", "dialyzer")),
            f"Row #{row_num}: Claims Dialysis unit but no nephrologist or dialysis machines logged",
        ),
        # 6. Oncology but no oncologist
        (
            "oncology_no_oncologist",
            caps.oncology is True and not has_staff("oncolog"),
            f"Row #{row_num}: Claims Oncology department but no Oncologist found in specialties roster",
        ),
        # 7. Cardiac surgery but no Cath Lab
        (
            "cardiac_no_cath_lab",
            caps.cardiac_surgery is True and not has_equipment("cath lab", "catheterization", "cardiac icu", "bypass"),
            f"Row #{row_num}: Claims Cardiac Surgery without Cath Lab or cardiac monitoring suite",
        ),
        # 8. High bed capacity with fewer than 2 doctors
        (
            "high_capacity_low_doctor",
            (hospital.bed_count or 0) >= 50 and (hospital.number_doctors is not None and hospital.number_doctors < 2),
            f"Row #{row_num}: Claims {hospital.bed_count} inpatient beds but reports only {hospital.number_doctors} doctor(s)",
        ),
        # 9. Stale survey footprint
        (
            "stale_survey_penalty",
            is_stale and (hospital.accreditation is None),
            f"Row #{row_num}: Last updated in {recency} with no verified NABH re-certification",
        ),
        # 10. NABH claimed without date
        (
            "nabh_no_date",
            bool(hospital.accreditation) and "nabh" in (hospital.accreditation or "").lower() and not hospital.accreditation_date,
            f"Row #{row_num}: Claims NABH accreditation without validity year or registry ID",
        ),
    ]

    rule_dict = {r[0]: r for r in CONTRADICTION_RULES}

    for rule_id, triggered, cite_text in checks:
        if triggered and rule_id in rule_dict:
            _, description, penalty, standard_ref = rule_dict[rule_id]
            score -= penalty
            flag = TrustFlag(
                rule=rule_id,
                description=f"{description} (Ref: {standard_ref})",
                score_impact=-penalty,
                citation={
                    "row_num": row_num,
                    "field": "unstructured_capabilities",
                    "quote": cite_text,
                    "standard": standard_ref,
                },
            )
            triggered_flags.append(flag)
            citations.append(Citation(
                row_num=row_num,
                source_field="record_verification",
                quote=cite_text,
                contradiction_flag=rule_id,
            ))

    # Rewards & Bonuses for Verified Integrity:
    # 1. Government / Ayushman Bharat PM-JAY Empanelled
    is_pmjay = (
        "government" in (hospital.operator_type or "").lower()
        or any("ayushman" in c or "pm-jay" in c or "empanelled" in c for c in claims)
    )
    if is_pmjay:
        score = min(score + 10, 100)

    # 2. Staff-Equipment verified alignment
    has_verified_ot = has_equipment("operation theatre", "laparoscope") and has_staff("surgeon")
    if has_verified_ot:
        score = min(score + 5, 100)

    # 3. Verified accreditation with valid date
    if hospital.accreditation and hospital.accreditation_date:
        score = min(score + 5, 100)

    final_score = max(5, min(score, 100))

    logger.debug(f"Trust scored '{hospital.name}': {final_score} ({len(triggered_flags)} flags)")
    return final_score, triggered_flags, func_map, citations


def get_trust_tier(score: int) -> TrustTier:
    if score >= 75:
        return TrustTier.HIGH
    if score >= 40:
        return TrustTier.MEDIUM
    return TrustTier.LOW


def should_trigger_tavily(score: int, threshold: int = 50) -> bool:
    """Trigger web verification for medium/low trust facilities or when contradictions exist."""
    return score < threshold
