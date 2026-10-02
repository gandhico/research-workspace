#!/usr/bin/env python3
"""Fit stable low-order roll-rate realizations to validated mid-frequency FRFs."""
import csv,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];FREQ=np.array([.35,.55,.8,1.1]);W=2*np.pi*FREQ
REF=ROOT/'configs/rich_R3_roll_frf_reference.json';CONF=ROOT/'configs/rich_R3_roll_frf_confirmation_01_score.json'
LOGS=(ROOT/'logs/rich_R3_roll_training_01_20260712_184050.csv',ROOT/'logs/rich_R3_roll_frf_confirmation_01_20260712_190405.csv')
def complex_frf(path):
 x=json.loads(path.read_text());allf=x['frequencies_hz'];idx=[allf.index(float(f)) for f in FREQ];mag=np.array(x['frf_magnitude'])[idx];phase=np.deg2rad(np.array(x['frf_phase_deg'])[idx]);return mag*np.exp(1j*phase)
def gain_fit(shape,h):
 weights=1/np.abs(h);g=shape*weights;y=h*weights;k=max(0.,float(np.real(np.vdot(g,y))/np.vdot(g,g).real));pred=k*shape;err=np.abs((pred-h)/h);return k,float(np.sqrt(np.mean(err**2))),pred
def candidates(h):
 out=[];k,e,p=gain_fit(np.ones_like(W,dtype=complex),h);out.append({'name':'static','gain':k,'relative_complex_rmse':e,'prediction':p})
 best=None
 for tau in np.logspace(-4,1,600):
  shape=1/(1+1j*W*tau);k,e,p=gain_fit(shape,h);item={'name':'first_order','gain':k,'tau_s':float(tau),'pole_rad_s':float(-1/tau),'relative_complex_rmse':e,'prediction':p}
  if best is None or e<best['relative_complex_rmse']:best=item
 out.append(best);best=None
 for wn in np.logspace(np.log10(1.2*W.max()),2.5,180):
  for zeta in np.linspace(.2,2.,100):
   shape=wn**2/((1j*W)**2+2*zeta*wn*(1j*W)+wn**2);k,e,p=gain_fit(shape,h);item={'name':'second_order','gain':k,'wn_rad_s':float(wn),'zeta':float(zeta),'relative_complex_rmse':e,'prediction':p}
   if best is None or e<best['relative_complex_rmse']:best=item
 out.append(best);return out
def replay_first_order(model,path):
 with path.open(newline='') as f:r=list(csv.DictReader(f))
 t=np.array([float(x['t_s']) for x in r]);u=np.array([float(x['total_roll_ratio']) for x in r]);p=np.array([float(x['p_deg_s']) for x in r]);pre=t<10;u-=u[pre].mean();p-=p[pre].mean();pred=np.zeros(len(t));tau=model.get('tau_s',0);gain=model['gain']
 for k in range(len(t)-1):
  if tau==0:pred[k+1]=gain*u[k+1]
  else:
   a=np.exp(-(t[k+1]-t[k])/tau);pred[k+1]=a*pred[k]+gain*(1-a)*u[k]
 m=(t>=12)&(t<=48);rmse=float(np.sqrt(np.mean((pred[m]-p[m])**2)));return {'file':path.name,'rate_rmse_deg_s':rmse,'rate_nrmse':rmse/float(np.std(p[m]))}
def encode(items):
 out=[]
 for x in items:
  z={k:v for k,v in x.items() if k!='prediction'};z['predicted_magnitude']=np.abs(x['prediction']).tolist();z['predicted_phase_deg']=np.angle(x['prediction'],deg=True).tolist();out.append(z)
 return out
def main():
 global W
 train=complex_frf(REF);confirm=complex_frf(CONF);joint=np.concatenate((train,confirm));shape_freq=np.tile(W,2)
 original=W.copy();W=shape_freq;joint_candidates=candidates(joint);W=original;train_candidates=candidates(train);confirm_candidates=candidates(confirm)
 selected=min(joint_candidates,key=lambda x:(x['relative_complex_rmse'],0 if x['name']=='static' else 1));replays=[]
 if selected['name'] in ('static','first_order'):replays=[replay_first_order(selected,p) for p in LOGS]
 fastest_tau=selected.get('tau_s');dynamic_resolved=selected['name']!='static' and fastest_tau is not None and fastest_tau>=.1
 result={'status':'selected' if dynamic_resolved and max(x['rate_nrmse'] for x in replays)<=1 else 'rejected_for_state_space_lqr','frequencies_hz':FREQ.tolist(),'training_frf':[[float(x.real),float(x.imag)] for x in train],'confirmation_frf':[[float(x.real),float(x.imag)] for x in confirm],'joint_candidates':encode(joint_candidates),'training_candidates':encode(train_candidates),'confirmation_candidates':encode(confirm_candidates),'best_joint_candidate':{k:v for k,v in selected.items() if k!='prediction'},'time_domain_replay':replays,'dynamic_time_constant_resolved_at_10hz':dynamic_resolved,'rejection_rule':'reject if best dynamics are faster than 0.1 s sample resolution or either log replay NRMSE exceeds 1.0','claim_boundary':'FRF interpolation only unless stable dynamics are sample-resolved and time replay passes'}
 out=ROOT/'configs/rich_R3_roll_frf_realization.json';out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
