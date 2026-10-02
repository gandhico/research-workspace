#!/usr/bin/env python3
"""Moving-block bootstrap power audit for the proposed six-pulse roll comparison."""
import csv,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];FILES={'baseline':ROOT/'logs/rich_R3_roll_matched_baseline_20260712_203402.csv','lqr':ROOT/'logs/rich_R3_roll_matched_lqr_20260712_203707.csv'};HZ=35;GRID=np.arange(0,1.0001,1/HZ);RNG=np.random.default_rng(20260712);TRIALS=1000;BOOT=500
def detrended(t,p,start):
 pre=(t>=start-.5)&(t<start);coef=np.polyfit(t[pre]-start,p[pre],1);return np.interp(start+GRID,t,p)-np.polyval(coef,GRID)
def source(path):
 r=list(csv.DictReader(path.open(newline='')));t=np.array([float(x['t_s']) for x in r]);p=np.array([float(x['p_deg_s']) for x in r]);template=np.mean([detrended(t,p,10),-detrended(t,p,12)],axis=0);anchors=np.arange(3,9,.75).tolist()+np.arange(14,28,.75).tolist();quiet=np.array([detrended(t,p,x) for x in anchors if x+1<=t[-1]]);quiet-=quiet.mean(axis=0);return template,quiet
def metric(x):return np.trapezoid(np.abs(x.mean(axis=0)),GRID)
def main():
 s={k:source(v) for k,v in FILES.items()};upper=[];ratios=[]
 for _ in range(TRIALS):
  samples={k:np.array([s[k][0]+s[k][1][RNG.integers(len(s[k][1]))] for _ in range(6)]) for k in s};ratio=metric(samples['lqr'])/metric(samples['baseline']);ratios.append(ratio);draw=[]
  for _ in range(BOOT):
   ix=RNG.integers(0,6,6);draw.append(metric(samples['lqr'][ix])/metric(samples['baseline'][ix]))
  upper.append(np.quantile(draw,.95))
 result={'status':'pass' if np.mean(np.array(upper)<1)>=.8 else 'fail','method':'moving-block residual bootstrap; deterministic seed 20260712','virtual_experiments':TRIALS,'bootstrap_resamples_each':BOOT,'pulses_each_controller':6,'median_estimated_ratio':float(np.median(ratios)),'ratio_5_95_percentiles':np.quantile(ratios,[.05,.95]).tolist(),'median_upper_95_bound':float(np.median(upper)),'power_upper_bound_below_one':float(np.mean(np.array(upper)<1)),'required_power':.8,'claim_boundary':'offline prospective power only'};out=ROOT/'configs/rich_R3_roll_statistical_power_audit.json';out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));raise SystemExit(0 if result['status']=='pass' else 1)
if __name__=='__main__':main()
