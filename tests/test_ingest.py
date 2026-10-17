import csv
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class IngestTests(unittest.TestCase):
    def test_same_job_in_two_searches_is_counted_once_when_description_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "jobs.csv"
            first = {
                "source_job_id": "same-job", "canonical_url": "https://example.test/job/1",
                "title": "Software Engineer", "employer_name": "Example",
                "location_text": "Cork, Ireland", "description_text": "Use Java and Docker.",
            }
            with source.open("w", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=list(first))
                writer.writeheader()
                writer.writerows([first, {**first, "description_text": "Use Java and Docker. Apply now."}])
            subprocess.run(
                [sys.executable, "-m", "career_radar.ingest", "--input", str(source),
                 "--source-name", "Test fixture", "--output-dir", str(root / "output")],
                cwd=ROOT, env=dict(os.environ, PYTHONPATH=str(ROOT / "src")),
                check=True, capture_output=True,
            )
            manifest = json.loads(next((root / "output").glob("ingestion_manifest_*.json")).read_text())
            self.assertEqual(manifest["source_row_count"], 2)
            self.assertEqual(manifest["unique_job_count"], 1)
            self.assertEqual(manifest["duplicates_removed"], 1)
            self.assertEqual(manifest["extraction_version"], "taxonomy-v2-tech")
