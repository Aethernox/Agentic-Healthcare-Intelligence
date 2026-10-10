# MedMap - Architecture Reference

> Deep-dive into how each layer fits together. Keep this updated when adding new components.

---

## System Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        BROWSER                                   │
│  React + Vite (port 5173 dev / port 80 prod)                    │
│                                                                  │
│  Home (Search)    Map (Leaflet)    Dashboard (Recharts)          │
│  ├─ SearchBar     ├─ MapDashboard  ├─ Trust Pie Chart            │
│  ├─ AgentPanel    ├─ Filter Sidebar├─ Specialty Gap Bars         │
│  └─ HospitalCard  └─ Detail Popup  └─ Desert Districts Table     │
└──────────────────────────────┬───────────────────────────────────┘
                               │ HTTP / SSE
┌──────────────────────────────▼───────────────────────────────────┐
│                    FastAPI Backend (port 8000)                   │
│                                                                  │
│  POST /api/search          → search router                       │
│  POST /api/search/stream   → SSE streaming router                │
│  GET  /api/hospitals       → hospitals router (filtered list)    │
│  GET  /api/hospitals/{id}  → single hospital detail              │
│  GET  /api/hospitals/map/markers → lightweight map data          │
│  GET  /api/dashboard/stats → aggregate stats                     │
│  GET  /api/dashboard/deserts → top underserved districts         │
└────┬────────────┬─────────────────┬───────────────┬─────────────┘
     │            │                 │               │
┌────▼──────┐ ┌──▼────────────┐ ┌──▼──────────┐ ┌─▼──────────────┐
│ AGENTS    │ │  TOOLS        │ │  PIPELINES  │ │  DATA LAYER    │
│           │ │               │ │             │ │                │
│extractor  │ │vector_search  │ │ingest.py    │ │PostgreSQL      │
│  └Claude  │ │  └Mosaic AI   │ │  └Excel→DB  │ │  └hospitals    │
│           │ │               │ │             │ │     table      │
│trust_score│ │tavily_search  │ │embed.py     │ │                │
│  └10 rules│ │  └Tavily API  │ │  └OpenAI    │ │Mosaic AI VS    │
│           │ │               │ │    embeds   │ │  └Semantic     │
│reasoner   │ │db_query       │ │             │ │    index       │
│  └LangChn │ │  └SQLAlchemy  │ │             │ │                │
│           │ │               │ │             │ │Redis Cache     │
│validator  │ │               │ │             │ │                │
│  └Claude  │ │               │ │             │ │MLflow 3        │
│   Haiku   │ │               │ │             │ │  └Trace DB     │
└───────────┘ └───────────────┘ └─────────────┘ └────────────────┘
```

---

## Request Flow - Search Query

```
User types: "Find nearest ICU in rural Bihar with 24/7 emergency"
                              │
                              ▼
            POST /api/search  (SearchRequest)
                              │
                              ▼
              reasoner.run_search_agent(request)
                              │
                    ┌─────────┴──────────┐
                    │  LangChain Agent   │
                    │                   │
                    │  Step 1: vector_search("ICU Bihar emergency")
                    │    → Mosaic AI Vector Search → top 20 records
                    │
                    │  Step 2: structured_lookup(state="Bihar", has_icu=True, has_emergency=True)
                    │    → PostgreSQL filter → 47 candidates
                    │
                    │  Step 3: trust_scorer_tool(facility_id) × 47
                    │    → trust_scorer.compute_trust_score() per record
                    │    → Flags contradictions
                    │
                    │  Step 4 (conditional): tavily_search for score < 50
                    │    → verify_hospital_with_tavily()
                    │    → Score adjusted ±10-15
                    │
                    │  Step 5: Claude generates ranked explanation
                    └─────────────────────────────────┘
                              │
                              ▼
              validator.validate_recommendations(top_5)
              [stretch - secondary contradiction check]
                              │
                              ▼
                    SearchResponse {
                      results: HospitalResponse[],
                      agent_steps: AgentStep[],
                      mlflow_run_id: str
                    }
                              │
                              ▼
                    Frontend renders:
                    - AgentThinkingPanel (steps)
                    - HospitalCard × N (results)
