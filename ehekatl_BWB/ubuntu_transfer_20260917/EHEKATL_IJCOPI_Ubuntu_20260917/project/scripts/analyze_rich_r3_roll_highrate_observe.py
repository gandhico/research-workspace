#!/usr/bin/env python3
"""Apply frozen 50 Hz read-only timing, state, and noise gates."""
import argparse,csv,json,math
from pathlib import Path
import numpy as np
REQUIRED=('altitude_m','pitch_deg','roll_deg','ias_kts','p_deg_s','p_dot_deg_s2','q_deg_s','r_deg_s','yoke_roll_ratio','total_roll_ratio','aileron_wing2l_deg','aileron_wing2r_deg','roll_moment_n_m','art_stab_on','override_roll','override_pitch','paused','sim_speed','replay')
def main():
 p=argparse.ArgumentParser();p.add_argument('csv',type=Path);a=p.parse_args()
 with a.csv.open(newline='') as f:rows=list(csv.DictReader(f))
 dt=np.array([float(r['dt_s']) for r in rows[1:]]);acq=np.array([float(r['acquisition_s']) for r in rows]);finite=all(math.isfinite(float(r[k])) for r in rows for k in REQUIRED);p_rate=np.array([float(r['p_deg_s']) for r in rows]);pdot=np.array([float(r['p_dot_deg_s2']) for r in rows]);derived=np.diff(p_rate)/dt;cor=float(np.corrcoef(derived,pdot[:-1])[0,1]) if np.std(derived)>0 and np.std(pdot[:-1])>0 else 0.
 checks={'completeness':len(rows)>=396,'maximum_gap':bool(len(dt)) and float(dt.max())<=.0625,'mean_rate':bool(len(dt)) and 39<=1/float(dt.mean())<=41,'finite':finite,'observe_only':all(r['controls_sent']=='0' for r in rows),'surface_shape_values':all(abs(float(r['aileron_wing2l_deg']))<100 and abs(float(r['aileron_wing2r_deg']))<100 for r in rows),'live_state':all(float(r['paused'])==0 and float(r['sim_speed'])==1 and float(r['replay'])==0 for r in rows),'ownership_clear':all(float(r['override_roll'])==0 and float(r['override_pitch'])==0 for r in rows),'artificial_stability_on':all(float(r['art_stab_on'])==1 for r in rows),'safety':all(abs(float(r['roll_deg']))<=10 and max(abs(float(r[k])) for k in ('p_deg_s','q_deg_s','r_deg_s'))<=20 for r in rows)}
 result={'file':str(a.csv),'rows':len(rows),'effective_hz':1/float(dt.mean()),'mean_dt_s':float(dt.mean()),'max_gap_s':float(dt.max()),'mean_acquisition_s':float(acq.mean()),'max_acquisition_s':float(acq.max()),'p_rate_range_deg_s':[float(p_rate.min()),float(p_rate.max())],'p_dot_range_deg_s2':[float(pdot.min()),float(pdot.max())],'finite_difference_to_pdot_correlation':cor,'checks':checks,'pass':all(checks.values())};print(json.dumps(result,indent=2));raise SystemExit(0 if result['pass'] else 1)
if __name__=='__main__':main()
