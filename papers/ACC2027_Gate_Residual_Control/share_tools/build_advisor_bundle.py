"""Build scoped, lossless advisor archives; never modify research source/data."""
from pathlib import Path
import argparse
import csv
import hashlib
import importlib.metadata as md
import io
import json
import platform
import shutil
import subprocess
import sys
import zipfile

REPO = Path(__file__).resolve().parents[1]
TOOLS = Path(__file__).resolve().parent
OUT = REPO/'share/advisor_reproducibility_2026-09-04'
STAGE = OUT/'_build/ACC2027_CODE'
NEF = REPO/'experiments/nengo_nef_replication_2026-08-29'
HOVER = Path('C:/Research/hover3dof')
HNEF = HOVER/'nengo_gui_hil_2026-08-29'
LEGACY = Path('C:/Research/papers/P3_Gate_Residual/learned/code')
SKIP = {'__pycache__', '.git', '.venv', 'results', 'tmp', 'reproduced'}


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def csv_bytes(rows, fields=None):
    f = io.StringIO(newline='')
    w = csv.DictWriter(f, fieldnames=fields or list(rows[0]))
    w.writeheader()
    w.writerows(rows)
    return f.getvalue().encode('utf-8')


def prepare():
    if (STAGE/'SOURCE_MAP.csv').exists():
        raise SystemExit('Stage already exists; refusing to replace it.')
    STAGE.mkdir(parents=True, exist_ok=True)
    sources = []
    def copy(src, dest):
        target = STAGE/dest
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
        sources.append({'source': str(src), 'bundle_path': dest.as_posix(), 'source_sha256': digest(src), 'change': 'none'})
    def tree(src, dest, suffixes=None):
        for path in sorted(src.rglob('*')):
            rel = path.relative_to(src)
            if path.is_file() and not (set(rel.parts) & SKIP) and path.suffix != '.pyc':
                if suffixes is None or path.suffix in suffixes:
                    copy(path, dest/rel)
    for folder in ['src', 'models', 'configs', 'tests', 'third_party']:
        tree(REPO/folder, Path('project')/folder)
    for f in ['pyproject.toml', 'README.md']:
        copy(REPO/f, Path('project')/f)
    copy(REPO/'paper/tools/plot_v5_evidence.py', Path('project/paper/tools/plot_v5_evidence.py'))
    tree(REPO/'scripts', Path('project/scripts'), {'.py', '.ps1'})
    tree(NEF, Path('project/experiments')/NEF.name, {'.py', '.cfg', '.md'})
    copy(NEF/'feature_calibration.json', Path('project/experiments')/NEF.name/'feature_calibration.json')
    for f in ['ACC2027_V4_TO_V5_AUDIT_2026-09-04.md', 'FULL_PROJECT_AUDIT_2026-09-02.md',
              'FULL_PROJECT_RESULT_LEDGER_2026-09-02.csv', 'FULL_PROJECT_PARAMETER_LEDGER_2026-09-02.csv']:
        copy(REPO/'docs'/f, Path('documentation')/f)
    for f in ['hover_nengo_hil_gui.py', 'hover_nengo_hil_gui.py.cfg', 'launch_hover_nengo_gui.py',
              'run_hover_direct_nengo.py', 'run_hover_headless.py', 'nengo_gui_backend_50hz.py', 'LAB_RUNBOOK.md', 'README.md']:
        copy(HNEF/f, Path('hover3dof')/HNEF.name/f)
    tree(HOVER/'pd_cmg_focused_final_round_2026-08-28/src', Path('hover3dof/pd_cmg_focused_final_round_2026-08-28/src'), {'.py'})
    copy(HOVER/'docs/SAFETY_CHECKLIST.md', Path('hover3dof/SAFETY_CHECKLIST.md'))
    tree(LEGACY/'experiments/controller_benchmarks', Path('legacy/code/experiments/controller_benchmarks'), {'.py'})
    copy(LEGACY/'experiments/mujoco_stn_hyperlif_benchmark/stn_pid_attitude_controller.py',
         Path('legacy/code/experiments/mujoco_stn_hyperlif_benchmark/stn_pid_attitude_controller.py'))
    for model in ['skydio_x2', 'bitcraze_crazyflie_2']:
        tree(LEGACY/'third_party/mujoco_menagerie'/model, Path('legacy/code/third_party/mujoco_menagerie')/model)
    for f in ['LICENSE', 'CITATION.cff']:
        copy(LEGACY/'third_party/mujoco_menagerie'/f, Path('legacy/code/third_party/mujoco_menagerie')/f)
    # Mechanical relocation only, limited to two root constants in the packaged copy.
    engine = STAGE/'hover3dof'/HNEF.name/'hover_nengo_hil_gui.py'
    text = engine.read_text(encoding='utf-8')
    replacements = {
        'HOVER_ROOT = Path(r"C:\\Research\\hover3dof")': 'HOVER_ROOT = HERE.parent',
        'ACC_ROOT = Path(r"C:\\Research\\papers\\ACC2027_Gate_Residual_Control")': 'ACC_ROOT = HERE.parents[1] / "project"',
    }
    for old, new in replacements.items():
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    engine.write_text(text, encoding='utf-8')
    for row in sources:
        if row['bundle_path'] == engine.relative_to(STAGE).as_posix():
            row['change'] = 'Two absolute root constants relocated; no controller, timing, learning, safety, or I/O changes.'
    for f in ['reproduce.py', 'verify_archive.py']:
        shutil.copy2(TOOLS/f, STAGE/f)
    shutil.copy2(TOOLS/'CODE_README.md', STAGE/'README.md')
    freeze = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'], text=True)
    pins = '\n'.join(s for s in freeze.splitlines() if s and not s.startswith(('#', '-e ')))+'\n'
    (STAGE/'requirements-lock.txt').write_text(pins)
    versions = {name: md.version(name) for name in ['mujoco', 'numpy', 'nengo', 'nengo-gui', 'matplotlib', 'pandas', 'PyYAML', 'pip']}
    (STAGE/'ENVIRONMENT.json').write_text(json.dumps({'python': platform.python_version(),
        'system': platform.system(), 'machine': platform.machine(), 'packages': versions,
        'capture': 'Current functioning research environment; per-run manifests retain their recorded environment.'}, indent=2)+'\n')
    (STAGE/'SOURCE_MAP.csv').write_bytes(csv_bytes(sources))
    print('Code staged at', STAGE, flush=True)


