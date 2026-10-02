#!/usr/bin/env python3
"""Strict observe-only gate for the frozen R4 dual-rate identification design."""
import argparse,csv,json,math,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from run_rich_r3_roll_highrate_observe_xp12 import waveform
_DictReader=csv.DictReader
class QbarReader(_DictReader):
 def __next__(self):
  row=super().__next__();row.setdefault('dynamic_pressure_pa',str(.5*float(row['air_density_kg_m3'])*float(row['tas_m_s'])**2));return row
csv.DictReader=QbarReader
def main():
 p=argparse.ArgumentParser();p.add_argument('csv',type=Path);a=p.parse_args();design=json.loads((ROOT/'configs/rich_R4_roll_highrate_design.json').read_text());rows=list(csv.DictReader(a.csv.open(newline='')));t=np.array([float(r['t_s']) for r in rows]);dt=np.diff(t);updates=np.array([int(r['controller_update']) for r in rows],bool);u=np.array([float(r['excitation']) for r in rows]);expected=np.array([waveform(x,design) for x in t]);bp=np.array([float(r['baseline_pitch_command']) for r in rows]);br=np.array([float(r['baseline_roll_command']) for r in rows]);held=np.ones(len(rows),bool);held[1:]=updates[1:]|(np.isclose(bp[1:],bp[:-1],atol=1e-15)&np.isclose(br[1:],br[:-1],atol=1e-15));first=rows[0];reasons=[]
 for failed,text in ((abs(float(first['altitude_m'])-1760)>100,'altitude outside R4'),(abs(float(first['ias_kts'])-47)>1.5,'IAS outside R4'),(abs(float(first['dynamic_pressure_pa'])-353.5)>25,'dynamic pressure outside R4'),(abs(float(first['cockpit_throttle_engine_0'])-.04142)>.008,'throttle outside R4'),(abs(float(first['pitch_deg']))>5,'pitch outside start envelope'),(abs(float(first['roll_deg']))>5,'roll outside start envelope'),(max(abs(float(first[k])) for k in ('p_deg_s','q_deg_s','r_deg_s'))>1,'body rate outside start envelope'),(float(first['art_stab_on'])!=1,'artificial stability mismatch'),(float(first['override_roll'])!=0 or float(first['override_pitch'])!=0,'axis already owned'),(float(first['paused'])!=0 or float(first['sim_speed'])!=1 or float(first['replay'])!=0,'simulator state invalid')):
  if failed:reasons.append(text)
 checks={'completeness':len(rows)>=1040,'maximum_gap':len(dt)>0 and float(dt.max())<=.071428572,'mean_rate':len(dt)>0 and 34<=1/float(dt.mean())<=36,'controller_updates':297<=int(updates.sum())<=303,'held':np.all(held),'exact_waveform':np.max(np.abs(u-expected))<=1e-15,'waveform_bound':np.max(np.abs(u))<=.0001+1e-15,'observe_only':all(r['engaged']=='0' and r['controls_sent']=='0' for r in rows),'no_latch':all(r['excitation_latched_off']=='0' and not r['latch_reason'] for r in rows),'start_gate':not reasons,'ownership_clear':all(float(r['override_roll'])==0 and float(r['override_pitch'])==0 for r in rows),'live':all(float(r['paused'])==0 and float(r['sim_speed'])==1 and float(r['replay'])==0 for r in rows),'safe':all(abs(float(r['pitch_deg']))<=10 and abs(float(r['roll_deg']))<=10 and max(abs(float(r[k])) for k in ('p_deg_s','q_deg_s','r_deg_s'))<=20 for r in rows),'finite':all(math.isfinite(float(v)) for r in rows for k,v in r.items() if k!='latch_reason')};checks={k:bool(v) for k,v in checks.items()};out={'file':str(a.csv),'rows':len(rows),'effective_hz':1/float(dt.mean()),'max_gap_s':float(dt.max()),'controller_updates':int(updates.sum()),'peak_excitation':float(np.max(np.abs(u))),'waveform_error':float(np.max(np.abs(u-expected))),'start_reasons':reasons,'checks':checks,'pass':all(checks.values())};print(json.dumps(out,indent=2));raise SystemExit(0 if out['pass'] else 1)
if __name__=='__main__':main()
