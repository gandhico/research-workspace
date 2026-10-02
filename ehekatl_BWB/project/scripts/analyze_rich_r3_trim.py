#!/usr/bin/env python3
"""Require every sample in an observe-only log to remain inside frozen R3 gates."""
import argparse,csv,json
from pathlib import Path
from rich_mission import gate_reasons,load_campaign

def main():
 p=argparse.ArgumentParser();p.add_argument("csv",type=Path);a=p.parse_args();campaign=load_campaign()
 with a.csv.open(newline="") as f:rows=list(csv.DictReader(f))
 required=("altitude_m","ias_kts","pitch_deg","roll_deg","p_deg_s","q_deg_s","r_deg_s","art_stab_on","paused","sim_speed","replay","override_joystick","override_roll","override_pitch","override_flightcontrol","override_surfaces")
 failures=[]
 for index,row in enumerate(rows):
  sample={key:float(row[key]) for key in required};reasons=gate_reasons(campaign,"R3",sample)
  if reasons:failures.append({"sample":index,"reasons":reasons})
 result={"file":str(a.csv),"rows":len(rows),"failed_samples":len(failures),"first_failure":failures[0] if failures else None,"pass":bool(rows) and not failures}
 print(json.dumps(result,indent=2));raise SystemExit(0 if result["pass"] else 1)
if __name__=="__main__":main()
