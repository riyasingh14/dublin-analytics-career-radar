"""Execute the portable SQL reference with the production model's table/column names."""
from pathlib import Path
import sqlite3
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SkillSQLTests(unittest.TestCase):
    def test_pair_sql_deduplicates_mentions_and_includes_no_skill_postings(self):
        with sqlite3.connect(':memory:') as database:
            database.execute("ATTACH DATABASE ':memory:' AS career_radar")
            database.execute('CREATE TABLE career_radar.job_posting (job_key INTEGER, status TEXT)')
            database.execute('CREATE TABLE career_radar.job_skill_evidence (job_key INTEGER, skill_id TEXT)')
            database.executemany('INSERT INTO career_radar.job_posting VALUES (?, ?)',
                                 [(1, 'active'), (2, 'active'), (3, 'active'), (4, 'expired'), (5, 'active')])
            database.executemany('INSERT INTO career_radar.job_skill_evidence VALUES (?, ?)',
                                 [(1, 'sql'), (1, 'python'), (1, 'sql'), (2, 'sql'),
                                  (3, 'python'), (4, 'python'), (4, 'sql'), (99, 'sql')])
            rows = database.execute((ROOT/'sql/20_skill_constellation.sql').read_text()).fetchall()
            self.assertEqual(len(rows), 1)
            skill_a, skill_b, joint, count_a, count_b, sample, support, jaccard, lift = rows[0]
            self.assertEqual((skill_a, skill_b), ('python', 'sql'))
            self.assertEqual((joint, count_a, count_b, sample), (1, 2, 2, 4))
            self.assertAlmostEqual(support, 0.25)
            self.assertAlmostEqual(jaccard, 1/3)
            self.assertAlmostEqual(lift, 1.0)

    def test_empty_sql_sample_returns_no_pairs(self):
        with sqlite3.connect(':memory:') as database:
            database.execute("ATTACH DATABASE ':memory:' AS career_radar")
            database.execute('CREATE TABLE career_radar.job_posting (job_key INTEGER, status TEXT)')
            database.execute('CREATE TABLE career_radar.job_skill_evidence (job_key INTEGER, skill_id TEXT)')
            self.assertEqual(database.execute((ROOT/'sql/20_skill_constellation.sql').read_text()).fetchall(), [])
