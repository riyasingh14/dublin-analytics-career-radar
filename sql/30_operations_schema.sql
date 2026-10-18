-- Executable, immutable analyst warehouse. Not used by the public Vercel demo.
-- Grain is explicit and every market model is scoped by run_id.
CREATE SCHEMA IF NOT EXISTS career_radar_ops;

CREATE TABLE IF NOT EXISTS career_radar_ops.analysis_run (
    run_id text PRIMARY KEY,
    source_name text NOT NULL,
    input_sha256 text NOT NULL,
    data_status text NOT NULL CHECK (data_status IN ('fixture', 'unreviewed')),
    collection_timestamp timestamptz NOT NULL,
    manifest jsonb NOT NULL,
    loaded_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS career_radar_ops.posting (
    run_id text NOT NULL REFERENCES career_radar_ops.analysis_run,
    canonical_url text NOT NULL,
    source_job_id text NOT NULL,
    title text NOT NULL,
    employer_name text,
    location_text text NOT NULL,
    geography text NOT NULL,
    role_name text NOT NULL,
    work_pattern text NOT NULL,
    description_text text NOT NULL,
    deduplication_key text NOT NULL,
    PRIMARY KEY (run_id, canonical_url),
    UNIQUE (run_id, source_job_id),
    UNIQUE (run_id, deduplication_key)
);

CREATE TABLE IF NOT EXISTS career_radar_ops.skill_evidence (
    run_id text NOT NULL,
    canonical_url text NOT NULL,
    skill_id text NOT NULL,
    source_phrase text NOT NULL,
    extraction_version text NOT NULL,
    human_review_status text NOT NULL DEFAULT 'unreviewed' CHECK (human_review_status = 'unreviewed'),
    PRIMARY KEY (run_id, canonical_url, skill_id, source_phrase, extraction_version),
    FOREIGN KEY (run_id, canonical_url) REFERENCES career_radar_ops.posting
);

CREATE TABLE IF NOT EXISTS career_radar_ops.requirement (
    run_id text NOT NULL,
    canonical_url text NOT NULL,
    requirement_id text NOT NULL,
    skill_id text NOT NULL,
    requirement_type text NOT NULL CHECK (requirement_type IN ('required','preferred','uncertain','negated')),
    source_phrase text NOT NULL,
    start_offset integer NOT NULL CHECK (start_offset >= 0),
    end_offset integer NOT NULL CHECK (end_offset > start_offset),
    extraction_version text NOT NULL,
    PRIMARY KEY (run_id, canonical_url, requirement_id),
    FOREIGN KEY (run_id, canonical_url) REFERENCES career_radar_ops.posting
);

CREATE OR REPLACE VIEW career_radar_ops.posting_skill AS
SELECT DISTINCT run_id, canonical_url, skill_id FROM career_radar_ops.skill_evidence;

CREATE OR REPLACE VIEW career_radar_ops.pair_metrics AS
WITH counts AS (
    SELECT run_id, skill_id, count(*) AS posting_count
    FROM career_radar_ops.posting_skill GROUP BY run_id, skill_id
), pairs AS (
    SELECT a.run_id, a.skill_id AS skill_a, b.skill_id AS skill_b, count(*) AS joint_count
    FROM career_radar_ops.posting_skill a JOIN career_radar_ops.posting_skill b
      ON a.run_id = b.run_id AND a.canonical_url = b.canonical_url AND a.skill_id < b.skill_id
    GROUP BY a.run_id, a.skill_id, b.skill_id
), samples AS (
    -- Includes postings without any extracted skills.
    SELECT run_id, count(*) AS sample_size FROM career_radar_ops.posting GROUP BY run_id
)
SELECT p.run_id, p.skill_a, p.skill_b, p.joint_count,
       a.posting_count AS skill_a_count, b.posting_count AS skill_b_count, s.sample_size,
       p.joint_count::double precision / s.sample_size AS support,
       p.joint_count::double precision / (a.posting_count + b.posting_count - p.joint_count) AS jaccard,
       p.joint_count::double precision * s.sample_size / (a.posting_count * b.posting_count) AS lift
FROM pairs p JOIN counts a ON a.run_id=p.run_id AND a.skill_id=p.skill_a
JOIN counts b ON b.run_id=p.run_id AND b.skill_id=p.skill_b
JOIN samples s ON s.run_id=p.run_id;

-- Synthetic data lives in independent tables with no FK to observed posting runs.
CREATE TABLE IF NOT EXISTS career_radar_ops.synthetic_scenario (
    scenario_id text PRIMARY KEY,
    metadata jsonb NOT NULL
);
CREATE TABLE IF NOT EXISTS career_radar_ops.synthetic_spell (
    scenario_id text NOT NULL REFERENCES career_radar_ops.synthetic_scenario,
    person_id text NOT NULL,
    spell_id text NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL CHECK (end_date > start_date),
    occupation text NOT NULL,
    employer_id text,
    industry text NOT NULL,
    seniority text NOT NULL,
    experience_years integer NOT NULL CHECK (experience_years >= 0),
    geography text NOT NULL,
    salary_eur_annual_fte double precision,
    currency text NOT NULL CHECK (currency = 'EUR'),
    salary_basis text NOT NULL CHECK (salary_basis = 'annual base FTE'),
    fte double precision NOT NULL CHECK (fte > 0),
    data_label text NOT NULL CHECK (data_label = 'Synthetic scenario — not observed labour-market outcomes'),
    generator_version text NOT NULL,
    PRIMARY KEY (scenario_id, spell_id),
    UNIQUE (scenario_id, person_id, start_date)
);

CREATE OR REPLACE VIEW career_radar_ops.synthetic_transition AS
WITH ordered AS (
    SELECT *, lead(spell_id) OVER w AS after_spell_id,
       lead(occupation) OVER w AS destination, lead(employer_id) OVER w AS next_employer,
       lead(industry) OVER w AS next_industry, lead(seniority) OVER w AS next_seniority,
       lead(geography) OVER w AS destination_geography,
       lead(salary_eur_annual_fte) OVER w AS after_salary,
       lead(start_date) OVER w AS transition_date, lead(fte) OVER w AS next_fte,
       lead(currency) OVER w AS next_currency, lead(salary_basis) OVER w AS next_basis
    FROM career_radar_ops.synthetic_spell
    WINDOW w AS (PARTITION BY scenario_id, person_id ORDER BY start_date)
), flags AS (
    SELECT *, occupation = 'Career break' OR destination = 'Career break' AS break_event,
        employer_id IS DISTINCT FROM next_employer AS employer_change,
        occupation IS DISTINCT FROM destination AS occupation_change,
        industry IS DISTINCT FROM next_industry AS industry_change,
        seniority IS DISTINCT FROM next_seniority AS level_change,
        array_position(ARRAY['Junior','Mid','Senior','Lead'], next_seniority) >
        array_position(ARRAY['Junior','Mid','Senior','Lead'], seniority) AS promotion,
        coalesce(salary_eur_annual_fte > 0 AND salary_eur_annual_fte < 'Infinity'::float8
          AND after_salary > 0 AND after_salary < 'Infinity'::float8
          AND currency = next_currency AND salary_basis = next_basis AND next_fte > 0, false) AS valid_pair
    FROM ordered WHERE after_spell_id IS NOT NULL
)
SELECT scenario_id, person_id, spell_id AS before_spell_id, after_spell_id,
       spell_id || '->' || after_spell_id AS transition_id,
       occupation AS origin, destination, destination_geography AS geography, experience_years,
       transition_date,
       CASE WHEN break_event THEN 'Career break / return'
            ELSE coalesce(nullif(concat_ws(' + ',
                CASE WHEN employer_change THEN 'employer' END,
                CASE WHEN occupation_change THEN 'occupation' END,
                CASE WHEN industry_change THEN 'industry' END,
                CASE WHEN promotion THEN 'promotion' END,
                CASE WHEN level_change AND NOT promotion THEN 'demotion' END), ''), 'Stayer') END AS category,
       salary_eur_annual_fte AS before_salary, after_salary,
       valid_pair AND NOT break_event AS valid_pair,
       CASE WHEN valid_pair AND NOT break_event THEN (after_salary / salary_eur_annual_fte - 1) * 100 END AS individual_pct_change,
       data_label, generator_version
FROM flags;

CREATE OR REPLACE VIEW career_radar_ops.synthetic_cohort_metrics AS
WITH cohorts AS (
    SELECT scenario_id, category, data_label, generator_version,
        count(*) AS events, count(DISTINCT person_id) AS people,
        count(*) FILTER (WHERE valid_pair) AS valid_pairs,
        count(*) FILTER (WHERE NOT valid_pair) AS excluded_pairs,
        percentile_cont(.5) WITHIN GROUP (ORDER BY individual_pct_change) AS median_individual,
        percentile_cont(.5) WITHIN GROUP (ORDER BY before_salary) FILTER (WHERE valid_pair) AS median_before,
        percentile_cont(.5) WITHIN GROUP (ORDER BY after_salary) FILTER (WHERE valid_pair) AS median_after,
        avg((individual_pct_change < 0)::int) FILTER (WHERE valid_pair) AS share_decreased
    FROM career_radar_ops.synthetic_transition
    GROUP BY scenario_id, category, data_label, generator_version
)
SELECT scenario_id, category, data_label, generator_version, events, people, valid_pairs, excluded_pairs,
       CASE WHEN valid_pairs >= 20 THEN median_individual END AS median_individual_pct_change,
       CASE WHEN valid_pairs >= 20 THEN (median_after / median_before - 1) * 100 END AS change_between_cohort_medians_pct,
       CASE WHEN valid_pairs >= 20 THEN share_decreased END AS share_decreased
FROM cohorts;
