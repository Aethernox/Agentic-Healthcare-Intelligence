# MedMap — Agentic Healthcare Intelligence System (PS-03)

> **Track:** Healthcare Intelligence  
> **Problem Statement PS-03:** "The Right Care is the Care You Can Actually Find"  
> **Built for:** Kinetics Hackathon (Team Pragati)  
> **Core Dataset:** `dataset.csv` (10,000+ medical facilities across India with deep unstructured notes)

---

## 📖 Executive Summary & Ananya's Scenario

### The Crisis
> **Meet Ananya:** 34 years old, semi-rural district in Bihar. It is **Tuesday, 2:30 PM**. Her father is suffering from acute, severe abdominal pain (suspected appendicitis).
> - **Transport:** Two-wheeler (restricted safe emergency travel radius ~30-40 km).
> - **Budget:** ₹500 cash in hand (requires Ayushman Bharat PM-JAY empaneled or subsidised public care).
> - **The Trap:** The nearest advertised hospital (15 km away) claims an "ICU" and "Emergency Surgery" on Google Maps, but real inspection logs reveal an unplugged oxygen concentrator and zero doctors on duty. Meanwhile, 20 km away lies a functional clinic with a resident physician and an equipped OT, hidden under an unstructured 2022 text dump.

### The Solution: MedMap Agentic Intelligence
MedMap replaces static directories with an **autonomous 6-stage clinical reasoning and verification architecture** that evaluates unstructured hospital logs, exposes phantom claims, cross-references national medical standards, cites exact dataset rows, and plots dynamic PIN code crisis maps.

---

## 🏛️ The Three Pillars of PS-03

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 MEDMAP AGENTIC ARCHITECTURE (PS-03)                              │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                 │
                   ┌─────────────────────────────┼─────────────────────────────┐
                   ▼                             ▼                             ▼
         [PILLAR 1: DECIDE & EXTRACT]   [PILLAR 2: REASON & SCORE]   [PILLAR 3: CLOSE THE LOOP]
                   │                             │                             │
    • Ingestion of 10,000+ rows    • Clinical Intent Parser     • Row-Level Dataset Citations
      from dataset.csv               (Triage hypothesis,          (dataset_row_num, source col,
    • Deep Unstructured Analysis     transport, budget)           unstructured proof quote)
      (OT logs, oxygen status,     • Multi-Attribute Candidate   • Self-Correcting Validator
      part-time/visiting docs)       Scoring (Distance × Trust)   (IPHS 2022 §4.2, NMC Ratios,
    • Functional vs Phantom        • 10 IPHS Contradiction        PM-JAY Financial Feasibility)
      Capability Classification      Rules Engine (-35 to +10)  • Dynamic PIN Crisis Maps
    • Specialized Desert Indices   • Tuesday 2:30 PM Time-        (Severity heatmaps for
      (Dialysis, Oncology, Trauma)   Aware Roster Analysis        Dialysis, Oncology, Trauma)
