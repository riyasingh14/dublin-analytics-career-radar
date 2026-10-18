import json
import unittest
from api.index import app
from career_radar.web_api import taxonomy
from career_radar.requirements_model import extract_requirements, RequirementLimitError


class APIResourceTests(unittest.TestCase):
    def test_extreme_json_integers_return_safe_json_instead_of_overflowing(self):
        for payload in ({'action':'mobility','scenario':{'seed':10**1000}},
                        {'action':'constellation','min_pair_count':10**1000}):
            response = app.test_client().post('/api/index', json=payload)
            self.assertEqual(response.status_code, 400)
            self.assertTrue(response.is_json)
            self.assertNotIn('Traceback', response.get_data(as_text=True))

    def test_repetitive_descriptions_fail_explicitly_without_truncating_evidence(self):
        for action in ('readiness', 'diagnostic'):
            response = app.test_client().post('/api/index', json={'action': action, 'text': 'SQL. '*6000})
            self.assertEqual(response.status_code, 400)
            self.assertIn('more than 200 skill mentions', response.get_json()['error'])

    def test_long_source_contexts_are_bounded_exact_slices_with_offsets(self):
        text = '😀 ' + 'context '*1500 + ' SQL required. '
        rows = extract_requirements(text, taxonomy())
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertTrue(row['context_truncated'])
        self.assertLessEqual(len(row['source_text']), 600)
        self.assertEqual(text[row['context_start']:row['context_end']], row['source_text'])
        self.assertEqual(text[row['start']:row['end']], row['source_phrase'])
        self.assertIn('SQL', row['source_text'])

    def test_repetitive_non_skill_findings_are_also_bounded(self):
        response = app.test_client().post('/api/index', json={'action':'diagnostic','text':'ANNA. '*4000})
        self.assertEqual(response.status_code, 400)
        self.assertIn('more than 200 review findings', response.get_json()['error'])

    def test_largest_accepted_repeated_context_stays_under_two_megabytes(self):
        text = ('SQL ' * 200) + (' context' * 3000)
        response = app.test_client().post('/api/index', json={'action':'readiness','text':text})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()['requirements']), 200)
        self.assertLess(len(response.data), 2_000_000)