def data_archive():
    entries = {}
    def add(path, dest):
        assert path.is_file(), path
        entries[dest.as_posix()] = path
    def tree(src, dest):
        for path in sorted(src.rglob('*')):
            if path.is_file() and path.suffix.lower() in {'.csv', '.json'} and 'plots' not in path.relative_to(src).parts:
                add(path, dest/path.relative_to(src))
    for sub in ['matched_45s', 'neuron_family_matched_45s', 'compiled', 'neuron_family_compiled']:
        tree(NEF/'results'/sub, Path('project/experiments')/NEF.name/'results'/sub)
    tree(REPO/'results/plots_data', Path('project/results/plots_data'))
    for name in ['x2_45s_dt0005', 'cf2_rotor_45s_scale15']:
        tree(REPO/'results/validation'/name, Path('project/results/validation')/name)
    for name in ['DIRECT_NENGO_FINAL_2026-09-01', 'hardware_armed_roll_n3_2026-09-01', 'FROZEN_AUDIT_2026-09-02']:
        tree(HNEF/'results'/name, Path('hover3dof')/HNEF.name/'results'/name)
    with (HNEF/'results/hardware_armed_roll_n3_2026-09-01/armed_roll_n3_paired_trials.csv').open(newline='') as f:
        for row in csv.DictReader(f):
            for field in ['pd_directory', 'cmg_directory']:
                source = Path(row[field])
                tree(source, Path('hover3dof')/HNEF.name/'results/hardware'/source.name)
    legacy_rows = []
    for filename, model, mission in [('learned_gate_skydio.json', 'X2', 'hard45'),
                                     ('learned_gate_results.json', 'CF2', 'hard45'),
                                     ('learned_gate_hardstep.json', 'CF2', 'hardstep')]:
        source = LEGACY/'experiments/controller_benchmarks'/filename
        add(source, Path('legacy')/filename)
        for controller, metrics in json.loads(source.read_text()).items():
            legacy_rows.append({'model': model, 'mission': mission, 'controller': controller,
                                **{k: v for k, v in metrics.items() if not isinstance(v, (dict, list))}, 'source_json': filename})
    names = sorted({key for row in legacy_rows for key in row})
    generated = {'README.md': (TOOLS/'RESULTS_README.md').read_bytes(),
                 'legacy/precursor_summaries.csv': csv_bytes(legacy_rows, names),
                 'documentation/ACC2027_V4_TO_V5_AUDIT_2026-09-04.md': (REPO/'docs/ACC2027_V4_TO_V5_AUDIT_2026-09-04.md').read_bytes()}
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT/'ACC2027_RESULTS_CSV.zip'
    total = sum(p.stat().st_size for p in entries.values())
    print(f'Results: {len(entries)} original files, {total/1024**2:.1f} MiB before lossless compression', flush=True)
    records = []
    with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9, allowZip64=True) as z:
        for i, (dest, source) in enumerate(sorted(entries.items())):
            archive_path = 'ACC2027_RESULTS/'+dest
            z.write(source, archive_path)
            records.append({'archive_path': archive_path, 'bytes': source.stat().st_size, 'sha256': digest(source), 'source': str(source)})
            if i % 30 == 0:
                print(f'Compressed {i+1}/{len(entries)} results files', flush=True)
        for dest, payload in generated.items():
            archive_path = 'ACC2027_RESULTS/'+dest
            z.writestr(archive_path, payload)
            records.append({'archive_path': archive_path, 'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest(), 'source': 'generated; see README'})
        z.writestr('ACC2027_RESULTS/FILES.csv', csv_bytes(records))
    (OUT/'RESULTS_BUILD.json').write_text(json.dumps({'archive': str(target), 'bytes': target.stat().st_size,
        'source_bytes': total, 'files': len(records), 'csv_files': sum(r['archive_path'].endswith('.csv') for r in records),
        'sha256': digest(target)}, indent=2)+'\n')
    print('RESULTS COMPLETE:', target, target.stat().st_size, flush=True)


def code_archive():
    target = OUT/'ACC2027_CODE.zip'
    with (STAGE/'SOURCE_MAP.csv').open(newline='') as f:
        for row in csv.DictReader(f):
            if row['change'] == 'none':
                assert digest(STAGE/row['bundle_path']) == row['source_sha256'], row['bundle_path']
    files = [p for p in sorted(STAGE.rglob('*')) if p.is_file() and not
             (set(p.relative_to(STAGE).parts) & {'.venv', '__pycache__', 'reproduced', 'results', 'tmp'}) and p.suffix != '.pyc']
    records = []
    with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path in files:
            arc = 'ACC2027_CODE/'+path.relative_to(STAGE).as_posix()
            z.write(path, arc)
            records.append({'archive_path': arc, 'bytes': path.stat().st_size, 'sha256': digest(path), 'source': 'staged code; see SOURCE_MAP.csv'})
        z.writestr('ACC2027_CODE/FILES.csv', csv_bytes(records))
    print('CODE COMPLETE:', target, target.stat().st_size, flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('task', choices=['prepare', 'data', 'code'])
    task = p.parse_args().task
    {'prepare': prepare, 'data': data_archive, 'code': code_archive}[task]()
