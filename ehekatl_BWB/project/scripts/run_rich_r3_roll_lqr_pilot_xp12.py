#!/usr/bin/env python3
"""Guarded R3 discrete roll-LQR pilot; default observe-only, explicit engagement."""
import argparse,csv,math,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'backstepping'))
import Backstepping,xpc
from lqr.discrete_cascade_roll_lqr import DiscreteCascadeRollLQR
from run_rich_r3_roll_highrate_observe_xp12 import FIELDS,scalar
from run_rich_r3_roll_dualrate_xp12 import ROLL_OVERRIDE,PITCH_OVERRIDE,ROLL_YOKE,PITCH_YOKE,start_reasons,abort_reason,update_original
from design_rich_r3_roll_lqr_disturbance import disturbance
from lqr.discrete_cascade_roll_lqr import COMMAND_LIMIT,SLEW_LIMIT

def parser():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--engage',action='store_true');p.add_argument('--controller',choices=('lqr','baseline'),default='lqr');p.add_argument('--disturbance',action='store_true');p.add_argument('--duration',type=float,default=30);p.add_argument('--io-hz',type=float,default=35);p.add_argument('--fallback-hz',type=float,default=10);p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=49009);p.add_argument('--timeout-ms',type=int,default=500);p.add_argument('--out',type=Path,required=True);return p

