#!/usr/bin/env python3
"""Apply frozen R3 zero-excitation baseline gates."""
import argparse,csv,json,math,statistics
from pathlib import Path
from rich_mission import gate_reasons,load_campaign

RICH=("art_stab_on","elevator_deflection_time_s","aileron_deflection_time_s","rudder_deflection_time_s","left_aileron_1_def_deg","right_aileron_1_def_deg","left_elevator_1_def_deg","right_elevator_1_def_deg","left_rudder_1_def_deg","right_rudder_1_def_deg","override_joystick","override_roll","override_pitch","override_flightcontrol","override_surfaces")
def truth(value):return value.strip().lower()=="true"
def main():
 p=argparse.ArgumentParser();p.add_argument("csv",type=Path);p.add_argument("--expect-engaged",action="store_true");a=p.parse_args()
 with a.csv.open(newline="") as f:rows=list(csv.DictReader(f))
 if not rows:raise SystemExit("FAIL: empty log")
 times=[float(r["t_s"]) for r in rows];dt=[b-a for a,b in zip(times,times[1:])];expected=300
 finite=all(r.get(k,"")!="" and math.isfinite(float(r[k])) for r in rows for k in RICH)
 engagement=sum(truth(r["engaged"]) for r in rows)/len(rows);expected_engagement=1.0 if a.expect_engaged else 0.0
 zero_excitation=all(float(r["identification_excitation"])==0 and float(r["recovery_pulse"])==0 for r in rows)
 safe=all(abs(float(r["pitch_deg"]))<=10 and abs(float(r["roll_deg"]))<=10 and max(abs(float(r[k])) for k in ("p_deg_s","q_deg_s","r_deg_s"))<=20 for r in rows)
 first=rows[0];sample={"altitude_m":float(first["alt_m"]),"ias_kts":float(first["ias_kts"]),"pitch_deg":float(first["pitch_deg"]),"roll_deg":float(first["roll_deg"]),"p_deg_s":float(first["p_deg_s"]),"q_deg_s":float(first["q_deg_s"]),"r_deg_s":float(first["r_deg_s"]),"art_stab_on":float(first["art_stab_on"]),"paused":float(first["sim_paused"]),"sim_speed":float(first["sim_speed"]),"replay":float(first["replay_mode"]),"override_joystick":float(first["override_joystick"]),"override_roll":float(first["override_roll"]),"override_pitch":float(first["override_pitch"]),"override_flightcontrol":float(first["override_flightcontrol"]),"override_surfaces":float(first["override_surfaces"])}
 reasons=gate_reasons(load_campaign(),"R3",sample)
 checks={"completeness":len(rows)>=297,"timing":bool(dt) and max(dt)<=.25,"rich_finite":finite,"engagement":math.isclose(engagement,expected_engagement),"zero_excitation":zero_excitation,"safety":safe,"start_gate":not reasons}
 result={"file":str(a.csv),"rows":len(rows),"mean_dt_s":statistics.mean(dt),"max_gap_s":max(dt),"engagement_fraction":engagement,"start_gate_reasons":reasons,"checks":checks,"pass":all(checks.values())}
 print(json.dumps(result,indent=2));raise SystemExit(0 if result["pass"] else 1)
if __name__=="__main__":main()
