#!/usr/bin/env python3
"""Audit whether existing R3 evidence covers the stated 17-percent throttle point."""
import csv,glob,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];TARGET=.17
def main():
 files=sorted(glob.glob(str(ROOT/'logs/rich_R3_baseline_*.csv')));runs=[]
 for name in files:
  rows=list(csv.DictReader(open(name,newline='')))
  if not rows or 'throttle_engine_0' not in rows[0]:continue
  def stats(k):
   x=np.array([float(r[k]) for r in rows]);return {'mean':float(x.mean()),'min':float(x.min()),'max':float(x.max())}
  runs.append({'file':str(Path(name).relative_to(ROOT)),'throttle_engine_0':stats('throttle_engine_0'),'throttle_engine_1':stats('throttle_engine_1'),'ias_kts':stats('ias_kts'),'tas_m_s':stats('tas_m_s'),'dynamic_pressure_pa':stats('dynamic_pressure_pa')})
 throttle=np.array([x['throttle_engine_0']['mean'] for x in runs]);result={'status':'coverage_fail','stated_target_throttle':TARGET,'existing_run_count':len(runs),'existing_throttle_mean_range':[float(throttle.min()),float(throttle.max())] if len(throttle) else None,'distance_to_target':float(np.min(np.abs(throttle-TARGET))) if len(throttle) else None,'high_rate_matched_logs_have_propulsion_channels':False,'runs':runs,'decision':'current LQR is local to 2.35-percent throttle evidence and cannot be claimed at 17 percent','required_next':['read-only 35-Hz propulsion/dataref availability and timing audit at actual steady trim','freeze actual throttle/IAS/dynamic-pressure envelope','only then decide whether new identification is required'],'flight_authorized':False};out=ROOT/'configs/rich_R3_propulsion_operating_point_audit.json';out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
