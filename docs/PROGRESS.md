# MedMap - Build Progress Log

> This file is updated every session. It tracks what has been built, what is pending, and decisions made along the way.

---

## Session 1 - Apr 25, 2026

**Goal:** Full project scaffold from empty repo

**Status:** done Complete

---

### What Was Built

#### Repository Setup
- Initialized git repo at `/Users/sriks/Documents/Projects/medmap`
- Created `.gitignore` (Python, Node, `.env`, data files, MLflow artifacts)
- Created `.env.example` documenting all required keys
- Initial commit: `a3a9ca2`

---

#### Frontend - `frontend/`

| File | Status | Description |
|------|--------|-------------|
| `package.json` | done | React 18, Vite 6, Tailwind 3, Leaflet, Recharts, Framer Motion, Lucide |
| `vite.config.js` | done | Vite config with `/api` proxy to backend |
| `tailwind.config.js` | done | Custom colors: `trust.high/medium/low`, `medmap.*` palette |
| `postcss.config.js` | done | Autoprefixer + Tailwind |
| `index.html` | done | Fonts (Inter, JetBrains Mono), Leaflet CSS |
| `src/main.jsx` | done | React root entry |
| `src/styles/index.css` | done | Tailwind layers, glass-card component, trust badge classes, Leaflet dark overrides |
| `src/App.jsx` | done | React Router, Navbar (Search / Map / Policy View), 10k records status indicator |
| `src/pages/Home.jsx` | done | Hero, stats row (10k records/28 states/6240 high-trust/847 deserts), search bar, example query chips, results + agent panel grid |
| `src/pages/Map.jsx` | done | Full-screen layout, filter sidebar (trust tier, specialty, desert overlay toggle), map area, hospital detail popup |
| `src/pages/Dashboard.jsx` | done | Policymaker view - 4 stat cards, trust distribution pie, specialty gap bar chart, state breakdown stacked bar, top-10 desert districts table |
| `src/components/SearchBar.jsx` | done | Natural language input, Enter key support, loading state with spinner |
| `src/components/HospitalCard.jsx` | done | Rank badge, capabilities checklist (8 types), trust badge, expandable "Why this trust score?" with contradiction flags + Tavily summary |
| `src/components/TrustScoreBadge.jsx` | done | badge keyed on 0-100 score, configurable size |
| `src/components/AgentThinkingPanel.jsx` | done | Live streaming step display, color-coded by step type, auto-scroll to latest |
| `src/components/MapDashboard.jsx` | done | Leaflet map centered on India, dynamic markers color-coded by trust score, filter-reactive, tooltip on hover |
| `src/utils/api.js` | done | Axios client, `searchHospitals()` with mock fallback (simulates 7 streaming steps + 3 sample hospitals), `getHospitals()`, `getDashboardStats()` |
| `Dockerfile` | done | Multi-stage: Node build - nginx serve |
| `nginx.conf` | done | SPA routing + `/api/` proxy |

**Frontend runs fully with mocks - no API keys needed:**
```bash
cd frontend && npm install && npm run dev
# http://localhost:5173
```

---

#### Backend - `backend/`

| File | Status | Description |
|------|--------|-------------|
| `main.py` | done | FastAPI app, CORS, lifespan, global error handler, router mounting |
| `config.py` | done | Pydantic Settings - all env vars with defaults (Anthropic, Tavily, Databricks, DB, Redis, MLflow, trust thresholds) |
| `requirements.txt` | done | FastAPI, LangChain, Anthropic, Tavily, SQLAlchemy, Redis, MLflow, pandas, openpyxl |
| `Dockerfile` | done | Python 3.11-slim, uvicorn with 2 workers |
| `migrations/init.sql` | done | Full PostgreSQL schema: hospitals table with PostGIS, geospatial indexes, `hospital_map_markers` view |

**Schemas (`schemas/`)**

| File | Status | Description |
|------|--------|-------------|
| `hospital.py` | done | `Capabilities`, `HospitalBase`, `HospitalExtracted`, `TrustFlag`, `HospitalTrustScore`, `HospitalResponse`, `SearchRequest`, `SearchResponse`, `AgentStep` |

**Agents (`agents/`)**

| File | Status | Description |
|------|--------|-------------|
| `extractor.py` | done | Claude extraction prompt → structured JSON, batch with semaphore concurrency control, fallback on error |
| `trust_scorer.py` | done | 10 contradiction rules, score from 100 with penalties, completeness bonus, `get_trust_tier()`, `should_trigger_tavily()` |
| `reasoner.py` | done | LangChain `create_tool_calling_agent` with 5 tools (vector_search, structured_lookup, get_nearby, trust_scorer_tool, tavily_search), system prompt, MLflow-ready |
| `validator.py` | done | Second-agent cross-check via claude-3-5-haiku, adjusts trust score and appends `[Validator]` flags |

**Tools (`tools/`)**

