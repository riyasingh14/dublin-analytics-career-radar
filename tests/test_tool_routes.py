"""Exercise the composed app, not only individual module render functions."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from career_radar.build_snapshot import build_snapshot_payload
from career_radar.normalise import load_taxonomy, extract_skills

ROOT = Path(__file__).resolve().parents[1]


class ToolRouteTests(unittest.TestCase):
    def snapshot(self):
        job = {
            'source_job_id': 'fixture-1', 'canonical_url': 'https://example.test/fixture-1',
            'title': 'Data Analyst', 'employer_name': 'Fictional Example',
            'location_text': 'Dublin, Ireland', 'role_name': 'Data Analyst',
            'work_pattern': 'hybrid', 'source_name': 'Labelled fixture',
            'description_text': 'SQL is required; Python is preferred. Dublin, hybrid, permanent.',
        }
        evidence = [{**row, 'canonical_url': job['canonical_url']}
                    for row in extract_skills(job['description_text'], load_taxonomy(ROOT/'data/reference/skills.csv'))]
        return build_snapshot_payload([job], evidence, 'Integration fixture', 'fixture')

    def test_all_four_home_entries_open_real_tools_without_a_dataset(self):
        entries = (
            ('open_constellation', 'Skill Constellation'),
            ('open_readiness', 'Opportunity Readiness Studio'),
            ('open_mobility', 'Career Mobility Lab'),
            ('open_diagnostic', 'Job Description Diagnostic'),
        )
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {'CAREER_RADAR_SNAPSHOT': str(Path(directory)/'missing.json')}):
                for button_key, heading in entries:
                    with self.subTest(tool=button_key):
                        app = AppTest.from_file(str(ROOT/'app.py')).run(timeout=30)
                        app.button(key=button_key).click().run(timeout=30)
                        self.assertFalse(app.exception)
                        self.assertTrue(any(item.value == heading for item in app.header))
                        if button_key == 'open_mobility':
                            self.assertTrue(any('Synthetic scenario' in item.value for item in app.warning))

    def test_imported_posting_is_available_to_both_requirement_tools(self):
        with tempfile.TemporaryDirectory() as directory:
            snapshot = Path(directory)/'snapshot.json'
            snapshot.write_text(json.dumps(self.snapshot()))
            with patch.dict(os.environ, {'CAREER_RADAR_SNAPSHOT': str(snapshot)}):
                app = AppTest.from_file(str(ROOT/'app.py')).run(timeout=30)
                app.button(key='open_readiness').click().run(timeout=30)
                source = next(item for item in app.radio if item.label == 'Requirement source')
                source.set_value('Select a source posting').run(timeout=30)
                self.assertFalse(app.exception)
                self.assertTrue(any('SQL' in str(item.value) for item in app.dataframe))
                app.radio(key='radar_route').set_value('JD Diagnostic').run(timeout=30)
                source = next(item for item in app.radio if item.label == 'Description source')
                source.set_value('Observed sample').run(timeout=30)
                self.assertFalse(app.exception)
                self.assertEqual(app.text_area[0].value, self.snapshot()['postings'][0]['description_text'])

    def test_constellation_demo_is_opt_in_and_explicitly_fictional(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {'CAREER_RADAR_SNAPSHOT': str(Path(directory)/'missing.json')}):
                app = AppTest.from_file(str(ROOT/'app.py')).run(timeout=30)
                app.button(key='open_constellation').click().run(timeout=30)
                self.assertFalse(app.exception)
                self.assertEqual(len(app.metric), 0)
                app.toggle(key='sc_demo').set_value(True).run(timeout=30)
                self.assertFalse(app.exception)
                self.assertEqual(app.metric[0].value, '30')
                self.assertTrue(any('fictional' in item.value for item in app.warning))
