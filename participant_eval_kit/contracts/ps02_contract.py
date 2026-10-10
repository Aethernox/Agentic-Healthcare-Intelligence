"""The PS-02 endpoint contract — what a team must implement.

POST /solve with the probe's "input" body; return the "output" shape.
This file is the single source of truth; the README quotes it, the sample
team implements it, and the evaluator validates against it.

INPUT (probe["input"]):
{
  "probe_id": "ps02_g1_divya",
  "kind": "profile_to_pathway",
  "profile_text": "<free text from the candidate>",
  "target_role_id": "soc_43-3031_00",
  "target_role_title": "Bookkeeping, Accounting, and Auditing Clerks",
  "persona": {"age": 23, "education": "Class 12",
              "location": "Hoshiarpur, Punjab",
              "budget_inr": 2000, "horizon_months": 12}
}

OUTPUT (what your system must return):
{
  "skills_profile": [
    {"skill": "Excel/Spreadsheets",          // must exist in the taxonomy
     "proficiency": "beginner",              // beginner|intermediate|advanced
     "evidence_span": "taught myself Excel", // VERBATIM substring of profile_text
     "confidence": 0.6}                      // 0..1
  ],
  "taxonomy_extension": [                    // optional, but the honest way
    {"skill": "Tally",                       // to use a skill the dataset
     "mapped_to": "ERP Systems",             // does not literally contain
     "definition": "accounting software by Tally Solutions"}
  ],
  "skill_gap": [
    {"skill": "Typing Speed", "required_by_role": true, "current": "none"}
  ],
  "retraining_pathway": [
    {"skill": "Typing Speed", "resource": "NIELIT CCC",
     "hours": 120, "cost_inr": 0, "weeks": 8}
  ],
  "transition_probability_12m": 0.62,       // a calibrated probability, 0..1
  "abstain": false,
  "abstain_reason": null,
  "uncertainty_note": null
}

DETERMINISM REQUIREMENTS (checked by script, every run):
  * evidence_span must be a verbatim (case/whitespace-insensitive) substring
    of profile_text. A skill with no quote does not count as grounded.
  * skill must exist in the Indian skills dataset vocabulary (the union of
    required_skills over all 820 roles), or in taxonomy_extension with a
    mapped_to that does exist. Inventing a skill code is a grounding failure.
  * transition_probability_12m must be a number in [0, 1] and must be stable:
    fire the same probe 4 times, the probabilities must agree within 0.05.
  * On an empty or one-line profile: abstain=true, or a probability < 0.4.
  * DELETE a sentence about a skill -> that skill must leave the profile or
    drop proficiency. The evaluator tests this by removing a sentence.
"""

INPUT_SCHEMA_NOTE = "probe['input'] is passed through verbatim to POST /solve"
OUTPUT_FIELDS = [
    "skills_profile", "taxonomy_extension", "skill_gap",
    "retraining_pathway", "transition_probability_12m",
    "abstain", "abstain_reason", "uncertainty_note",
]
