#!/usr/bin/env python3
"""Apply frozen Stage-5 pitch-rate confirmation gates to one saved CSV."""

import argparse, csv, math
from pathlib import Path

def corr(a,b):
    ma=sum(a)/len(a);mb=sum(b)/len(b);aa=[x-ma for x in a];bb=[x-mb for x in b]
    den=(sum(x*x for x in aa)*sum(x*x for x in bb))**.5
    return sum(x*y for x,y in zip(aa,bb))/den if den else float('nan')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('log',type=Path);a=p.parse_args()
    with a.log.open(newline='') as f:r=list(csv.DictReader(f))
    v=lambda k:[float(x[k]) for x in r];t=v('t_s');q=v('q_deg_s');pitch=v('pitch_deg')
    pre=[i for i,x in enumerate(t) if x<10];post=[i for i,x in enumerate(t) if 10<=x<20];final=[i for i,x in enumerate(t) if x>=25]
    q0=sum(q[i] for i in pre)/len(pre);dq=[x-q0 for x in q];peak=max(abs(dq[i]) for i in post);fmax=max(abs(dq[i]) for i in final)
    frms=math.sqrt(sum(dq[i]**2 for i in final)/len(final));ratio=frms/peak
    sent=v('sent_ctrl_0');total=v('total_pitch_ratio');gates={
      'rows':len(r)==300,'gap':max(b-a for a,b in zip(t,t[1:]))<=.25,
      'engaged':all(x['engaged']=='True' for x in r),'start':all(x['start_allowed']=='True' for x in r),
      'safety':not any(x['experiment_latched_off']=='True' or x['abort_reason'] for x in r),
      'live':all(float(x['sim_paused'])==0 and float(x['sim_speed'])>0 and float(x['replay_mode'])==0 for x in r),
      'measurable':peak>=.008,'final_max':fmax<=.015,'decay_ratio':ratio<=.45,
      'attitude_envelope':max(max(abs(x) for x in pitch),max(abs(float(x['roll_deg'])) for x in r))<10,
      'rate_envelope':max(abs(float(x[k])) for x in r for k in ('p_deg_s','q_deg_s','r_deg_s'))<20,
    }
    print('file',a.log);print('q_pre_mean',q0);print('peak_delta_q',peak);print('final5_max_delta_q',fmax);print('final5_rms_delta_q',frms);print('decay_ratio',ratio)
    print('sent_total_lag1_corr',corr(sent[:-1],total[1:]));print('final_pitch_offset',max(abs(pitch[i]-sum(pitch[j] for j in pre)/len(pre)) for i in final))
    for k,x in gates.items():print('gate_'+k,'PASS' if x else 'FAIL')
    print('decision','PASS' if all(gates.values()) else 'FAIL')

if __name__=='__main__':main()
