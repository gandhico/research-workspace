#!/usr/bin/env python3
"""Freeze a matched paired-pulse comparison for R3 roll LQR versus backstepping."""
import itertools,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
from synthesize_rich_r3_roll_discrete_lqr import matrices
from lqr.discrete_cascade_roll_lqr import COMMAND_LIMIT,SLEW_LIMIT,K
HZ=35.;DT=1/HZ;SECONDS=30.;STARTS=(10.,12.);DURATION=.2;AMPLITUDE=.00005

def disturbance(t):
 for i,start in enumerate(STARTS):
  sign=1. if i%2==0 else -1.
  if start<=t<=start+DURATION:return sign*AMPLITUDE*np.sin(np.pi*(t-start)/DURATION)
 return 0.

def backstepping(phi,u):
 k=.001;ku=33.;tau=.03;ud=-k*phi;error_u=u-ud;du=-k*(error_u-ud);return u+tau*(du-phi-ku*error_u)

def simulate(A,B,mode):
 x=np.zeros(3);phi=0.;base=previous=0.;next_fallback=0.;p=[];angle=[];base_commands=[];sent=[];dist=[]
 for n in range(round(SECONDS*HZ)):
  t=n*DT
  if mode=='lqr':requested=float(-K@x)
  elif t+1e-12>=next_fallback:
   while next_fallback<=t+1e-12:next_fallback+=.1
   requested=backstepping(phi,x[2])
  else:requested=base
  base=float(np.clip(requested,-COMMAND_LIMIT,COMMAND_LIMIT));base=float(np.clip(base,previous-SLEW_LIMIT,previous+SLEW_LIMIT));d=disturbance(t);actual=base+d;x=A@x+B[:,0]*actual;phi+=DT*x[0];previous=base;p.append(x[0]);angle.append(phi);base_commands.append(base);sent.append(actual);dist.append(d)
 a=np.array(p);ang=np.array(angle);cmd=np.array(base_commands);actual=np.array(sent);d=np.array(dist);active=(np.arange(len(a))*DT>=STARTS[0])&(np.arange(len(a))*DT<18);final=np.arange(len(a))*DT>=25
 return {'peak_abs_p_deg_s':float(np.max(np.abs(a[active]))),'integral_abs_p_deg':float(np.sum(np.abs(a[active]))*DT),'peak_abs_roll_deg':float(np.max(np.abs(ang))),'final_5s_max_abs_p_deg_s':float(np.max(np.abs(a[final]))),'final_5s_max_abs_roll_deg':float(np.max(np.abs(ang[final]))),'peak_abs_base_command':float(np.max(np.abs(cmd))),'peak_abs_sent_command':float(np.max(np.abs(actual))),'maximum_base_slew':float(np.max(np.abs(np.diff(np.r_[0.,cmd])))),'maximum_sent_slew':float(np.max(np.abs(np.diff(np.r_[0.,actual])))),'minimum_realized_disturbance_ratio':float(np.min(np.abs((actual-cmd)[np.abs(d)>1e-12]/d[np.abs(d)>1e-12]))),'magnitude_limited_samples':int(np.sum(np.abs(cmd)>=COMMAND_LIMIT-1e-12)),'sent_limit_exceeded_samples':int(np.sum(np.abs(actual)>COMMAND_LIMIT+1e-12))}

