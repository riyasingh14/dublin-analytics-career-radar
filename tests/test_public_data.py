"""Only artificial, test-authored review fixtures; no real data is released."""
from datetime import timedelta
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_approved_release import fixture, NOW
from career_radar.approved_release import prepare_approved_release, load_approved_release
from career_radar.public_data import public_dataset, PublicDataUnavailable
from career_radar.web_api import dispatch
from api.index import app


class PublicDataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        jobs, evidence, evaluation, policy = fixture()
        self.release_id = policy['release_id']
        self.directory = self.root / 'data/releases' / self.release_id
        prepare_approved_release(jobs, evidence, evaluation, policy, self.directory, now=NOW)
        self.now = NOW
        self.patch_root = patch('career_radar.public_data.ROOT', self.root)
        self.patch_root.start(); self.addCleanup(self.patch_root.stop)
        self.patch_clock = patch('career_radar.public_data.load_approved_release', side_effect=lambda path: load_approved_release(path, now=self.now))
        self.patch_clock.start(); self.addCleanup(self.patch_clock.stop)
        self.env = patch.dict('os.environ', {'CAREER_RADAR_PUBLIC_RELEASE': self.release_id})
        self.env.start(); self.addCleanup(self.env.stop)

    def test_explicit_release_uses_one_dataset_for_network_and_comparison(self):
        data = public_dataset()
        self.assertEqual(data['data_mode'], 'reviewed-sample')
        self.assertIs(data['snapshot'], data['comparison'])
        bootstrap = dispatch('bootstrap')
        self.assertEqual(bootstrap['snapshot']['market']['sample_size'], 101)
        self.assertEqual(bootstrap['release']['release_id'], self.release_id)
        self.assertNotIn('owner_approved', bootstrap['release'])
        self.assertNotIn('permission_basis', bootstrap['release']['sources'][0])
        result = dispatch('constellation')
        self.assertEqual(result['sample_size'], 101)
        self.assertEqual(sum(role['sample_size'] for role in result['role_comparison']['roles']), 101)
        self.assertEqual(result['jobs_with_skills'], 100)

    def test_health_bootstrap_and_constellation_fail_closed_with_no_path_leak(self):
        (self.directory / 'snapshot.json').write_text('corrupt')
        client = app.test_client()
        for action in ['health', 'bootstrap', 'constellation']:
            response = client.post('/api/index', json={'action': action})
            self.assertEqual(response.status_code, 503)
            self.assertNotIn(str(self.root), response.get_data(as_text=True))
            self.assertNotIn('fixture', response.get_data(as_text=True))
        # The private, user-provided analysis tools are independent of market release failures.
        self.assertEqual(client.post('/api/index', json={'action': 'diagnostic', 'text': 'SQL required.'}).status_code, 200)

    def test_warm_process_rechecks_expiration(self):
        self.assertEqual(dispatch('health')['status'], 'ok')
        self.now = NOW + timedelta(days=10)
        with self.assertRaises(PublicDataUnavailable):
            public_dataset()

    def test_selector_cannot_read_private_paths_or_symlinks(self):
        for value in ['../../raw/private', '/tmp/private', 'UPPERCASE', 'bad.json']:
            with patch.dict('os.environ', {'CAREER_RADAR_PUBLIC_RELEASE': value}):
                with self.assertRaises(PublicDataUnavailable):
                    public_dataset()
        alias = self.directory.parent / 'alias'
        alias.symlink_to(self.directory, target_is_directory=True)
        with patch.dict('os.environ', {'CAREER_RADAR_PUBLIC_RELEASE': 'alias'}):
            with self.assertRaises(PublicDataUnavailable):
                public_dataset()

    def test_no_selector_uses_demo_and_ignores_private_snapshot_paths(self):
        private = self.root / "private.json"
        private.write_text('{"private_marker":"NEVER_PUBLIC"}')
        with patch('career_radar.public_data.ROOT', Path(__file__).resolve().parents[1]), patch.dict('os.environ', {'CAREER_RADAR_PUBLIC_RELEASE': '', 'CAREER_RADAR_SNAPSHOT': str(private)}):
            result = dispatch('bootstrap')
            self.assertEqual(result['data_mode'], 'synthetic-demo')
            self.assertIsNone(result['release'])
            self.assertEqual(result['snapshot']['market']['sample_size'], 30)
            self.assertNotIn('NEVER_PUBLIC', str(result))
