-- PostgreSQL schema for Dublin Analytics Career Radar.
-- Every insight is traceable to an authorised source and extraction record.

CREATE SCHEMA IF NOT EXISTS career_radar;

CREATE TABLE IF NOT EXISTS career_radar.job_source (
    source_key INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_name TEXT NOT NULL UNIQUE,
    source_type TEXT NOT NULL CHECK (source_type IN ('official_api', 'company_careers_api', 'user_upload')),
    source_home_url TEXT NOT NULL,
    terms_checked_on DATE,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS career_radar.role_taxonomy (
    role_key INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    role_name TEXT NOT NULL UNIQUE,
    role_description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS career_radar.skill (
    skill_id TEXT PRIMARY KEY,
    skill_name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    proof_of_work_recommendation TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS career_radar.job_posting (
    job_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_key INTEGER NOT NULL REFERENCES career_radar.job_source,
    source_job_id TEXT NOT NULL,
    canonical_url TEXT NOT NULL,
    title TEXT NOT NULL,
    employer_name TEXT,
    location_text TEXT NOT NULL,
    work_pattern TEXT CHECK (work_pattern IN ('onsite', 'hybrid', 'remote', 'unknown')) DEFAULT 'unknown',
    industry TEXT,
    role_key INTEGER REFERENCES career_radar.role_taxonomy,
    role_confidence NUMERIC(4,3),
    description_text TEXT,
    posted_at TIMESTAMPTZ,
    first_seen_at TIMESTAMPTZ NOT NULL,
    last_seen_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'expired', 'removed')) DEFAULT 'active',
    deduplication_key TEXT NOT NULL UNIQUE,
    UNIQUE (source_key, source_job_id)
);

CREATE TABLE IF NOT EXISTS career_radar.job_snapshot (
    snapshot_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_key BIGINT NOT NULL REFERENCES career_radar.job_posting,
    collected_at TIMESTAMPTZ NOT NULL,
    snapshot_week DATE NOT NULL,
    source_url TEXT NOT NULL,
    UNIQUE (job_key, snapshot_week)
);

CREATE TABLE IF NOT EXISTS career_radar.job_skill_evidence (
    evidence_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_key BIGINT NOT NULL REFERENCES career_radar.job_posting,
    skill_id TEXT NOT NULL REFERENCES career_radar.skill,
    source_phrase TEXT NOT NULL,
    extraction_method TEXT NOT NULL CHECK (extraction_method IN ('rule', 'llm', 'human')),
    extraction_version TEXT NOT NULL,
    confidence NUMERIC(4,3) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    human_review_status TEXT NOT NULL CHECK (human_review_status IN ('unreviewed', 'accepted', 'rejected')) DEFAULT 'unreviewed',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_job_posting_role ON career_radar.job_posting (role_key);
CREATE INDEX IF NOT EXISTS ix_job_posting_location ON career_radar.job_posting (location_text);
CREATE INDEX IF NOT EXISTS ix_snapshot_week ON career_radar.job_snapshot (snapshot_week);
CREATE INDEX IF NOT EXISTS ix_skill_evidence_skill ON career_radar.job_skill_evidence (skill_id);
