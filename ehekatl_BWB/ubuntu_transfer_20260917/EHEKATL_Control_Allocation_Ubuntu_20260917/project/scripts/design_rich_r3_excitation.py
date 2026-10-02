#!/usr/bin/env python3
"""Freeze R3 excitation amplitudes from accepted baseline spectra and Stage-3 models."""
import csv,itertools,json,math
from pathlib import Path
import numpy as np
from synthesize_stage4_lqr import c2d_rk4

ROOT=Path(__file__).resolve().parents[1];FREQ=(.10,.20,.35,.55,.80,1.10);PHASE=(0.,1.256637,2.513274,3.769911,5.026548,0.628319);CAND=(.0002,.0005,.0010)
LOGS=(ROOT/'logs/rich_R3_baseline_01_20260712_174514.csv',ROOT/'logs/rich_R3_baseline_02_20260712_174845.csv')
def read(path,field):
 with path.open(newline='') as f:r=list(csv.DictReader(f))
 t=np.array([float(x['t_s']) for x in r]);x=np.array([float(z[field]) for z in r]);m=t>=5;return t[m],x[m]-x[m].mean()
def spectral_noise(field):
 runs=[]
 for path in LOGS:
  t,x=read(path,field);amps=[]
  for f in FREQ:
   design=np.column_stack((np.sin(2*np.pi*f*t),np.cos(2*np.pi*f*t)));amps.append(float(np.linalg.norm(np.linalg.lstsq(design,x,rcond=None)[0])))
  runs.append(amps)
 return np.max(runs,axis=0)
def waveform(t,amp):
 local=t-10
 if local<0 or local>40:return 0.
 edge=min(local,40-local);env=1. if edge>=2 else .5*(1-math.cos(math.pi*edge/2))
 return amp*env*sum(math.sin(2*math.pi*f*local+p) for f,p in zip(FREQ,PHASE))/len(FREQ)
def response(beta,amp,delay=3):
 a=np.array([[0.,1.],[beta[0],beta[1]]]);b=np.array([[0.],[beta[2]]]);ad,bd=c2d_rk4(a,b);x=np.zeros(2);hist=[0.]*delay;rate=[];command=[]
 for k in range(600):
  u=waveform(k*.1,amp);x=ad@x+bd[:,0]*hist.pop(0);hist.append(u);rate.append(x[1]);command.append(u)
 active=np.array(rate)[100:500];return {'rate_rms_deg_s':float(np.sqrt(np.mean(active**2))),'peak_abs_rate_deg_s':float(np.max(np.abs(active))),'peak_abs_excitation':float(np.max(np.abs(command)))}
def main():
 models=json.loads((ROOT/'configs/stage3_models.json').read_text())['models'];result={'regime':'R3','baseline_logs':[p.name for p in LOGS],'frequencies_hz':FREQ,'phases_rad':PHASE,'window':{'start_s':10.,'duration_s':40.,'ramp_s':2.},'selection_gates':{'minimum_input_spectral_snr':2.,'minimum_predicted_rate_snr':5.},'axes':{}}
 for axis,control,rate in (('pitch','total_pitch_ratio','q_deg_s'),('roll','total_roll_ratio','p_deg_s')):
  noise=spectral_noise(control);rate_noise=max(float(np.sqrt(np.mean(read(p,rate)[1]**2))) for p in LOGS);cases=[]
  for amp in CAND:
   nominal=response(np.array(models[axis]['beta']),amp);input_snr=float(np.min((amp/len(FREQ))/noise));rate_snr=nominal['rate_rms_deg_s']/rate_noise;cases.append({'amplitude':amp,'minimum_input_spectral_snr':input_snr,'predicted_rate_snr':rate_snr,**nominal})
  accepted=next(c for c in cases if c['minimum_input_spectral_snr']>=2 and c['predicted_rate_snr']>=5)
  beta=np.array(models[axis]['beta']);stderr=np.array(models[axis]['stderr']);audit=[]
  for signs in itertools.product((-2,0,2),repeat=3):
   for delay in (2,3,4):audit.append(response(beta+np.array(signs)*stderr,accepted['amplitude'],delay))
  result['axes'][axis]={'baseline_control_spectral_amplitude':noise.tolist(),'baseline_rate_rms_deg_s':rate_noise,'candidates':cases,'selected_amplitude':accepted['amplitude'],'selected_nominal_response':accepted,'uncertainty_delay_cases':len(audit),'uncertainty_peak_abs_rate_range_deg_s':[min(x['peak_abs_rate_deg_s'] for x in audit),max(x['peak_abs_rate_deg_s'] for x in audit)],'uncertainty_rate_rms_range_deg_s':[min(x['rate_rms_deg_s'] for x in audit),max(x['rate_rms_deg_s'] for x in audit)]}
 out=ROOT/'configs/rich_R3_excitation_design.json';out.write_text(json.dumps(result,indent=2)+'\n');print(out)
if __name__=='__main__':main()
