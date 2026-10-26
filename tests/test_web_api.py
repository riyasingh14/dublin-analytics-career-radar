"""HTTP boundary, privacy, resource limits and reuse of the analytical core."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from api.index import app
from career_radar.web_api import dispatch


class WebAPITests(unittest.TestCase):
    def setUp(self):
        self.client=app.test_client()

    def post(self,action,**payload):
        return self.client.post('/api/index',json={'action':action,**payload})

    def test_bootstrap_defaults_to_public_demo_not_private_snapshot(self):
        response=self.client.get('/api/index?action=bootstrap')
        self.assertEqual(response.status_code,200)
        data=response.get_json()
        self.assertEqual(data['data_mode'],'synthetic-demo')
        self.assertEqual(data['snapshot']['metadata']['data_status'],'fixture')
        self.assertEqual(data['snapshot']['market']['sample_size'],30)
        self.assertFalse(data['snapshot']['metadata']['publish_allowed'])
        self.assertTrue(all(p['canonical_url'].startswith('fixture://') for p in data['snapshot']['postings']))
        self.assertEqual(response.headers['Cache-Control'],'no-store')

    def test_posting_filters_recompute_constellation_denominators(self):
        full=self.post('constellation').get_json()
        dublin=self.post('constellation',geography='Dublin').get_json()
        cork=self.post('constellation',geography='Rest of Ireland').get_json()
        self.assertEqual((full['sample_size'],dublin['sample_size'],cork['sample_size']),(30,20,10))
        self.assertFalse(cork['network_eligible'])
        self.assertTrue(full['eligible_pairs'])

    def test_diagnostic_uses_shared_negation_and_exact_spans(self):
        text='No SQL or Python experience is required. Excel is preferred.'
        result=self.post('diagnostic',text=text).get_json()
        kinds={r['skill_id']:r['requirement_type'] for r in result['requirements']}
        self.assertEqual(kinds,{'sql':'negated','python':'negated','excel':'preferred'})
        for requirement in result['requirements']:
            self.assertEqual(text[requirement['start']:requirement['end']],requirement['source_phrase'])

    def test_readiness_report_omits_notes_and_does_not_store_state(self):
        text='SQL is required. Python is preferred.'
        first=self.post('readiness',text=text).get_json()
        requirements=first['requirements']
        note='Private coursework description, not for export'
        evidence={r['requirement_id']:{'status':'supported','note':note} for r in requirements}
        overrides={r['requirement_id']:r['requirement_type'] for r in requirements}
        assessed=self.post('readiness',text=text,evidence=evidence,classifications=overrides).get_json()
        self.assertEqual(assessed['assessment']['alignment_pct'],100)
        self.assertNotIn(note,json.dumps(assessed['report']))
        again=self.post('readiness',text=text).get_json()
        self.assertIsNone(again['assessment']['alignment_pct'])
        self.assertTrue(all(not r['evidence_note'] for r in again['assessment']['rows']))

    def test_client_cannot_inject_requirements_or_arbitrary_ids(self):
        response=self.post('readiness',text='SQL required.',evidence={'forged':{'status':'supported','note':'secret content'}})
        self.assertEqual(response.status_code,400)
        self.assertNotIn('secret content',response.get_data(as_text=True))

    def test_action_plan_uses_corrected_requirements_and_leaves_baseline_unchanged(self):
        text = 'SQL is required. Python is preferred.'
        initial = self.post('readiness', text=text).get_json()
        by_skill = {r['skill_id']: r['requirement_id'] for r in initial['requirements']}
        self.assertTrue(all(a['kind'] == 'clarify_evidence' for a in initial['action_plan']['actions']))
        evidence = {by_skill['sql']: {'status': 'missing'},
                    by_skill['python']: {'status': 'supported', 'note': 'PRIVATE_TEST_EVIDENCE'}}
        assessed = self.post('readiness', text=text, evidence=evidence).get_json()
        self.assertEqual(len(assessed['action_plan']['actions']), 1)
        self.assertEqual(assessed['action_plan']['actions'][0]['skill_id'], 'sql')
        self.assertIn('window functions', assessed['action_plan']['actions'][0]['project_brief'])
        self.assertEqual(assessed['assessment']['alignment_pct'], 25)
        scenario = self.post('readiness', text=text, evidence=evidence,
            hypothetical={'requirement_id': by_skill['sql'], 'note': 'PLANNED_TEST_EVIDENCE'}).get_json()
        self.assertEqual(scenario['scenario']['alignment_pct'], 100)
        self.assertEqual(scenario['assessment']['alignment_pct'], 25)
        self.assertEqual(scenario['action_plan'], assessed['action_plan'])
        self.assertNotIn('PRIVATE_TEST_EVIDENCE', json.dumps(scenario['report']))
        self.assertNotIn('PLANNED_TEST_EVIDENCE', json.dumps(scenario['report']))
        corrected = self.post('readiness', text=text, evidence=evidence,
            classifications={by_skill['sql']: 'negated'}).get_json()
        self.assertEqual(corrected['action_plan']['actions'], [])
        self.assertEqual(corrected['assessment']['total_weight'], 1)

    def test_scenarios_are_deterministic_and_labelled(self):
        payload={'scenario':{'people':50,'seed':42,'years':3}}
        first=self.post('mobility',**payload).get_json()
        second=self.post('mobility',**payload).get_json()
        self.assertEqual(first,second)
        self.assertEqual(first['metrics']['events'],100)
        self.assertIn('Synthetic',first['metadata']['data_label'])
        self.assertEqual(sum(f['events'] for f in first['flows']),100)

    def test_empty_and_sparse_mobility_suppress_aggregate_salary(self):
        data=self.post('mobility',scenario={'people':50,'years':3},filters={'origin':'Not an occupation'}).get_json()
        self.assertEqual(data['metrics']['events'],0)
        self.assertIsNone(data['metrics']['median_individual_pct_change'])
        self.assertEqual(data['distributions'],{'before':[],'after':[]})
        data=self.post('mobility',scenario={'people':50,'years':3}).get_json()
        for flow in data['flows']:
            if flow['valid_pairs']<20:
                self.assertIsNone(flow['median_individual_pct_change'])

    def test_validation_and_resource_limits(self):
        requests=[('diagnostic',{'text':''}),('diagnostic',{'text':'x'*30001}),
                  ('mobility',{'scenario':{'people':5000}}),('mobility',{'scenario':{'seed':True}}),
                  ('mobility',{'scenario':{'promotion_pct':float('nan')}}),
                  ('constellation',{'min_pair_count':-1}),('unknown',{})]
        for action,payload in requests:
            with self.subTest(action=action,payload_keys=list(payload)):
                response=self.post(action,**payload)
                self.assertEqual(response.status_code,400)
                self.assertNotIn('Traceback',response.get_data(as_text=True))
        self.assertEqual(self.client.post('/api/index',data='not json',content_type='application/json').status_code,400)
        self.assertEqual(self.client.post('/api/index',data='x'*70000,content_type='application/json').status_code,413)
        self.assertEqual(self.client.get('/api/index?action=diagnostic').status_code,405)
