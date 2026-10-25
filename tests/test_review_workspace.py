import copy
import csv
import io
import json
import unittest

from career_radar.build_snapshot import build_snapshot_payload
from career_radar.review_workspace import (load_queue_csv, queue_fingerprint, initial_annotations,
    annotate, evaluate_workspace, export_checkpoint, restore_checkpoint, export_review_csv, review_progress)
from career_radar.validation import build_review_queue, evaluate_review, review_dataset_fingerprint


def sample(size=3):
    jobs = [{'source_job_id':str(i),'canonical_url':f'https://example.test/{i}',
             'title':'Data Analyst','employer_name':'Fictional employer','location_text':'Dublin, Ireland',
             'description_text':'SQL is essential.','role_name':'Data Analyst','work_pattern':'unknown',
             'source_name':'Fixture'} for i in range(size)]
    evidence = [{'canonical_url':j['canonical_url'],'skill_id':'sql','skill_name':'SQL',
                 'category':'Data','source_phrase':'SQL','extraction_method':'rule',
                 'extraction_version':'taxonomy-v2-tech'} for j in jobs]
    return jobs, evidence


def csv_bytes(rows):
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output,fieldnames=list(rows[0]))
    writer.writeheader();writer.writerows(rows)
    return output.getvalue().encode()


class ReviewWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.jobs,self.evidence=sample()
        self.queue=load_queue_csv(csv_bytes(build_review_queue(self.jobs,self.evidence)))
        self.annotations=initial_annotations(self.queue)
        self.identifier=self.queue[0]['review_id']

    def test_no_labels_are_generated_and_uncertain_is_not_a_precision_failure(self):
        self.assertEqual(review_progress(self.queue,self.annotations)['unreviewed'],3)
        updated=annotate(self.queue,self.annotations,self.identifier,'uncertain','Need more context')
        evaluation=evaluate_workspace(self.queue,updated)
        self.assertEqual(evaluation['reviewed_count'],0)
        self.assertEqual(evaluation['uncertain_count'],1)
        self.assertFalse(evaluation['publication_threshold_met'])
        self.assertEqual(self.annotations[self.identifier]['status'],'unreviewed')

    def test_checkpoint_roundtrip_and_reordered_queue_preserve_manual_work(self):
        changed=annotate(self.queue,self.annotations,self.identifier,'rejected','Wrong contextual meaning')
        saved=export_checkpoint(self.queue,changed)
        self.assertEqual(restore_checkpoint(list(reversed(self.queue)),saved),changed)
        decoded=json.loads(saved)
        self.assertNotIn('source_phrase',json.dumps(decoded))
        self.assertNotIn('https://example.test',json.dumps(decoded))
        imported=load_queue_csv(export_review_csv(self.queue,changed))
        self.assertEqual(initial_annotations(imported),changed)
        self.assertEqual(queue_fingerprint(imported),queue_fingerprint(self.queue))

    def test_checkpoint_cannot_reuse_decisions_after_source_or_rule_changes(self):
        saved=export_checkpoint(self.queue,self.annotations)
        for field in ['context','source_phrase','canonical_url','extraction_version','dataset_fingerprint']:
            changed=copy.deepcopy(self.queue);changed[0][field]+=' changed'
            with self.subTest(field=field),self.assertRaises(ValueError):
                restore_checkpoint(changed,saved)

    def test_duplicate_rows_cannot_inflate_review_counts(self):
        row={**self.queue[0],'reviewer_label':'accepted'}
        with self.assertRaises(ValueError):
            load_queue_csv(csv_bytes([row]*100))
        with self.assertRaises(ValueError):
            evaluate_review([row]*100)
        copy_id={**row,'review_id':'another'}
        with self.assertRaises(ValueError):
            evaluate_review([row,copy_id])

    def test_annotations_and_imports_are_bounded_and_strict(self):
        for status,notes in [('accepted','x'*1001),('invented',''),([],''),('accepted',{})]:
            with self.subTest(status=status),self.assertRaises(ValueError):
                annotate(self.queue,self.annotations,self.identifier,status,notes)
        with self.assertRaises(ValueError):load_queue_csv(b'x'*(4*1024*1024+1))
        with self.assertRaises(ValueError):load_queue_csv(b'review_id,review_id\n1,1\n')
        checkpoint=json.loads(export_checkpoint(self.queue,self.annotations));checkpoint['annotations']['forged']={'status':'accepted','notes':''}
        with self.assertRaises(ValueError):restore_checkpoint(self.queue,json.dumps(checkpoint).encode())

    def test_legacy_csv_remains_reviewable_but_cannot_supply_an_applicable_gate(self):
        legacy=[{k:v for k,v in row.items() if k not in {'dataset_fingerprint','population_categories','population_extraction_versions'}} for row in self.queue]
        queue=load_queue_csv(csv_bytes(legacy))
        result=evaluate_workspace(queue,initial_annotations(queue))
        self.assertFalse(result['review_lineage_valid'])
        self.assertTrue(any('lineage' in reason for reason in result['gate_reasons']))

    def test_genuine_100_record_review_binds_to_dataset_and_not_a_later_snapshot(self):
        jobs,evidence=sample(100)
        rows=build_review_queue(jobs,evidence)
        for row in rows:row['reviewer_label']='accepted'
        evaluation=evaluate_review(rows)
        self.assertTrue(evaluation['publication_threshold_met'])
        self.assertTrue(build_snapshot_payload(jobs,evidence,'Fixture','validated',evaluation=evaluation)['metadata']['publish_allowed'])
        changed=copy.deepcopy(jobs);changed[0]['description_text']='SQL preferred; source revised.'
        self.assertFalse(build_snapshot_payload(changed,evidence,'Fixture','validated',evaluation=evaluation)['metadata']['publish_allowed'])
        self.assertEqual(review_dataset_fingerprint(jobs,evidence),review_dataset_fingerprint(list(reversed(jobs)),list(reversed(evidence))))
        self.assertFalse(build_snapshot_payload(jobs,evidence,'Fixture','unreviewed',evaluation=evaluation)['metadata']['publish_allowed'])

    def test_unreviewed_population_versions_and_categories_keep_gate_closed(self):
        jobs,evidence=sample(101)
        evidence[-1].update(category='New category',extraction_version='new-rules')
        rows=build_review_queue(jobs,evidence,sample_size=101)
        for row in rows:
            row['reviewer_label']='accepted' if row['category']=='Data' else ''
        result=evaluate_review(rows)
        self.assertEqual(result['reviewed_count'],100)
        self.assertEqual(result['precision_pct'],100)
        self.assertFalse(result['publication_threshold_met'])
        self.assertIn('New category',result['unreviewed_population_categories'])

    def test_export_allowlist_drops_unrelated_imported_profile_fields(self):
        rows=[{**r,'api_token':'DO_NOT_KEEP','recruiter_name':'DO_NOT_KEEP'} for r in self.queue]
        queue=load_queue_csv(csv_bytes(rows))
        self.assertNotIn('DO_NOT_KEEP',export_review_csv(queue,initial_annotations(queue)).decode())

    def test_large_or_malformed_csv_cells_have_recoverable_errors(self):
        oversized=[{**self.queue[0],'context':'x'*140000}]
        with self.assertRaises(ValueError):load_queue_csv(csv_bytes(oversized))
        with self.assertRaises(ValueError):load_queue_csv(b'"unterminated')

    def test_cli_scoring_cannot_count_uncertain_records_with_stale_accepted_labels(self):
        row={**self.queue[0],'reviewer_label':'accepted','review_status':'uncertain'}
        with self.assertRaises(ValueError):evaluate_review([row])

    def test_reviewed_evidence_membership_is_checked_not_only_a_copied_dataset_token(self):
        jobs,evidence=sample(100)
        for field in ('skill_id','skill_name','source_phrase','context','job_title','employer_name'):
            rows=build_review_queue(jobs,evidence)
            for row in rows:
                row['reviewer_label']='accepted'
                row[field]='Changed after the queue was prepared'
            report=evaluate_review(rows)
            self.assertTrue(report['publication_threshold_met'])
            with self.subTest(field=field):
                self.assertFalse(build_snapshot_payload(jobs,evidence,'Fixture','validated',evaluation=report)['metadata']['publish_allowed'])

    def test_precision_display_rounding_cannot_pass_a_below_threshold_review(self):
        jobs,evidence=sample(999)
        rows=build_review_queue(jobs,evidence,sample_size=999)
        for index,row in enumerate(rows):row['reviewer_label']='accepted' if index<899 else 'rejected'
        result=evaluate_review(rows)
        self.assertEqual(result['precision_pct'],90.0)
        self.assertFalse(result['publication_threshold_met'])
