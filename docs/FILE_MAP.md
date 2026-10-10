# MedMap - File Map

> Every file in the project, what it does, and its current status.
> Update this whenever you add, rename, or delete a file.

---

## Root

| File | Status | Purpose |
|------|--------|---------|
| `README.md` | done | Public-facing overview, setup, architecture, demo script |
| `docker-compose.yml` | done | Orchestrates backend + frontend + postgres + redis |
| `.env.example` | done | Template for all required environment variables |
| `.gitignore` | done | Excludes .env, node_modules, data files, MLflow artifacts |

---

## `frontend/`

| File | Status | Purpose |
|------|--------|---------|
| `package.json` | done | Dependencies: React 18, Vite 6, Tailwind 3, Leaflet, Recharts, Framer Motion, Lucide, Axios |
| `vite.config.js` | done | Dev server port 5173, proxy `/api` → `localhost:8000` |
| `tailwind.config.js` | done | Custom tokens: `trust.*`, `medmap.*`, `cursor-blink` animation |
| `postcss.config.js` | done | Tailwind + autoprefixer |
| `index.html` | done | Entry HTML, Google Fonts (Inter, JetBrains Mono), Leaflet CSS |
| `nginx.conf` | done | SPA fallback to `index.html`, proxy `/api/` to backend |
| `Dockerfile` | done | Node build → nginx multi-stage |

### `frontend/src/`

| File | Status | Purpose |
|------|--------|---------|
| `main.jsx` | done | React 18 `createRoot` entry point |
| `App.jsx` | done | Router, Navbar, route declarations for Home / Map / Dashboard |
| `styles/index.css` | done | Tailwind base/components/utilities, `.glass-card`, `.trust-badge-*`, Leaflet dark mode overrides |

### `frontend/src/pages/`

| File | Status | Purpose |
|------|--------|---------|
| `Home.jsx` | done | Hero section, stats row, SearchBar, example query chips, results grid (AgentPanel + HospitalCards) |
| `Map.jsx` | done | Full-screen Leaflet map, filter sidebar, hospital detail popup on marker click |
| `Dashboard.jsx` | done | Policymaker view: 4 KPI cards, trust pie, specialty gap bars, state stacked bars, desert districts table |

### `frontend/src/components/`

| File | Status | Purpose |
|------|--------|---------|
| `SearchBar.jsx` | done | Controlled input, Enter key submit, loading spinner, clear button |
| `HospitalCard.jsx` | done | Rank badge, 8-capability checklist, trust badge, expandable detail (flags + Tavily + source) |
| `TrustScoreBadge.jsx` | done | High/Medium/Low badge + score display, configurable size (sm/md/lg) |
| `AgentThinkingPanel.jsx` | done | Step-by-step streaming panel, color by step type, auto-scroll, cursor blink |
| `MapDashboard.jsx` | done | Dynamic Leaflet import, trust-colored markers, filter-reactive, click → `onSelectHospital` callback |

### `frontend/src/utils/`

| File | Status | Purpose |
|------|--------|---------|
| `api.js` | done | `searchHospitals()` with SSE streaming + mock fallback, `getHospitals()`, `getDashboardStats()` |

---

## `backend/`

| File | Status | Purpose |
|------|--------|---------|
| `main.py` | done | FastAPI app init, CORS, lifespan, router mounting, global error handler |
| `config.py` | done | Pydantic Settings from `.env` - all keys, thresholds, trust bands |
| `requirements.txt` | done | All Python dependencies with pinned versions |
| `Dockerfile` | done | Python 3.11-slim, uvicorn 2 workers |

### `backend/schemas/`

| File | Status | Purpose |
|------|--------|---------|
| `hospital.py` | done | `TrustTier`, `Capabilities`, `HospitalBase`, `HospitalExtracted`, `TrustFlag`, `HospitalTrustScore`, `HospitalResponse`, `SearchRequest`, `SearchResponse`, `AgentStep` |
| `__init__.py` | done | Re-exports all schema classes |

### `backend/agents/`

| File | Status | Purpose |
|------|--------|---------|
| `extractor.py` | done | `extract_hospital_record()` - Claude prompt → structured JSON; `batch_extract()` with semaphore |
| `trust_scorer.py` | done | `compute_trust_score()` - 10 rules, penalties, bonuses; `get_trust_tier()`; `should_trigger_tavily()` |
| `reasoner.py` | done | `build_agent()` - LangChain tool-calling agent with 5 tools; `run_search_agent()` |
| `validator.py` | done | `validate_recommendations()` - claude-3-5-haiku secondary check, score adjustment, flag appending |
| `__init__.py` | done | Re-exports all agent functions |

### `backend/tools/`

| File | Status | Purpose |
|------|--------|---------|
| `tavily_search.py` | done | `verify_hospital_with_tavily()` - 2 targeted queries, signal detection, summary + adjustment |
| `vector_search.py` | done | `semantic_search()` - Databricks Vector Search client with mock fallback |
| `db_query.py` | done | `query_hospitals()` dynamic SQL filters, `get_hospital_by_id()` |
| `__init__.py` | done | Re-exports all tool functions |

### `backend/pipelines/`

| File | Status | Purpose |
|------|--------|---------|
| `ingest.py` | done | `load_dataset()` Excel/CSV, `clean_dataframe()` normalize, `get_records_for_extraction()` batch |
| `embed.py` | done | `build_embedding_text()` rich text builder, `generate_embeddings()` OpenAI batched, `index_to_vector_search()` upsert |
| `__init__.py` | done | Re-exports pipeline functions |

### `backend/routers/`

| File | Status | Purpose |
|------|--------|---------|
| `search.py` | done | `POST /api/search`, `POST /api/search/stream` (SSE) |
| `hospitals.py` | done | `GET /api/hospitals`, `GET /api/hospitals/{id}`, `GET /api/hospitals/map/markers` |
| `dashboard.py` | done | `GET /api/dashboard/stats`, `GET /api/dashboard/deserts` |
| `__init__.py` | done | Empty init |

### `backend/migrations/`

| File | Status | Purpose |
|------|--------|---------|
| `init.sql` | done | Full `hospitals` table DDL, geospatial indexes, `hospital_map_markers` view |

---

## `databricks/`

| File | Status | Purpose |
|------|--------|---------|
| `mlflow_config.py` | done | `setup_mlflow()`, `@trace_agent_step` decorator, `log_search_run()` |

### `databricks/notebooks/`

| File | Status | Purpose |
|------|--------|---------|
| `01_ingest.py` | done | Excel → normalize → `medmap.raw.hospitals` Delta table |
| `02_extract.py` | done | Claude batch extraction with per-record MLflow runs → `medmap.extracted.hospitals_json` |
| `03_embed_index.py` | done | OpenAI embeddings → Mosaic AI Vector Search index creation + upsert |
| `04_trust_score.py` | done | Rule engine + Tavily → `medmap.scored.hospital_trust` + MLflow metrics |

---

## `docs/`

| File | Status | Purpose |
|------|--------|---------|
| `PROGRESS.md` | done | Session-by-session build log, what's done, what's pending, decisions |
| `ARCHITECTURE.md` | done | System diagram, request flow, trust scoring pipeline, DB schema, env vars |
| `FILE_MAP.md` | done | This file - complete map of every file and its role |

---

## `data/`

| File | Status | Purpose |
|------|--------|---------|
| `VF_Hackathon_Dataset_India_Large.xlsx` | pending | Place the raw dataset here (gitignored) |
