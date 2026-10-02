#!/usr/bin/env python3
"""Read-only 10-Hz availability/timing diagnostic for rich LQR datarefs."""

from __future__ import annotations
import argparse, csv, math, time
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import xpc

DATAREFS=(
 ('art_stab_on','sim/cockpit/switches/art_stab_on'),
 ('yoke_pitch','sim/joystick/yoke_pitch_ratio'),('yoke_roll','sim/joystick/yoke_roll_ratio'),
 ('total_pitch','sim/cockpit2/controls/total_pitch_ratio'),('total_roll','sim/cockpit2/controls/total_roll_ratio'),
 ('trim_elev','sim/cockpit2/controls/elevator_trim'),('trim_ail','sim/cockpit2/controls/aileron_trim'),
 ('elev_def_time','sim/aircraft/controls/acf_elev_def_time'),('ail_def_time','sim/aircraft/controls/acf_ailn_def_time'),
 ('rud_def_time','sim/aircraft/controls/acf_rudd_def_time'),
 ('ail1','sim/flightmodel/controls/lail1def'),('ail2','sim/flightmodel/controls/rail1def'),
 ('elv1','sim/flightmodel/controls/hstab1_elv1def'),('elv2','sim/flightmodel/controls/hstab1_elv2def'),
 ('rud1','sim/flightmodel/controls/vstab1_rud1def'),('rud2','sim/flightmodel/controls/vstab1_rud2def'),
 ('roll_moment','sim/flightmodel/forces/L_total'),('pitch_moment','sim/flightmodel/forces/M_total'),('yaw_moment','sim/flightmodel/forces/N_total'),
 ('as_hi_v','sim/aircraft/artstability/acf_AShiV'),('as_lo_v','sim/aircraft/artstability/acf_ASloV'),
 ('as_maxp_lo','sim/aircraft/artstability/acf_ASmaxp_lo'),('as_p_lo_rate','sim/aircraft/artstability/acf_ASp_lo_rate'),
 ('as_maxh_lo','sim/aircraft/artstability/acf_ASmaxh_lo'),('as_h_lo_rate','sim/aircraft/artstability/acf_ASh_lo_rate'),
 ('as_maxr_lo','sim/aircraft/artstability/acf_ASmaxr_lo'),('as_r_lo_rate','sim/aircraft/artstability/acf_ASr_lo_rate'),
 ('override_joystick','sim/operation/override/override_joystick'),('override_roll','sim/operation/override/override_joystick_roll'),
 ('override_pitch','sim/operation/override/override_joystick_pitch'),('override_flightcontrol','sim/operation/override/override_flightcontrol'),
 ('override_surfaces','sim/operation/override/override_control_surfaces'),('paused','sim/time/paused'),('sim_speed','sim/time/sim_speed'),('replay','sim/operation/prefs/replay_mode'),
)

def flatten(value):
 while isinstance(value,(list,tuple)) and len(value)==1 and isinstance(value[0],(list,tuple)): value=value[0]
 if isinstance(value,(list,tuple)): return [float(x) for x in value]
 return [float(value)]

def main():
 p=argparse.ArgumentParser();p.add_argument('--duration',type=float,default=10);p.add_argument('--hz',type=float,default=10);p.add_argument('--out',type=Path,required=True);p.add_argument('--batch-size',type=int,default=12);p.add_argument('--isolate',action='store_true');a=p.parse_args()
 if a.duration<=0 or a.hz<=0 or a.batch_size<=0:p.error('--duration, --hz, and --batch-size must be positive')
 period=1/a.hz;rows=[];start=next_tick=time.monotonic()
 with xpc.XPlaneConnect(xpHost='127.0.0.1',xpPort=49009,timeout=300) as c:
  names=[d for _,d in DATAREFS]; size=1 if a.isolate else a.batch_size; chunks=[list(range(i,min(i+size,len(names)))) for i in range(0,len(names),size)]
  while time.monotonic()-start<a.duration:
   now=time.monotonic()
   if now<next_tick:time.sleep(min(.002,next_tick-now));continue
   next_tick+=period;row={'t_s':now-start,'dt_s':now-start-(rows[-1]['t_s'] if rows else 0)}
   for chunk in chunks:
    try: vals=c.getDREFs([names[i] for i in chunk])
    except Exception:
     vals=[None]*len(chunk)
    for i,value in zip(chunk,vals):
     key=DATAREFS[i][0]
     if value is None: row[key]=float('nan');continue
     z=flatten(value);row[key]=z[0] if len(z)==1 else max(abs(x) for x in z)
   rows.append(row)
 a.out.parent.mkdir(parents=True,exist_ok=True)
 with a.out.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
 print(f'Saved {len(rows)} samples: {a.out.resolve()}')

if __name__=='__main__':main()
