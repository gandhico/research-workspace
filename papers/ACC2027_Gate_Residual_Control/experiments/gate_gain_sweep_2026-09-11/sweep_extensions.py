"""Independent readout-gain audit; never opens hardware or edits frozen sources."""
from __future__ import annotations
import argparse
import concurrent.futures
import functools
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
CANON = REPO / 'experiments/nengo_nef_replication_2026-08-29'
GAINS = [1, 100, 1000, 10000, 100000, 1000000]
MISSIONS = ['roll', 'full3', 'hard45', 'hardstep', 'yaw360']

def case_id(c):
    base=f"{c['platform']}_{c['mission']}_{c['backend']}_G{c['gain']}_chi{c['chi']}"
    return base+(f"_gamma{c['gamma']}_bias{c['bias']}" if 'bias' in c else '')

def cases():
    result=[dict(platform='x2',mission=m,backend='direct',gain=g,chi=c,gamma=.5,bias=1.)
            for m in ['full3','hardstep'] for g in [1,3] for c in [0,1]]
    result += [dict(platform=p,mission=m,backend='constant',gain=1,chi=0)
               for p,m in [('x2','roll'),('x2','full3'),('cf2-rotor','hardstep')]]
    result += [dict(platform='x2',mission='hardstep',backend='pd',gain=0,chi=0),
               dict(platform='x2',mission='hardstep',backend='direct',gain=100000,chi=1)]
    return result

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False), encoding='utf-8')

