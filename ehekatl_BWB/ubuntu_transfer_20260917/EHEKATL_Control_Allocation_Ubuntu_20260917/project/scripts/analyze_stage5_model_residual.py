#!/usr/bin/env python3
"""Compare measured pitch-rate acceleration with the frozen Stage-3 model."""

import argparse, csv, json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('logs',nargs='+',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    model=json.loads((ROOT/'configs/stage3_models.json').read_text())['models']['pitch'];beta=np.array(model['beta'],float);delay=3;reports=[]
    for path in a.logs:
        with path.open(newline='') as f:r=list(csv.DictReader(f))
        t=np.array([float(x['t_s']) for x in r]);theta=np.array([float(x['pitch_deg']) for x in r]);q=np.array([float(x['q_deg_s']) for x in r]);u=np.array([float(x['total_pitch_ratio']) for x in r]);base=t<10
        theta-=theta[base].mean();q-=q[base].mean();u-=u[base].mean();dt=np.diff(t);measured=np.diff(q)/dt;indices=np.arange(delay,len(r)-1);pred=beta[0]*theta[indices]+beta[1]*q[indices]+beta[2]*u[indices-delay];res=measured[indices]-pred
        windows={'pre':indices[t[indices]<10],'pulse':indices[(t[indices]>=10)&(t[indices]<12)],'post':indices[(t[indices]>=12)&(t[indices]<20)],'final':indices[t[indices]>=25]}
        stats={}
        for name,ix in windows.items():
            # indices are source row indices; residual is indexed by source index-delay alignment
            mask=np.isin(indices,ix);z=res[mask];stats[name]={'count':int(len(z)),'residual_rms':float(np.sqrt(np.mean(z*z))) if len(z) else None,'residual_mean':float(np.mean(z)) if len(z) else None,'measured_qdot_rms':float(np.sqrt(np.mean(measured[ix]**2))) if len(z) else None}
        reports.append({'file':path.name,'stats':stats,'beta':beta.tolist(),'sample_delay':delay})
    a.out.write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps(reports,indent=2))

if __name__=='__main__':main()
