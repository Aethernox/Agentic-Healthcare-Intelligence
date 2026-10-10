# Participant Guide — All Tracks (PS-01 · PS-02 · PS-03)

This document tells you **what to build**, **what to submit**, and **how you will be scored**.  
It does **not** reveal golden answers or hidden probes.

---

## Selection flow (all tracks)

1. **Answer evaluation (elimination)** — submit predictions / endpoint responses on public + hidden probes. Some teams are eliminated.
2. **PPT + video presentation** — teams that pass submit a pitch deck and a short video walkthrough.
3. **Shortlist presentations (invited)** — shortlisted candidates may be asked for a live presentation or Q&A.
4. **Winners announced**

---

## Common submission options

You may submit **either**:

| Mode | What you provide |
|------|------------------|
| **JSONL file** | One JSON object per probe / scenario id |
| **HTTP endpoint** | `POST /solve` (or track-specific path) that accepts the probe input and returns the output shape within **≤ 8 seconds** |

Both modes are scored by the same deterministic checks. Endpoint mode is preferred for Stage 1 if you can keep a server up during evaluation windows.

---

# PS-01 — Commerce (Decisioned Offer)

### What to implement
A system that, given a scenario (user + merchant + moment), decides `send` or `skip`, optionally produces a grounded offer + localized notification, and may estimate profit.

### Input
Public scenarios: `scenarios_public.csv` (labels available for self-debug).  
Hidden holdout: distributed as **blind** (no expected labels) or scored privately by organizers.

### Output (JSON, one per scenario)

```json
{
  "scenario_id": "cur_001",
  "action": "send",
  "reason": "short grounded explanation",
  "offer": {
    "merchant_id": "m_001",
    "discount_pct": 15,
    "item_id": "optional",
    "final_price_inr": 170,
    "valid_minutes": 25
  },
  "notification": {
    "title": "...",
    "body": "...",
    "language": "hi-en",
    "cta": "Grab it"
  },
  "ui_hints": {
    "distance_m": 180,
    "walk_minutes": 3,
    "weather_note": "hot afternoon"
  },
  "profit_estimate_inr": 42.5
}
```

For `skip`, omit or null `offer` / `notification`; still provide `reason`.

### What is scored (high level)
- Decision match on hidden cases  
- Groundedness (names & numbers exist in data)  
- Constraint respect (consent, hours, max discount, margin)  
- Localization (language matches user preference)  
- Profit awareness (optional field present and sensible)

Hard rules: `marketing_consent = false` is a promotional block; discount ≤ merchant max; respect open hours.

---

# PS-02 — Career / Skills (The Unmapped)

### What to implement (at least 2 of 3 components)
1. **Skills Signal Engine** — map free-text experience to a structured skills profile grounded in the Indian skills taxonomy (optional O*NET / ESCO extension).  
2. **Transition Recommender** — skill gap + retraining pathway + **calibrated** 12-month transition probability (a number in [0,1], not a vague “high match”).  
3. **Aggregate Signals Dashboard** — at least 2 econometric signals (wage trends, employment growth, automation exposure) from the packaged sources.

### Self-topic constraint
Submit a **falsifiable claim** in `card.md` before building.  
Format: name an intervention, measurable threshold, mechanism, control condition.  
Missing or unfalsifiable claim → card score 0.

### Endpoint / JSON contract

**Input (example):**
```json
{
  "probe_id": "ps02_g1_divya",
  "kind": "profile_to_pathway",
  "profile_text": "<free text>",
  "target_role_id": "soc_43-3031_00",
  "target_role_title": "Bookkeeping, Accounting, and Auditing Clerks",
  "persona": {
    "age": 23,
    "education": "Class 12",
    "location": "Hoshiarpur, Punjab",
    "budget_inr": 2000,
    "horizon_months": 12
  }
}
```

