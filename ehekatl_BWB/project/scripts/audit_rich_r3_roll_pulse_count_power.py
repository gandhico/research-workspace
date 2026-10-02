#!/usr/bin/env python3
"""Map moving-block bootstrap power against repeated roll-pulse count."""
import json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from audit_rich_r3_roll_statistical_power import FILES,GRID,source,metric
RNG=np.random.default_rng(20260713);COUNTS=(6,12,24,48);TRIALS=300;BOOT=300
def audit_count(count,sources):
 ratios=[];upper=[]
 for _ in range(TRIALS):
  samples={k:np.array([sources[k][0]+sources[k][1][RNG.integers(len(sources[k][1]))] for _ in range(count)]) for k in sources};ratios.append(metric(samples['lqr'])/metric(samples['baseline']));draw=[]
  for _ in range(BOOT):
   il=RNG.integers(0,count,count);ib=RNG.integers(0,count,count);draw.append(metric(samples['lqr'][il])/metric(samples['baseline'][ib]))
  upper.append(np.quantile(draw,.95))
 return {'pulse_count_each_controller':count,'minimum_seconds_at_3s_spacing':3*count+5,'median_ratio':float(np.median(ratios)),'median_upper_95_bound':float(np.median(upper)),'power_upper_bound_below_one':float(np.mean(np.array(upper)<1))}
def main():
 sources={k:source(v) for k,v in FILES.items()};curve=[audit_count(n,sources) for n in COUNTS];qualified=[x for x in curve if x['power_upper_bound_below_one']>=.8];result={'status':'practical_candidate_found' if qualified else 'no_practical_candidate_through_48','method':'same measured moving-block residual bootstrap; independent controller resampling; deterministic seed 20260713','virtual_experiments_per_count':TRIALS,'bootstrap_resamples_each':BOOT,'required_power':.8,'curve':curve,'minimum_qualified_count':qualified[0]['pulse_count_each_controller'] if qualified else None,'decision':'no flight authorization; duration and 243-case cumulative safety audit still required even if power qualifies'};out=ROOT/'configs/rich_R3_roll_pulse_count_power.json';out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));raise SystemExit(0 if qualified else 1)
if __name__=='__main__':main()
