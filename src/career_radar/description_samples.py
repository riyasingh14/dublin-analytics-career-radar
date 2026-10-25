"""Explicitly licensed archived descriptions, separate from market observations."""
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

CATALOG = Path(__file__).resolve().parents[2] / 'data/reference/job_description_samples.json'
FIELDS = ('id', 'title', 'organisation', 'geography', 'status', 'source_url', 'source_commit',
          'retrieved_on', 'license', 'license_url', 'text', 'content_sha256', 'derivation')


def load_description_samples(path: Path = CATALOG) -> list[dict]:
    payload = json.loads(path.read_text(encoding='utf-8'))
    if payload.get('catalog_version') != 'jd-references-v1' or not isinstance(payload.get('samples'), list) or len(payload['samples']) > 12:
        raise ValueError('Invalid description reference catalogue.')
    samples = []
    seen = set()
    for row in payload['samples']:
        if not isinstance(row, dict) or any(not isinstance(row.get(key), str) or not row[key].strip() for key in FIELDS):
            raise ValueError('Description reference metadata is incomplete.')
        if row['id'] in seen or row['status'] != 'archived' or row['license'] != 'CC0-1.0':
            raise ValueError('Unexpected description identity, status or licence.')
        if not 1000 <= len(row['text']) <= 30000:
            raise ValueError('Reference descriptions must contain a complete, bounded source document.')
        if hashlib.sha256(row['text'].encode('utf-8')).hexdigest() != row['content_sha256']:
            raise ValueError('Description reference content hash does not match.')
        for field in ('source_url', 'license_url'):
            url = urlsplit(row[field])
            if url.scheme != 'https' or url.hostname != 'github.com' or url.username or url.password or url.query or url.fragment or not url.path.startswith('/18F/join.tts.gsa.gov/blob/' + row['source_commit'] + '/'):
                raise ValueError('Reference links must identify the pinned official source archive.')
        seen.add(row['id'])
        samples.append({key: row[key] for key in FIELDS})
    return samples