def main():
 a=parser().parse_args();names=list(dict.fromkeys(x[1] for x in FIELDS));lqr=DiscreteCascadeRollLQR();roll=Backstepping.Backstepping(.001,33,.03);pitch=Backstepping.Backstepping(.001,39,.03);roll.SetPoint=0.;pitch.SetPoint=1.3;rows=[];period=1/a.io_hz;fallback_period=1/a.fallback_hz;start=next_io=next_fallback=time.monotonic();bias=None;fallback_roll=fallback_pitch=0.;bounded_baseline_perturbation=previous_sent_perturbation=0.;latch=False;latch_reason='';owned=False;restoration={'restored_roll_override':0,'restored_pitch_override':0,'restored_roll_yoke_error':0.,'restored_pitch_yoke_error':0.}
 with xpc.XPlaneConnect(xpHost=a.host,xpPort=a.port,timeout=a.timeout_ms) as c:
  try:
   while time.monotonic()-start<a.duration:
    now=time.monotonic()
    if now<next_io:time.sleep(min(.001,next_io-now));continue
    scheduled=next_io;next_io+=period;reply=c.getDREFs(names);done=time.monotonic();values=dict(zip(names,reply));m={field:scalar(values[dref],index) for field,dref,index in FIELDS};elapsed=now-start
    if bias is None:
     bias={'p':m['p_deg_s'],'total':m['total_roll_ratio'],'yoke_roll':m['yoke_roll_ratio'],'yoke_pitch':m['yoke_pitch_ratio']};reasons=start_reasons(m)
     if a.engage and reasons:print('Start gate BLOCKED: '+'; '.join(reasons));break
     print('Start gate PASS' if not reasons else 'Observe start state: '+'; '.join(reasons))
     if a.engage:c.sendDREF(ROLL_OVERRIDE,1);c.sendDREF(PITCH_OVERRIDE,1);owned=True;print('Both-axis ownership: ACTIVE')
    fallback_update=now>=next_fallback
    if fallback_update:
     while next_fallback<=now:next_fallback+=fallback_period
     fallback_roll=bias['yoke_roll']+update_original(roll,m['roll_deg'],m['yoke_roll_ratio']-bias['yoke_roll']);fallback_pitch=bias['yoke_pitch']+update_original(pitch,m['pitch_deg'],m['yoke_pitch_ratio']-bias['yoke_pitch'])
    p_error=m['p_deg_s']-bias['p'];total_perturbation=m['total_roll_ratio']-bias['total'];yoke_perturbation=m['yoke_roll_ratio']-bias['yoke_roll'];candidate=lqr.update(p_error,total_perturbation,yoke_perturbation);reason=abort_reason(m)
    if not all(math.isfinite(candidate[k]) for k in ('command','raw_command')):reason='non-finite LQR output'
    if reason and not latch:latch=True;latch_reason=reason;print('ROLL FALLBACK LATCHED: '+reason)
    desired_baseline=max(-COMMAND_LIMIT,min(COMMAND_LIMIT,fallback_roll-bias['yoke_roll']));bounded_baseline_perturbation=max(bounded_baseline_perturbation-SLEW_LIMIT,min(bounded_baseline_perturbation+SLEW_LIMIT,desired_baseline));bounded_baseline_roll=bias['yoke_roll']+bounded_baseline_perturbation
    lqr_roll=bias['yoke_roll']+candidate['command'];base_roll=bounded_baseline_roll if latch or a.controller=='baseline' else lqr_roll;requested_disturbance=disturbance(elapsed) if a.disturbance and not latch else 0.;sent_perturbation=base_roll-bias['yoke_roll']+requested_disturbance
    if not latch and (abs(sent_perturbation)>COMMAND_LIMIT+1e-15 or abs(sent_perturbation-previous_sent_perturbation)>SLEW_LIMIT+1e-15):latch=True;latch_reason='combined command limit exceeded';print('ROLL FALLBACK LATCHED: '+latch_reason);base_roll=bounded_baseline_roll;requested_disturbance=0.;sent_perturbation=base_roll-bias['yoke_roll']
    selected_roll=bias['yoke_roll']+sent_perturbation;selected_pitch=fallback_pitch;previous_sent_perturbation=sent_perturbation
    if a.engage:c.sendCTRL([selected_pitch,selected_roll,0.,-998.]);c.sendDREF(PITCH_YOKE,selected_pitch);c.sendDREF(ROLL_YOKE,selected_roll)
    row={'sample':len(rows),'t_s':elapsed,'dt_s':now-(rows[-1]['_tick'] if rows else start),'deadline_lateness_s':now-scheduled,'acquisition_s':done-now,'fallback_update':int(fallback_update),'controller_mode':a.controller,'disturbance_enabled':int(a.disturbance),'disturbance_command':requested_disturbance,'sent_roll_perturbation':sent_perturbation,'bounded_baseline_perturbation':bounded_baseline_perturbation,'p_bias_deg_s':bias['p'],'total_roll_bias':bias['total'],'yoke_roll_bias':bias['yoke_roll'],'yoke_pitch_bias':bias['yoke_pitch'],'p_error_deg_s':p_error,'total_roll_perturbation':total_perturbation,'yoke_roll_perturbation':yoke_perturbation,'lqr_command_perturbation':candidate['command'],'lqr_raw_command':candidate['raw_command'],'lqr_magnitude_limited':int(candidate['magnitude_limited']),'lqr_slew_limited':int(candidate['slew_limited']),'lqr_roll_command':lqr_roll,'fallback_roll_command':fallback_roll,'fallback_pitch_command':fallback_pitch,'selected_roll_command':selected_roll,'selected_pitch_command':selected_pitch,'fallback_latched':int(latch),'fallback_reason':latch_reason,'engaged':int(a.engage),'controls_sent':int(a.engage),'_tick':now,**m};rows.append(row)
  finally:
   if owned:
    c.sendDREF(PITCH_YOKE,bias['yoke_pitch']);c.sendDREF(ROLL_YOKE,bias['yoke_roll']);c.sendDREF(PITCH_OVERRIDE,0);c.sendDREF(ROLL_OVERRIDE,0)
    restored=c.getDREFs([ROLL_OVERRIDE,PITCH_OVERRIDE,ROLL_YOKE,PITCH_YOKE]);restoration={'restored_roll_override':int(scalar(restored[0],0)),'restored_pitch_override':int(scalar(restored[1],0)),'restored_roll_yoke_error':scalar(restored[2],0)-bias['yoke_roll'],'restored_pitch_yoke_error':scalar(restored[3],0)-bias['yoke_pitch']};print('Both-axis ownership: RESTORED')
 for r in rows:r.pop('_tick');r.update(restoration)
 if rows:
  a.out.parent.mkdir(parents=True,exist_ok=True)
  with a.out.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
  print(f'Saved {len(rows)} guarded roll-LQR samples: {a.out.resolve()}')

if __name__=='__main__':main()
