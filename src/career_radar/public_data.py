"""Explicit public dataset selection; never read private research snapshots."""
from functools import lru_cache
from pathlib import Path
import os
import re

from career_radar.approved_release import load_approved_release
from career_radar.constellation_comparison_demo import comparison_demo
from career_radar.demo import constellation_demo
from career_radar.normalise import load_taxonomy

ROOT = Path(__file__).resolve().parents[2]


class PublicDataUnavailable(RuntimeError):
    """Configured public artefact cannot be served; callers must fail closed."""


@lru_cache(maxsize=1)
def _fixtures():
    taxonomy = load_taxonomy(ROOT / 'data/reference/skills.csv')
    return constellation_demo(taxonomy), comparison_demo(taxonomy)


def public_dataset():
    release_id = os.environ.get('CAREER_RADAR_PUBLIC_RELEASE', '')
    if not release_id:
        snapshot, comparison = _fixtures()
        return {'snapshot': snapshot, 'comparison': comparison, 'release': None, 'data_mode': 'synthetic-demo'}
    try:
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,62}', release_id):
            raise ValueError('Invalid selector')
        root = ROOT / 'data/releases'
        directory = root / release_id
        if root.resolve() != root or directory.is_symlink() or directory.resolve().parent != root:
            raise ValueError('Invalid release location')
        # Revalidate each request, including expiry. No private-path override or demo fallback.
        bundle = load_approved_release(directory)
        manifest = bundle['release']
        if manifest['release_id'] != release_id:
            raise ValueError('Release identity mismatch')
        summary = {key: manifest[key] for key in ('release_id', 'dataset_label', 'published_at', 'collected_from', 'collected_through', 'expires_at', 'snapshot_sha256')}
        summary['sources'] = [{key: source[key] for key in ('source_name', 'homepage_url', 'terms_url', 'terms_reviewed_on')} for source in manifest['sources']]
        return {'snapshot': bundle['snapshot'], 'comparison': bundle['snapshot'], 'release': summary, 'data_mode': 'reviewed-sample'}
    except (OSError, ValueError, TypeError, KeyError) as error:
        raise PublicDataUnavailable('The configured market release is unavailable.') from error
