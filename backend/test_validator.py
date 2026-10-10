import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.validator import validate_facility_against_standards
from schemas.hospital import HospitalResponse
from tools.geocoder import resolve_user_location, haversine_distance, detect_ip_location

def test_validator():
    mock_hospital = {
        "id": 1,
        "name": "Patna Medical College",
        "city": "Patna",
        "state": "Bihar",
        "trust_score": 80,
        "trust_tier": "high",
        "functional_capabilities": {},
        "staff_specialties": ["Cardiology"],
        "equipment_list": ["ECG"],
    }
    h = HospitalResponse(**mock_hospital)

    # Test with procedure_needed as None
    context_with_none = {
        "procedure_needed": None,
        "is_emergency": False,
        "budget": None,
    }
    res = validate_facility_against_standards(h, context_with_none)
    assert res["verdict"] in ("PASSED", "PASSED_WITH_CONDITIONS", "FAILED_STANDARDS")

    # Test with surgery procedure
    context_surgery = {
        "procedure_needed": "Emergency Appendectomy",
        "is_emergency": True,
        "budget": 500,
    }
    res2 = validate_facility_against_standards(h, context_surgery)
    assert res2["verdict"] in ("PASSED", "PASSED_WITH_CONDITIONS", "FAILED_STANDARDS")


def test_location_resolution():
    # 1. Manual City Name
    loc1 = resolve_user_location(user_location="Saharsa")
    assert loc1["lat"] is not None and loc1["lng"] is not None
    assert "Saharsa" in loc1["address"]
    assert loc1["source"] == "manual"

    # 2. Manual PIN Code
    loc2 = resolve_user_location(user_location="852200")
    assert loc2["lat"] is not None and loc2["lng"] is not None
    assert "852200" in loc2["address"]

    # 3. Explicit GPS Coordinates
    loc3 = resolve_user_location(lat=25.6120, lng=85.1580)
    assert loc3["lat"] == 25.612
    assert loc3["lng"] == 85.158
    assert loc3["source"] == "gps"

    # 4. Auto-detect Fallback
    loc4 = resolve_user_location(auto_detect=True)
    assert loc4["lat"] is not None and loc4["lng"] is not None
    assert loc4["source"] in ("ip_auto", "fallback")

    # 5. Distance check (Patna to Saharsa ~ 150-160 km)
    dist = haversine_distance(25.6120, 85.1580, 25.8834, 86.5851)
    assert 120 < dist < 180

from agents.reasoner import (
    analyze_natural_language_request,
    evaluate_hospital_clinical_fitness,
    detect_clinical_domain,
)

def test_reasoner_nlp():
    # 1. Natural Language Hindi / Hinglish Query
    query_hindi = "mere pet me kal raat se bohot tez dard hai aur ulti ho rahi hai"
    analysis1 = analyze_natural_language_request(query_hindi)
    assert len(analysis1.questions) >= 3, f"Expected 3-5 questions, got {len(analysis1.questions)}"
    assert analysis1.urgency_tier in ("CRITICAL_EMERGENCY", "URGENT")
    assert any("append" in d.lower() or "abdom" in d.lower() for d in analysis1.differential_diagnosis)
    print("Test 1 Passed: Hinglish abdominal pain correctly parsed, generated", len(analysis1.questions), "questions.")

    # 2. Chest pain & cardiac natural language
    query_cardiac = "My elderly uncle has crushing chest pressure radiating to left arm with cold sweats"
    analysis2 = analyze_natural_language_request(query_cardiac)
    assert len(analysis2.questions) >= 3
    assert analysis2.urgency_tier == "CRITICAL_EMERGENCY"
    assert "icu" in analysis2.required_capabilities or "cardiac_surgery" in analysis2.required_capabilities
    print("Test 2 Passed: Cardiac emergency parsed, generated", len(analysis2.questions), "questions.")

    # 3. Interactive refinement with user answers
    answers = {
        "q_pain_migration": "Yes, shifted to lower right and hurts when walking",
        "q_fever_vomiting": "Both fever (>100°F) and vomiting",
        "q_food_tolerance": "Cannot keep anything down (vomiting everything)",
    }
    refined_analysis = analyze_natural_language_request(
        "Severe stomach pain since 18 hours",
        diagnostic_answers=answers
    )
    assert refined_analysis.confirmed_diagnosis is not None
    assert "Appendicitis" in refined_analysis.confirmed_diagnosis
    assert refined_analysis.clarification_summary is not None
    assert "surgery" in refined_analysis.required_capabilities
    print("Test 3 Passed: Interactive diagnosis refined with 3 answers ->", refined_analysis.confirmed_diagnosis)

    # 4. Clinical fitness evaluation
    mock_equipped = {
        "functional_capabilities": {
            "surgery": {"status": "VERIFIED_FUNCTIONAL", "evidence": "Operational OT with on-call surgeon"},
            "emergency_24h": {"status": "VERIFIED_FUNCTIONAL", "evidence": "24/7 casualty"},
        },
        "capabilities": {"surgery": True, "emergency_24h": True},
        "equipment_list": ["Laparoscopy OT", "Ultrasound Abdomen"],
        "staff_specialties": ["General Surgery"],
    }
    bonus, reasons = evaluate_hospital_clinical_fitness(mock_equipped, refined_analysis)
    assert bonus > 30.0
    assert len(reasons) > 0
    print(f"Test 4 Passed: Hospital clinical fitness evaluated: bonus={bonus}, reasons={reasons}")


if __name__ == "__main__":
    test_validator()
    test_location_resolution()
    test_reasoner_nlp()
    print("All validator and clinical reasoning unit tests passed successfully!")

