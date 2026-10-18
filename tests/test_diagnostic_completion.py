"""Authored adversarial document fixtures; these are not a human precision evaluation."""
from pathlib import Path
import unittest
from career_radar.diagnostic import analyze_description
from career_radar.normalise import load_taxonomy


class DiagnosticCompletionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.taxonomy = load_taxonomy(Path(__file__).resolve().parents[1] / 'data/reference/skills.csv')

    def analyze(self, text):
        return analyze_description(text, self.taxonomy)

    def test_export_artifacts_preserve_unicode_offsets_and_intentional_code_uncertainty(self):
        text = '📊 Data Analyst\nUse <div> in documentation. SQL required. Broken export: \ufffd'
        flags = [f for f in self.analyze(text)['findings'] if f['rule'] == 'quality.possible_export_artifact']
        self.assertEqual([f['source_phrase'] for f in flags], ['<div>', '\ufffd'])
        for flag in flags:
            self.assertEqual(text[flag['start']:flag['end']], flag['source_phrase'])
            self.assertIn('intentional', flag['rationale'])
            self.assertIn('unchanged', flag['suggestion'])

    def test_repeated_long_lines_flag_only_second_exact_occurrence(self):
        line = 'You will produce weekly reporting and explain measures to stakeholders.'
        text = f'Data Analyst\n{line}\n{line}'
        flags = [f for f in self.analyze(text)['findings'] if f['rule'] == 'quality.duplicate_line']
        self.assertEqual(len(flags), 1)
        self.assertEqual(flags[0]['start'], text.rindex(line))
        self.assertEqual(text[flags[0]['start']:flags[0]['end']], line)

    def test_alignment_is_a_review_question_with_exact_evidence(self):
        text = 'Data Analyst\nYou will act as a Software Engineer for the platform.'
        flags = [f for f in self.analyze(text)['findings'] if f['rule'] == 'alignment.role_wording']
        self.assertEqual(len(flags), 1)
        self.assertEqual(flags[0]['severity'], 'review')
        self.assertIn('intentional', flags[0]['rationale'])
        self.assertEqual(text[flags[0]['start']:flags[0]['end']], flags[0]['source_phrase'])

    def test_synthetic_text_cannot_create_an_observed_benchmark(self):
        result = self.analyze('Synthetic Data Analyst. Dublin, hybrid. SQL required.')
        self.assertIsNone(result['benchmark'])
        self.assertEqual(result['benchmark_status']['minimum_sample'], 20)
        self.assertEqual(result['benchmark_status']['comparable_observed_postings'], 0)
        self.assertFalse(result['benchmark_status']['available'])
        self.assertIn('Synthetic', result['benchmark_status']['reason'])

    def test_training_budget_is_not_salary_disclosure(self):
        result = self.analyze('Data Analyst. Training budget EUR 1500 annually. Salary not disclosed.')
        self.assertEqual(result['completeness']['salary']['status'], 'unknown')
        self.assertEqual(result['completeness']['salary']['source_phrase'], 'Salary')
        self.assertEqual(self.analyze('Salary: EUR 55000 annually.')['completeness']['salary']['status'], 'present')

    def test_uppercase_name_is_not_copied_into_default_suggestion(self):
        flags = self.analyze('Contact ANNA for details.')['findings']
        abbreviation = next(f for f in flags if f['rule'] == 'clarity.possible_abbreviation')
        self.assertEqual(abbreviation['source_phrase'], 'ANNA')
        self.assertNotIn('ANNA', abbreviation['suggestion'])
        self.assertNotIn('ANNA', abbreviation['rationale'])

    def test_hours_do_not_establish_contract_tenure(self):
        for hours in ('Full-time', 'Part time'):
            with self.subTest(hours=hours):
                field = self.analyze(f'Data Analyst. {hours}.')['completeness']['contract_type']
                self.assertEqual(field['status'], 'unknown')
                self.assertEqual(field['source_phrase'], hours)
        for tenure in ('Permanent', 'Fixed-term', 'Temporary', 'Internship', 'Contractor'):
            with self.subTest(tenure=tenure):
                self.assertEqual(self.analyze(f'Data Analyst. {tenure}.')['completeness']['contract_type']['status'], 'present')
