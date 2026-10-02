#!/usr/bin/env python3
"""Redesign R3 pitch excitation using observed closed-loop frequency retention."""
import csv,itertools,json,math
from pathlib import Path
import numpy as np
from synthesize_stage4_lqr import c2d_rk4

ROOT=Path(__file__).resolve().parents[1];FREQ=(.35,.55,.80,1.10);PHASE=(2.513274,3.769911,5.026548,.628319);AMP=.001
BASE=(ROOT/'logs/rich_R3_baseline_01_20260712_174514.csv',ROOT/'logs/rich_R3_baseline_02_20260712_174845.csv');TRAIN=ROOT/'logs/rich_R3_pitch_training_01_20260712_180253.csv'
def rows(path):
 with path.open(newline='') as f:return list(csv.DictReader(f))
def spectral(data,field,start,end):
 t=np.array([float(r['t_s']) for r in data]);x=np.array([float(r[field]) for r in data]);m=(t>=start)&(t<=end);t=t[m];x=x[m]-x[m].mean();out=[]
 for f in FREQ:
  d=np.column_stack((np.sin(2*np.pi*f*t),np.cos(2*np.pi*f*t)));out.append(float(np.linalg.norm(np.linalg.lstsq(d,x,rcond=None)[0])))
 return np.array(out)
def wave(t):
 z=t-10
 if z<0 or z>40:return 0.
 edge=min(z,40-z);env=1 if edge>=2 else .5*(1-math.cos(math.pi*edge/2));return AMP*env*sum(math.sin(2*math.pi*f*z+p) for f,p in zip(FREQ,PHASE))/len(FREQ)
def simulate(beta,delay):
 ad,bd=c2d_rk4(np.array([[0.,1.],[beta[0],beta[1]]]),np.array([[0.],[beta[2]]]));x=np.zeros(2);hist=[0.]*delay;rate=[];u=[]
 for k in range(600):
  v=wave(k*.1);x=ad@x+bd[:,0]*hist.pop(0);hist.append(v);rate.append(x[1]);u.append(v)
 active=np.array(rate)[100:500];return float(np.sqrt(np.mean(active**2))),float(np.max(np.abs(active))),float(np.max(np.abs(u)))
def main():
 baseline=np.max([spectral(rows(p),'total_pitch_ratio',5,29.5) for p in BASE],axis=0);observed=spectral(rows(TRAIN),'total_pitch_ratio',10,50)
 old_component=.001/6;retention=observed/old_component;projected=retention*(AMP/len(FREQ));snr=projected/baseline
 model=json.loads((ROOT/'configs/stage3_models.json').read_text())['models']['pitch'];beta=np.array(model['beta']);stderr=np.array(model['stderr']);audit=[]
 for signs in itertools.product((-2,0,2),repeat=3):
  for delay in (2,3,4):audit.append(simulate(beta+np.array(signs)*stderr,delay))
 result={'regime':'R3','axis':'pitch','status':'frozen_replacement','source_rejected_training_log':TRAIN.name,'baseline_logs':[p.name for p in BASE],'amplitude':AMP,'frequencies_hz':FREQ,'phases_rad':PHASE,'window':{'start_s':10.,'duration_s':40.,'ramp_s':2.},'baseline_spectral_amplitude':baseline.tolist(),'observed_old_total_input_amplitude':observed.tolist(),'observed_closed_loop_retention':retention.tolist(),'projected_revised_total_input_amplitude':projected.tolist(),'projected_input_spectral_snr':snr.tolist(),'minimum_projected_input_spectral_snr':float(snr.min()),'selection_gate':2.,'uncertainty_delay_cases':len(audit),'uncertainty_rate_rms_range_deg_s':[min(x[0] for x in audit),max(x[0] for x in audit)],'uncertainty_peak_rate_range_deg_s':[min(x[1] for x in audit),max(x[1] for x in audit)],'peak_command':max(x[2] for x in audit)}
 if result['minimum_projected_input_spectral_snr']<2:raise SystemExit('replacement does not pass projected SNR gate')
 out=ROOT/'configs/rich_R3_pitch_revised_design.json';out.write_text(json.dumps(result,indent=2)+'\n');print(out)
if __name__=='__main__':main()
