"""Reproducible synthetic HTTP-boundary timings; excludes hosting and browser paint."""
from datetime import datetime
import json
import math
from pathlib import Path
import platform
import statistics
import sys
from time import perf_counter
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from api.index import app


def main():
    client = app.test_client()
    workloads = [
        ('bootstrap', None),
        ('constellation', {'action':'constellation'}),
        ('filtered_constellation', {'action':'constellation','geography':'Dublin'}),
        ('diagnostic', {'action':'diagnostic','text':'SQL required. Python preferred. Dublin, permanent, hybrid. You will create reports.'}),
        ('readiness', {'action':'readiness','text':'SQL required. Python preferred.'}),
        ('mobility', {'action':'mobility','scenario':{'seed':42,'people':500,'years':5}}),
        ('filtered_mobility', {'action':'mobility','scenario':{'seed':42,'people':500,'years':5},'filters':{'origin':'Data Analyst'}}),
    ]
    report = {'measured_at':datetime.now(ZoneInfo('Europe/Dublin')).isoformat(),
              'python':platform.python_version(), 'platform':platform.system()+' '+platform.machine(),
              'method':'Flask test client, one first measured request then 10 repeated requests per workload; p95 nearest rank.',
              'scope':'Local synthetic API only. Excludes Python startup, network, hosted cold starts, browser rendering and animation.',
              'workloads':[]}
    for name, payload in workloads:
        times = []
        sizes = []
        for _ in range(11):
            start = perf_counter()
            response = client.get('/api/index?action=bootstrap') if payload is None else client.post('/api/index',json=payload)
            elapsed = (perf_counter()-start)*1000
            if response.status_code != 200:
                raise RuntimeError(f'{name} returned HTTP {response.status_code}')
            times.append(elapsed)
            sizes.append(len(response.data))
        warm = sorted(times[1:])
        report['workloads'].append({'name':name,'repeats':10,'first_request_ms':round(times[0],2),
            'p50_ms':round(statistics.median(warm),2),'p95_ms':round(warm[math.ceil(.95*len(warm))-1],2),
            'max_response_bytes':max(sizes)})
    output = ROOT / 'data/validation/platform-benchmark.json'
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
