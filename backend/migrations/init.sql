-- MedMap PostgreSQL Schema
-- Run once on first startup (handled by Docker entrypoint)

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS hospitals (
    id              SERIAL PRIMARY KEY,
    record_id       INTEGER UNIQUE,
    name            TEXT NOT NULL,
    city            TEXT,
    district        TEXT,
    state           TEXT,
    pin_code        VARCHAR(6),
    latitude        DOUBLE PRECISION,
    longitude       DOUBLE PRECISION,

    -- Structured extraction
    bed_count       INTEGER,
    icu_beds        INTEGER,
    ventilator_count INTEGER,
    staff_specialties TEXT[],
    equipment_list  TEXT[],
    accreditation   TEXT,
    accreditation_date TEXT,

    -- Capabilities (extracted)
    cap_icu         BOOLEAN,
    cap_surgery     BOOLEAN,
    cap_emergency_24h BOOLEAN,
    cap_dialysis    BOOLEAN,
    cap_nicu        BOOLEAN,
    cap_oncology    BOOLEAN,
    cap_trauma      BOOLEAN,
    cap_blood_bank  BOOLEAN,
    cap_cardiac_surgery BOOLEAN,
    cap_neurosurgery BOOLEAN,

    -- Trust scoring
    trust_score     INTEGER DEFAULT 0,
    trust_tier      TEXT CHECK (trust_tier IN ('high', 'medium', 'low')),
    trust_flags     TEXT[],

    -- Tavily verification
    tavily_verified BOOLEAN DEFAULT FALSE,
    tavily_summary  TEXT,
    tavily_score_adjustment INTEGER DEFAULT 0,

    -- Raw data
    raw_text        TEXT,
    extraction_source TEXT,
    extraction_confidence DOUBLE PRECISION,

    -- Metadata
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- Geospatial index for proximity search
CREATE INDEX IF NOT EXISTS idx_hospitals_location
    ON hospitals (latitude, longitude)
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- Index for common filter patterns
CREATE INDEX IF NOT EXISTS idx_hospitals_state ON hospitals (state);
CREATE INDEX IF NOT EXISTS idx_hospitals_district ON hospitals (district);
CREATE INDEX IF NOT EXISTS idx_hospitals_trust ON hospitals (trust_score DESC);
CREATE INDEX IF NOT EXISTS idx_hospitals_pin ON hospitals (pin_code);

-- View for map markers (lightweight)
CREATE OR REPLACE VIEW hospital_map_markers AS
SELECT id, name, city, state, latitude, longitude,
       trust_score, trust_tier, cap_icu, cap_surgery, cap_emergency_24h
FROM hospitals
WHERE latitude IS NOT NULL AND longitude IS NOT NULL;
