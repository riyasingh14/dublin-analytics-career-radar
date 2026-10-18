-- Reference analytical model: active-posting skill co-occurrence.
-- PostgreSQL-compatible SQL, also executed against an equivalent SQLite fixture.
-- Each posting counts once per skill; pair ordering prevents double counting.
-- A filtered deployment must apply geography/role/date scope inside scoped_postings.
WITH scoped_postings AS (
    SELECT job_key FROM career_radar.job_posting WHERE status = 'active'
),
mentions AS (
    SELECT DISTINCT evidence.job_key, evidence.skill_id
    FROM career_radar.job_skill_evidence AS evidence
    INNER JOIN scoped_postings ON scoped_postings.job_key = evidence.job_key
),
skill_counts AS (
    SELECT skill_id, COUNT(*) AS posting_count FROM mentions GROUP BY skill_id
),
pair_counts AS (
    SELECT a.skill_id AS skill_a, b.skill_id AS skill_b, COUNT(*) AS joint_count
    FROM mentions AS a
    INNER JOIN mentions AS b ON a.job_key = b.job_key AND a.skill_id < b.skill_id
    GROUP BY a.skill_id, b.skill_id
),
sample AS (
    SELECT COUNT(*) AS sample_size FROM scoped_postings
)
SELECT pairs.skill_a, pairs.skill_b, pairs.joint_count,
       a.posting_count AS skill_a_count, b.posting_count AS skill_b_count,
       sample.sample_size,
       1.0 * pairs.joint_count / NULLIF(sample.sample_size, 0) AS support,
       1.0 * pairs.joint_count /
           NULLIF(a.posting_count + b.posting_count - pairs.joint_count, 0) AS jaccard,
       1.0 * pairs.joint_count * sample.sample_size /
           NULLIF(a.posting_count * b.posting_count, 0) AS lift
FROM pair_counts AS pairs
INNER JOIN skill_counts AS a ON a.skill_id = pairs.skill_a
INNER JOIN skill_counts AS b ON b.skill_id = pairs.skill_b
CROSS JOIN sample
ORDER BY pairs.joint_count DESC, pairs.skill_a, pairs.skill_b;