**Output:**
```json
{
  "skills_profile": [
    {
      "skill": "Excel/Spreadsheets",
      "proficiency": "beginner",
      "evidence_span": "taught myself Excel",
      "confidence": 0.6
    }
  ],
  "taxonomy_extension": [
    {
      "skill": "Tally",
      "mapped_to": "ERP Systems",
      "definition": "accounting software by Tally Solutions"
    }
  ],
  "skill_gap": [
    {"skill": "Typing Speed", "required_by_role": true, "current": "none"}
  ],
  "retraining_pathway": [
    {
      "skill": "Typing Speed",
      "resource": "NIELIT CCC",
      "hours": 120,
      "cost_inr": 0,
      "weeks": 8
    }
  ],
  "transition_probability_12m": 0.62,
  "abstain": false,
  "abstain_reason": null,
  "uncertainty_note": null
}
```

### What is scored (high level — no hidden answers revealed)
- **Grounding**: every skill must exist in the taxonomy **or** be declared in `taxonomy_extension` with a real `mapped_to`. `evidence_span` must be a **verbatim substring** of `profile_text`.  
- **Stability**: same input → same skills / probability (within tight tolerance) across repeated runs.  
- **Direction**: removing evidence about a skill must remove or weaken that skill.  
- **Abstention**: empty / one-line profiles must abstain or return low probability.  
- **Calibration shape**: probability is a real number in [0,1], not a label.  
- Optional LLM-judged quality on pathway realism and mapping fairness (constrained; must quote your output).

---

# PS-03 — Healthcare Intelligence (The Right Care)

### What to implement
An agentic system that:
1. Extracts and verifies real capabilities from messy facility text (functional ICU vs listed only).  
2. Reasons over multi-attribute queries and applies a **Trust Scorer** (flag contradictions, e.g. “advanced surgery” with no anesthesiologist).  
3. Returns row-level **citations** (verbatim spans), self-correction, and optional crisis / desert signals by PIN.

### Endpoint / JSON contract

**Input (example):**
```json
{
  "probe_id": "ps03_g1_ananya",
  "kind": "crisis_facility_search",
  "query_text": "severe abdominal pain, suspected appendicitis, emergency surgery tonight",
  "user_location": {
    "lat": 26.24,
    "lng": 84.40,
    "pin": "841226",
    "transport": "two-wheeler",
    "budget_inr": 500
  },
  "time": "Tuesday 14:30"
}
```

**Output:**
```json
{
  "facilities": [
    {
      "facility_name": "Dr. R K Thakur Hospital",
      "facility_pin": "841428",
      "verdict": "verified",
      "trust_score": 0.82,
      "distance_km": 24.7,
      "capabilities": ["generalSurgery", "emergencyMedicine"],
      "citations": [
        {
          "facility_name": "Dr. R K Thakur Hospital",
          "source_field": "procedure",
          "span": "Performs general surgery for appendicitis"
        }
      ],
      "why": "...",
      "why_not_runner_up": "..."
    }
  ],
  "abstain": false,
  "abstain_reason": null,
  "desert_flags": []
}
```

`verdict` must be one of: `verified` | `advertised_only` | `unverifiable`.

### What is scored (high level)
- **Grounding**: facility names must exist in the India 10k dataset; every citation `span` must appear **verbatim** in that facility’s text fields.  
- **Trust / contradiction**: systems that claim “verified” without evidence, or ignore clear contradictions, lose points.  
- **Distance**: reported `distance_km` must match haversine to the real coordinates (±2 km).  
- **Abstention**: when nothing is in range, abstain (or empty list) with a sensible fallback.  
- **Injection / direction probes**: hidden tests that inject a negative fact into a facility’s text; trust or verdict must move in the right direction.  
- Optional constrained LLM judge on explanation quality.

---

## After Stage 1 (all tracks)

Submit:
- **Pitch deck** (PPT/PDF, ≤ 8–10 slides)  
- **Video** (≈ 2–4 minutes) of the system on public cases  

Shortlisted teams may be invited to present live. Winners are announced after that.

## Practical tips

- Prefer deterministic, auditable pipelines over pure LLM guessing.  
- Always return citations / evidence spans when the contract asks for them.  
- Prefer abstaining over hallucinating.  
- Keep latency ≤ 8 s per request for endpoint mode.  
- Do not train on or peek at labeled hidden holdouts.
