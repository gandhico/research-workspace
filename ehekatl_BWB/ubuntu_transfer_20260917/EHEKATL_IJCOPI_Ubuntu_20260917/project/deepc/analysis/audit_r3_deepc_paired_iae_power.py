#!/usr/bin/env python3
"""Power audit using paired mean per-pulse integrated absolute P response."""
import json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'deepc/analysis'))
from audit_r3_deepc_separate_power import FILES,GRID,source
COUNTS=(4,6,8,12,16,24);TRIALS=300;BOOT=300;RNG=np.random.default_rng(20260812)
def iae(samples):return float(np.mean(np.trapezoid(np.abs(samples),GRID,axis=1)))
def audit(count,sources):
 ratios=[];upper=[];available=min(len(v[1]) for v in sources.values())
 for _ in range(TRIALS):
  anchors=RNG.integers(0,available,count);samples={k:np.array([v[0]+v[1][i] for i in anchors]) for k,v in sources.items()};ratios.append(iae(samples['deepc'])/iae(samples['lqr']));draw=[]
  for _ in range(BOOT):
   ix=RNG.integers(0,count,count);draw.append(iae(samples['deepc'][ix])/iae(samples['lqr'][ix]))
  upper.append(np.quantile(draw,.95))
 return {'paired_pulses_each_controller':count,'minimum_seconds_at_6s_per_pair_plus_settle':6*count+8,'median_ratio':float(np.median(ratios)),'ratio_5_95_percentiles':np.quantile(ratios,[.05,.95]).tolist(),'median_upper_95_bound':float(np.median(upper)),'power_upper_bound_below_one':float(np.mean(np.array(upper)<1))}
def main():
 sources={k:source(v) for k,v in FILES.items()};curve=[audit(n,sources) for n in COUNTS];qualified=[x for x in curve if x['power_upper_bound_below_one']>=.8];result={'status':'paired_iae_candidate' if qualified else 'underpowered','primary_estimand':'ratio of mean per-pulse integral absolute detrended P response over 1 second','method':'paired moving-block residual bootstrap using common local-background index; deterministic seed 20260812','source_files':{k:str(v.relative_to(ROOT)) for k,v in FILES.items()},'virtual_experiments_per_count':TRIALS,'bootstrap_resamples_each':BOOT,'required_power':.8,'curve':curve,'minimum_qualified_count':qualified[0]['paired_pulses_each_controller'] if qualified else None,'flight_authorized':False,'claim_boundary':'Prospective paired IAE power only; no flight authorization.'};out=ROOT/'configs/rich_R3_deepc_paired_iae_power.json';out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));raise SystemExit(0 if qualified else 1)
if __name__=='__main__':main()
