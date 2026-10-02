#!/usr/bin/env python3
"""Evaluate a rich-mission observe-only CSV against frozen campaign gates."""

import argparse, csv, json, math, statistics
from pathlib import Path
from rich_mission import gate_reasons, load_campaign

def analyze(path, campaign, regime):
    with Path(path).open(newline="") as f: rows=list(csv.DictReader(f))
    if not rows: raise ValueError("empty observe log")
    numeric=lambda row,key: float(row[key])
    dt=[numeric(row,"dt_s") for row in rows[1:]]
    expected=round(campaign["observe_duration_s"]*campaign["sample_rate_hz"])
    text_fields={"regime","test_id","aircraft_config","payload","fuel","weather","failures"}
    nonfinite=sum(not math.isfinite(float(value)) for row in rows for key,value in row.items() if key not in text_fields and value!="")
    sample={key:float(rows[0][key]) for key in ("altitude_m","ias_kts","pitch_deg","roll_deg","p_deg_s","q_deg_s","r_deg_s","art_stab_on","paused","sim_speed","replay","override_joystick","override_roll","override_pitch","override_flightcontrol","override_surfaces")}
    reasons=gate_reasons(campaign,regime,sample)
    timing_ok=len(rows)>=math.ceil(expected*campaign["timing"]["minimum_completeness"]) and bool(dt) and max(dt)<=campaign["timing"]["maximum_gap_s"]
    metadata_ok=all(row["regime"]==regime for row in rows) and all(row["controls_sent"]=="0" for row in rows)
    return {"file":str(path),"regime":regime,"rows":len(rows),"expected_rows":expected,"mean_dt_s":statistics.mean(dt),"max_gap_s":max(dt),"nonfinite_values":nonfinite,"start_gate_reasons":reasons,"timing_pass":timing_ok,"metadata_pass":metadata_ok,"pass":timing_ok and metadata_ok and nonfinite==0 and not reasons}

def main():
    p=argparse.ArgumentParser();p.add_argument("csv",type=Path);p.add_argument("--regime",required=True,choices=[f"R{i}" for i in range(1,7)]);p.add_argument("--config",type=Path,default=None);p.add_argument("--out",type=Path);a=p.parse_args()
    result=analyze(a.csv,load_campaign(a.config) if a.config else load_campaign(),a.regime); text=json.dumps(result,indent=2);print(text)
    if a.out:a.out.write_text(text+"\n")
    raise SystemExit(0 if result["pass"] else 1)
if __name__=="__main__":main()
