#!/usr/bin/env python3
"""Pure configuration and gate helpers for the rich LQR mission."""

from __future__ import annotations
import json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configs/rich_mission_campaign.json"
OVERRIDE_FIELDS = ("override_joystick", "override_roll", "override_pitch", "override_flightcontrol", "override_surfaces")

def load_campaign(path=DEFAULT_CONFIG):
    campaign=json.loads(Path(path).read_text())
    required=("sample_rate_hz","observe_duration_s","timing","start_envelope","required_state","regimes","allocation_per_regime","frozen_metadata")
    missing=[name for name in required if name not in campaign]
    if missing: raise ValueError(f"campaign missing fields: {', '.join(missing)}")
    if set(campaign["regimes"]) != {f"R{i}" for i in range(1,7)}: raise ValueError("campaign must define exactly R1..R6")
    return campaign

def run_manifest(campaign):
    return [dict(regime=regime, run_id=f"{regime}_{item['kind']}_{item['replicate']:02d}", **item)
            for regime in campaign["regimes"] for item in campaign["allocation_per_regime"]]

def gate_reasons(campaign, regime_id, sample):
    regime=campaign["regimes"][regime_id]; env=campaign["start_envelope"]; required=campaign["required_state"]; reasons=[]
    checks=(
      (abs(sample["altitude_m"]-regime["altitude_m"])>env["altitude_tolerance_m"],"altitude outside regime envelope"),
      (abs(sample["ias_kts"]-regime["ias_kts"])>env["ias_tolerance_kts"],"IAS outside regime envelope"),
      (abs(sample["pitch_deg"])>env["maximum_abs_pitch_deg"],"pitch outside start envelope"),
      (abs(sample["roll_deg"])>env["maximum_abs_roll_deg"],"roll outside start envelope"),
      (max(abs(sample[x]) for x in ("p_deg_s","q_deg_s","r_deg_s"))>env["maximum_abs_body_rate_deg_s"],"body rate outside start envelope"),
      (sample["art_stab_on"]!=required["artificial_stability_on"],"artificial stability state mismatch"),
      (sample["paused"]!=required["paused"],"simulator is paused"),
      (sample["sim_speed"]!=required["sim_speed"],"simulation speed mismatch"),
      (sample["replay"]!=required["replay"],"simulator is in replay mode"),
      (required["all_overrides_off"] and any(sample[x]!=0 for x in OVERRIDE_FIELDS),"control override already active"),
    )
    reasons.extend(reason for failed,reason in checks if failed)
    reasons.extend(f"non-finite {key}" for key,value in sample.items() if isinstance(value,(int,float)) and not math.isfinite(value))
    return reasons
