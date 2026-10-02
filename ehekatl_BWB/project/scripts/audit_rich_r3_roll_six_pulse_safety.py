#!/usr/bin/env python3
"""Audit the proposed six-pulse waveform over all 243 frozen plant cases."""
import itertools,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
import design_rich_r3_roll_lqr_disturbance as d
def main():
 d.STARTS=(7.,10.,13.,16.,19.,22.);m=json.loads((ROOT/'configs/rich_R3_roll_discrete_cascade.json').read_text());yt=m['yoke_to_total']['selected'];sp=m['surface_to_p']['selected'];at=yt['beta'][0];b0,b1=yt['beta'][1:];g=m['total_to_surface']['static_gain'];ap,c=sp['beta'];cases=[]
 for scales in itertools.product((.75,1.,1.25),repeat=5):
  A,B=d.matrices(at*scales[0],b0*scales[1],b1*scales[2],g,ap*scales[3],c*scales[4]);cases.append({mode:d.simulate(A,B,mode) for mode in ('backstepping','lqr')})
 summary={'cases':len(cases),'pulse_starts_s':d.STARTS,'pulse_duration_s':d.DURATION,'pulse_amplitude':d.AMPLITUDE,'maximum_sent_command':max(x[m]['peak_abs_sent_command'] for x in cases for m in x),'maximum_sent_slew':max(x[m]['maximum_sent_slew'] for x in cases for m in x),'maximum_roll_deg':max(x[m]['peak_abs_roll_deg'] for x in cases for m in x),'maximum_final_5s_p_deg_s':max(x[m]['final_5s_max_abs_p_deg_s'] for x in cases for m in x),'sent_limit_exceeded_samples':sum(x[m]['sent_limit_exceeded_samples'] for x in cases for m in x)};passed=summary['maximum_sent_command']<=.0002+1e-15 and summary['maximum_sent_slew']<=.00005+1e-15 and summary['maximum_roll_deg']<=.05 and summary['maximum_final_5s_p_deg_s']<=.002 and summary['sent_limit_exceeded_samples']==0;out={'status':'pass' if passed else 'fail','summary':summary,'pass':passed,'claim_boundary':'offline repeated-waveform command/safety audit only'};path=ROOT/'configs/rich_R3_roll_six_pulse_safety_audit.json';path.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));raise SystemExit(0 if passed else 1)
if __name__=='__main__':main()
