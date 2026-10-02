#!/usr/bin/env python3
"""Dual-rate R3 roll experiment: 35 Hz I/O, original backstepping updates at 10 Hz."""
import argparse,csv,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'backstepping'))
import Backstepping,xpc
from run_rich_r3_roll_highrate_observe_xp12 import FIELDS,scalar,waveform
ROLL_OVERRIDE='sim/operation/override/override_joystick_roll';PITCH_OVERRIDE='sim/operation/override/override_joystick_pitch';ROLL_YOKE='sim/joystick/yoke_roll_ratio';PITCH_YOKE='sim/joystick/yoke_pitch_ratio'
def update_original(controller,feedback,control):controller.update(feedback,control);return float(controller.output)
def start_reasons(m):
 checks=((abs(m['altitude_m']-1700)>100,'altitude outside R3'),(abs(m['ias_kts']-39)>2,'IAS outside R3'),(abs(m['pitch_deg']-1.3)>3.7,'pitch outside start envelope'),(abs(m['roll_deg'])>5,'roll outside start envelope'),(max(abs(m[k]) for k in ('p_deg_s','q_deg_s','r_deg_s'))>2,'body rate outside start envelope'),(m['art_stab_on']!=1,'artificial stability mismatch'),(m['override_roll']!=0 or m['override_pitch']!=0,'axis already owned'),(m['paused']!=0,'simulator paused'),(m['sim_speed']!=1,'simulation speed mismatch'),(m['replay']!=0,'replay active'));return [text for failed,text in checks if failed]
def abort_reason(m):
 if abs(m['pitch_deg'])>10:return 'pitch envelope exceeded'
 if abs(m['roll_deg'])>10:return 'roll envelope exceeded'
 if max(abs(m[k]) for k in ('p_deg_s','q_deg_s','r_deg_s'))>20:return 'body-rate envelope exceeded'
 if m['paused']!=0 or m['sim_speed']!=1 or m['replay']!=0:return 'simulator state invalid'
 return ''
def parser():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--engage',action='store_true');p.add_argument('--duration',type=float,default=30);p.add_argument('--io-hz',type=float,default=35);p.add_argument('--controller-hz',type=float,default=10);p.add_argument('--design',type=Path,default=ROOT/'configs/rich_R3_roll_highrate_design.json');p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=49009);p.add_argument('--timeout-ms',type=int,default=500);p.add_argument('--out',type=Path,required=True);return p
def main():
 a=parser().parse_args();design=json.loads(a.design.read_text());roll=Backstepping.Backstepping(.001,33,.03);pitch=Backstepping.Backstepping(.001,39,.03);roll.SetPoint=0.;pitch.SetPoint=1.3;names=list(dict.fromkeys(x[1] for x in FIELDS));rows=[];period=1/a.io_hz;control_period=1/a.controller_hz;start=next_io=next_control=time.monotonic();baseline_pitch=baseline_roll=0.;trim_pitch=trim_roll=None;latch=False;latch_reason='';owned=False
 with xpc.XPlaneConnect(xpHost=a.host,xpPort=a.port,timeout=a.timeout_ms) as c:
  try:
   while time.monotonic()-start<a.duration:
    now=time.monotonic()
    if now<next_io:time.sleep(min(.001,next_io-now));continue
    scheduled=next_io;next_io+=period;reply=c.getDREFs(names);done=time.monotonic();values=dict(zip(names,reply));m={field:scalar(values[dref],index) for field,dref,index in FIELDS};m['dynamic_pressure_pa']=.5*m['air_density_kg_m3']*m['tas_m_s']**2;elapsed=now-start
    if trim_pitch is None:
     trim_pitch=m['yoke_pitch_ratio'];trim_roll=m['yoke_roll_ratio'];reasons=start_reasons(m)
     if a.engage and reasons:print('Start gate BLOCKED: '+'; '.join(reasons));break
     print('Start gate PASS' if not reasons else 'Observe start state: '+'; '.join(reasons))
     if a.engage:c.sendDREF(ROLL_OVERRIDE,1);c.sendDREF(PITCH_OVERRIDE,1);owned=True;print('Both-axis ownership: ACTIVE')
    control_update=now>=next_control
    if control_update:
     while next_control<=now:next_control+=control_period
     baseline_roll=trim_roll+update_original(roll,m['roll_deg'],m['yoke_roll_ratio']-trim_roll);baseline_pitch=trim_pitch+update_original(pitch,m['pitch_deg'],m['yoke_pitch_ratio']-trim_pitch)
    reason=abort_reason(m)
    if reason and not latch:latch=True;latch_reason=reason
    excitation=0. if latch else waveform(elapsed,design);sent_roll=baseline_roll+excitation;sent_pitch=baseline_pitch
    if a.engage:c.sendCTRL([sent_pitch,sent_roll,0.,-998.]);c.sendDREF(PITCH_YOKE,sent_pitch);c.sendDREF(ROLL_YOKE,sent_roll)
    row={'sample':len(rows),'t_s':elapsed,'dt_s':now-(rows[-1]['_tick'] if rows else start),'deadline_lateness_s':now-scheduled,'acquisition_s':done-now,'controller_update':int(control_update),'baseline_pitch_command':baseline_pitch,'baseline_roll_command':baseline_roll,'excitation':excitation,'sent_pitch_command':sent_pitch,'sent_roll_command':sent_roll,'engaged':int(a.engage),'controls_sent':int(a.engage),'excitation_latched_off':int(latch),'latch_reason':latch_reason,'_tick':now,**m};rows.append(row)
  finally:
   if owned:c.sendDREF(PITCH_YOKE,trim_pitch);c.sendDREF(ROLL_YOKE,trim_roll);c.sendDREF(PITCH_OVERRIDE,0);c.sendDREF(ROLL_OVERRIDE,0);print('Both-axis ownership: RESTORED')
 for r in rows:r.pop('_tick')
 a.out.parent.mkdir(parents=True,exist_ok=True)
 with a.out.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
 print(f'Saved {len(rows)} dual-rate samples: {a.out.resolve()}')
if __name__=='__main__':main()
