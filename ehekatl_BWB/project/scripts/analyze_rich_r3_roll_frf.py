#!/usr/bin/env python3
"""Estimate roll P/total-control FRF and compare a run with frozen training reference."""
import argparse,csv,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];ALL=(.1,.2,.35,.55,.8,1.1)
def load(path):
 with Path(path).open(newline='') as f:r=list(csv.DictReader(f))
 t=np.array([float(x['t_s']) for x in r]);m=(t>=12)&(t<=48);return t[m],np.array([float(x['total_roll_ratio']) for x in r])[m],np.array([float(x['p_deg_s']) for x in r])[m]
def harmonic(t,x):
 columns=[]
 for f in ALL:columns.extend((np.sin(2*np.pi*f*t),np.cos(2*np.pi*f*t)))
 X=np.column_stack(columns+[np.ones(len(t)),t-t.mean()]);b=np.linalg.lstsq(X,x,rcond=None)[0];return np.array([b[2*i]-1j*b[2*i+1] for i in range(len(ALL))])
def estimate(path):
 t,u,p=load(path);uc=harmonic(t,u);pc=harmonic(t,p);h=pc/uc;return {'input_complex':[[float(x.real),float(x.imag)] for x in uc],'rate_complex':[[float(x.real),float(x.imag)] for x in pc],'frf_magnitude':np.abs(h).tolist(),'frf_phase_deg':np.angle(h,deg=True).tolist()}
def main():
 p=argparse.ArgumentParser();p.add_argument('csv',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--reference',type=Path);p.add_argument('--apply-gate',action='store_true');a=p.parse_args();current=estimate(a.csv);result={'file':a.csv.name,'frequencies_hz':ALL,**current}
 if a.reference:
  ref=json.loads(a.reference.read_text());ratio=np.array(current['frf_magnitude'])/np.array(ref['frf_magnitude']);phase=(np.array(current['frf_phase_deg'])-np.array(ref['frf_phase_deg'])+180)%360-180;result['reference_file']=ref['file'];result['magnitude_ratio']=ratio.tolist();result['phase_difference_deg']=phase.tolist()
  if a.apply_gate:
   gate=json.loads((ROOT/'configs/rich_R3_roll_frf_gate.json').read_text());idx=[ALL.index(x) for x in gate['validated_frequency_candidates_hz']];checks={'magnitude_ratio':all(gate['minimum_magnitude_ratio']<=ratio[i]<=gate['maximum_magnitude_ratio'] for i in idx),'phase_difference':all(abs(phase[i])<=gate['maximum_absolute_phase_difference_deg'] for i in idx)};result['frozen_gate_checks']=checks;result['frozen_gate_pass']=all(checks.values())
 a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));raise SystemExit(0 if not a.apply_gate or result['frozen_gate_pass'] else 1)
if __name__=='__main__':main()