| File | Status | Description |
|------|--------|-------------|
| `tavily_search.py` | done | `verify_hospital_with_tavily()` - 2 queries per hospital, positive/negative signal analysis, returns summary + score adjustment |
| `vector_search.py` | done | Databricks Mosaic AI Vector Search client, mock fallback for local dev |
| `db_query.py` | done | SQLAlchemy `query_hospitals()` with dynamic filters, `get_hospital_by_id()` |

**Pipelines (`pipelines/`)**

| File | Status | Description |
|------|--------|-------------|
| `ingest.py` | done | Load Excel/CSV, normalize column names, build `raw_text`, return batches for extraction |
| `embed.py` | done | `build_embedding_text()`, `generate_embeddings()` via OpenAI, `index_to_vector_search()` via Databricks SDK |

**Routers (`routers/`)**

| File | Status | Description |
|------|--------|-------------|
| `search.py` | done | `POST /api/search` (full response), `POST /api/search/stream` (SSE with 0.5s step delay) |
| `hospitals.py` | done | `GET /api/hospitals` (filtered list), `GET /api/hospitals/{id}`, `GET /api/hospitals/map/markers` |
| `dashboard.py` | done | `GET /api/dashboard/stats`, `GET /api/dashboard/deserts` |

---

#### Databricks - `databricks/`

| File | Status | Description |
|------|--------|-------------|
| `notebooks/01_ingest.py` | done | Load Excel from DBFS, normalize columns, write to `medmap.raw.hospitals` Delta table |
| `notebooks/02_extract.py` | done | Claude Sonnet batch extraction, MLflow run per record, write to `medmap.extracted.hospitals_json` |
| `notebooks/03_embed_index.py` | done | OpenAI embeddings, Mosaic AI Vector Search endpoint + index creation, upsert in 1000-record chunks |
| `notebooks/04_trust_score.py` | done | Rule engine over all records, Tavily for low-trust, write to `medmap.scored.hospital_trust`, MLflow metrics |
| `mlflow_config.py` | done | `setup_mlflow()`, `@trace_agent_step` decorator, `log_search_run()` |

---

#### Infrastructure

| File | Status | Description |
|------|--------|-------------|
| `docker-compose.yml` | done | backend + frontend + postgres:16 + redis:7, healthcheck, volumes |
| `README.md` | done | Full project overview, setup, architecture diagram, trust scoring table, demo script, evaluation mapping |

---

### Trust Scoring Rules (implemented)

| Rule ID | Trigger | Penalty |
|---------|---------|---------|
| `surgery_no_anesthesiologist` | Surgery claimed, no anesthesiologist in staff | -30 |
| `icu_no_ventilators` | ICU claimed, no ventilators | -25 |
| `emergency_no_night_staff` | 24/7 claimed, no night staff | -20 |
| `nicu_no_equipment` | NICU claimed, no incubator/equipment | -25 |
| `oncology_no_oncologist` | Oncology claimed, no oncologist | -30 |
| `nabh_no_date` | Accreditation claimed, no date | -15 |
| `cardiac_no_cath_lab` | Cardiac surgery, no cath lab | -25 |
| `dialysis_no_nephrologist` | Dialysis, no nephrologist | -20 |
| `surgery_no_ot` | Surgery, no operation theatre | -20 |
| `high_bed_count_no_icu` | 200+ beds, ICU marked false | -15 |

---

## What Is NOT Yet Done

| Item | Priority | Notes |
|------|----------|-------|
| PostgreSQL connection wired to backend | High | Schema exists, SQLAlchemy engine needs DB running |
| Real Mosaic AI Vector Search query | High | Mock in place - needs Databricks workspace + token |
| Real Claude extraction run on full 10k dataset | High | Prompt ready, needs API key + Databricks notebook run |
| Tavily live API calls | Medium | Logic ready, needs `TAVILY_API_KEY` |
| Geolocation from PIN codes | Medium | Tool stub exists (`tools/geocoder.py`), needs geocoding API |
| SSE streaming consumed by frontend | Medium | Backend SSE endpoint done, frontend uses polling mock |
| MLflow traces in UI (stretch goal) | Low | MLflow config done, trace button in HospitalCard not wired |
| Validator agent integration into search flow | Low | Agent written, not called from search router yet |
| Real map data (10k dots from DB) | Medium | `/api/hospitals/map/markers` ready, MapDashboard uses mock |

---

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| Mock-first frontend | Frontend works day 1 without any API keys - critical for parallel dev |
| `VITE_USE_MOCK=true` default | Prevents blank screen when backend not running |
| Leaflet over Mapbox | Free tier, no token needed for basic tiles |
| claude-3-5-haiku for validator | Cheaper/faster for secondary pass; sonnet for primary extraction |
| Semaphore concurrency in batch extract | Prevents Claude API rate limit hits |
| SSE for agent streaming | Real-time step display without WebSocket complexity |
| PostGIS for proximity | Future-proof for radius queries once coordinates are geocoded |
