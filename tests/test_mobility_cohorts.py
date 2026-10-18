import unittest
from career_radar.mobility import Scenario, generate_histories, derive_transitions
from career_radar.mobility_cohorts import validate_filters, select_cohort, flow_metrics, cohort_details, origin_stayer_reference

class MobilityCohortTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = derive_transitions(generate_histories(Scenario(people=100)))

    def test_linked_flow_totals_reconcile_and_state_selection(self):
        flows = flow_metrics(self.rows)
        self.assertEqual(sum(row['events'] for row in flows), len(self.rows))
        first = flows[0]
        selected = select_cohort(self.rows, {}, first['origin'] + ' → ' + first['destination'])
        self.assertEqual(len(selected), first['events'])
        self.assertEqual(flow_metrics(selected)[0], first)

    def test_period_experience_and_state_filters_apply_together(self):
        filters = validate_filters({'year_min':'2023', 'year_max':'2023',
                                    'experience_min':'5', 'experience_max':'10', 'origin_seniority':'Mid'})
        selected = select_cohort(self.rows, filters)
        self.assertTrue(selected)
        self.assertTrue(all(row['date'].startswith('2023') and 5 <= row['experience_years'] <= 10
                            and row['origin_seniority'] == 'Mid' for row in selected))

    def test_stayers_preserve_state_flow_and_other_cohort_cuts(self):
        move = next(row for row in self.rows if row['origin_state'] != row['destination_state'])
        self.assertEqual(select_cohort(self.rows, {}, move['origin_state'] + ' → ' + move['destination_state'], 'Stayer'), [])
        selected = select_cohort(self.rows, {'geography':'Dublin', 'category':'employer'}, category='Stayer')
        self.assertTrue(selected)
        self.assertTrue(all(row['category'] == 'Stayer' and row['geography'] == 'Dublin' for row in selected))

    def test_small_flow_suppression_and_explicit_table_cap(self):
        rows = self.rows[:10]
        self.assertTrue(all(row['median_individual_pct_change'] is None for row in flow_metrics(rows)))
        details = cohort_details(self.rows)
        self.assertEqual(details['transition_rows_total'], 400)
        self.assertEqual(len(details['transition_rows']), 200)

    def test_invalid_or_inverted_bounds_rejected(self):
        for filters in ({'year_min':'2024', 'year_max':'2022'}, {'experience_min':'-1'}, {'unknown':''}):
            with self.assertRaises(ValueError):
                validate_filters(filters)


class OriginStayerReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = derive_transitions(generate_histories(Scenario(people=500)))

    def test_promotion_flow_has_relevant_origin_stayers(self):
        promotion = next(row for row in self.rows if row['promotion'] and row['geography'] == 'Dublin')
        filters = {'geography': 'Dublin', 'destination_seniority': promotion['destination_seniority'],
                   'year_min': promotion['date'][:4], 'year_max': promotion['date'][:4]}
        flow = promotion['origin_state'] + ' → ' + promotion['destination_state']
        cohort = select_cohort(self.rows, filters, flow)
        self.assertTrue(cohort)
        self.assertEqual(select_cohort(self.rows, filters, flow, category='Stayer'), [])
        reference = origin_stayer_reference(self.rows, filters, cohort)
        self.assertTrue(reference)
        self.assertTrue(all(row['category'] == 'Stayer' and row['geography'] == 'Dublin'
                            and row['date'] == promotion['date']
                            and row['origin_state'] == promotion['origin_state'] for row in reference))
        self.assertTrue(all(row['destination_state'] == row['origin_state'] for row in reference))

    def test_reference_retains_origin_industry_experience_and_period(self):
        stayer = next(row for row in self.rows if row['category'] == 'Stayer' and row['origin_industry'] == 'Technology')
        filters = {'origin_industry':stayer['origin_industry'], 'origin_seniority':stayer['origin_seniority'],
                   'experience_min':str(stayer['experience_years']), 'experience_max':str(stayer['experience_years']),
                   'year_min':stayer['date'][:4], 'year_max':stayer['date'][:4], 'geography':stayer['geography'],
                   'destination':'Unrelated occupation', 'category':'occupation'}
        selected = [row for row in self.rows if row['origin_state'] == stayer['origin_state']]
        reference = origin_stayer_reference(self.rows, filters, selected)
        self.assertTrue(reference)
        self.assertIn(stayer, reference)
        self.assertTrue(all(row['origin_industry'] == stayer['origin_industry']
                            and row['origin_seniority'] == stayer['origin_seniority']
                            and row['origin_state'] == stayer['origin_state'] and row['geography'] == stayer['geography']
                            and row['experience_years'] == stayer['experience_years'] and row['date'] == stayer['date']
                            for row in reference))

    def test_empty_selected_cohort_has_no_reference(self):
        self.assertEqual(origin_stayer_reference(self.rows, {}, []), [])
