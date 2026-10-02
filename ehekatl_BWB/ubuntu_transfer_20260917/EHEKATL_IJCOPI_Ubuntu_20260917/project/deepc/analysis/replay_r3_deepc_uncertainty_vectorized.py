#!/usr/bin/env python3
"""Vectorized 243-case offline replay of the provisional R3 DeePC controller."""

from __future__ import annotations

import csv, itertools, json, sys, time
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from deepc.src.regularized_deepc import RegularizedDeePC
from lqr.discrete_cascade_roll_lqr import COMMAND_LIMIT,SLEW_LIMIT,K
from synthesize_rich_r3_roll_discrete_lqr import matrices

HZ=35.;DT=1/HZ;N=1050;STARTS=(10.,12.);DURATION=.2;AMP=.00005
RU=.01;RDU=.02
TRAIN=ROOT/'logs/rich_R3_roll_dualrate_pilot_20260712_193416.csv'
OUT=ROOT/'configs/rich_R3_deepc_uncertainty_replay.json'

def disturbance(t):
 for i,s in enumerate(STARTS):
  if s<=t<=s+DURATION:return (1 if i%2==0 else -1)*AMP*np.sin(np.pi*(t-s)/DURATION)
 return 0.

def build():
 with TRAIN.open(newline='') as f:r=np.array([[float(x[k]) for k in ('t_s','yoke_roll_ratio','p_deg_s')] for x in csv.DictReader(f)])
 z=r[(r[:,0]>=5)&(r[:,0]<15),1:];center=z.mean(0);scale=z.std(0,ddof=1);z=(z-center)/scale
 return RegularizedDeePC(z[:,0],z[:,1],5,5,10.),center,scale

def project(v,previous,limit,slew):
 out=np.empty_like(v);prior=previous.copy()
 for j in range(v.shape[1]):
  x=np.clip(v[:,j],-limit,limit);x=np.clip(x,prior-slew,prior+slew);x=np.clip(x,-limit,limit);out[:,j]=x;prior=x
 return out

def deepc_batch(ctrl,u_hist,p_hist,center,scale):
 # Both histories are perturbations about the training means. A zero cascade
 # P-error therefore maps to normalized zero, not to negative absolute bias.
 past=np.hstack((u_hist/scale[0],p_hist/scale[1]));constant=past@ctrl._past_map.T;m=ctrl._future_input_map
 ref=0.;d=np.eye(5);d[1:,:-1]-=np.eye(4);prev=u_hist[:,-1]/scale[0];pv=np.zeros((len(prev),5));pv[:,0]=prev
 h=m.T@m+RU*np.eye(5)+RDU*d.T@d;linear=(constant-ref)@m-RDU*pv@d
 step=.95/max(np.linalg.eigvalsh(h)[-1],1e-12);u=np.repeat(prev[:,None],5,axis=1);limit=COMMAND_LIMIT/scale[0];slew=SLEW_LIMIT/scale[0]
 converged=np.zeros(len(prev),bool)
 for it in range(1,301):
  candidate=project(u-step*(u@h.T+linear),prev,limit,slew);delta=np.max(np.abs(candidate-u),axis=1);converged|=delta<=1e-7;u=candidate
  if np.all(converged):break
 return u[:,0]*scale[0],converged,it

