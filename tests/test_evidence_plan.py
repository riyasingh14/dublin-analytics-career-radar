"""Hand-reconciled skill buckets and safe, conservative evidence actions."""
import copy
import json
import unittest

from career_radar.evidence_plan import build_evidence_plan
from career_radar.readiness import assess_readiness, export_analysis


def requirement(identifier, skill, kind="required"):
    return {"requirement_id": identifier, "skill_id": skill, "skill_name": skill.upper(),
            "requirement_type": kind, "source_phrase": "PRIVATE_AD_PHRASE",
            "source_text": "PRIVATE_AD_CONTEXT"}


class EvidencePlanTests(unittest.TestCase):
    def test_weighted_buckets_reconcile_with_repeated_and_excluded_requirements(self):
        requirements = [requirement("s1", "sql"), requirement("s2", "sql"),
                        requirement("s3", "sql", "preferred"), requirement("p", "python"),
                        requirement("e", "excel", "preferred"), requirement("g", "git", "preferred"),
                        requirement("r", "r", "negated")]
        evidence = {"s1": {"status": "supported", "note": "Reconciled analysis"},
                    "s2": {"status": "missing"}, "p": {"status": "partial", "note": "Transformations only"},
                    "e": {"status": "missing"}}
        result = assess_readiness(requirements, evidence)
        self.assertEqual(result["confirmed_skill_count"], 4)
        self.assertEqual(result["total_weight"], 8)
        self.assertEqual(result["assessed_weight"], 7)
        self.assertEqual(result["earned_weight"], 1.5)
        self.assertAlmostEqual(result["alignment_pct"], 100 * 1.5 / 7)
        self.assertEqual(result["evidence_breakdown"], {
            "supported": {"skill_count": 0, "weight": 0},
            "partial": {"skill_count": 1, "weight": 3},
            "missing": {"skill_count": 2, "weight": 4},
            "unknown": {"skill_count": 1, "weight": 1},
        })
        sql = next(s for s in result["skill_summary"] if s["skill_id"] == "sql")
        self.assertEqual(sql["requirement_ids"], ["s1", "s2"])
        self.assertEqual(sql["status"], "missing")

    def test_unknown_evidence_prompts_review_instead_of_inventing_a_skill_deficit(self):
        requirements = [requirement("p", "python"), requirement("s", "sql"),
                        requirement("e", "excel", "preferred")]
        assessment = assess_readiness(requirements, {
            "s": {"status": "supported", "note": ""}, "p": {"status": "missing"},
            "e": {"status": "missing"}})
        plan = build_evidence_plan(assessment, {"sql": "Build SQL work", "python": "Test a pipeline"})
        self.assertEqual([a["skill_id"] for a in plan["actions"]], ["sql", "python", "excel"])
        self.assertEqual(plan["actions"][0]["kind"], "clarify_evidence")
        self.assertIsNone(plan["actions"][0]["project_brief"])
        self.assertEqual(plan["actions"][1]["project_brief"], "Test a pipeline")
        self.assertIsNone(assessment["alignment_pct"])

    def test_supported_skills_and_weaker_repeats_do_not_generate_spurious_projects(self):
        requirements = [requirement("s1", "sql"), requirement("s2", "sql", "preferred"),
                        requirement("r", "r", "uncertain")]
        result = assess_readiness(requirements, {"s1": {"status": "supported", "note": "Tested SQL project"},
                                                  "s2": {"status": "missing"}})
        self.assertEqual(result["alignment_pct"], 100)
        self.assertEqual(build_evidence_plan(result, {})["actions"], [])

    def test_plan_and_report_are_nonmutating_and_omit_private_text(self):
        requirements = [requirement("s", "sql")]
        evidence = {"s": {"status": "partial", "note": "PRIVATE_CANDIDATE_NOTE"}}
        result = assess_readiness(requirements, evidence)
        before = copy.deepcopy(result)
        plan = build_evidence_plan(result, {"sql": "Build a documented SQL analysis"})
        report = {**export_analysis(result), "action_plan": plan}
        encoded = json.dumps(report)
        for text in ["PRIVATE_AD_PHRASE", "PRIVATE_AD_CONTEXT", "PRIVATE_CANDIDATE_NOTE"]:
            self.assertNotIn(text, encoded)
        self.assertEqual(result, before)
        self.assertTrue(any("CTE" in check for check in plan["actions"][0]["completion_checks"]))
        plan["actions"][0]["requirement_ids"].append("client-edit")
        self.assertEqual(result, before)

    def test_empty_and_unconfirmed_samples_have_no_actions_or_weight(self):
        for requirements in [[], [requirement("n", "sql", "negated")]]:
            result = assess_readiness(requirements)
            self.assertEqual(sum(b["weight"] for b in result["evidence_breakdown"].values()), 0)
            self.assertEqual(build_evidence_plan(result, {})["actions"], [])
