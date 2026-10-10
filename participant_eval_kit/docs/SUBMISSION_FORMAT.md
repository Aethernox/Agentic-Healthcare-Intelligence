# Submission Format Cheat Sheet

## JSONL (offline)

One JSON object per line. Key field must match the probe/scenario id.

### PS-01
```json
{"scenario_id": "cur_001", "action": "send", "reason": "...", "offer": {...}, "notification": {...}}
```

### PS-02
```json
{"probe_id": "ps02_g1_divya", "skills_profile": [...], "skill_gap": [...], "retraining_pathway": [...], "transition_probability_12m": 0.62, "abstain": false}
```

### PS-03
```json
{"probe_id": "ps03_g1_ananya", "facilities": [{"facility_name": "...", "verdict": "verified", "trust_score": 0.8, "distance_km": 12.3, "citations": [...]}], "abstain": false}
```

## HTTP

```
POST /solve
Content-Type: application/json

<probe input body>

→ <output JSON as above>
```

Optional: `GET /health` → `{"ok": true}`

Timeout: **8 seconds** per call.

Full field contracts: see `ps02_career/contract.py` and `ps03_healthcare/contract.py` in the evaluator kit, or the Participant Guide.