def simulate(a,b,mode,ctrl,center,scale):
 count=len(a);x=np.zeros((count,3));phi=np.zeros(count);previous=np.zeros(count);uh=np.zeros((count,5));ph=np.zeros((count,5));peak=np.zeros(count);integral=np.zeros(count);peakroll=np.zeros(count);maxcmd=np.zeros(count);maxslew=np.zeros(count);nonconv=np.zeros(count,int);runtimes=[]
 for n in range(N):
  t=n*DT
  if mode=='lqr':requested=-(x@K)
  else:
   began=time.perf_counter();requested,conv,_=deepc_batch(ctrl,uh,ph,center,scale);runtimes.append((time.perf_counter()-began)*1000);nonconv+=~conv
  command=np.clip(requested,-COMMAND_LIMIT,COMMAND_LIMIT);command=np.clip(command,previous-SLEW_LIMIT,previous+SLEW_LIMIT);sent=command+disturbance(t)
  x=np.einsum('cij,cj->ci',a,x)+b[:,:,0]*sent[:,None];phi+=DT*x[:,0];slew=np.abs(command-previous);previous=command;uh=np.hstack((uh[:,1:],command[:,None]));ph=np.hstack((ph[:,1:],x[:,[0]]))
  if 10<=t<18:peak=np.maximum(peak,np.abs(x[:,0]));integral+=np.abs(x[:,0])*DT
  peakroll=np.maximum(peakroll,np.abs(phi));maxcmd=np.maximum(maxcmd,np.abs(sent));maxslew=np.maximum(maxslew,np.abs(slew+0))
 finalp=np.abs(x[:,0]);finalroll=np.abs(phi)
 return {'peak':peak,'integral':integral,'peakroll':peakroll,'maxcmd':maxcmd,'maxslew':maxslew,'finalp':finalp,'finalroll':finalroll,'nonconv':nonconv,'runtime':np.array(runtimes)}

def main():
 ctrl,center,scale=build();model=json.loads((ROOT/'configs/rich_R3_roll_discrete_cascade.json').read_text());yt=model['yoke_to_total']['selected']['beta'];sp=model['surface_to_p']['selected']['beta'];g=model['total_to_surface']['static_gain'];scales=list(itertools.product((.75,1.,1.25),repeat=5));ab=[matrices(yt[0]*s[0],yt[1]*s[1],yt[2]*s[2],g,sp[0]*s[3],sp[1]*s[4]) for s in scales];a=np.stack([q[0] for q in ab]);b=np.stack([q[1] for q in ab])
 lqr=simulate(a,b,'lqr',ctrl,center,scale);deepc=simulate(a,b,'deepc',ctrl,center,scale);ir=deepc['integral']/lqr['integral'];pr=deepc['peak']/lqr['peak'];summary={'cases':243,'worst_integral_ratio_deepc_to_lqr':float(ir.max()),'median_integral_ratio_deepc_to_lqr':float(np.median(ir)),'worst_peak_ratio_deepc_to_lqr':float(pr.max()),'maximum_sent_command':float(deepc['maxcmd'].max()),'maximum_base_slew':float(deepc['maxslew'].max()),'optimizer_nonconverged_updates':int(deepc['nonconv'].sum()),'batch_runtime_ms_median':float(np.median(deepc['runtime'])),'batch_runtime_ms_max':float(deepc['runtime'].max()),'estimated_per_case_runtime_ms_max':float(deepc['runtime'].max()/243),'control_period_ms':1000/HZ}
 gates={'worst_integral_ratio_max':.90,'worst_peak_ratio_max':1.10,'sent_command_max':COMMAND_LIMIT,'base_slew_max':SLEW_LIMIT,'nonconverged_updates_max':0,'estimated_per_case_runtime_ms_max':1000/HZ};passed=summary['worst_integral_ratio_deepc_to_lqr']<=.9 and summary['worst_peak_ratio_deepc_to_lqr']<=1.1 and summary['maximum_sent_command']<=COMMAND_LIMIT+1e-15 and summary['maximum_base_slew']<=SLEW_LIMIT+1e-15 and summary['optimizer_nonconverged_updates']==0 and summary['estimated_per_case_runtime_ms_max']<1000/HZ
 cases=[{'coefficient_scales':scales[i],'lqr_integral':float(lqr['integral'][i]),'deepc_integral':float(deepc['integral'][i]),'integral_ratio':float(ir[i]),'lqr_peak':float(lqr['peak'][i]),'deepc_peak':float(deepc['peak'][i]),'peak_ratio':float(pr[i])} for i in range(243)];result={'status':'pass' if passed else 'fail','training_file':str(TRAIN.relative_to(ROOT)),'held_out_response_files_opened':[],'summary':summary,'prospective_gates':gates,'cases':cases,'pass':passed,'claim_boundary':'Frozen-model vectorized uncertainty replay; no X-Plane or superiority claim.'};OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'summary':summary,'gates':gates},indent=2));raise SystemExit(0 if passed else 1)

if __name__=='__main__':main()
