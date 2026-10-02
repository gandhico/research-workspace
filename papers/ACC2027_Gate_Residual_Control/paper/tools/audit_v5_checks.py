"""Read-only checks of experimental inputs; writes only the audit JSON output.

No simulator, controller, Q8, or hardware module is imported or executed.
These numerical algebra checks complement, and do not replace, the proofs.
"""
from pathlib import Path
import csv
import hashlib
import json
import re
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / 'paper'
NEF = ROOT / 'experiments/nengo_nef_replication_2026-08-29'
OUTPUT = ROOT / 'docs/ACC2027_V5_VALIDATION_2026-09-04.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mul(p, q):
    return np.r_[p[0]*q[0]-p[1:]@q[1:],
                 p[0]*q[1:]+q[0]*p[1:]+np.cross(p[1:], q[1:])]


def conj(q):
    return q * np.array([1., -1., -1., -1.])


def rotate(q, x):
    return mul(mul(q, np.r_[0., x]), conj(q))[1:]


def algebra_checks():
    rng = np.random.default_rng(20260904)
    worst = 0.
    for _ in range(1000):
        q, qd = rng.normal(size=(2, 4))
        q /= np.linalg.norm(q)
        qd /= np.linalg.norm(qd)
        w, wd = rng.normal(size=(2, 3))
        dq = -.5*mul(np.r_[0., w], q)
        dqd = -.5*mul(np.r_[0., wd], qd)
        qe = mul(qd, conj(q))
        product_derivative = mul(dqd, conj(q)) + mul(qd, conj(dq))
        we = w - rotate(conj(qe), wd)
        stated_derivative = .5*mul(qe, np.r_[0., we])
        worst = max(worst, float(np.max(np.abs(product_derivative-stated_derivative))))
    assert worst < 1e-12
    limits = rng.uniform(.001, 1., (10000, 3))
    u0 = rng.uniform(-1., 1., (10000, 3))*limits
    beta = rng.uniform(0., 1., (10000, 1))
    s = rng.uniform(-1., 1., (10000, 3))
    u = np.clip(u0 + beta*limits*s, -limits, limits)
    assert np.all(np.abs(u-u0) <= beta*limits+1e-14)
    assert np.all(np.abs(u) <= limits)
    a, z = rng.uniform(0, 1, (2, 6))
    W = rng.normal(0, .1, (3, 6))
    target = rng.normal(0, .1, 3)
    eta = .0008
    error = target-W@a
    Wnext = W+eta*np.outer(error, a)
    assert np.allclose(target-Wnext@a, (1-eta*(a@a))*error, atol=1e-14)
    Wtrace = W+eta*np.outer(error, z)
    assert np.allclose(target-Wtrace@a, (1-eta*(z@a))*error, atol=1e-14)
    return {'passive_quaternion_product_identity_max_abs_error': worst,
            'quaternion_cases': 1000, 'authority_bound_random_cases': 10000,
            'frozen_feature_PES_and_AAT_identities': 'PASS',
            'scope': 'Numerical algebra checks, not full-loop stability tests.'}


