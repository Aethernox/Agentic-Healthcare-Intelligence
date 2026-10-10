# MedMap — Codebase Explanation & System Architecture

> **Project:** MedMap — Agentic Healthcare Intelligence System (PS-03)  
> **Team:** Pragati | Kinetics Hackathon 2026  
> **Core Dataset:** `dataset.csv` (10,000+ Indian medical facilities with deep unstructured notes)

---

## Table of Contents

1. [High-Level System Architecture](#1-high-level-system-architecture)
2. [Backend Architecture](#2-backend-architecture)
   - [Entry Point & Application Lifecycle](#21-entry-point--application-lifecycle)
   - [Database Layer](#22-database-layer)
   - [API Routers](#23-api-routers)
   - [Data Ingestion Pipeline](#24-data-ingestion-pipeline)
3. [AI / Agentic Architecture](#3-ai--agentic-architecture)
   - [Overview — 6-Stage Agentic Pipeline](#31-overview--6-stage-agentic-pipeline)
   - [Agent 1 — Clinical Intent & Triage Decomposer](#32-agent-1--clinical-intent--triage-decomposer)
   - [Agent 2 — Retrieval Agent (Facility Corpus Search)](#33-agent-2--retrieval-agent)
   - [Agent 3 — Capability Verification Engine (Phantom vs Functional)](#34-agent-3--capability-verification-engine)
   - [Agent 4 — Trust Scorer Agent (IPHS Contradiction Rules)](#35-agent-4--trust-scorer-agent)
   - [Agent 5 — Validator Agent (Medical Standards Self-Correction)](#36-agent-5--validator-agent)
   - [Agent 6 — Synthesis Agent](#37-agent-6--synthesis-agent)
   - [LLM-Powered Extractor Agent](#38-llm-powered-extractor-agent)
   - [Multi-Step Reasoning Agent (LangChain)](#39-multi-step-reasoning-agent-langchain)
4. [Frontend Architecture](#4-frontend-architecture)
   - [Application Shell & Routing](#41-application-shell--routing)
   - [Pages](#42-pages)
   - [Components](#43-components)
   - [API Layer & Mock Simulation](#44-api-layer--mock-simulation)
5. [Databricks & MLOps Layer](#5-databricks--mlops-layer)
6. [Tech Stack Summary](#6-tech-stack-summary)
7. [External Resources & Services](#7-external-resources--services)
8. [Infrastructure & Deployment](#8-infrastructure--deployment)
9. [File Map](#9-file-map)

---

## 1. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          MEDMAP SYSTEM ARCHITECTURE                             │
└─────────────────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐      HTTP/REST       ┌───────────────────────────────────────┐
  │   FRONTEND   │◄────────────────────►│              BACKEND                  │
  │  (React SPA) │       + SSE          │          (FastAPI / Python)           │
  │              │                      │                                       │
  │  Vite + JSX  │                      │  ┌──────────────────────────────────┐ │
  │  TailwindCSS │                      │  │    6-Stage Agentic Pipeline      │ │
  │  React Router│                      │  │                                  │ │
  │  Leaflet Maps│                      │  │  Triage → Retrieval → Capability │ │
  │  Recharts    │                      │  │  → Trust Score → Validator →     │ │
  │  Framer Mot. │                      │  │  Synthesis                       │ │
  │              │                      │  └──────────┬───────────────────────┘ │
  └──────────────┘                      │             │                         │
                                        │  ┌──────────▼───────────────────────┐ │
                                        │  │  SQLAlchemy ORM + SQLite/Postgres│ │
                                        │  └──────────────────────────────────┘ │
                                        └───────────────┬───────────────────────┘
                                                        │
                               ┌────────────────────────┼────────────────────────┐
                               │                        │                        │
                       ┌───────▼───────┐        ┌───────▼───────┐       ┌────────▼────────┐
                       │  Tavily API   │        │  OpenAI API   │       │  Databricks     │
                       │ (Web Verify)  │        │  (GPT-4o /    │       │  Mosaic AI      │
                       │               │        │   Embeddings) │       │  Vector Search  │
                       └───────────────┘        └───────────────┘       │  + MLflow 3     │
                                                                        └─────────────────┘
```

The system follows a **decoupled client-server** architecture with a React SPA frontend communicating with a FastAPI backend via REST and SSE (Server-Sent Events). The backend orchestrates a **6-stage autonomous agentic reasoning pipeline** that evaluates 10,000+ hospital records, cross-references Indian medical standards (IPHS 2022, NMC, PM-JAY), and surfaces verified healthcare facilities with row-level traceability from `dataset.csv`.

---

## 2. Backend Architecture

**Root Directory:** `backend/`  
**Language:** Python 3.11  
**Framework:** FastAPI with Uvicorn ASGI server

### 2.1 Entry Point & Application Lifecycle

**File:** `backend/main.py`

The FastAPI application uses a **lifespan context manager** that:

1. **Initializes the database** — calls `init_db()` to create all SQLAlchemy tables
2. **Auto-seeds on first start** — checks if the `hospitals` table is empty; if so, locates `dataset.csv` in the project root and runs the ingestion pipeline to load the first 2,500 records (for fast startup)
3. **Registers CORS middleware** — allows cross-origin requests from `localhost:5173` (Vite dev server) and `medmap.vercel.app`
4. **Mounts three API routers:**
   - `/api/search` — Agentic search pipeline
   - `/api/hospitals` — Hospital directory with filtering
   - `/api/dashboard` — Policymaker dashboard stats and crisis maps
5. **Global health check** at `GET /health` returning facility count
6. **Global exception handler** for unhandled errors

**Configuration** (`backend/config.py`): Uses `pydantic-settings` (`BaseSettings`) to load environment variables from `.env` files. Manages API keys (Anthropic, OpenAI, Tavily, Databricks), database URLs, trust scoring thresholds, CORS origins, and MLflow tracking URIs.

### 2.2 Database Layer

| Component | File | Description |
|-----------|------|-------------|
| **Engine & Session** | `backend/database.py` | SQLAlchemy `create_engine` with automatic fallback from PostgreSQL to SQLite for local dev. Provides `SessionLocal` factory and `get_db()` dependency. |
| **ORM Model** | `backend/models.py` | Single `Hospital` model with 40+ columns covering identity, geography, contact, facility details, capabilities (JSON), functional capabilities (JSON), trust scoring, citations (JSON), validator verdicts, Tavily verification, raw text, and timestamps. Includes composite indexes on `state`, `district`, `trust_score`, `trust_tier`, `pin_code`, and `(latitude, longitude)`. |
| **Pydantic Schemas** | `backend/schemas/hospital.py` | Defines `Capabilities`, `Citation`, `FunctionalCapabilityDetail`, `HospitalExtracted`, `TrustFlag`, `HospitalTrustScore`, `HospitalResponse`, `SearchRequest`, `AgentStep`, `SearchResponse`, and `TrustTier` enum. |
| **Migrations** | `backend/migrations/init.sql` | PostgreSQL schema with PostGIS extension, geospatial indexes, and a `hospital_map_markers` view for lightweight map queries. |

**Dual Database Strategy:**

- **Development:** SQLite (`medmap.db`) — zero-config, file-based
- **Production (Docker):** PostgreSQL 16 Alpine with PostGIS for spatial queries

### 2.3 API Routers

#### Search Router (`backend/routers/search.py`)

**`POST /api/search`** — The primary endpoint that executes the full agentic pipeline:

1. **Parses clinical intent** from natural language query (emergency type, procedure needed, location, budget, transport mode, time-of-day awareness)
2. **Queries the database** with state/district/trust filters
3. **Runs capability verification** — identifies phantom vs. functional facilities
4. **Executes the Validator Agent** — cross-references IPHS 2022, NMC staffing, PM-JAY eligibility
5. **Computes composite ranking** — `Trust Score - (Distance × 0.4) + Budget Bonus + Part-Time Doctor Bonus`
6. **Returns structured response** with `results`, `agent_steps` (reasoning trace), `clinical_intent`, and `validator_summary`

Also supports **SSE streaming** via `GET /api/search/stream` (in `backend/agents/search_agent.py`) for real-time agent step updates.

#### Hospitals Router (`backend/routers/hospitals.py`)

- **`GET /api/hospitals`** — Paginated, filterable hospital directory (state, district, trust tier, minimum trust score, specialty). JSON-based capability filtering done in Python.
- **`GET /api/hospitals/{id}`** — Single hospital detail with full citations, functional capabilities, and validator verdict.

#### Dashboard Router (`backend/routers/dashboard.py`)

- **`GET /api/dashboard/stats`** — Aggregate healthcare intelligence: total facilities, trust distribution (High/Medium/Low), state-level breakdowns, specialty coverage gaps (Dialysis, Oncology, Trauma, NICU, Cardiac, Neurosurgery), medical desert districts with population data.
- **`GET /api/dashboard/deserts`** — Low-trust and phantom facility coordinates for heatmap overlay.
- **`GET /api/dashboard/pin_crisis`** — Dynamic crisis map by PIN code: desert severity index (0–100), phantom ratio, verified vs. ghost facility counts, and specialized desert tags (Dialysis, Oncology, Trauma).

### 2.4 Data Ingestion Pipeline

**Files:** `backend/pipelines/ingest.py`, `backend/pipelines/embed.py`, `backend/pipelines/seed_data.py`

The ingestion pipeline (`ingest.py`) performs:

1. **CSV Parsing** — Reads `dataset.csv` with robust handling of messy fields (JSON arrays in CSV cells, malformed quotes, large field sizes)
2. **Column Normalization** — Maps varied column names (`Hospital Name` / `name`, `address_city` / `city`, etc.) to a unified schema
3. **Capability Flag Synthesis** — Text-scans across `specialties`, `procedures`, `equipment`, `capability`, and `description` fields to derive boolean capability flags (ICU, Surgery, Emergency, Dialysis, etc.)
4. **Trust Scoring** — Feeds each parsed record through the `compute_trust_score()` engine to generate trust scores, flags, functional capability maps, and row-level citations
5. **Desert Index Computation** — Heuristic-based desert severity calculation considering capability gaps, trust scores, and geographic region
6. **Geocoding** — Uses `tools/geocoder.py` with state-capital centroids + random jitter (for point spread) as primary strategy, with optional Nominatim OSM fallback
7. **Batch Database Insertion** — Writes records in configurable batch sizes (default 200) with progress logging

---

## 3. AI / Agentic Architecture

### 3.1 Overview — 6-Stage Agentic Pipeline

```
┌────────────┐    ┌────────────┐    ┌─────────────────┐    ┌──────────────┐    ┌───────────┐    ┌───────────┐
│  TRIAGE    │───►│ RETRIEVAL  │───►│  CAPABILITY     │───►│  TRUST       │───►│ VALIDATOR │───►│ SYNTHESIS │
│  AGENT     │    │ AGENT      │    │  ENGINE         │    │  SCORER      │    │ AGENT     │    │ AGENT     │
│            │    │            │    │                 │    │              │    │           │    │           │
│ Parse      │    │ DB Query   │    │ Phantom vs      │    │ 10 IPHS     │    │ IPHS 2022 │    │ Composite │
│ Clinical   │    │ 10k corpus │    │ Functional      │    │ Contradiction│    │ NMC, JAY  │    │ Ranking & │
│ Intent     │    │ filtering  │    │ Classification  │    │ Rules        │    │ Standards │    │ Advisory  │
└────────────┘    └────────────┘    └─────────────────┘    └──────────────┘    └───────────┘    └───────────┘
```

Each stage emits a structured `AgentStep` event (with `type`, `title`, `agent`, `message`, `count`) that is streamed to the frontend via SSE or returned as part of the POST response's `agent_steps` array.

### 3.2 Agent 1 — Clinical Intent & Triage Decomposer

**Implementation:** `backend/routers/search.py` → `parse_clinical_intent()`

Decomposes a natural language healthcare query into structured clinical intent:

| Field | Description | Example |
|-------|-------------|---------|
| `state` / `district` | Geographic targeting (matches against 30+ Indian states, Bihar district list) | Bihar / Saharsa |
| `is_emergency` | Whether the query indicates acute urgency | `True` for "appendectomy" |
| `urgency_level` | CRITICAL_EMERGENCY / routine | CRITICAL_EMERGENCY |
| `procedure_needed` | Specific medical procedure required | Emergency Appendectomy |
| `clinical_diagnosis_hypothesis` | AI-inferred diagnosis list | [Acute Appendicitis] |
| `required_capabilities` | Capabilities the facility must have | [surgery, emergency_24h] |
| `budget` | Patient cash constraint (₹) | 500 |
| `transport_mode` | Transport type (affects radius) | two-wheeler (≤25 km) |
| `max_radius_km` | Maximum safe travel distance | 25.0 |
| `allows_part_time_doctors` | Whether visiting/on-call doctors are acceptable | True/False |
| `day_time_shift` | Time-of-day awareness (Tuesday 2:30 PM) | afternoon_shift |

### 3.3 Agent 2 — Retrieval Agent

**Implementation:** `backend/routers/search.py` → SQLAlchemy queries

Scans the 10,000+ facility database with:

- State and district filtering (case-insensitive `ILIKE`)
- Trust score minimum thresholds
- Retrieves up to 200 candidate facilities per search

Optional **semantic search** via Databricks Mosaic AI Vector Search (`backend/tools/vector_search.py`) for query-text embedding similarity.

### 3.4 Agent 3 — Capability Verification Engine

**Implementation:** `backend/agents/trust_scorer.py` → `verify_functional_capabilities()`

This is the core differentiator. For each claimed capability, the engine evaluates whether it is **functionally real** or a **phantom claim**:

| Capability | Verification Logic | Status Values |
|------------|-------------------|---------------|
| **ICU** | Checks ventilator count > 0 AND (intensivist in staff OR ≥3 doctors) | `VERIFIED_FUNCTIONAL` / `PHANTOM_CLAIM` |
| **Surgery** | Checks (OT equipment OR surgeon) AND (anesthesiologist OR on-call notation) | `VERIFIED_FUNCTIONAL` / `CONDITIONAL_CAPABILITY` / `PHANTOM_CLAIM` |
| **Emergency 24h** | Checks emergency staff/CMO AND not outpatient-only AND has beds | `VERIFIED_FUNCTIONAL` / `PHANTOM_CLAIM` |
| **Dialysis** | Checks dialysis machines AND nephrologist/tech | `VERIFIED_FUNCTIONAL` / `PHANTOM_CLAIM` |
| **Oncology** | Checks oncologist AND chemo/radiation facilities | `VERIFIED_FUNCTIONAL` / `PHANTOM_CLAIM` |

Each verification produces:
- **Status:** `VERIFIED_FUNCTIONAL` / `CONDITIONAL_CAPABILITY` / `PHANTOM_CLAIM` / `NOT_AVAILABLE`
- **Confidence:** 0.0 – 1.0
- **Evidence:** Human-readable explanation
- **Missing Requirements:** List of what's absent
- **Row-level Citation:** `dataset_row_num`, source field, exact quote, contradiction flag

### 3.5 Agent 4 — Trust Scorer Agent

**Implementation:** `backend/agents/trust_scorer.py` → `compute_trust_score()`

Every facility starts at a **base score of 100** and is subjected to **10 automated IPHS contradiction checks**:

| # | Rule ID | Penalty | Medical Standard |
|---|---------|---------|-----------------|
| 1 | `surgery_no_anesthesiologist` | **-30** | NMC Standards & IPHS 2022 §4.2 |
| 2 | `icu_no_ventilators` | **-25** | IPHS 2022 ICU Standards |
| 3 | `emergency_no_resident_doctor` | **-20** | IPHS 2022 Casualty Standards |
| 4 | `cosmetic_dental_claiming_hospital_icu` | **-35** | Clinical Establishment Act |
| 5 | `dialysis_no_nephrologist_or_machine` | **-25** | PMNDP Guidelines |
| 6 | `oncology_no_oncologist` | **-30** | NCG Standards |
| 7 | `cardiac_no_cath_lab` | **-25** | IPHS Tertiary Benchmarks |
| 8 | `high_capacity_low_doctor` | **-20** | NMC Staff-to-Bed Ratio |
| 9 | `stale_survey_penalty` | **-15** | Recency Protocol |
| 10 | `nabh_no_date` | **-15** | NABH Registry |

**Bonuses:**
- `+10` for PM-JAY / Government empanelled
- `+5` for verified operation theatre + surgeon
- `+5` for accreditation with valid date

**Trust Tiers:** High (≥75), Medium (≥40), Low (<40)

**Tavily Trigger:** Facilities scoring below threshold (default 50) are flagged for web verification.

### 3.6 Agent 5 — Validator Agent

**Implementation:** `backend/agents/validator.py` → `validate_facility_against_standards()`

A **self-correction layer** that cross-references the top candidates against clinical standards:

1. **NMC Staff-to-Bed Ratio** — Flags if doctor-to-bed ratio exceeds 1:25 (NMC recommends 1:10)
2. **IPHS 2022 §4.2 Surgical Readiness** — Validates surgeon availability, anesthesiologist coverage (including part-time/visiting doctor allowances per IPHS CHC guidelines)
3. **24/7 Casualty & Night Roster** — Cross-checks functional emergency status against phantom claims
4. **PM-JAY Financial Feasibility** — Validates if the patient's budget (e.g., ₹500) is feasible given facility type (Government/PM-JAY = covered; Private = warning)
5. **Distance & Transport Feasibility** — Calculates two-wheeler travel time on rural roads (~25 km/h)

**Output:** Verdict (`PASSED` / `PASSED_WITH_CONDITIONS` / `FAILED_STANDARDS`), confidence adjustment (-30 to +15), issues list, advisories list, and standards referenced.

### 3.7 Agent 6 — Synthesis Agent

**Implementation:** End of `backend/routers/search.py` and `backend/agents/search_agent.py`

Computes the final **composite ranking score**:

```
Ranking = Trust Score - (Distance_km × 0.4) + Budget Bonus + Part-Time Doctor Bonus
```

- **Budget Bonus:** +20 if budget ≤ ₹1000 and facility is Government/PM-JAY
- **Part-Time Doctor Bonus:** +15 if query requested visiting doctors and facility uses on-call staff

Returns the top N results sorted by composite rank with patient advisories.

### 3.8 LLM-Powered Extractor Agent

**Implementation:** `backend/agents/extractor.py`

Uses **OpenAI GPT-4o** with structured JSON output to extract structured hospital records from raw unstructured text. Features:

- Extraction prompt with 12 capability fields, confidence scoring, and strict JSON-only output
- Batch extraction with semaphore-based concurrency control (5 parallel requests)
- Fallback to empty structure on failure

### 3.9 Multi-Step Reasoning Agent (LangChain)

**Implementation:** `backend/agents/reasoner.py`

A **LangChain `AgentExecutor`** with GPT-4o backbone and custom tools:

| Tool | Purpose |
|------|---------|
| `vector_search` | Semantic search over hospital vector index |
| `structured_lookup` | Filter by state, specialty, beds, ICU, emergency |
| `get_nearby` | Proximity search within radius of coordinates |
| `trust_scorer_tool` | Detailed trust score breakdown for a facility |
| `tavily_search` | Web verification via Tavily API |

Uses `ChatPromptTemplate` with system prompt defining the agent's healthcare intelligence persona. Supports up to 10 reasoning iterations with intermediate step logging.

---

## 4. Frontend Architecture

**Root Directory:** `frontend/`  
**Framework:** React 18 with Vite  
**Styling:** TailwindCSS 3.4 with custom `medmap` and `trust` color palettes

### 4.1 Application Shell & Routing

**File:** `frontend/src/App.jsx`

Uses `react-router-dom` v6 with three routes:

| Route | Page Component | Description |
|-------|----------------|-------------|
| `/` | `Home` | Search interface with Ananya scenario hero card |
| `/map` | `Map` | Interactive geospatial crisis map |
| `/dashboard` | `Dashboard` | Policymaker analytics view |

Navigation bar includes:
- MedMap logo with custom `medmap-600` brand color
- "PS-03 Intelligence Engine" status badge with pulse animation
- "10k Dataset" indicator and system online status dot

### 4.2 Pages

#### Home Page (`frontend/src/pages/Home.jsx`)

- **Ananya's Emergency Hero Card** — "Meet Ananya's Real Scenario" with a pre-configured test button
- **Search Bar** — Natural language input that triggers the agentic pipeline
- **Agent Thinking Panel** — Real-time streaming display of the 6-stage reasoning chain
- **Hospital Result Cards** — Trust-scored facility cards with citations, capabilities, and validator verdicts

#### Map Page (`frontend/src/pages/Map.jsx`)

- **Interactive Leaflet Map** — India-wide geospatial view centered on the Gangetic Plain
- **Trust-Colored Markers** — Green (High), Amber (Medium), Red (Low) with tooltips showing dataset row numbers
- **Dynamic Crisis Zones** — Dashed circle overlays for Critical/Severe medical deserts by PIN code
- **Filter Controls** — Trust tier, specialty, desert type (Dialysis/Oncology/Trauma), PIN code search

#### Dashboard Page (`frontend/src/pages/Dashboard.jsx`)

- **National Statistics** — Total facilities, medical deserts count, population at risk, phantom clinics
- **Trust Distribution** — Pie/donut chart (High/Medium/Low)
- **State-Level Breakdown** — Bar chart of facility counts by state and trust tier
- **Specialty Coverage Gaps** — Horizontal bar chart showing covered vs. uncovered percentages
- **Desert Districts Table** — Most underserved districts with population, facility count, and gap severity

### 4.3 Components

| Component | File | Purpose |
|-----------|------|---------|
| **AgentThinkingPanel** | `components/AgentThinkingPanel.jsx` | Animated reasoning trace with step-specific icons and color-coded styles (Framer Motion `AnimatePresence`) |
| **HospitalCard** | `components/HospitalCard.jsx` | Rich facility card showing trust score, capabilities, citations, functional verification status, validator verdict |
| **MapDashboard** | `components/MapDashboard.jsx` | Leaflet map wrapper with marker rendering, crisis zone overlays, and dynamic data fetching |
| **SearchBar** | `components/SearchBar.jsx` | Search input with styling |
| **TrustScoreBadge** | `components/TrustScoreBadge.jsx` | Color-coded trust tier badge |

### 4.4 API Layer & Mock Simulation

**File:** `frontend/src/utils/api.js`

Provides a **dual-mode API layer**:

1. **Live Mode** — Axios client hitting `VITE_API_URL` (default: `http://localhost:8000/api`)
2. **Mock Mode** (`VITE_USE_MOCK=true`) — Full offline simulation including:
   - **Ananya Scenario Dataset** — 4 realistic hospital records (Arogya Mandir, Aadarsh Balaji, Vaishali MediCare phantom clinic, AIIMS Patna) with complete trust scores, functional capabilities, citations, and validator verdicts
   - **Simulated Agent Steps** — Timed delay sequence mimicking the 6-stage reasoning chain
   - **Crisis PIN Data** — 7 pre-defined crisis zone PIN codes for Bihar, UP, and Rajasthan

API functions: `searchHospitals()`, `getHospitals()`, `getHospital()`, `getDashboardStats()`, `getCrisisMapPins()`

**Vite Dev Proxy:** API requests to `/api` are proxied to `http://localhost:8000` during development.

---

## 5. Databricks & MLOps Layer

**Root Directory:** `databricks/`

### Notebooks (4-Stage Pipeline)

| Notebook | Stage | Description |
|----------|-------|-------------|
| `01_ingest.py` | Data Ingestion | Loads raw Excel/CSV into Unity Catalog Delta table (`medmap.raw.hospitals`) via PySpark |
| `02_extract.py` | LLM Extraction | Batch-processes raw records through GPT-4o structured extraction |
| `03_embed_index.py` | Embedding & Indexing | Generates `text-embedding-3-small` vectors and indexes into Mosaic AI Vector Search (`medmap.hospitals.embeddings`) with 1536-dimension embeddings |
| `04_trust_score.py` | Trust Scoring | Runs the 10-rule IPHS contradiction engine on all records at scale |

### MLflow 3 Configuration (`databricks/mlflow_config.py`)

- **Experiment Tracking** — All agent runs logged under `/medmap/agent-runs`
- **`@trace_agent_step` Decorator** — Wraps individual agent functions with automatic MLflow span logging (inputs, outputs, duration, errors)
- **Search Run Logging** — Tracks queries, result counts, trust distributions, and Tavily trigger rates

### Mosaic AI Vector Search

- **Endpoint:** `medmap-endpoint`
- **Index:** `medmap.hospitals.embeddings`
- **Schema:** id, name, city, state, pin_code, trust_score, raw_text, embedding (1536-dim float array)
- **Access:** Via `databricks-vector-search` SDK client with token authentication

---

## 6. Tech Stack Summary

### Backend

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **Framework** | FastAPI | ≥0.115 | Async REST API with automatic OpenAPI docs |
| **ASGI Server** | Uvicorn | ≥0.32 | High-performance Python web server |
| **Validation** | Pydantic v2 | ≥2.10 | Data models and request/response schemas |
| **Configuration** | Pydantic Settings | ≥2.6 | Type-safe environment variable loading |
| **ORM** | SQLAlchemy | ≥2.0.30 | Database abstraction with mapped columns |
| **Migration** | Alembic | ≥1.14 | Schema versioning and migration management |
| **Database (Dev)** | SQLite + aiosqlite | ≥0.20 | Zero-config local development database |
| **Database (Prod)** | PostgreSQL 16 | Alpine | Production-grade RDBMS with PostGIS |
| **Cache** | Redis 7 | Alpine | Response caching and session management |
| **AI / LLM** | LangChain | ≥0.3 | Agent orchestration, tool calling, prompt templates |
| **AI / LLM** | LangChain-OpenAI | ≥0.2 | GPT-4o integration for reasoning agent |
| **AI / LLM** | OpenAI SDK | ≥1.50 | Direct GPT-4o API calls for extraction + embeddings |
| **Web Search** | Tavily Python | ≥0.5 | Real-time web verification of hospital claims |
| **Data Processing** | Pandas | ≥2.2 | CSV parsing and data transformation |
| **Data Processing** | NumPy | ≥2.0 | Numerical operations for embeddings |
| **Data Processing** | OpenPyXL | ≥3.1 | Excel file reading for dataset ingestion |
| **HTTP Client** | HTTPX | ≥0.28 | Async HTTP for Nominatim geocoding |
| **Env Management** | python-dotenv | ≥1.0 | `.env` file loading |

### Frontend

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **UI Framework** | React | 18.3 | Component-based SPA development |
| **Build Tool** | Vite | 6.0 | Lightning-fast HMR and optimized builds |
| **Routing** | React Router DOM | 6.28 | Client-side navigation with NavLink |
| **CSS Framework** | TailwindCSS | 3.4 | Utility-first styling with custom theme |
| **Animations** | Framer Motion | 11.13 | Physics-based animations (AnimatePresence) |
| **Charts** | Recharts | 2.13 | Dashboard data visualization (bar, pie charts) |
| **Maps** | Leaflet | 1.9.4 | Interactive geospatial mapping |
| **Maps (React)** | React-Leaflet | 4.2.1 | React bindings for Leaflet |
| **Icons** | Lucide React | 0.462 | 1000+ SVG icons for UI elements |
| **HTTP Client** | Axios | 1.7.9 | Backend API communication |
| **Utilities** | clsx | 2.1 | Conditional CSS class merging |
| **PostCSS** | PostCSS + Autoprefixer | 8.4 / 10.4 | CSS post-processing pipeline |
| **Typography** | Inter (Google Fonts) | — | Primary sans-serif typeface |
| **Typography** | JetBrains Mono | — | Monospace typeface for data displays |

### Databricks / Cloud

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Compute** | Databricks Workspace | Notebook execution for batch pipelines |
| **Storage** | Unity Catalog (Delta) | Managed lakehouse tables for raw + processed data |
| **Vector DB** | Mosaic AI Vector Search | Semantic similarity search over hospital embeddings |
| **MLOps** | MLflow 3 | Experiment tracking, agent tracing, model registry |
| **Spark** | PySpark | Distributed data processing for 10k+ records |

---

## 7. External Resources & Services

### AI / LLM APIs

| Service | Usage in Codebase | Files |
|---------|-------------------|-------|
| **OpenAI GPT-4o** | Structured data extraction from unstructured hospital records; Multi-step reasoning agent backbone | `agents/extractor.py`, `agents/reasoner.py` |
| **OpenAI text-embedding-3-small** | 1536-dimensional embeddings for semantic search over hospital corpus | `pipelines/embed.py`, `databricks/notebooks/03_embed_index.py` |
| **Tavily Search API** | Real-time web verification of hospital claims — searches for accreditation, operational status, and public complaints | `tools/tavily_tool.py`, `tools/tavily_search.py` |
| **Anthropic Claude** | API key configured in settings (alternative LLM provider) | `config.py`, `.env.example` |

### Geospatial & Mapping

| Service | Usage | Files |
|---------|-------|-------|
| **OpenStreetMap Tile Server** | Map tile layer for Leaflet (`https://{s}.tile.openstreetmap.org`) | `components/MapDashboard.jsx` |
| **Nominatim OSM Geocoder** | Fallback PIN code → lat/lng geocoding for unknown locations | `tools/geocoder.py` |
| **Survey of India PIN Dataset** | State capital centroids covering ~30,000 Indian PIN codes (bundled in-memory) | `tools/geocoder.py` |

### Medical Standards & Regulatory References (Grounding Sources)

| Standard | How It's Used |
|----------|---------------|
| **IPHS 2022** (Indian Public Health Standards) | §4.2 Surgical Safety, ICU Standards, Casualty & Emergency norms — used as contradiction rule anchors |
| **NMC Staffing Norms** | National Medical Commission doctor-to-bed ratio mandates (1:10 minimum) — validator agent |
| **Ayushman Bharat PM-JAY** | Financial feasibility check for low-budget patients — cashless package validation |
| **Clinical Establishment Act 2010** | Equipment minimum standards for emergency centers — phantom facility detection |
| **NABH/NABL Accreditation** | National accreditation board verification with date validation |
| **NCG India Standards** | National Cancer Grid guidelines for oncology facility verification |
| **PMNDP Guidelines** | Pradhan Mantri National Dialysis Programme — dialysis facility standards |

### Data Sources

| Source | Description | File |
|--------|-------------|------|
| **`dataset.csv`** | 10,000+ Indian medical facilities with 30+ columns (name, location, specialties, equipment, procedures, capabilities, descriptions — including deep unstructured text notes) | Root directory, ~10 MB |
| **`data/seed_hospitals.json`** | Pre-processed seed data with 198 KB of curated hospital records | `data/` directory |

---

## 8. Infrastructure & Deployment

### Docker Compose Architecture

**File:** `docker-compose.yml` — 4 containerized services:

```yaml
services:
  backend:    # Python 3.11-slim, FastAPI + Uvicorn (port 8000)
  frontend:   # Node 20 Alpine build → Nginx Alpine (port 80 → mapped 5173)
  postgres:   # PostgreSQL 16 Alpine with health checks
  redis:      # Redis 7 Alpine with AOF persistence
```

### Backend Dockerfile (`backend/Dockerfile`)

- Base: `python:3.11-slim`
- Installs `gcc` + `libpq-dev` for PostgreSQL driver compilation
- Runs Uvicorn with 2 workers on port 8000

### Frontend Dockerfile (`frontend/Dockerfile`)

- **Multi-stage build:** Node 20 Alpine for `npm ci` + `vite build`, then Nginx Alpine for serving static assets
- Custom `nginx.conf` for SPA routing and API reverse proxy

### Environment Variables (`.env.example`)

| Category | Variables |
|----------|-----------|
| AI/LLM | `ANTHROPIC_API_KEY`, `TAVILY_API_KEY` |
| Databricks | `DATABRICKS_HOST`, `DATABRICKS_TOKEN`, `VECTOR_SEARCH_ENDPOINT`, `VECTOR_SEARCH_INDEX` |
| Database | `DATABASE_URL` (PostgreSQL), `REDIS_URL` |
| MLflow | `MLFLOW_TRACKING_URI`, `MLFLOW_EXPERIMENT_NAME` |
| App | `ENVIRONMENT`, `LOG_LEVEL` |
| Frontend | `VITE_API_URL`, `VITE_USE_MOCK` |

---

## 9. File Map

```
Agentic-Healthcare-Intelligence/
├── .env.example                    # Environment variable template
├── .gitignore                      # Git ignore rules
├── README.md                       # Project overview and quick start
├── dataset.csv                     # 10k Indian medical facility dataset (~10 MB)
├── docker-compose.yml              # 4-service Docker orchestration
├── explanation.md                  # ← This file
│
├── backend/
│   ├── Dockerfile                  # Python 3.11 production image
│   ├── main.py                     # FastAPI entry point + lifespan auto-seed
│   ├── config.py                   # Pydantic Settings configuration
│   ├── database.py                 # SQLAlchemy engine, session, Base
│   ├── models.py                   # Hospital ORM model (40+ columns)
│   ├── requirements.txt            # Python dependencies
│   ├── medmap.db                   # SQLite database (dev)
│   │
│   ├── agents/
│   │   ├── __init__.py             # Lazy imports for optional dependencies
│   │   ├── extractor.py            # GPT-4o structured data extraction
│   │   ├── reasoner.py             # LangChain multi-step reasoning agent
│   │   ├── search_agent.py         # SSE streaming agentic search pipeline
│   │   ├── trust_scorer.py         # 10-rule IPHS contradiction engine + capability verification
│   │   └── validator.py            # Medical standards cross-referencing & self-correction
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── search.py               # POST /api/search — full agentic pipeline
│   │   ├── hospitals.py            # GET /api/hospitals — directory & detail
│   │   └── dashboard.py            # GET /api/dashboard/* — stats, deserts, crisis map
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── hospital.py             # Pydantic models (17 schema classes)
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── db_query.py             # Database query utilities
│   │   ├── geocoder.py             # PIN → lat/lng with Nominatim fallback
│   │   ├── seed_db.py              # Database seeding utilities
│   │   ├── tavily_search.py        # Tavily search wrapper
│   │   ├── tavily_tool.py          # Web verification with heuristic scoring
│   │   └── vector_search.py        # Mosaic AI Vector Search client
│   │
│   ├── pipelines/
│   │   ├── __init__.py
│   │   ├── ingest.py               # CSV → DB ingestion with trust scoring
│   │   ├── embed.py                # OpenAI embedding generation + vector indexing
│   │   └── seed_data.py            # Seed data generation pipeline
│   │
│   └── migrations/
│       └── init.sql                # PostgreSQL schema with PostGIS
│
├── frontend/
│   ├── Dockerfile                  # Multi-stage Node → Nginx build
│   ├── index.html                  # SPA entry HTML
│   ├── nginx.conf                  # Nginx reverse proxy configuration
│   ├── package.json                # NPM dependencies
│   ├── vite.config.js              # Vite dev server + API proxy
│   ├── tailwind.config.js          # Custom theme (medmap, trust colors)
│   ├── postcss.config.js           # PostCSS pipeline
│   │
│   └── src/
│       ├── main.jsx                # React DOM render entry point
│       ├── App.jsx                 # Router + Navbar shell
│       │
│       ├── pages/
│       │   ├── Home.jsx            # Search UI + Ananya scenario demo
│       │   ├── Map.jsx             # Interactive Leaflet crisis map
│       │   └── Dashboard.jsx       # Policymaker analytics dashboard
│       │
│       ├── components/
│       │   ├── AgentThinkingPanel.jsx  # Animated reasoning trace display
│       │   ├── HospitalCard.jsx        # Trust-scored facility result card
│       │   ├── MapDashboard.jsx        # Leaflet map with markers + desert zones
│       │   ├── SearchBar.jsx           # Search input component
│       │   └── TrustScoreBadge.jsx     # Color-coded trust tier badge
│       │
│       ├── utils/
│       │   └── api.js              # Axios client + mock simulation layer
│       │
│       └── styles/
│           └── index.css           # Global CSS + Tailwind base
│
├── databricks/
│   ├── mlflow_config.py            # MLflow 3 experiment setup + decorators
│   └── notebooks/
│       ├── 01_ingest.py            # PySpark data ingestion to Unity Catalog
│       ├── 02_extract.py           # Batch LLM extraction
│       ├── 03_embed_index.py       # Embedding + Mosaic AI Vector Search indexing
│       └── 04_trust_score.py       # Batch trust scoring at scale
│
├── data/
│   └── seed_hospitals.json         # Pre-processed seed hospital data
│
└── docs/
    ├── ARCHITECTURE.md             # Architecture documentation
    ├── FILE_MAP.md                 # File map documentation
    └── PROGRESS.md                 # Development progress tracker
```

---

> **Built by Team Pragati — Kinetics Hackathon 2026**
