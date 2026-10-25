import copy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from api.index import app
from career_radar.description_samples import CATALOG, load_description_samples
from career_radar.web_api import taxonomy
from career_radar.diagnostic import analyze_description
from career_radar.listing_conditions import extract_listing_conditions


class DescriptionSampleTests(unittest.TestCase):
    def test_complete_employer_sources_have_license_archive_status_and_content_integrity(self):
        samples=load_description_samples()
        self.assertEqual(len(samples),4)
        for sample in samples:
            self.assertEqual(sample['license'],'CC0-1.0')
            self.assertEqual(sample['status'],'archived')
            self.assertIn('United States',sample['geography'])
            self.assertIn('not an Ireland-market sample',sample['geography'])
            self.assertGreater(len(sample['text']),6000)
            self.assertIn('How',sample['text'])
            self.assertNotIn('{{',sample['text'])
            self.assertEqual(hashlib.sha256(sample['text'].encode()).hexdigest(),sample['content_sha256'])
            self.assertNotIn('raw_file',sample)

    def test_all_real_documents_are_analyzable_with_source_grounded_requirement_spans(self):
        for sample in load_description_samples():
            with self.subTest(sample=sample['id']):
                result=analyze_description(sample['text'],taxonomy())
                self.assertGreater(len(result['requirements']),0)
                for requirement in result['requirements']:
                    self.assertEqual(sample['text'][requirement['start']:requirement['end']],requirement['source_phrase'])
                self.assertFalse(result['benchmark_status']['available'])

    def test_loading_reference_inputs_does_not_turn_them_into_irish_market_observations(self):
        data=app.test_client().get('/api/index?action=bootstrap').get_json()
        self.assertEqual(data['data_mode'],'synthetic-demo')
        self.assertEqual(data['snapshot']['market']['sample_size'],30)
        self.assertTrue(all(p['canonical_url'].startswith('fixture://') for p in data['snapshot']['postings']))
        self.assertEqual(len(data['description_samples']),4)
        for sample in data['description_samples']:
            response=app.test_client().post('/api/index',json={'action':'readiness','text':sample['text']})
            self.assertEqual(response.status_code,200)
            self.assertIsNone(response.get_json()['assessment']['alignment_pct'])

    def test_tampered_text_or_unpinned_sources_are_rejected(self):
        original=json.loads(CATALOG.read_text())
        for field,value in [('text','x'*7000),('source_url','https://example.com/unverified'),('license','unspecified')]:
            changed=copy.deepcopy(original);changed['samples'][0][field]=value
            with TemporaryDirectory() as directory:
                path=Path(directory)/'samples.json';path.write_text(json.dumps(changed))
                with self.subTest(field=field),self.assertRaises(ValueError):load_description_samples(path)

    def test_real_us_eligibility_is_visible_and_never_scored_as_a_candidate_failure(self):
        sample=next(s for s in load_description_samples() if s['id']=='tts-fedramp-cyber-data-analyst')
        conditions=extract_listing_conditions(sample['text'])
        self.assertTrue(any(c['category']=='work_eligibility' and 'citizens' in c['source_text'] for c in conditions))
        self.assertTrue(all(c['excluded_from_index'] and c['status']=='unknown' for c in conditions))