def main():
    with (NEF/'results/compiled/matched_results.csv').open(newline='') as stream:
        rows = [r for r in csv.DictReader(stream) if r['mission'] != 'hover']
    assert len(rows) == 10
    inputs = [PAPER/'ACC2027_v4.tex', PAPER/'references.bib',
              ROOT/'src/gra_control/gate.py', ROOT/'src/gra_control/platforms/drone.py',
              NEF/'nengo_cmg.py', NEF/'run_mujoco_nef.py',
              NEF/'results/compiled/matched_results.csv',
              NEF/'results/compiled/archived_equivalence.csv']
    validated = []
    for row in rows:
        bpath, npath = Path(row['baseline_run']), Path(row['nengo_run'])
        b = json.loads((bpath/'summary.json').read_text())
        n = json.loads((npath/'summary.json').read_text())
        for prefix, summary in [('baseline', b), ('nengo', n)]:
            assert np.isclose(float(row[prefix+'_mean_rad']), summary['qerr_mean_rad'], rtol=0, atol=1e-13)
            assert np.isclose(float(row[prefix+'_saturation_fraction']), summary['saturation_fraction'], rtol=0, atol=1e-13)
            assert summary['duration'] == 45 and summary['dt'] == .0005
        reduction = 100*(b['qerr_mean_rad']-n['qerr_mean_rad'])/b['qerr_mean_rad']
        assert abs(reduction-float(row['mean_improvement_percent'])) < 1e-10
        assert reduction > 0
        trace = np.genfromtxt(npath/'trace.csv', delimiter=',', names=True)
        assert len(trace) == n.get('logged_steps', n['n_steps'])
        assert np.isfinite(trace['qerr']).all()
        assert (np.diff(trace['t']) > 0).all()
        assert np.isclose(np.median(np.diff(trace['t'])), n.get('logged_dt', n['dt']))
        assert trace['t'][0] == 0 and trace['t'][-1] >= 44.99
        qe = np.column_stack([trace['qe_'+axis] for axis in ['w', 'x', 'y', 'z']])
        angle = 2*np.arctan2(np.linalg.norm(qe[:, 1:], axis=1), np.abs(qe[:, 0]))
        assert np.allclose(angle, trace['qerr'], rtol=0, atol=1e-7)
        if len(trace) == n['n_steps']:
            assert np.isclose(np.mean(trace['qerr']), n['qerr_mean_rad'], rtol=0, atol=1e-12)
        for j in range(6):
            assert np.isfinite(trace[f'voltage_{j}']).all()
            assert ((trace[f'gate_{j}'] >= 0) & (trace[f'gate_{j}'] <= 1)).all()
            assert np.allclose(trace[f'activity_{j}'], np.clip(1e5*trace[f'gate_{j}'], 0, 1), atol=1e-9)
        for j in range(18):
            assert (np.abs(trace[f'decoder_w_{j}']) <= 6+1e-12).all()
        inputs += [bpath/'summary.json', npath/'summary.json', npath/'trace.csv']
        validated.append({'platform': row['platform'], 'mission': row['mission'],
                          'baseline_mean_rad': b['qerr_mean_rad'], 'cmg_mean_rad': n['qerr_mean_rad'],
                          'reduction_percent': reduction,
                          'baseline_bound_occupancy_percent': 100*b['saturation_fraction'],
                          'cmg_bound_occupancy_percent': 100*n['saturation_fraction'],
                          'full_rate_summary_steps': n['n_steps'], 'logged_trace_steps': len(trace),
                          'logged_trace_end_s': float(trace['t'][-1]),
                          'logged_spacing_s': float(np.median(np.diff(trace['t'])))})
    tex = (PAPER/'ACC2027_v5_audited.tex').read_text()
    bib = (PAPER/'references_v5_audited.bib').read_text()
    cites = {k for group in re.findall(r'\\cite\{([^}]+)\}', tex) for k in group.split(',')}
    bibkeys = set(re.findall(r'@\w+\{([^,]+),', bib))
    assert cites <= bibkeys
    assert '\r' not in tex
    report = {'date': '2026-09-04', 'status': 'PASS', 'algebra': algebra_checks(),
              'canonical_cells': validated, 'resolved_bibliography_keys': sorted(cites),
              'trace_scope': 'Summaries use 90000 integration samples. Most saved traces are decimated to 9000 samples; X2 Hard45 retains all 90000. Full-rate means were cross-checked against summaries, not reconstructed from decimated traces.',
              'new_experiments_executed': False,
              'manuscript_sha256': sha(PAPER/'ACC2027_v5_audited.tex'),
              'curated_bibliography_sha256': sha(PAPER/'references_v5_audited.bib'),
              'source_sha256': {str(p): sha(p) for p in inputs}}
    OUTPUT.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'canonical_pairs': len(rows), 'nengo_trace_rows_checked': sum(c['logged_trace_steps'] for c in validated),
                      'output': str(OUTPUT), 'algebra': report['algebra']}, indent=2))


if __name__ == '__main__':
    main()