```

---

### Pillar 1: Decide & Extract (Functional vs. Phantom Capabilities)
- **Deep Log Parsing:** Sifts through messy text in `dataset.csv` fields (`description`, `capability`, `equipment`, `procedure`, `specialties`).
- **Phantom ICU / OT Detection:** Flags facilities that advertise advanced surgery or ICU but have disconnected equipment, zero ventilators, or outpatient-only infrastructure.
- **Specialized Desert Identification:** Computes PIN-code-level deficit indices for:
  - **Oncology Deserts:** Zero oncologists or chemo infusion units within 50 km.
  - **Dialysis Deserts:** Absence of operational hemodialysis machines.
  - **Trauma Deserts:** Absence of blood bank or 24/7 general surgeon.

---

### Pillar 2: Reason & Score (10 IPHS Contradiction Rules)
Every candidate hospital begins at a base score of 80 and is subjected to 10 automated contradiction checks:

| # | Contradiction Rule | Clinical Standard | Penalty |
|---|-------------------|-------------------|---------|
| 1 | **Surgery without Anesthesiologist** | IPHS 2022 §4.2 Surgical Safety | **-30** |
| 2 | **ICU without Ventilators or Monitors** | Phantom ICU Rule | **-25** |
| 3 | **Neonatal Care without NICU Equipment** | IPHS SNCU / NICU Protocol | **-25** |
| 4 | **Oncology without Oncologist** | NCG India Chemotherapy Standards | **-30** |
| 5 | **Cardiac Surgery without Cath Lab / Perfusion** | National Interventional Cardiology | **-25** |
| 6 | **Emergency 24/7 without Night Roster** | IPHS Casualty Shift Norms | **-20** |
| 7 | **Dialysis without Nephrologist / Trained Tech** | PMNDP Dialysis Protocol | **-20** |
| 8 | **Major Surgery without Operation Theatre** | Clinical Establishment Act | **-20** |
| 9 | **Outpatient / Dental Clinic Claiming Hospital ICU** | Severe Facility Type Mismatch | **-35** |
| 10 | **200+ Beds with 0 Doctors or Phantom Capacity** | Ghost Bed Ratio Rule | **-25** |

*Bonuses:* `+5` for verified government accreditation with date; `+5` for verified functional operating theatre.

---

### Pillar 3: Close the Loop (Traceability & Self-Correction)
1. **Row-Level Citations:** Every recommendation cites the exact `dataset_row_num` in `dataset.csv`, referencing the exact column (`description`, `capability`, `equipment`, `procedure`) and extracting the raw unedited quote.
2. **Validator Agent (Self-Correction Layer):**
   - Cross-references the top candidate against **IPHS 2022 Community Health Centre (CHC) §4.2 guidelines** (allowing visiting/contracted surgeons for acute daytime appendectomies).
   - Validates **NMC Staffing Ratios** and **Ayushman Bharat PM-JAY** package compatibility for Ananya's ₹500 budget.
   - Adjusts the candidate trust score (e.g., `+10` bonus for verified daytime surgeon availability).
3. **Dynamic PIN Code Crisis Maps:**
   - Real-time geospatial crisis heatmaps across rural and semi-rural PIN codes (e.g., Bihar `852201`, `844121`, `854301`, `800001`).
   - Identifies high-risk medical deserts with live metric counters.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ & npm

### 2. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server (Auto-seeds from dataset.csv on startup)
python -m uvicorn main:app --reload --port 8000
```
- API Documentation: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
- Open browser: `http://localhost:5173`

*(Note: If running without backend, the frontend defaults to `VITE_USE_MOCK=true` with the full Ananya persona, dataset facilities, and interactive crisis maps.)*

---

## 🎯 Testing Ananya's Scenario (1-Click Demo)

1. Open `http://localhost:5173`.
2. Look at the hero card: **"Meet Ananya's Real Scenario (PS-03)"**.
3. Click the **"Test Ananya's Emergency Search"** button.
4. Watch the **Agent Thinking Panel** stream through:
   - **Triage Agent:** Acute abdominal pain → Emergency Appendectomy suspected, ₹500 budget filter, 35 km two-wheeler radius.
   - **Retrieval Agent:** Fetches candidates from `dataset.csv` in rural/semi-rural Bihar.
   - **Capability Engine:** Disqualifies phantom facilities (unplugged concentrator, zero doctors).
   - **Trust Scorer:** Flags IPHS contradictions on suspicious clinics.
   - **Validator Agent:** Certifies Arogya Mandir Saharsa (Row #1001) under IPHS 2022 §4.2 daytime visiting surgeon norms.
   - **Synthesis Agent:** Delivers verified recommendation with row citation and direct phone call link.

---

## 📡 API Endpoints Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/search` | Full agentic search pipeline with triage, trust scoring, and validator self-correction |
| `GET` | `/api/search/stream` | Server-Sent Events (SSE) streaming reasoning steps to the frontend |
| `GET` | `/api/hospitals` | Filtered hospital database with row citations and functional capabilities |
| `GET` | `/api/dashboard/stats` | National/state healthcare intelligence statistics and contradiction frequencies |
| `GET` | `/api/dashboard/pin_crisis` | Dynamic crisis map points by PIN code with specialized desert tags |

---

## 🛡️ Medical Standards & Grounding
- **IPHS 2022:** Indian Public Health Standards for Sub-Centres, PHCs, CHCs, and District Hospitals.
- **NMC Staffing Norms:** National Medical Commission regulations for clinical establishment doctor-to-bed ratios.
- **PM-JAY Scheme:** Ayushman Bharat Pradhan Mantri Jan Arogya Yojana emergency package rules.
- **Clinical Establishment Act 2010:** Equipment minimum standards for emergency care centers.

---

**Team Pragati | Kinetics Hackathon 2026**