def worker(c):
    import numpy as np
    sys.path.insert(0, str(CANON))
    import run_mujoco_nef as runner
    from gra_control.gate import CMGConfig, CMGResidualAugmentor, AugmentorOutput
    out = HERE / 'results' / case_id(c)
    out.mkdir(parents=True, exist_ok=True)
    holder = []
    class RecordedCMG(CMGResidualAugmentor):
        def __init__(self, limits, beta, learning_rate):
            super().__init__(3, limits, mode='online_pes', beta=beta,
                             learning_rate=learning_rate, adaptive_conductance=bool(c['chi']),
                             cfg=CMGConfig(gate_gain=c['gain'],gamma=c.get('gamma',2),current_bias=c.get('bias',.75)))
            self.n = 0
            self.arrays = {k: np.empty((90004, *shape)) for k, shape in {
                'baseline_Nm': (3,), 'target': (3,), 'current': (6,),
                'voltage': (6,), 'gate': (6,), 'activity': (6,),
                'weights_pre': (3,6), 'weight_delta': (3,6),
                'decoded_raw_pre': (3,), 'decoded_clipped_pre': (3,),
                'command_Nm': (3,), 'residual_after_axis_clip_Nm': (3,)}.items()}

        def step(self, baseline, dt, learning_target=None):
            wpre = self.W.copy()
            u0 = np.clip(baseline, -self.limits, self.limits)
            norm = u0 / self.limits
            current = np.r_[self.cfg.current_bias + 1.25*np.maximum(norm,0), self.cfg.current_bias+1.25*np.maximum(-norm,0)]
            if c['backend'] in ['linear','constant']:
                activity = np.ones(6) if c['backend']=='constant' else np.r_[np.maximum(norm,0), np.maximum(-norm,0)]
                signed = np.clip(self.W@activity,-1,1)
                self.W += self.learning_rate*np.outer(learning_target-signed,activity)-self.leak*self.W
                np.clip(self.W,-6,6,out=self.W)
                command = np.clip(u0+self.beta*self.limits*signed,-self.limits,self.limits)
                self.units.r[:] = activity
                result = AugmentorOutput(command,u0,command-u0,activity,activity)
            else:
                result = super().step(baseline,dt,learning_target)
            vals = dict(baseline_Nm=u0,target=learning_target,current=current,
                        voltage=self.units.v,gate=self.units.r,activity=result.activity,
                        weights_pre=wpre,weight_delta=self.W-wpre,
                        decoded_raw_pre=wpre@result.activity,
                        decoded_clipped_pre=np.clip(wpre@result.activity,-1,1),
                        command_Nm=result.command,residual_after_axis_clip_Nm=result.residual)
            for k,v in vals.items(): self.arrays[k][self.n] = v
            self.n += 1
            return result

        def archive(self):
            arrays = {k:v[:self.n] for k,v in self.arrays.items()}
            arrays['t_control_s'] = np.arange(self.n)*0.0005
            arrays['weights_final'] = self.W.copy()
            np.savez_compressed(out/'neural_full_rate.npz',**arrays)
            a = arrays['activity']; r = arrays['gate']
            conductance = (120+30*c['chi']*np.abs(arrays['current']))*r*r
            # Linear features are NOT gates or conductances. Exclude surrogate state fields.
            valid_cmg = c['backend'] == 'direct'
            return dict(neural_samples=self.n,
                        activity_saturated_fraction=float(np.mean(a>=1-1e-8)),
                        activity_mean=float(np.mean(a)),
                        activity_gram_eigenvalues=np.linalg.eigvalsh(a.T@a/self.n).tolist(),
                        raw_gate_mean=float(r.mean()) if valid_cmg else None,
                        raw_gate_gt_0p1_fraction=float(np.mean(r>0.1)) if valid_cmg else None,
                        raw_gate_gt_0p9_fraction=float(np.mean(r>0.9)) if valid_cmg else None,
                        conductance_over_leak_mean=float(np.mean(conductance*0.05)) if valid_cmg else None,
                        conductance_over_leak_max=float(np.max(conductance*0.05)) if valid_cmg else None,
                        conductance_exceeds_leak_fraction=float(np.mean(conductance>20)) if valid_cmg else None,
                        decoder_drift_fro=float(np.linalg.norm(self.W-np.c_[np.eye(3),-np.eye(3)])),
                        decoder_abs_max=float(max(np.abs(arrays['weights_pre']).max(),np.abs(self.W).max())))

    original_factory = runner._build_augmentor
    def factory(name,limits,dt,beta,learning_rate,seed):
        if c['backend'] in ['direct','linear','constant']:
            obj = RecordedCMG(limits,beta,learning_rate)
            holder.append(obj)
            return obj
        return original_factory(name,limits,dt,beta,learning_rate,seed)
    runner._build_augmentor = factory
    # Runtime-only constructor parameter injection; the NeuronType itself is unchanged.
    if c['backend'] == 'nengo':
        import nengo_cmg
        nengo_cmg.CoupledMembraneGate = functools.partial(nengo_cmg.CoupledMembraneGate,gate_gain=c['gain'])
    # Canonical CSV diagnostics otherwise recompute G*r, unsuitable for the linear control.
    state_fn = runner._neuron_state
    if c['backend'] in ['linear','constant']:
        def linear_state(aug,current,target):
            a = aug.units.r.copy()
            return np.zeros(6), np.zeros(6), a, aug.W.copy(), np.clip(aug.W@a,-1,1)-target
        runner._neuron_state = linear_state
    controller = {'pd':'classical','direct':'direct-online-pes','linear':'direct-online-pes','constant':'direct-online-pes','nengo':'nengo-nef-pes'}[c['backend']]
    args = runner.make_parser().parse_args([
        '--platform',c['platform'],'--controller',controller,'--mission',c['mission'],
        '--duration','45','--dt','0.0005','--beta','0.5','--learning-rate','0.0008',
        '--actuator-scale','1.5' if c['platform']=='cf2-rotor' else '1',
        '--log-every','10','--output',str(out)])
    start = time.perf_counter()
    summary = runner.run(args)
    if holder:
        summary.update(holder[0].archive())
        summary['neural_trace_full_rate'] = str(out/'neural_full_rate.npz')
    if 'bias' in c:
        # Correct the canonical logger's fixed .75 diagnostic current for this NEW encoding.
        import csv
        with (out/'trace.csv').open(newline='') as stream:
            reader=csv.DictReader(stream);fields=reader.fieldnames;rows=list(reader)
        for k,row in enumerate(rows):
            for j in range(6):row[f'current_{j}']=holder[0].arrays['current'][k*10,j]
        with (out/'trace.csv').open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    summary.update(c)
    if c['backend'] in ['linear','constant']: summary['controller']=c['backend']+'-basis-online-pes'
    summary['controller_backend']='none' if c['backend']=='pd' else 'canonical-numpy-reference'
    summary['nengo_pes_learning_rate']=None
    summary['decoder_leak_per_step'] = 0 if c['backend']=='pd' else 1e-6
    summary['elapsed_wall_s'] = time.perf_counter()-start
    summary['complete'] = True
    summary['sweep_note'] = 'New sensitivity experiment, not a replacement for frozen main results.'
    write_json(out/'summary.json',summary)
    sources = [Path(__file__), HERE/'PLAN.md', CANON/'run_mujoco_nef.py',CANON/'nengo_cmg.py',
               REPO/'src/gra_control/gate.py',REPO/'src/gra_control/math3d.py',REPO/'src/gra_control/platforms/drone.py']
    write_json(out/'sweep_manifest.json',dict(case=c,source_sha256={str(p):sha(p) for p in sources},
        python=sys.version,executable=sys.executable,numpy=np.__version__,
        overrides='Only _build_augmentor factory and gain parameter at runtime; canonical sources unmodified.',
        archive_timing='post CMG-state integration; exact pre-PES W and its increment; command before rotor allocation',
        linear_schema_note='For linear comparator, voltage and gate archive slots are placeholders, not neuron states; use activity only.',
        trace_pes_error_note='Canonical decimated CSV uses post-update W for direct diagnostic error; full-rate archive retains pre-update decoded output.'))
    return summary

def launch(c):
    out = HERE/'results'/case_id(c)
    if (out/'summary.json').exists() and (out/'sweep_manifest.json').exists():
        s=json.loads((out/'summary.json').read_text())
        if s.get('complete'): return case_id(c),'cached'
    out.mkdir(parents=True,exist_ok=True)
    with (out/'run.log').open('w',encoding='utf-8') as f:
        run=subprocess.run([sys.executable,str(Path(__file__)),'--worker',json.dumps(c)],stdout=f,stderr=subprocess.STDOUT)
    return case_id(c),run.returncode

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--worker')
    p.add_argument('--jobs',type=int,default=3)
    p.add_argument('--anchor-only',action='store_true')
    a=p.parse_args()
    if a.worker:
        print(json.dumps(worker(json.loads(a.worker)),indent=2))
    else:
        todo=cases()
        if a.anchor_only: todo=[dict(platform='x2',mission='full3',backend='direct',gain=100000,chi=1)]
        write_json(HERE/'campaign_cases.json',cases())
        with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as pool:
            futures=[pool.submit(launch,c) for c in todo]
            for n,f in enumerate(concurrent.futures.as_completed(futures),1):
                print(f'{n}/{len(todo)} {f.result()}',flush=True)
