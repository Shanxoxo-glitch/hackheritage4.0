-- Canonical PostgreSQL DDL generated directly from Base.metadata

CREATE TABLE dispatch_logs (
	id VARCHAR(36) NOT NULL, 
	case_id VARCHAR(36) NOT NULL, 
	tier VARCHAR(20) NOT NULL, 
	action VARCHAR(100) NOT NULL, 
	dispatched_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id)
);

CREATE TABLE victims (
	id VARCHAR(36) NOT NULL, 
	name_encrypted TEXT NOT NULL, 
	contact_encrypted TEXT NOT NULL, 
	email_encrypted TEXT, 
	vulnerability_category VARCHAR(50) NOT NULL, 
	preferred_language VARCHAR(10) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id)
);

CREATE TABLE case_files (
	id VARCHAR(36) NOT NULL, 
	victim_id VARCHAR(36) NOT NULL, 
	fir_number VARCHAR(100) NOT NULL, 
	act_section VARCHAR(100) NOT NULL, 
	case_stage VARCHAR(50) NOT NULL, 
	registered_on DATE NOT NULL, 
	next_hearing_date DATE, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(victim_id) REFERENCES victims (id)
);

CREATE TABLE consent_records (
	id VARCHAR(36) NOT NULL, 
	victim_id VARCHAR(36) NOT NULL, 
	scope VARCHAR(100) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	granted_at TIMESTAMP WITHOUT TIME ZONE, 
	revoked_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(victim_id) REFERENCES victims (id)
);

CREATE TABLE interactions (
	id VARCHAR(36) NOT NULL, 
	case_id VARCHAR(36) NOT NULL, 
	channel VARCHAR(20) NOT NULL, 
	language VARCHAR(10) NOT NULL, 
	occurred_at TIMESTAMP WITHOUT TIME ZONE, 
	transcript TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(case_id) REFERENCES case_files (id)
);

CREATE TABLE distress_scores (
	id VARCHAR(36) NOT NULL, 
	interaction_id VARCHAR(36) NOT NULL, 
	sentiment_score FLOAT NOT NULL, 
	voice_stress_score FLOAT NOT NULL, 
	threat_flag BOOLEAN NOT NULL, 
	composite_score FLOAT NOT NULL, 
	confidence FLOAT NOT NULL, 
	trend_flag VARCHAR(20) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(interaction_id) REFERENCES interactions (id)
);

CREATE TABLE alerts (
	id VARCHAR(36) NOT NULL, 
	score_id VARCHAR(36) NOT NULL, 
	official_id VARCHAR(36), 
	risk_level VARCHAR(20) NOT NULL, 
	raised_at TIMESTAMP WITHOUT TIME ZONE, 
	status VARCHAR(30), 
	confirmed_outcome VARCHAR(30), 
	previous_hash VARCHAR(64) NOT NULL, 
	current_hash VARCHAR(64) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(score_id) REFERENCES distress_scores (id)
);

CREATE TABLE interventions (
	id VARCHAR(36) NOT NULL, 
	alert_id VARCHAR(36) NOT NULL, 
	official_id VARCHAR(36) NOT NULL, 
	intervention_type VARCHAR(50) NOT NULL, 
	status VARCHAR(30), 
	scheduled_on TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(alert_id) REFERENCES alerts (id)
);
