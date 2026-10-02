"""Open-loop diagnosis and separately labelled exploratory feedback regimes."""
import argparse
import concurrent.futures
import functools
import json
from pathlib import Path
import subprocess
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]

def open_loop():
    sys.path.insert(0,str(REPO/'src'))
    from gra_control.gate import CMGConfig,CoupledMembraneGateBank
    h=.0005; t=np.arange(0,16,h)
    # Identical rising/falling current ramp; gate memory is not reset at the peak.
    current=np.where(t<8,.75+1.25*t/8,2-1.25*(t-8)/8)
    traces={}; rows=[]
    for gamma in [0,.5,1,2]:
        pair=[]
        for chi in [0,1]:
            p=CMGConfig(gamma=gamma)
            bank=CoupledMembraneGateBank(1,bool(chi),p)
            data=np.empty((len(t),3))
            for k,I in enumerate(current):
                bank.step(np.array([I]),h)
                data[k]=[bank.v[0],bank.r[0],(120+chi*30*I)*bank.r[0]**2]
            traces[f'gamma{gamma}_chi{chi}']=data
            pair.append(data)
        rows.append(dict(gamma=gamma,mean_abs_delta_v=float(np.mean(abs(pair[1][:,0]-pair[0][:,0]))),
                         mean_abs_delta_r=float(np.mean(abs(pair[1][:,1]-pair[0][:,1]))),
                         max_abs_delta_r=float(np.max(abs(pair[1][:,1]-pair[0][:,1])))))
    out=HERE/'open_loop';out.mkdir(exist_ok=True)
    np.savez_compressed(out/'ramp_states.npz',t_s=t,current=current,**traces)
    (out/'summary.json').write_text(json.dumps(rows,indent=2))
    print(json.dumps(rows,indent=2))

def regime_cases():
    # Declared before inspecting closed-loop regime results; development cases, not held-out tests.
    return [dict(platform='x2',mission=m,backend='direct',gain=g,chi=c,gamma=gamma)
            for m in ['full3','hardstep'] for gamma in [0,.5] for g in [1,3] for c in [0,1]]

def worker(c):
    sys.path.insert(0,str(REPO/'src'))
    import gra_control.gate as gate
    import sweep
    base_id=sweep.case_id
    sweep.case_id=lambda x: base_id(x)+f"_gamma{x['gamma']}"
    gate.CMGConfig=functools.partial(gate.CMGConfig,gamma=c['gamma'])
    result=sweep.worker(c)
    out=HERE/'results'/sweep.case_id(c)
    manifest=json.loads((out/'sweep_manifest.json').read_text())
    manifest['source_sha256'][str(Path(__file__))]=sweep.sha(Path(__file__))
    manifest['overrides']+=' CMGConfig gamma override (new exploratory architecture regime).'
    sweep.write_json(out/'sweep_manifest.json',manifest)
    return result

def launch(c):
    import sweep
    cid=sweep.case_id(c)+f"_gamma{c['gamma']}"
    out=HERE/'results'/cid;out.mkdir(parents=True,exist_ok=True)
    if (out/'sweep_manifest.json').exists(): return cid,'cached'
    with (out/'run.log').open('w') as f:
        p=subprocess.run([sys.executable,str(Path(__file__)),'--worker',json.dumps(c)],stdout=f,stderr=subprocess.STDOUT)
    return cid,p.returncode

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--worker');p.add_argument('--closed-loop',action='store_true');p.add_argument('--jobs',type=int,default=2)
    a=p.parse_args()
    if a.worker: print(json.dumps(worker(json.loads(a.worker)),indent=2))
    elif a.closed_loop:
        cases=regime_cases()
        (HERE/'regime_cases.json').write_text(json.dumps(cases,indent=2))
        with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as pool:
            for i,f in enumerate(concurrent.futures.as_completed([pool.submit(launch,c) for c in cases]),1): print(i,len(cases),f.result(),flush=True)
    else: open_loop()
