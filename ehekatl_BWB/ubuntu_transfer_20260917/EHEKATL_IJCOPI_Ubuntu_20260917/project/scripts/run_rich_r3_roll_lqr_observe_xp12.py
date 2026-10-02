#!/usr/bin/env python3
"""Structurally observe-only integration gate for the exact R3 discrete roll LQR."""
import argparse,csv,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'backstepping'))
import Backstepping,xpc
from lqr.discrete_cascade_roll_lqr import DiscreteCascadeRollLQR
from run_rich_r3_roll_highrate_observe_xp12 import FIELDS,scalar
from run_rich_r3_roll_dualrate_xp12 import start_reasons,abort_reason,update_original
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--duration',type=float,default=30);p.add_argument('--io-hz',type=float,default=35);p.add_argument('--fallback-hz',type=float,default=10);p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=49009);p.add_argument('--timeout-ms',type=int,default=500);p.add_argument('--out',type=Path,required=True);a=p.parse_args();names=list(dict.fromkeys(x[1] for x in FIELDS));lqr=DiscreteCascadeRollLQR();roll=Backstepping.Backstepping(.001,33,.03);pitch=Backstepping.Backstepping(.001,39,.03);roll.SetPoint=0.;pitch.SetPoint=1.3;rows=[];start=next_io=next_fallback=time.monotonic();period=1/a.io_hz;fallback_period=1/a.fallback_hz;bias=None;fallback_roll=fallback_pitch=0.;latch=False;latch_reason=''
 with xpc.XPlaneConnect(xpHost=a.host,xpPort=a.port,timeout=a.timeout_ms) as c:
  while time.monotonic()-start<a.duration:
   now=time.monotonic()
   if now<next_io:time.sleep(min(.001,next_io-now));continue
   scheduled=next_io;next_io+=period;reply=c.getDREFs(names);done=time.monotonic();values=dict(zip(names,reply));m={field:scalar(values[dref],index) for field,dref,index in FIELDS};elapsed=now-start
   if bias is None:bias={'p':m['p_deg_s'],'total':m['total_roll_ratio'],'yoke_roll':m['yoke_roll_ratio'],'yoke_pitch':m['yoke_pitch_ratio']};reasons=start_reasons(m);print('Start gate PASS' if not reasons else 'Observe start state: '+'; '.join(reasons))
   fallback_update=now>=next_fallback
   if fallback_update:
    while next_fallback<=now:next_fallback+=fallback_period
    fallback_roll=bias['yoke_roll']+update_original(roll,m['roll_deg'],m['yoke_roll_ratio']-bias['yoke_roll']);fallback_pitch=bias['yoke_pitch']+update_original(pitch,m['pitch_deg'],m['yoke_pitch_ratio']-bias['yoke_pitch'])
   p_error=m['p_deg_s']-bias['p'];total_perturbation=m['total_roll_ratio']-bias['total'];yoke_perturbation=m['yoke_roll_ratio']-bias['yoke_roll'];candidate=lqr.update(p_error,total_perturbation,yoke_perturbation);reason=abort_reason(m)
   if reason and not latch:latch=True;latch_reason=reason
   selected_roll=fallback_roll if latch else bias['yoke_roll']+candidate['command'];row={'sample':len(rows),'t_s':elapsed,'dt_s':now-(rows[-1]['_tick'] if rows else start),'deadline_lateness_s':now-scheduled,'acquisition_s':done-now,'fallback_update':int(fallback_update),'p_bias_deg_s':bias['p'],'total_roll_bias':bias['total'],'yoke_roll_bias':bias['yoke_roll'],'p_error_deg_s':p_error,'total_roll_perturbation':total_perturbation,'yoke_roll_perturbation':yoke_perturbation,'lqr_command_perturbation':candidate['command'],'lqr_raw_command':candidate['raw_command'],'lqr_magnitude_limited':int(candidate['magnitude_limited']),'lqr_slew_limited':int(candidate['slew_limited']),'fallback_roll_command':fallback_roll,'fallback_pitch_command':fallback_pitch,'selected_roll_command':selected_roll,'fallback_latched':int(latch),'fallback_reason':latch_reason,'controls_sent':0,'_tick':now,**m};rows.append(row)
 for r in rows:r.pop('_tick')
 a.out.parent.mkdir(parents=True,exist_ok=True)
 with a.out.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
 print(f'Saved {len(rows)} roll-LQR observe-only samples: {a.out.resolve()}')
if __name__=='__main__':main()
