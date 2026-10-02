#!/usr/bin/env python3
"""Minimal one-batch high-rate roll diagnostic with no control-send path."""
import argparse,csv,json,math,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'));import xpc
FIELDS=(
 ('altitude_m','sim/flightmodel/position/elevation',0),('pitch_deg','sim/flightmodel/position/theta',0),('roll_deg','sim/flightmodel/position/phi',0),('alpha_deg','sim/flightmodel/position/alpha',0),('ias_kts','sim/flightmodel/position/indicated_airspeed',0),('tas_m_s','sim/flightmodel/position/true_airspeed',0),('air_density_kg_m3','sim/weather/rho',0),
 ('cockpit_throttle_engine_0','sim/cockpit2/engine/actuators/throttle_ratio',0),('cockpit_throttle_engine_1','sim/cockpit2/engine/actuators/throttle_ratio',1),('hardware_throttle_engine_0','sim/cockpit2/engine/actuators/hardware_throttle_ratio',0),('hardware_throttle_engine_1','sim/cockpit2/engine/actuators/hardware_throttle_ratio',1),('engine_used_ratio_0','sim/flightmodel2/engines/throttle_used_ratio',0),('engine_used_ratio_1','sim/flightmodel2/engines/throttle_used_ratio',1),('throttle_engine_0','sim/flightmodel/engine/ENGN_thro',0),('throttle_engine_1','sim/flightmodel/engine/ENGN_thro',1),('throttle_used_engine_0','sim/flightmodel/engine/ENGN_thro_use',0),('throttle_used_engine_1','sim/flightmodel/engine/ENGN_thro_use',1),('n1_engine_0_pct','sim/flightmodel/engine/ENGN_N1_',0),('n1_engine_1_pct','sim/flightmodel/engine/ENGN_N1_',1),('thrust_engine_0_n','sim/flightmodel/engine/POINT_thrust',0),('thrust_engine_1_n','sim/flightmodel/engine/POINT_thrust',1),
 ('p_deg_s','sim/flightmodel/position/P',0),('p_dot_deg_s2','sim/flightmodel/position/P_dot',0),('q_deg_s','sim/flightmodel/position/Q',0),('r_deg_s','sim/flightmodel/position/R',0),
 ('yoke_pitch_ratio','sim/joystick/yoke_pitch_ratio',0),('yoke_roll_ratio','sim/joystick/yoke_roll_ratio',0),('total_pitch_ratio','sim/cockpit2/controls/total_pitch_ratio',0),('total_roll_ratio','sim/cockpit2/controls/total_roll_ratio',0),('aileron_wing2l_deg','sim/flightmodel/controls/ail1_def',8),('aileron_wing2r_deg','sim/flightmodel/controls/ail1_def',9),('roll_moment_n_m','sim/flightmodel/forces/L_total',0),
 ('art_stab_on','sim/cockpit/switches/art_stab_on',0),('override_roll','sim/operation/override/override_joystick_roll',0),('override_pitch','sim/operation/override/override_joystick_pitch',0),('paused','sim/time/paused',0),('sim_speed','sim/time/sim_speed',0),('replay','sim/operation/prefs/replay_mode',0))
def scalar(value,index):
 while isinstance(value,(list,tuple)):
  if not value:raise ValueError('empty dataref value')
  value=value[min(index,len(value)-1)];index=0
 return float(value)
def waveform(t,design):
 z=t-design['excitation_start_s'];duration=design['excitation_duration_s']
 if z<0 or z>duration:return 0.
 edge=min(z,duration-z);ramp=design['ramp_s'];envelope=1. if edge>=ramp else .5*(1-math.cos(math.pi*edge/ramp))
 return design['amplitude']*envelope*sum(math.sin(2*math.pi*f*z+p) for f,p in zip(design['frequencies_hz'],design['phases_rad']))/len(design['frequencies_hz'])
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--duration',type=float,default=10);p.add_argument('--hz',type=float,default=35);p.add_argument('--design',type=Path);p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=49009);p.add_argument('--timeout-ms',type=int,default=500);p.add_argument('--out',type=Path,required=True);a=p.parse_args();design=json.loads(a.design.read_text()) if a.design else None
 if a.duration<=0 or a.hz<=0:p.error('duration and hz must be positive')
 names=list(dict.fromkeys(x[1] for x in FIELDS));rows=[];start=next_tick=time.monotonic();period=1/a.hz
 with xpc.XPlaneConnect(xpHost=a.host,xpPort=a.port,timeout=a.timeout_ms) as c:
  while time.monotonic()-start<a.duration:
   now=time.monotonic()
   if now<next_tick:time.sleep(min(.001,next_tick-now));continue
   scheduled=next_tick;next_tick+=period;reply=c.getDREFs(names);done=time.monotonic()
   if len(reply)!=len(names):raise RuntimeError('dataref reply count mismatch')
   values=dict(zip(names,reply));elapsed=now-start;row={'sample':len(rows),'t_s':elapsed,'dt_s':now-(rows[-1]['_tick'] if rows else start),'deadline_lateness_s':now-scheduled,'acquisition_s':done-now,'hypothetical_excitation':waveform(elapsed,design) if design else 0.,'controls_sent':0,'_tick':now};row.update({field:scalar(values[dref],index) for field,dref,index in FIELDS});row['dynamic_pressure_pa']=.5*row['air_density_kg_m3']*row['tas_m_s']**2;rows.append(row)
 for r in rows:r.pop('_tick')
 a.out.parent.mkdir(parents=True,exist_ok=True)
 with a.out.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
 print(f'Saved {len(rows)} high-rate observe-only samples: {a.out.resolve()}')
if __name__=='__main__':main()
