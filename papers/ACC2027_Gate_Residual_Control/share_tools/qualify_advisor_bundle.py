"""Qualification of the staged bundle, using its newly installed environment."""
from pathlib import Path
import csv
import hashlib
import json
import os
import subprocess
import sys
import time

REPO = Path(__file__).resolve().parents[1]
STAGE = REPO/'share/advisor_reproducibility_2026-09-04/_build/ACC2027_CODE'
PY = STAGE/'.venv/Scripts/python.exe'
NEF = STAGE/'project/experiments/nengo_nef_replication_2026-08-29'
report = {'scope': 'Fresh Windows Python 3.13.11 venv; original CSVs and physical hardware untouched.', 'tests': []}
log = STAGE/'QUALIFICATION.log'


def run(label, cmd):
    print('QUALIFY:', label, flush=True)
    start = time.perf_counter()
    with log.open('a', encoding='utf-8') as f:
        f.write('\n=== '+label+' ===\n')
        f.flush()
        proc = subprocess.run([str(c) for c in cmd], cwd=STAGE, stdout=f, stderr=subprocess.STDOUT)
    report['tests'].append({'test': label, 'exit_code': proc.returncode, 'wall_seconds': time.perf_counter()-start})
    (STAGE/'QUALIFICATION.json').write_text(json.dumps(report, indent=2)+'\n')
    if proc.returncode:
        raise SystemExit(f'Failed: {label}. See {log}')


run('pip dependency consistency', [PY, '-m', 'pip', 'check'])
run('fresh-environment core/neuron/GUI/dual-platform smoke suite',
    [PY, STAGE/'reproduce.py', 'smoke', '--output', STAGE/'reproduced/qualification_fresh'])
run('relocated Hover engine, PD and Nengo, emulated I/O only',
    [PY, STAGE/'reproduce.py', 'hover-emulated', '--mission', 'roll', '--duration', '.1',
     '--output', STAGE/'reproduced/qualification_fresh'])
run('legacy dependencies and all three comparison routes, short smoke only',
    [PY, STAGE/'reproduce.py', 'legacy', '--duration', '.1', '--output', STAGE/'reproduced/qualification_fresh'])
for platform in ['x2', 'cf2-rotor']:
    run(platform+' full 45-s Nengo Hard45 regression',
        [PY, STAGE/'reproduce.py', 'single', '--platform', platform, '--mission', 'hard45',
         '--output', STAGE/'reproduced/qualification_full'])

with (REPO/'experiments/nengo_nef_replication_2026-08-29/results/compiled/matched_results.csv').open(newline='') as f:
    expected = {r['platform']: float(r['nengo_mean_rad']) for r in csv.DictReader(f) if r['mission'] == 'hard45'}
for platform, target in expected.items():
    path = STAGE/'reproduced/qualification_full/single'/platform/'hard45/nengo-nef-pes/summary.json'
    value = json.loads(path.read_text())['qerr_mean_rad']
    rel = abs(value-target)/abs(target)
    report['tests'].append({'test': platform+' 45-s saved mean comparison', 'actual': value,
                            'saved': target, 'relative_difference': rel, 'tolerance': 1e-5})
    if rel > 1e-5:
        raise SystemExit(f'Full-run regression mismatch: {platform}, {rel}')
report['status'] = 'PASS'
report['not_tested'] = ['Physical Q8 actuation', 'interactive 3D viewer rendering',
                      'all 110 full-length neuron-family cases in the fresh environment',
                      'full-length legacy annealing results', 'cross-OS bitwise equivalence']
report['known_metadata_issue'] = 'The unchanged run_mujoco_nef.py can label direct-online-pes controller_backend as Nengo. The controller field and _build_augmentor select the actual direct NumPy implementation. No algorithm changed to hide this inherited metadata issue.'
(STAGE/'QUALIFICATION.json').write_text(json.dumps(report, indent=2)+'\n')

# Include the newly added figure source in the provenance map.
source = REPO/'paper/tools/plot_v5_evidence.py'
with (STAGE/'SOURCE_MAP.csv').open(newline='') as f:
    rows = list(csv.DictReader(f))
rel = 'project/paper/tools/plot_v5_evidence.py'
if not any(r['bundle_path'] == rel for r in rows):
    rows.append({'source': str(source), 'bundle_path': rel,
                 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'change': 'none'})
with (STAGE/'SOURCE_MAP.csv').open('w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print(json.dumps(report, indent=2), flush=True)
