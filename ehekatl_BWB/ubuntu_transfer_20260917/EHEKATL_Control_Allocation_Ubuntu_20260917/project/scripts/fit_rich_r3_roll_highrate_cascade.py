#!/usr/bin/env python3
"""Fit stable first-order-plus-delay stages to the rejected high-rate design pilot."""
import csv,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];LOG=ROOT/'logs/rich_R3_roll_dualrate_pilot_20260712_193416.csv';F=np.array([2.,4.,6.,8.,10.]);W=2*np.pi*F
def load():
 with LOG.open(newline='') as f:r=list(csv.DictReader(f))
 t=np.array([float(x['t_s']) for x in r]);m=(t>=7)&(t<=23);fields=('yoke_roll_ratio','total_roll_ratio','aileron_wing2l_deg','p_deg_s');return t[m],{k:np.array([float(x[k]) for x in r])[m] for k in fields}
def harmonics(t,x):
 cols=[]
 for f in F:cols.extend((np.sin(2*np.pi*f*t),np.cos(2*np.pi*f*t)))
 X=np.column_stack(cols+[np.ones(len(t)),t-t.mean()]);b=np.linalg.lstsq(X,x,rcond=None)[0];return np.array([b[2*i]-1j*b[2*i+1] for i in range(len(F))])
def fit_stage(h):
 best=None
 for delay in np.linspace(0,.15,151):
  for tau in np.logspace(-3,0,300):
   shape=np.exp(-1j*W*delay)/(1+1j*W*tau);weights=1/np.abs(h);g=shape*weights;y=h*weights;k=float(np.real(np.vdot(g,y))/np.vdot(g,g).real);pred=k*shape;err=float(np.sqrt(np.mean(np.abs((pred-h)/h)**2)));item={'gain':k,'tau_s':float(tau),'delay_s':float(delay),'pole_rad_s':float(-1/tau),'relative_complex_rmse':err,'predicted_magnitude':np.abs(pred).tolist(),'predicted_phase_deg':np.angle(pred,deg=True).tolist()}
   if best is None or err<best['relative_complex_rmse']:best=item
 return best
def main():
 t,x=load();c={k:harmonics(t,v) for k,v in x.items()};stages=(('yoke_to_total','yoke_roll_ratio','total_roll_ratio'),('total_to_surface','total_roll_ratio','aileron_wing2l_deg'),('surface_to_p','aileron_wing2l_deg','p_deg_s'));result={'status':'design_evidence_only','source_log':LOG.name,'frequencies_hz':F.tolist(),'fit_window_s':[7,23],'sample_period_s':1/35,'stages':{}}
 product=np.ones(len(F),complex)
 for name,inp,out in stages:
  # Coefficients use exp(-i phase); conjugation restores the conventional physical phase sign.
  h=np.conj(c[out]/c[inp]);fit=fit_stage(h);result['stages'][name]={'measured_magnitude':np.abs(h).tolist(),'measured_phase_deg':np.angle(h,deg=True).tolist(),'fit':fit,'time_constant_sample_resolved':fit['tau_s']>=1/35,'delay_sample_resolved':fit['delay_s']>=1/35};product*=h
 direct=np.conj(c['p_deg_s']/c['yoke_roll_ratio']);closure=np.abs((product-direct)/direct);result['cascade_closure_relative_error']=closure.tolist();result['maximum_cascade_closure_error']=float(closure.max());result['all_stage_fit_rmse_below_0_25']=all(s['fit']['relative_complex_rmse']<=.25 for s in result['stages'].values());result['all_dynamic_times_sample_resolved']=all(s['time_constant_sample_resolved'] for s in result['stages'].values());result['decision']='candidate_for_new_validation_plan' if result['all_stage_fit_rmse_below_0_25'] and result['all_dynamic_times_sample_resolved'] else 'rejected_for_dynamic_lqr_realization'
 out=ROOT/'configs/rich_R3_roll_highrate_cascade.json';out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
