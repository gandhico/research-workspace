#!/usr/bin/env python3
"""Audit exact dual-rate scheduling, holds, waveform, timing, and safety observe-only."""
import argparse,csv,json,math,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'));from run_rich_r3_roll_highrate_observe_xp12 import waveform
from run_rich_r3_roll_dualrate_xp12 import start_reasons
def main():
 p=argparse.ArgumentParser();p.add_argument('csv',type=Path);p.add_argument('--expect-engaged',action='store_true');p.add_argument('--cascade-confirmation',action='store_true');a=p.parse_args();design=json.loads((ROOT/'configs/rich_R3_roll_highrate_design.json').read_text())
 with a.csv.open(newline='') as f:rows=list(csv.DictReader(f))
 t=np.array([float(r['t_s']) for r in rows]);dt=np.diff(t);updates=np.array([int(r['controller_update']) for r in rows],bool);u=np.array([float(r['excitation']) for r in rows]);expected=np.array([waveform(x,design) for x in t]);bp=np.array([float(r['baseline_pitch_command']) for r in rows]);br=np.array([float(r['baseline_roll_command']) for r in rows]);held=np.ones(len(rows),bool);held[1:]=updates[1:]|(np.isclose(bp[1:],bp[:-1],atol=1e-15)&np.isclose(br[1:],br[:-1],atol=1e-15))
 first={k:float(rows[0][k]) for k in ('altitude_m','ias_kts','pitch_deg','roll_deg','p_deg_s','q_deg_s','r_deg_s','art_stab_on','override_roll','override_pitch','paused','sim_speed','replay')};reasons=start_reasons(first)
 realization=None
 if a.expect_engaged:
  sent=np.array([float(r['sent_roll_command']) for r in rows[:-1]]);actual=np.array([float(r['total_roll_ratio']) for r in rows[1:]]);realization=float(np.corrcoef(sent,actual)[0,1])
 engagement_ok=all(r['engaged']=='1' and r['controls_sent']=='1' for r in rows) if a.expect_engaged else all(r['engaged']=='0' and r['controls_sent']=='0' for r in rows)
 checks={'completeness':len(rows)>=1040,'maximum_gap':len(dt)>0 and float(dt.max())<=.071428572,'mean_rate':len(dt)>0 and 34<=1/float(dt.mean())<=36,'controller_update_count':297<=int(updates.sum())<=303,'baseline_held_between_updates':bool(np.all(held)),'exact_waveform':float(np.max(np.abs(u-expected)))<=1e-15,'waveform_bound':float(np.max(np.abs(u)))<=design['amplitude']+1e-15,'engagement':engagement_ok,'legacy_realized_input':not a.expect_engaged or a.cascade_confirmation or realization>=.99,'no_latch':all(r['excitation_latched_off']=='0' and not r['latch_reason'] for r in rows),'start_gate':not reasons,'ownership_state':all(float(r['override_roll'])==(1 if a.expect_engaged else 0) and float(r['override_pitch'])==(1 if a.expect_engaged else 0) for r in rows[1:]),'live_state':all(float(r['paused'])==0 and float(r['sim_speed'])==1 and float(r['replay'])==0 for r in rows),'safety':all(abs(float(r['roll_deg']))<=10 and max(abs(float(r[k])) for k in ('p_deg_s','q_deg_s','r_deg_s'))<=20 for r in rows),'finite':all(math.isfinite(float(v)) for r in rows for k,v in r.items() if k!='latch_reason')}
 result={'file':str(a.csv),'rows':len(rows),'effective_hz':1/float(dt.mean()),'max_gap_s':float(dt.max()),'controller_updates':int(updates.sum()),'peak_abs_excitation':float(np.max(np.abs(u))),'maximum_waveform_error':float(np.max(np.abs(u-expected))),'realized_input_lag1_correlation':realization,'start_gate_reasons':reasons,'checks':checks,'pass':all(checks.values())};print(json.dumps(result,indent=2));raise SystemExit(0 if result['pass'] else 1)
if __name__=='__main__':main()
