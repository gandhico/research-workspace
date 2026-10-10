"""Portable, simulation-only entry point for the advisor reproducibility bundle."""
from pathlib import Path
import argparse
import csv
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT/'project'
NEF = PROJECT/'experiments/nengo_nef_replication_2026-08-29'
MISSIONS = ('roll', 'full3', 'hard45', 'hardstep', 'yaw360')
PLATFORMS = {'x2': 1.0, 'cf2-rotor': 1.5}


def run(command):
    print('RUN:', subprocess.list2cmdline([str(x) for x in command]), flush=True)
    env = os.environ.copy()
    env['PYTHONPATH'] = str(PROJECT/'src')
    subprocess.run([str(x) for x in command], cwd=ROOT, env=env, check=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('task', choices=['smoke', 'single', 'primary', 'neurons', 'ablation', 'gui', 'legacy', 'hover-emulated', 'compare'])
    p.add_argument('--platform', choices=tuple(PLATFORMS), default='x2')
    p.add_argument('--mission', choices=(*MISSIONS, 'hover'), default='hard45')
    p.add_argument('--controller', choices=['classical', 'direct-online-pes', 'nengo-nef-pes'], default='nengo-nef-pes')
    p.add_argument('--duration', type=float, default=45.)
    p.add_argument('--output', type=Path, default=ROOT/'reproduced')
    p.add_argument('--results', type=Path, default=ROOT.parent/'ACC2027_RESULTS')
    p.add_argument('--full-neural-data', action='store_true')
    a = p.parse_args()
    a.output = a.output.resolve()
    if a.task == 'compare':
        expected = a.results/'project/experiments/nengo_nef_replication_2026-08-29/results/compiled/matched_results.csv'
        with expected.open(newline='') as f:
            rows = [r for r in csv.DictReader(f) if r['mission'] != 'hover']
        checked = []
        for r in rows:
            for control, field in [('classical', 'baseline_mean_rad'), ('nengo-nef-pes', 'nengo_mean_rad')]:
                path = a.output/'primary'/r['platform']/r['mission']/control/'summary.json'
                value = json.loads(path.read_text())['qerr_mean_rad']
                target = float(r[field])
                rel = abs(value-target)/max(abs(target), 1e-12)
                if rel > 1e-5:
                    raise SystemExit(f'MISMATCH {path}: relative difference {rel}')
                checked.append({'platform': r['platform'], 'mission': r['mission'], 'controller': control, 'relative_difference': rel})
        (a.output/'comparison.json').write_text(json.dumps(checked, indent=2)+'\n')
        print(f'PASS: {len(checked)} mean-error comparisons within relative tolerance 1e-5')
        return
    if a.task == 'smoke':
        run([sys.executable, NEF/'test_nengo_cmg.py'])
        run([sys.executable, NEF/'test_neuron_family.py'])
        run([sys.executable, NEF/'smoke_test_gui.py', '--duration', '.05', '--output', a.output/'gui_smoke.json'])
    if a.task in ('smoke', 'single', 'primary'):
        platforms = PLATFORMS if a.task != 'single' else [a.platform]
        missions = MISSIONS if a.task == 'primary' else [a.mission]
        controllers = ('classical', 'direct-online-pes', 'nengo-nef-pes') if a.task != 'single' else [a.controller]
        for platform in platforms:
            for mission in missions:
                for controller in controllers:
                    output = a.output/a.task/platform/mission/controller
                    if (output/'summary.json').exists():
                        raise SystemExit(f'Refusing to overwrite an existing result: {output}. Choose --output with a new directory.')
                    cmd = [sys.executable, NEF/'run_mujoco_nef.py', '--platform', platform,
                           '--mission', mission, '--controller', controller, '--duration', '.1' if a.task == 'smoke' else str(a.duration),
                           '--dt', '.0005', '--beta', '.5', '--learning-rate', '.0008', '--k-error', '8', '--k-rate', '0',
                           '--actuator-scale', str(PLATFORMS[platform]), '--torque-policy', 'model', '--seed', '1',
                           '--log-every', '10', '--output', output]
                    if not a.full_neural_data:
                        cmd.append('--no-neural-archive')
                    run(cmd)
    elif a.task == 'neurons':
        cmd = [sys.executable, NEF/'run_neuron_family_campaign.py', '--duration', str(a.duration),
               '--output-root', a.output/'neurons']
        if not a.full_neural_data:
            cmd.append('--no-neural-archive')
        run(cmd)
    elif a.task == 'ablation':
        for platform in PLATFORMS:
            for mission in MISSIONS:
                for control in ['classical', 'fixed-residual', 'adaptive-residual', 'online-pes-fixed', 'online-pes-adaptive']:
                    run([sys.executable, '-m', 'gra_control.cli', 'simulate', '--platform', platform,
                         '--mission', mission, '--controller', control, '--duration', str(a.duration), '--dt', '.0005',
                         '--beta', '.5', '--learning-rate', '.0008', '--k-error', '8', '--k-rate', '0',
                         '--actuator-scale', str(PLATFORMS[platform]), '--output', a.output/'ablation'/platform/mission/control])
    elif a.task == 'gui':
        run([sys.executable, NEF/'launch_gui.py', '--platform', a.platform, '--mission', a.mission,
             '--duration', str(a.duration), '--mujoco-viewer', 'neural', '--realtime'])
    elif a.task == 'legacy':
        legacy = ROOT/'legacy/code/experiments/controller_benchmarks/learned_gate_experiment.py'
        a.output.mkdir(parents=True, exist_ok=True)
        for quad, mission in [('skydio_x2', 'hard45'), ('bitcraze_crazyflie_2', 'hard45'), ('bitcraze_crazyflie_2', 'hardstep')]:
            run([sys.executable, legacy, '--quad', quad, '--mission', mission, '--sim-time', str(a.duration),
                 '--dt', '.0005', '--lr', '.0008', '--k-err', '8', '--k-rate', '0', '--leak', '0',
                 '--methods', 'classical,online_pes,eprop_anneal', '--out', a.output/f'legacy_{quad}_{mission}.json'])
    elif a.task == 'hover-emulated':
        runner = ROOT/'hover3dof/nengo_gui_hil_2026-08-29/run_hover_headless.py'
        for controller in ['pd', 'nengo-pes']:
            run([sys.executable, runner, '--io', 'emulated', '--mission', a.mission,
                 '--duration', str(a.duration), '--controller', controller, '--output-root', a.output/'hover_emulated'])


if __name__ == '__main__':
    main()
