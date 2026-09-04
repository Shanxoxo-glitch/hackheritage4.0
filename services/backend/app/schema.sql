-- SIH 2026 PS 26094 Canonical DDL
CREATE TABLE IF NOT EXISTS victims (
    id VARCHAR PRIMARY KEY,
    name_encrypted VARCHAR NOT NULL,
    contact_encrypted VARCHAR NOT NULL,
    state VARCHAR NOT NULL,
    district VARCHAR NOT NULL,
    caste_category VARCHAR NOT NULL,
    preferred_language VARCHAR DEFAULT 'en',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS consent_records (
    id VARCHAR PRIMARY KEY,
    victim_id VARCHAR REFERENCES victims(id),
    data_sharing_opt_in BOOLEAN DEFAULT TRUE,
    auto_escalation_opt_in BOOLEAN DEFAULT TRUE,
    anonymized_research_opt_in BOOLEAN DEFAULT FALSE,
    safe_pause_active BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS case_files (
    id VARCHAR PRIMARY KEY,
    victim_id VARCHAR REFERENCES victims(id),
    case_number VARCHAR UNIQUE NOT NULL,
    legal_stage VARCHAR DEFAULT 'FIR',
    fir_number VARCHAR,
    police_station VARCHAR,
    poa_sections VARCHAR,
    status VARCHAR DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS interactions (
    id VARCHAR PRIMARY KEY,
    case_id VARCHAR REFERENCES case_files(id),
    channel VARCHAR NOT NULL,
    raw_content VARCHAR,
    metadata_json VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS distress_scores (
    id VARCHAR PRIMARY KEY,
    case_id VARCHAR REFERENCES case_files(id),
    composite_score FLOAT NOT NULL,
    confidence_level FLOAT NOT NULL,
    tier VARCHAR NOT NULL,
    contributing_signals_json VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alerts (
    id VARCHAR PRIMARY KEY,
    case_id VARCHAR REFERENCES case_files(id),
    tier VARCHAR NOT NULL,
    trigger_reason VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'PENDING',
    hash_checksum VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS interventions (
    id VARCHAR PRIMARY KEY,
    alert_id VARCHAR REFERENCES alerts(id),
    action_taken VARCHAR NOT NULL,
    performed_by VARCHAR NOT NULL,
    notes VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