def main():
 model=json.loads((ROOT/'configs/rich_R3_roll_discrete_cascade.json').read_text());yt=model['yoke_to_total']['selected'];sp=model['surface_to_p']['selected'];at=yt['beta'][0];b0,b1=yt['beta'][1:];g=model['total_to_surface']['static_gain'];ap,c=sp['beta'];cases=[]
 for scales in itertools.product((.75,1.,1.25),repeat=5):
  A,B=matrices(at*scales[0],b0*scales[1],b1*scales[2],g,ap*scales[3],c*scales[4]);baseline=simulate(A,B,'backstepping');lqr=simulate(A,B,'lqr');cases.append({'coefficient_scales':scales,'baseline':baseline,'lqr':lqr,'peak_p_ratio_lqr_to_baseline':lqr['peak_abs_p_deg_s']/baseline['peak_abs_p_deg_s'],'integral_p_ratio_lqr_to_baseline':lqr['integral_abs_p_deg']/baseline['integral_abs_p_deg']})
 summary={'sample_rate_hz':HZ,'duration_s':SECONDS,'pulse':{'starts_s':STARTS,'duration_s':DURATION,'signs':[1,-1],'amplitude':AMPLITUDE,'location':'additive after selected controller; no clipping permitted'},'uncertainty_cases':len(cases),'worst_peak_p_ratio_lqr_to_baseline':max(x['peak_p_ratio_lqr_to_baseline'] for x in cases),'worst_integral_p_ratio_lqr_to_baseline':max(x['integral_p_ratio_lqr_to_baseline'] for x in cases),'minimum_baseline_peak_abs_p_deg_s':min(x['baseline']['peak_abs_p_deg_s'] for x in cases),'maximum_lqr_peak_abs_p_deg_s':max(x['lqr']['peak_abs_p_deg_s'] for x in cases),'maximum_lqr_peak_abs_roll_deg':max(x['lqr']['peak_abs_roll_deg'] for x in cases),'maximum_sent_command':max(max(x[m]['peak_abs_sent_command'] for m in ('baseline','lqr')) for x in cases),'maximum_base_slew':max(max(x[m]['maximum_base_slew'] for m in ('baseline','lqr')) for x in cases),'maximum_sent_slew':max(max(x[m]['maximum_sent_slew'] for m in ('baseline','lqr')) for x in cases),'sent_limit_exceeded_samples':sum(x[m]['sent_limit_exceeded_samples'] for x in cases for m in ('baseline','lqr')),'minimum_realized_disturbance_ratio':min(x[m]['minimum_realized_disturbance_ratio'] for x in cases for m in ('baseline','lqr'))}
 gates={'baseline_peak_abs_p_deg_s_min':.0015,'peak_p_ratio_lqr_to_baseline_max':1.10,'integral_p_ratio_lqr_to_baseline_max':.70,'sent_command_abs_max':COMMAND_LIMIT,'sent_slew_max':SLEW_LIMIT,'realized_disturbance_ratio_min':.999999,'final_5s_abs_p_deg_s_max':.002,'final_5s_abs_roll_deg_max':.05}
 passed=summary['minimum_baseline_peak_abs_p_deg_s']>=gates['baseline_peak_abs_p_deg_s_min'] and summary['worst_peak_p_ratio_lqr_to_baseline']<=gates['peak_p_ratio_lqr_to_baseline_max'] and summary['worst_integral_p_ratio_lqr_to_baseline']<=gates['integral_p_ratio_lqr_to_baseline_max'] and summary['maximum_sent_command']<=gates['sent_command_abs_max']+1e-15 and summary['maximum_sent_slew']<=gates['sent_slew_max']+1e-15 and summary['minimum_realized_disturbance_ratio']>=gates['realized_disturbance_ratio_min'] and all(x[m]['final_5s_max_abs_p_deg_s']<=gates['final_5s_abs_p_deg_s_max'] and x[m]['final_5s_max_abs_roll_deg']<=gates['final_5s_abs_roll_deg_max'] for x in cases for m in ('baseline','lqr'))
 result={'status':'frozen_offline_design' if passed else 'rejected_offline_design','summary':summary,'future_flight_gates':gates,'cases':cases,'pass':passed,'claim_boundary':'offline matched-disturbance design only; no flight performance claim'};out=ROOT/'configs/rich_R3_roll_lqr_disturbance_design.json';out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'summary':summary,'future_flight_gates':gates,'pass':passed},indent=2));raise SystemExit(0 if passed else 1)

if __name__=='__main__':main()
