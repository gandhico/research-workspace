#!/usr/bin/env python3
"""Audit the exact 40 Hz high-rate waveform logger without sending controls."""
import argparse,csv,json,math,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'));from run_rich_r3_roll_highrate_observe_xp12 import waveform
def main():
 p=argparse.ArgumentParser();p.add_argument('csv',type=Path);a=p.parse_args();design=json.loads((ROOT/'configs/rich_R3_roll_highrate_design.json').read_text())
 with a.csv.open(newline='') as f:rows=list(csv.DictReader(f))
 t=np.array([float(r['t_s']) for r in rows]);dt=np.diff(t);u=np.array([float(r['hypothetical_excitation']) for r in rows]);expected=np.array([waveform(x,design) for x in t]);active=(t>=design['excitation_start_s'])&(t<=design['excitation_start_s']+design['excitation_duration_s']);outside=~active
 checks={'completeness':len(rows)>=1040,'maximum_gap':len(dt)>0 and float(dt.max())<=.071428572,'mean_rate':len(dt)>0 and 34<=1/float(dt.mean())<=36,'exact_waveform':float(np.max(np.abs(u-expected)))<=1e-15,'zero_outside_window':bool(np.all(np.abs(u[outside])<=1e-15)),'active_waveform':int(np.count_nonzero(np.abs(u[active])>1e-12))>0,'amplitude_bound':float(np.max(np.abs(u)))<=design['amplitude']+1e-15,'nyquist_guard':max(design['frequencies_hz'])<=design['maximum_frequency_fraction_of_nyquist']*design['nyquist_hz'],'observe_only':all(r['controls_sent']=='0' for r in rows),'live_state':all(float(r['paused'])==0 and float(r['sim_speed'])==1 and float(r['replay'])==0 for r in rows),'ownership_clear':all(float(r['override_roll'])==0 and float(r['override_pitch'])==0 for r in rows),'safety':all(abs(float(r['roll_deg']))<=10 and max(abs(float(r[k])) for k in ('p_deg_s','q_deg_s','r_deg_s'))<=20 for r in rows),'finite':all(math.isfinite(float(v)) for r in rows for k,v in r.items() if k!='sample')}
 result={'file':str(a.csv),'rows':len(rows),'effective_hz':1/float(dt.mean()),'max_gap_s':float(dt.max()),'active_samples':int(np.count_nonzero(np.abs(u)>1e-12)),'peak_abs_hypothetical_excitation':float(np.max(np.abs(u))),'maximum_waveform_error':float(np.max(np.abs(u-expected))),'checks':checks,'pass':all(checks.values())};print(json.dumps(result,indent=2));raise SystemExit(0 if result['pass'] else 1)
if __name__=='__main__':main()
