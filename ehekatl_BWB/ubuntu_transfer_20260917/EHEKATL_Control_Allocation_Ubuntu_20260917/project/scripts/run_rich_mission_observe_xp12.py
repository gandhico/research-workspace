#!/usr/bin/env python3
"""Observe-only rich-mission logger. This program has no control-send path."""

from __future__ import annotations
import argparse, csv, math, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"));sys.path.insert(0,str(ROOT/"backstepping"))
import xpc
from run_backstepping_baseline_xp12 import MEASUREMENTS, scalar
from diagnose_rich_mission_datarefs import DATAREFS as EXTRA_DATAREFS, flatten
from rich_mission import load_campaign

BASE=tuple((field,dref,index) for field,dref,index in MEASUREMENTS)
EXTRA=tuple((field,dref,0) for field,dref in EXTRA_DATAREFS)
FIELDS=BASE+tuple(item for item in EXTRA if item[0] not in {x[0] for x in BASE})

def read_fields(client,batch_size):
    names=list(dict.fromkeys(dref for _,dref,_ in FIELDS)); values={}
    for start in range(0,len(names),batch_size):
        chunk=names[start:start+batch_size]
        reply=client.getDREFs(chunk)
        if len(reply)!=len(chunk): raise RuntimeError(f"dataref reply count {len(reply)} != request count {len(chunk)}")
        values.update(zip(chunk,reply))
    result={field:scalar(values[dref],index) for field,dref,index in FIELDS}
    result["dynamic_pressure_pa"]=0.5*result["air_density_kg_m3"]*result["tas_m_s"]**2
    return result

def parser():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--regime",required=True,choices=[f"R{i}" for i in range(1,7)]);p.add_argument("--config",type=Path,default=None);p.add_argument("--duration",type=float);p.add_argument("--hz",type=float);p.add_argument("--batch-size",type=int,default=48);p.add_argument("--host",default="127.0.0.1");p.add_argument("--port",type=int,default=49009);p.add_argument("--timeout-ms",type=int,default=500);p.add_argument("--test-id",required=True);p.add_argument("--aircraft-config",required=True);p.add_argument("--payload",required=True);p.add_argument("--fuel",required=True);p.add_argument("--weather",required=True);p.add_argument("--failures",required=True);p.add_argument("--out",type=Path,required=True);return p

def main():
    a=parser().parse_args();campaign=load_campaign(a.config) if a.config else load_campaign();duration=a.duration or campaign["observe_duration_s"];hz=a.hz or campaign["sample_rate_hz"]
    if duration<=0 or hz<=0 or a.batch_size<=0: raise SystemExit("duration, hz, and batch size must be positive")
    declared={k:getattr(a,k) for k in ("aircraft_config","payload","fuel","weather","failures")}; expected=campaign["frozen_metadata"]
    mismatch=[k for k in declared if declared[k]!=expected[k]]
    if mismatch: raise SystemExit("metadata differs from frozen campaign: "+", ".join(mismatch))
    rows=[];start=next_tick=time.monotonic();period=1/hz
    with xpc.XPlaneConnect(xpHost=a.host,xpPort=a.port,timeout=a.timeout_ms) as client:
        while time.monotonic()-start<duration:
            now=time.monotonic()
            if now<next_tick: time.sleep(min(.002,next_tick-now));continue
            next_tick+=period;pos=client.getPOSI();measurements=read_fields(client,a.batch_size);now2=time.monotonic()
            row={"regime":a.regime,"test_id":a.test_id,**declared,"controls_sent":0,"t_s":now-start,"dt_s":now-(rows[-1]["_tick"] if rows else start),"acquisition_s":now2-now,"latitude_deg":pos[0],"longitude_deg":pos[1],"altitude_m":pos[2],"pitch_deg":pos[3],"roll_deg":pos[4],"heading_deg":pos[5],**measurements,"_tick":now}
            rows.append(row)
    for row in rows:row.pop("_tick")
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open("w",newline="") as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    print(f"Saved {len(rows)} observe-only samples: {a.out.resolve()}")

if __name__=="__main__":main()
