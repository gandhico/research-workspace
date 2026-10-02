"""Freeze checksums, validate completed run contracts, and summarize evidence."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
import sweep
import focused

HERE=Path(__file__).resolve().parent
OUT=HERE/'analysis'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

df=pd.read_csv(OUT/'all_completed_cases.csv')
checks=json.loads((OUT/'archive_checks.json').read_text())
assert len(df)==71 and len(checks)==59
assert df.n_steps.eq(90000).all() and df.logged_steps.eq(9000).all()
assert df.dt.eq(.0005).all() and df.duration.eq(45).all()
assert df.baseline_mean_rad.notna().all() and df.improvement_pct.notna().all()
assert all(c['archive_finite'] for c in checks)
assert max(c['pes_increment_max_abs_mismatch'] for c in checks)<1e-12
assert max(c.get('gate_step_max_abs_mismatch',0) for c in checks)<1e-12
assert max(c.get('membrane_step_max_abs_mismatch',0) for c in checks)<1e-12
assert all((HERE/'results'/sweep.case_id(c)/'sweep_manifest.json').exists() for c in focused.cases())

neural=[]
for s in df[df.backend=='nengo'].itertuples():
    with np.load(s.neural_trace_full_rate) as d:
        assert len(d['t'])==90000
        assert all(np.isfinite(d[k]).all() for k in d.files)
        assert d['weights'].shape==(90000,3,6)
        assert d['activity'].shape==(90000,6)
        neural.append(dict(case=s.case_id,signals=list(d.files),samples=90000))

source_versions={}
reproduction_cases=[]
for p in (HERE/'results').glob('*/sweep_manifest.json'):
    m=json.loads(p.read_text())
    reproduction_cases.append(m['case'])
    for path,h in m['source_sha256'].items():
        if 'gate_gain_sweep_2026-09-11' not in path:
            source_versions.setdefault(path,set()).add(h)
assert all(len(v)==1 for v in source_versions.values()),'Canonical source changed across cases'
assert all(sha(Path(k))==next(iter(v)) for k,v in source_versions.items()),'Canonical source no longer matches run hashes'
HERE.joinpath('reproduction_cases.json').write_text(json.dumps(reproduction_cases,indent=2))

manifest=[]
for p in sorted((HERE/'results').rglob('*')):
    if p.is_file():manifest.append(dict(path=str(p.relative_to(HERE)),bytes=p.stat().st_size,sha256=sha(p)))
OUT.joinpath('frozen_result_manifest.json').write_text(json.dumps(manifest,indent=2))
summary=dict(completed_mujoco_runs=71,counts_by_backend=df.groupby('backend').size().to_dict(),
             total_plant_steps=int(df.n_steps.sum()),plant_trace_sample_interval_s=.005,
             neural_archive_sample_interval_s=.0005,full_rate_neural_archives=67,
             canonical_sources_unchanged=True,canonical_hashes={k:next(iter(v)) for k,v in source_versions.items()},
             max_direct_pes_increment_mismatch=max(c['pes_increment_max_abs_mismatch'] for c in checks),
             max_gate_step_mismatch=max(c.get('gate_step_max_abs_mismatch',0) for c in checks),
             max_membrane_step_mismatch=max(c.get('membrane_step_max_abs_mismatch',0) for c in checks),
             max_constant_activity_recursion_mismatch=max(c['saturated_filter_recursion_max_abs_mismatch'] or 0 for c in checks),
             nengo_archive_checks=neural,
             max_nengo_direct_relative_mean_difference=float(pd.read_csv(OUT/'backend_checks.csv').relative_mean_difference.max()),
             result_bytes=sum(p['bytes'] for p in manifest),
             planned_full_factorial_completed=False,
             scope='Focused stage, completed Roll sensitivity curve, and explicitly adaptive development extensions; not all missions at every gain.')
OUT.joinpath('FINAL_VALIDATION.json').write_text(json.dumps(summary,indent=2))
print(json.dumps({k:v for k,v in summary.items() if k not in ['nengo_archive_checks','canonical_hashes']},indent=2))
