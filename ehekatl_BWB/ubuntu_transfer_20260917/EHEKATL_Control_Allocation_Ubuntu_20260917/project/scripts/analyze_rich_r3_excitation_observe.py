#!/usr/bin/env python3
"""Audit an R3 single-axis excitation wrapper in observe-only mode."""
import argparse,csv,json,math
from pathlib import Path
from rich_mission import gate_reasons,load_campaign

def truth(x):return x.strip().lower()=="true"
def main():
 p=argparse.ArgumentParser();p.add_argument('csv',type=Path);p.add_argument('--axis',required=True,choices=('pitch','roll'));p.add_argument('--expect-engaged',action='store_true');a=p.parse_args()
 if a.axis=='pitch':
  selected=json.loads(Path('configs/rich_R3_pitch_revised_design.json').read_text());amp=selected['amplitude'];expected_frequencies=selected['frequencies_hz']
 else:
  selected=json.loads(Path('configs/rich_R3_excitation_design.json').read_text());amp=selected['axes']['roll']['selected_amplitude'];expected_frequencies=selected['frequencies_hz']
 with a.csv.open(newline='') as f:rows=list(csv.DictReader(f))
 if not rows:raise SystemExit('FAIL: empty log')
 t=[float(r['t_s']) for r in rows];dt=[b-a for a,b in zip(t,t[1:])];u=[float(r['identification_excitation']) for r in rows]
 rich=('art_stab_on','left_aileron_1_def_deg','right_aileron_1_def_deg','left_elevator_1_def_deg','right_elevator_1_def_deg','override_joystick','override_roll','override_pitch','override_flightcontrol','override_surfaces')
 finite=all(r.get(k,'')!='' and math.isfinite(float(r[k])) for r in rows for k in rich)
 outside=all(abs(value)<=1e-15 for time,value in zip(t,u) if time<10 or time>50);active=sum(abs(value)>1e-12 for value in u)
 safe=all(abs(float(r['pitch_deg']))<=10 and abs(float(r['roll_deg']))<=10 and max(abs(float(r[k])) for k in ('p_deg_s','q_deg_s','r_deg_s'))<=20 for r in rows)
 first=rows[0];sample={'altitude_m':float(first['alt_m']),'ias_kts':float(first['ias_kts']),'pitch_deg':float(first['pitch_deg']),'roll_deg':float(first['roll_deg']),'p_deg_s':float(first['p_deg_s']),'q_deg_s':float(first['q_deg_s']),'r_deg_s':float(first['r_deg_s']),'art_stab_on':float(first['art_stab_on']),'paused':float(first['sim_paused']),'sim_speed':float(first['sim_speed']),'replay':float(first['replay_mode']),'override_joystick':float(first['override_joystick']),'override_roll':float(first['override_roll']),'override_pitch':float(first['override_pitch']),'override_flightcontrol':float(first['override_flightcontrol']),'override_surfaces':float(first['override_surfaces'])};reasons=gate_reasons(load_campaign(),'R3',sample)
 engaged=[truth(r['engaged']) for r in rows];realization=None
 if a.expect_engaged:
  sent_key,total_key=('sent_ctrl_0','total_pitch_ratio') if a.axis=='pitch' else ('sent_ctrl_1','total_roll_ratio');x=[float(r[sent_key]) for r in rows[:-1]];y=[float(r[total_key]) for r in rows[1:]];mx=sum(x)/len(x);my=sum(y)/len(y);num=sum((a-mx)*(b-my) for a,b in zip(x,y));den=math.sqrt(sum((a-mx)**2 for a in x)*sum((b-my)**2 for b in y));realization=num/den if den else 0.
 checks={'completeness':len(rows)>=594,'timing':bool(dt) and max(dt)<=.25,'engagement':all(engaged) if a.expect_engaged else not any(engaged),'axis':all(r['identification_axis']==a.axis for r in rows),'frequencies':all([float(x) for x in r['identification_frequencies_hz'].split(',')]==expected_frequencies for r in rows),'waveform_window':outside and active>0,'waveform_bound':max(map(abs,u))<=amp+1e-12,'no_latch_abort':not any(truth(r['identification_latched_off']) or r['identification_abort_reason'].strip() for r in rows),'zero_recovery':all(float(r['recovery_pulse'])==0 for r in rows),'no_saturation':not any(truth(r['ctrl_0_saturated']) or truth(r['ctrl_1_saturated']) for r in rows),'realized_input':not a.expect_engaged or realization>=.99,'rich_finite':finite,'safety':safe,'start_gate':not reasons}
 result={'file':str(a.csv),'axis':a.axis,'rows':len(rows),'max_gap_s':max(dt),'active_samples':active,'peak_abs_excitation':max(map(abs,u)),'selected_amplitude':amp,'realized_input_lag1_correlation':realization,'start_gate_reasons':reasons,'checks':checks,'pass':all(checks.values())};print(json.dumps(result,indent=2));raise SystemExit(0 if result['pass'] else 1)
if __name__=='__main__':main()
