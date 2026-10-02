#!/usr/bin/env python3
"""Prospective power audit for separate-reload frozen DeePC versus LQR pulses."""
import csv,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];HZ=35.;GRID=np.arange(0,1.0001,1/HZ);COUNTS=(6,12,24,48);TRIALS=300;BOOT=300;RNG=np.random.default_rng(20260810)
FILES={'lqr':ROOT/'logs/rich_R3_roll_matched_lqr_20260712_203707.csv','deepc':ROOT/'logs/rich_R3_roll_deepc_pilot_20260810_144136.csv'}
def detrended(t,p,start):
 pre=(t>=start-.5)&(t<start);coef=np.polyfit(t[pre]-start,p[pre],1);return np.interp(start+GRID,t,p)-np.polyval(coef,GRID)
def source(path):
 rows=list(csv.DictReader(path.open(newline='')));t=np.array([float(x['t_s']) for x in rows]);p=np.array([float(x['p_deg_s']) for x in rows]);template=np.mean([detrended(t,p,10),-detrended(t,p,12)],axis=0);anchors=np.arange(3,9,.75).tolist()+np.arange(14,28,.75).tolist();quiet=np.array([detrended(t,p,x) for x in anchors if x+1<=t[-1]]);quiet-=quiet.mean(axis=0);return template,quiet
def metric(x):return np.trapezoid(np.abs(x.mean(axis=0)),GRID)
def audit(count,sources):
 ratios=[];upper=[]
 for _ in range(TRIALS):
  samples={k:np.array([v[0]+v[1][RNG.integers(len(v[1]))] for _ in range(count)]) for k,v in sources.items()};ratios.append(metric(samples['deepc'])/metric(samples['lqr']));draw=[]
  for _ in range(BOOT):
   idp=RNG.integers(0,count,count);ilq=RNG.integers(0,count,count);draw.append(metric(samples['deepc'][idp])/metric(samples['lqr'][ilq]))
  upper.append(np.quantile(draw,.95))
 return {'pulses_each_controller':count,'minimum_seconds_each_run_at_3s_spacing':3*count+5,'median_ratio':float(np.median(ratios)),'ratio_5_95_percentiles':np.quantile(ratios,[.05,.95]).tolist(),'median_upper_95_bound':float(np.median(upper)),'power_upper_bound_below_one':float(np.mean(np.array(upper)<1))}
def main():
 sources={k:source(v) for k,v in FILES.items()};curve=[audit(n,sources) for n in COUNTS];qualified=[x for x in curve if x['power_upper_bound_below_one']>=.8];result={'status':'candidate' if qualified else 'underpowered','method':'independent separate-reload moving-block residual bootstrap; deterministic seed 20260810','source_files':{k:str(v.relative_to(ROOT)) for k,v in FILES.items()},'source_allocation':'LQR metric-design and DeePC design pilot only; no confirmation responses','virtual_experiments_per_count':TRIALS,'bootstrap_resamples_each':BOOT,'required_power':.8,'curve':curve,'minimum_qualified_count':qualified[0]['pulses_each_controller'] if qualified else None,'flight_authorized':False,'claim_boundary':'Prospective separate-reload power only; design evidence may overestimate effect.'};out=ROOT/'configs/rich_R3_deepc_separate_power.json';out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));raise SystemExit(0 if qualified else 1)
if __name__=='__main__':main()
