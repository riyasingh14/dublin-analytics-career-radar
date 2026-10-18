-- PostgreSQL reference model for the SYNTHETIC mobility module.
-- This is an optional analyst worksheet, not required by the in-memory app.
-- No observed jobs or candidate profiles are joined. All objects are session-local.
-- Load generate_histories() output into this contract in an analyst session.
CREATE TEMP TABLE synthetic_career_spells (
    person_id text NOT NULL,
    spell_id text PRIMARY KEY,
    start_date date NOT NULL,
    end_date date NOT NULL CHECK (end_date > start_date),
    occupation text NOT NULL,
    employer_id text,
    industry text NOT NULL,
    seniority text NOT NULL,
    experience_years integer NOT NULL,
    geography text NOT NULL,
    salary_eur_annual_fte double precision,
    currency text NOT NULL CHECK (currency = 'EUR'),
    salary_basis text NOT NULL CHECK (salary_basis = 'annual base FTE'),
    fte double precision NOT NULL CHECK (fte > 0),
    data_label text NOT NULL CHECK (data_label = 'Synthetic scenario — not observed labour-market outcomes'),
    generator_version text NOT NULL,
    UNIQUE(person_id, start_date)
);

-- Half-open intervals must not overlap; this query must return zero rows.
SELECT a.person_id, a.spell_id, b.spell_id
FROM synthetic_career_spells a
JOIN synthetic_career_spells b ON a.person_id = b.person_id AND a.spell_id < b.spell_id
WHERE a.start_date < b.end_date AND b.start_date < a.end_date;

CREATE TEMP VIEW synthetic_mobility_pairs AS
WITH ordered AS (
    SELECT *,
        lead(spell_id) OVER w AS next_spell_id,
        lead(occupation) OVER w AS destination,
        lead(employer_id) OVER w AS next_employer,
        lead(industry) OVER w AS next_industry,
        lead(seniority) OVER w AS next_seniority,
        lead(salary_eur_annual_fte) OVER w AS after_salary
    FROM synthetic_career_spells
    WINDOW w AS (PARTITION BY person_id ORDER BY start_date)
), flags AS (
    SELECT *, occupation = 'Career break' OR destination = 'Career break' AS break_event,
        employer_id IS DISTINCT FROM next_employer AS employer_change,
        occupation IS DISTINCT FROM destination AS occupation_change,
        industry IS DISTINCT FROM next_industry AS industry_change,
        array_position(ARRAY['Junior','Mid','Senior','Lead'], next_seniority) >
        array_position(ARRAY['Junior','Mid','Senior','Lead'], seniority) AS promotion,
        coalesce(salary_eur_annual_fte > 0 AND salary_eur_annual_fte < 'Infinity'::float8
                 AND after_salary > 0 AND after_salary < 'Infinity'::float8, false) AS valid_pair
    FROM ordered WHERE next_spell_id IS NOT NULL
)
SELECT person_id, spell_id AS before_spell_id, next_spell_id AS after_spell_id,
       occupation AS origin, destination, geography, experience_years,
       CASE WHEN break_event THEN 'Career break / return'
            ELSE coalesce(nullif(concat_ws(' + ',
                CASE WHEN employer_change THEN 'employer' END,
                CASE WHEN occupation_change THEN 'occupation' END,
                CASE WHEN industry_change THEN 'industry' END,
                CASE WHEN promotion THEN 'promotion' END), ''), 'Stayer') END AS category,
       salary_eur_annual_fte AS before_salary, after_salary,
       valid_pair AND NOT break_event AS valid_pair,
       CASE WHEN valid_pair AND NOT break_event
            THEN (after_salary / salary_eur_annual_fte - 1) * 100 END AS individual_pct_change,
       data_label, generator_version
FROM flags;

-- Transition-weighted statistics; repeated moves remain separate events.
-- The two percentage-change measures have intentionally different names.
WITH cohorts AS (
    SELECT category, data_label, generator_version,
        count(*) AS events, count(DISTINCT person_id) AS people,
        count(*) FILTER (WHERE valid_pair) AS valid_pairs,
        count(*) FILTER (WHERE NOT valid_pair) AS excluded_pairs,
        percentile_cont(.5) WITHIN GROUP (ORDER BY individual_pct_change) AS median_individual,
        percentile_cont(.5) WITHIN GROUP (ORDER BY before_salary) FILTER (WHERE valid_pair) AS median_before,
        percentile_cont(.5) WITHIN GROUP (ORDER BY after_salary) FILTER (WHERE valid_pair) AS median_after,
        avg((individual_pct_change < 0)::int) FILTER (WHERE valid_pair) AS share_decreased
    FROM synthetic_mobility_pairs
    GROUP BY category, data_label, generator_version
)
SELECT category, data_label, generator_version, events, people, valid_pairs, excluded_pairs,
       CASE WHEN valid_pairs >= 20 THEN median_individual END AS median_individual_pct_change,
       CASE WHEN valid_pairs >= 20 THEN (median_after / median_before - 1) * 100 END AS change_between_cohort_medians_pct,
       CASE WHEN valid_pairs >= 20 THEN share_decreased END AS share_decreased
FROM cohorts ORDER BY events DESC, category;