```

---

## Data Pipeline Flow (Databricks)

```
VF_Hackathon_Dataset_India_Large.xlsx
              │
              ▼ 01_ingest.py
  medmap.raw.hospitals (Delta)
  10,000 rows, raw_text column
              │
              ▼ 02_extract.py  [Claude Sonnet × 10,000]
  medmap.extracted.hospitals_json (Delta)
  Structured JSON per record
  MLflow: extraction_confidence logged
              │
              ▼ 03_embed_index.py  [text-embedding-3-small]
  1,536-dim embeddings generated
  Mosaic AI Vector Search endpoint + index
  Upserted in chunks of 1,000
              │
              ▼ 04_trust_score.py  [Rule engine + Tavily]
  medmap.scored.hospital_trust (Delta)
  trust_score, trust_tier, flags, tavily_summary
  MLflow: trust distribution metrics logged
              │
              ▼ Sync to PostgreSQL (backend)
  hospitals table (query-ready)
```

---

## Trust Scoring Pipeline

```
HospitalExtracted record
        │
        ▼
  START score = 100
        │
        ├─ has surgery=True AND no anesthesiologist → -30
        ├─ has icu=True AND no ventilators → -25
        ├─ has emergency_24h=True AND no night staff → -20
        ├─ has nicu=True AND no neonatal equipment → -25
        ├─ has oncology=True AND no oncologist → -30
        ├─ has accreditation AND no date → -15
        ├─ has cardiac_surgery AND no cath lab → -25
        ├─ has dialysis AND no nephrologist → -20
        ├─ has surgery AND no operation theatre → -20
        └─ 200+ beds AND icu=False → -15
        │
        ├─ accreditation + date present → +5
        └─ extraction_confidence ≥ 0.9 → +3
        │
        ▼
  final_score = clamp(0, score, 100)
        │
        ├─ >= 75 -> HIGH TRUST
        ├─ >= 40 -> MEDIUM TRUST
        └─ < 40 -> LOW TRUST
        │
        ▼ (if score < 50)
  Tavily web verification triggered
        │
        ├─ Positive signals found → +10-15
        └─ Negative signals found → -15
```

---

## Agent Tools

| Tool | Input | Output | Backend |
|------|-------|--------|---------|
| `vector_search` | query string, top_k | Record IDs + summaries | Mosaic AI Vector Search |
| `structured_lookup` | state, specialty, beds, icu, emergency flags | Filtered hospital list | PostgreSQL |
| `get_nearby` | lat, lng, radius_km | Nearby facility IDs | PostGIS `ST_DWithin` |
| `trust_scorer_tool` | facility_id | Trust score breakdown | `trust_scorer.py` rules |
| `tavily_search` | query string | Web evidence summary | Tavily API |

---

## Database Schema (PostgreSQL)

```sql
hospitals (
  id, record_id,
  name, city, district, state, pin_code,
  latitude, longitude,                       -- PostGIS-indexed
  bed_count, icu_beds, ventilator_count,
  staff_specialties TEXT[],
  equipment_list TEXT[],
  accreditation, accreditation_date,
  cap_icu, cap_surgery, cap_emergency_24h,   -- extracted booleans
  cap_dialysis, cap_nicu, cap_oncology,
  cap_trauma, cap_blood_bank,
  cap_cardiac_surgery, cap_neurosurgery,
  trust_score INT,                           -- 0-100
  trust_tier TEXT,                           -- high/medium/low
  trust_flags TEXT[],
  tavily_verified BOOL,
  tavily_summary TEXT,
  raw_text TEXT,
  extraction_source TEXT,
  extraction_confidence DOUBLE
)
```

---

## Environment Variables

| Variable | Used By | Required |
|----------|---------|----------|
| `ANTHROPIC_API_KEY` | extractor, reasoner, validator | Yes |
| `TAVILY_API_KEY` | tavily_search tool | Yes |
| `DATABRICKS_HOST` | vector_search, embed pipeline | Yes (prod) |
| `DATABRICKS_TOKEN` | vector_search, embed pipeline | Yes (prod) |
| `VECTOR_SEARCH_ENDPOINT` | Mosaic AI | Yes (prod) |
| `DATABASE_URL` | db_query, SQLAlchemy | Yes |
| `REDIS_URL` | response cache | Optional |
| `MLFLOW_TRACKING_URI` | mlflow_config | Yes (prod) |
| `VITE_API_URL` | frontend api.js | Optional (defaults to /api) |
| `VITE_USE_MOCK` | frontend api.js | Set `true` for local dev |
