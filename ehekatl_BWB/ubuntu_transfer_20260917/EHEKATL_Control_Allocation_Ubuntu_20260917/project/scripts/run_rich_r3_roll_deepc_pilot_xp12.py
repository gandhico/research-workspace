#!/usr/bin/env python3
"""Guarded R3 roll DeePC design pilot; default observe-only, explicit engagement."""
import argparse,csv,json,math,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'backstepping')]
import Backstepping,xpc
from deepc.src.r3_roll_runtime import R3RollDeePCRuntime
from run_rich_r3_roll_highrate_observe_xp12 import FIELDS,scalar
from run_rich_r3_roll_dualrate_xp12 import ROLL_OVERRIDE,PITCH_OVERRIDE,ROLL_YOKE,PITCH_YOKE,start_reasons,abort_reason,update_original
from design_rich_r3_roll_lqr_disturbance import disturbance

CONFIG=ROOT/'deepc/configs/rich_R3_deepc_pilot.json'
def parser():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--engage',action='store_true');p.add_argument('--disturbance',action='store_true');p.add_argument('--duration',type=float,default=30);p.add_argument('--io-hz',type=float,default=35);p.add_argument('--fallback-hz',type=float,default=10);p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=49009);p.add_argument('--timeout-ms',type=int,default=500);p.add_argument('--out',type=Path,required=True);return p
def history(prefix,values):return {f'{prefix}_{i}':float(v) for i,v in enumerate(values)}
def main():
 a=parser().parse_args();cfg=json.loads(CONFIG.read_text());limit=cfg['limits']['command'];slew=cfg['limits']['slew_per_sample'];names=list(dict.fromkeys(x[1] for x in FIELDS));deepc=R3RollDeePCRuntime();roll=Backstepping.Backstepping(.001,33,.03);pitch=Backstepping.Backstepping(.001,39,.03);roll.SetPoint=0.;pitch.SetPoint=1.3;rows=[];period=1/a.io_hz;fallback_period=1/a.fallback_hz;start=next_io=next_fallback=time.monotonic();bias=None;fallback_roll=fallback_pitch=0.;bounded_fallback=previous_sent=0.;latch=False;latch_reason='';owned=False;initial=None;restoration={'restored_roll_override':0,'restored_pitch_override':0,'restored_roll_yoke_error':0.,'restored_pitch_yoke_error':0.}
 with xpc.XPlaneConnect(xpHost=a.host,xpPort=a.port,timeout=a.timeout_ms) as c:
  try:
   while time.monotonic()-start<a.duration:
    now=time.monotonic()
    if now<next_io:time.sleep(min(.001,next_io-now));continue
    scheduled=next_io;next_io+=period;reply=c.getDREFs(names);acquired=time.monotonic();values=dict(zip(names,reply));m={field:scalar(values[dref],index) for field,dref,index in FIELDS};m['dynamic_pressure_pa']=.5*m['air_density_kg_m3']*m['tas_m_s']**2;elapsed=now-start
    if bias is None:
     bias={'p':m['p_deg_s'],'total':m['total_roll_ratio'],'yoke_roll':m['yoke_roll_ratio'],'yoke_pitch':m['yoke_pitch_ratio']};initial={'ro':m['override_roll'],'po':m['override_pitch'],'ry':m['yoke_roll_ratio'],'py':m['yoke_pitch_ratio']};reasons=start_reasons(m)
     if a.engage and reasons:print('Start gate BLOCKED: '+'; '.join(reasons));break
     print('Start gate PASS' if not reasons else 'Observe start state: '+'; '.join(reasons))
     if a.engage:c.sendDREF(ROLL_OVERRIDE,1);c.sendDREF(PITCH_OVERRIDE,1);owned=True;print('Both-axis ownership: ACTIVE')
    fallback_update=now>=next_fallback
    if fallback_update:
     while next_fallback<=now:next_fallback+=fallback_period
     fallback_roll=bias['yoke_roll']+update_original(roll,m['roll_deg'],m['yoke_roll_ratio']-bias['yoke_roll']);fallback_pitch=bias['yoke_pitch']+update_original(pitch,m['pitch_deg'],m['yoke_pitch_ratio']-bias['yoke_pitch'])
    desired=max(-limit,min(limit,fallback_roll-bias['yoke_roll']));bounded_fallback=max(bounded_fallback-slew,min(bounded_fallback+slew,desired));p_error=m['p_deg_s']-bias['p'];pre_u=deepc.u_history.copy();pre_p=deepc.p_history.copy();began=time.perf_counter();result=deepc.update(p_error);runtime_ms=(time.perf_counter()-began)*1000.;reason=abort_reason(m)
    if result['fallback_required']:reason=result['reason']
    if not math.isfinite(result['command']) or runtime_ms>=cfg['pilot_gates']['maximum_runtime_ms']:reason='DeePC runtime invalid or deadline missed'
    if reason and not latch:latch=True;latch_reason=reason;print('DEEPC FALLBACK LATCHED: '+reason)
    requested_disturbance=disturbance(elapsed) if a.disturbance and not latch else 0.;base=bounded_fallback if latch else result['command'];sent=base+requested_disturbance
    if latch:bounded_fallback=max(previous_sent-slew,min(previous_sent+slew,bounded_fallback));sent=bounded_fallback
    if not latch and (abs(sent)>limit+1e-15 or abs(sent-previous_sent)>slew+1e-15):
     latch=True;latch_reason='combined command limit exceeded';deepc.latch(latch_reason);requested_disturbance=0.;sent=bounded_fallback;print('DEEPC FALLBACK LATCHED: '+latch_reason)
    selected_roll=bias['yoke_roll']+sent;selected_pitch=fallback_pitch;previous_sent=sent
    if a.engage:c.sendCTRL([selected_pitch,selected_roll,0.,-998.]);c.sendDREF(PITCH_YOKE,selected_pitch);c.sendDREF(ROLL_YOKE,selected_roll)
    rows.append({'sample':len(rows),'t_s':elapsed,'dt_s':now-(rows[-1]['_tick'] if rows else start),'deadline_lateness_s':now-scheduled,'acquisition_s':acquired-now,'runtime_ms':runtime_ms,'fallback_update':int(fallback_update),'disturbance_enabled':int(a.disturbance),'disturbance_command':requested_disturbance,'p_bias_deg_s':bias['p'],'p_error_deg_s':p_error,'total_roll_bias':bias['total'],'yoke_roll_bias':bias['yoke_roll'],'yoke_pitch_bias':bias['yoke_pitch'],'deepc_command':result['command'],'deepc_converged':int(result['converged']),'deepc_iterations':result['iterations'],'deepc_fallback_required':int(result['fallback_required']),'deepc_fallback_reason':result['reason'],'bounded_fallback_perturbation':bounded_fallback,'fallback_roll_command':fallback_roll,'fallback_pitch_command':fallback_pitch,'sent_roll_perturbation':sent,'selected_roll_command':selected_roll,'selected_pitch_command':selected_pitch,'fallback_latched':int(latch),'fallback_reason':latch_reason,'engaged':int(a.engage),'controls_sent':int(a.engage),**history('pre_u_history',pre_u),**history('pre_p_history',pre_p),**history('post_u_history',deepc.u_history),**history('post_p_history',deepc.p_history),'_tick':now,**m})
  finally:
   if owned:
    c.sendDREF(PITCH_YOKE,initial['py']);c.sendDREF(ROLL_YOKE,initial['ry']);c.sendDREF(PITCH_OVERRIDE,initial['po']);c.sendDREF(ROLL_OVERRIDE,initial['ro']);restored=c.getDREFs([ROLL_OVERRIDE,PITCH_OVERRIDE,ROLL_YOKE,PITCH_YOKE]);restoration={'restored_roll_override':int(scalar(restored[0],0)),'restored_pitch_override':int(scalar(restored[1],0)),'restored_roll_yoke_error':scalar(restored[2],0)-initial['ry'],'restored_pitch_yoke_error':scalar(restored[3],0)-initial['py']};print('Both-axis ownership: RESTORED')
 for r in rows:r.pop('_tick');r.update(restoration)
 if rows:
  a.out.parent.mkdir(parents=True,exist_ok=True)
  with a.out.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
  print(f'Saved {len(rows)} guarded DeePC samples: {a.out.resolve()}')
if __name__=='__main__':main()
