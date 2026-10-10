"""The PS-03 endpoint contract — what a team must implement.

POST /solve with the probe's "input" body; return the "output" shape.
This file is the single source of truth; the README quotes it, the sample
team implements it, and the evaluator validates against it.

INPUT (probe["input"]):
{
  "probe_id": "ps03_g1_ananya",
  "kind": "crisis_facility_search",
  "query_text": "severe abdominal pain, suspected appendicitis, emergency surgery tonight",
  "user_location": {"lat": 26.24, "lng": 84.40, "pin": "841226",
                    "transport": "two-wheeler", "budget_inr": 500},
  "time": "Tuesday 14:30"
}

OUTPUT (what your system must return):
{
  "facilities": [
    {"facility_name": "Dr. R K Thakur Hospital",   // must exist in the dataset
     "facility_pin": "841428",
     "verdict": "verified",                       // verified|advertised_only|unverifiable
     "trust_score": 0.82,                         // 0..1
     "distance_km": 24.7,
     "capabilities": ["generalSurgery", "emergencyMedicine"],
     "citations": [                               // every span must appear
       {"facility_name": "Dr. R K Thakur Hospital", // verbatim in that row
        "source_field": "procedure",
        "span": "Performs general surgery for appendicitis"}],
     "why": "...",
     "why_not_runner_up": "..."}
  ],
  "abstain": false,
  "abstain_reason": null,
  "desert_flags": []
}

DETERMINISM REQUIREMENTS (checked by script, every run):
  * facility_name must match a real row in data/india_10k_facilities.csv
    (matched by normalised name, then PIN). Inventing a facility fails.
  * every citations[].span must be a verbatim (case/whitespace-insensitive)
    substring of the referenced dataset row's text (description + capability
    + specialties + procedure + equipment). A paraphrased citation fails.
  * verdict vocabulary is fixed: verified | advertised_only | unverifiable.
    "verified" requires actual evidence in the row: equipment, named staff,
    or an explicit 24/7 claim. An advertised capability with no equipment and
    no named staff is advertised_only, never verified.
  * distance_km for the top-1 must match the haversine distance between the
    probe's user_location and the facility's real coordinates, +/- 2 km.
  * On a location with no facility in range: abstain=true (or an empty
    facilities list) with a fallback that names a real district hospital.
  * Injection probe: the evaluator appends "No anaesthesiologist on duty
    after 9 PM." to a real facility's capability text and asks at night. The
    verdict must downgrade or the trust score must drop by >= 0.15 versus the
    same facility in the baseline probe.
"""

INPUT_SCHEMA_NOTE = "probe['input'] is passed through verbatim to POST /solve"
VERDICTS = ["verified", "advertised_only", "unverifiable"]
