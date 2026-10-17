import json
from pathlib import Path
import tempfile
import unittest

from career_radar.apify_import import import_export, normalise_export


def sample_job():
    return {
        "id": "example-42", "jobUrl": "https://www.linkedin.com/jobs/view/example-42/?tracking=test",
        "title": "Business Analyst", "companyName": "Example", "location": "Dublin, Ireland",
        "description": "Gather requirements and use SQL.", "publishedAt": "2026-10-15",
        "posterFullName": "Excluded Person", "posterProfileUrl": "https://example.test/profile",
        "scrapingInfo": {"title": "Product Analyst", "location": "Dublin, Ireland"},
    }


class ApifyImportTests(unittest.TestCase):
    def test_import_keeps_job_evidence_and_excludes_profile_fields(self):
        result = normalise_export([sample_job()])[0]
        self.assertEqual(result["canonical_url"], "https://www.linkedin.com/jobs/view/example-42")
        self.assertEqual(result["description_text"], "Gather requirements and use SQL.")
        self.assertEqual(result["title"], "Business Analyst")
        self.assertNotIn("posterFullName", result)
        self.assertEqual(len(result), 7)

    def test_invalid_or_out_of_scope_records_fail_before_writing(self):
        for changes in ({"location": "Dublin, Ohio, United States"}, {"description": ""},
                        {"jobUrl": "javascript:alert(1)"}, {"description": {"nested": "text"}}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                normalise_export([{**sample_job(), **changes}])

    def test_provenance_preserves_unknown_collection_time_and_query_separately(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "export.json"
            source.write_text(json.dumps([sample_job()]))
            output = import_export(source, root / "import")
            provenance = json.loads((output.parent / "provenance.json").read_text())
            self.assertIsNone(provenance["collection_timestamp"])
            self.assertEqual(provenance["job_searches"][0]["searched_title"], "Product Analyst")
            self.assertEqual(provenance["data_status"], "unreviewed")
            self.assertNotIn("Excluded Person", output.read_text())
            self.assertNotIn("Excluded Person", json.dumps(provenance))
            with self.assertRaises(FileExistsError):
                import_export(source, output.parent)

    def test_timezone_required_for_collection_time(self):
        with self.assertRaises(ValueError):
            import_export(Path("unused.json"), Path("unused"), "2026-10-18T12:00:00")
