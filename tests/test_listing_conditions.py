"""Listing cues preserve explicit text and never decide candidate eligibility."""
import unittest
from career_radar.listing_conditions import extract_listing_conditions


class ListingConditionTests(unittest.TestCase):
    def test_each_category_keeps_literal_source_and_no_score(self):
        text = "SQL required.\nA degree or equivalent experience is preferred.\nAt least 3 years of experience. Based in Dublin. Right to work in Ireland."
        rows = extract_listing_conditions(text)
        self.assertEqual({r['category'] for r in rows}, {'degree', 'experience', 'location', 'work_eligibility'})
        for row in rows:
            self.assertEqual(text[row['start']:row['end']], row['source_text'])
            self.assertEqual(row['status'], 'unknown')
            self.assertTrue(row['needs_manual_review'])
            self.assertTrue(row['excluded_from_index'])
        self.assertFalse(any('SQL' in r['source_text'] for r in rows))

    def test_negation_alternatives_and_optional_language_not_resolved(self):
        text = 'No degree required. Visa sponsorship may be available. A degree or equivalent experience is accepted.'
        rows = extract_listing_conditions(text)
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(r['status'] == 'unknown' for r in rows))
        self.assertEqual(rows[0]['source_text'], 'No degree required.')

    def test_no_inference_from_job_title_or_demographics(self):
        self.assertEqual(extract_listing_conditions('Senior Data Analyst. University prestige is irrelevant. Age and nationality omitted.'), [])
        self.assertEqual(extract_listing_conditions(''), [])

    def test_experience_range_and_multicategory_literal_context(self):
        rows = extract_listing_conditions('2–5 years of relevant experience. Hybrid role in Dublin, Ireland.')
        self.assertEqual([r['category'] for r in rows], ['experience', 'location'])

    def test_archived_us_ad_citizenship_remains_a_literal_unassessed_condition(self):
        text='Open to U.S. citizens or nationals. One year of specialized experience is required.'
        rows=extract_listing_conditions(text)
        self.assertEqual([row['category'] for row in rows], ['work_eligibility','experience'])
        self.assertEqual(rows[0]['source_text'],'Open to U.S. citizens or nationals.')
        self.assertTrue(all(row['status']=='unknown' and row['excluded_from_index'] for row in rows))

    def test_decimal_grade_and_abbreviation_do_not_break_literal_spans(self):
        text='📊 Minimum GPA 3.5. Based in the U.K. office.'
        rows=extract_listing_conditions(text)
        self.assertEqual(rows[0]['source_text'],'📊 Minimum GPA 3.5.')
        self.assertEqual(rows[1]['source_text'],'Based in the U.K. office.')
        for row in rows:self.assertEqual(text[row['start']:row['end']],row['source_text'])

    def test_explicit_location_header_does_not_require_a_known_city_name(self):
        rows=extract_listing_conditions('Location: Washington, DC.')
        self.assertEqual(rows[0]['category'],'location')
        self.assertEqual(rows[0]['source_text'],'Location: Washington, DC.')

    def test_wrapped_citizenship_sentence_keeps_its_full_literal_context(self):
        text='Open to U.S. citizens or nationals (residents of American Samoa and Swains\nIsland).'
        rows=extract_listing_conditions(text)
        self.assertEqual(rows[0]['category'],'work_eligibility')
        self.assertEqual(rows[0]['source_text'],text)
        self.assertEqual(text[rows[0]['start']:rows[0]['end']],text)
