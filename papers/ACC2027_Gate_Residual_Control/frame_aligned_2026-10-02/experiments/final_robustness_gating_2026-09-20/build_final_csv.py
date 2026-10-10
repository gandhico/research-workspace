"""Assemble the final result tables in the schema the analysis scripts already read.

Primary CMG arm (label `cmg_pes_gated`):  X2 -> exact-saturation gate, beta = 0.5   (campaigns as run)
                                          CF2 -> exact-saturation gate, beta = 0.2   (amendment A2 selection; noise-safe)
The CF2 beta = 0.5 gated results stay on record under the label `cmg_pes_gated_b05`.
Rows from the A2 development stage (CF2 Hardstep, moderate noise, seeds 1-2 -- used for selection) are flagged
`used_for_selection = 1`.

Writes results/final_nominal.csv, final_noise.csv, final_disturbance.csv.
"""
from __future__ import annotations

import csv
import glob
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = HERE / "results"
sys.path.insert(0, str(HERE))
import run_campaign as rc  # noqa: E402

B02_LABEL = "cmg_pes_gated_b02"


def read(path):
    return list(csv.DictReader(path.open())) if path.exists() else []


def flatten_summary(summary_path: Path, *, platform, mission, seed, noise_level, disturbance_level, label, selection_flag):
    s = json.load(open(summary_path))
    m, a, hs, ph = s["metrics"], s["actuation"], s.get("hardstep") or {}, s["disturbance_phase_metrics_true_state"]
    return {
        "case_id": str(summary_path.parent), "protocol": "confirmatory_a2", "campaign": "a2", "platform": platform,
        "mission": mission, "label": label, "controller": "nengo-nef-pes", "beta": s["cmg_pes"]["beta"], "seed": seed,
        "noise_level": noise_level, "disturbance_level": disturbance_level, "output_gate": s["output_gate"]["mode"],
        "gate_load_threshold": s["output_gate"]["load_threshold_fraction_of_axis_limit"],
        "qerr_true_mean_rad": m["qerr_true_mean_rad"], "qerr_feedback_mean_rad": m["qerr_feedback_mean_rad"],
        "qerr_true_max_rad": m["qerr_true_max_rad"], "residual_normalized_rms": m["realized_residual_normalized_rms"],
        "gate_blocked_fraction": s["output_gate"]["blocked_fraction_any_axis"],
        "torque_box_sat_fraction": a["torque_box_saturation_fraction_any_axis"],
        "rotor_sat_fraction": a["rotor_saturation_fraction_any_rotor"],
        "hardstep_slew_mean_rad": hs.get("slew_mean_rad"), "hardstep_settled_mean_rad": hs.get("settled_mean_rad"),
        "hardstep_settling_time_5deg_s": hs.get("settling_time_5deg_s_mean"),
        "disturbance_active_mean_rad": ph["active"]["mean_rad"], "disturbance_quiet_mean_rad": ph["quiet"]["mean_rad"],
        "run_id": s["run_id"], "configuration_sha256": s["configuration_sha256"], "output": str(summary_path.parent),
        "status": "final", "used_for_selection": selection_flag,
    }


def a2_rows():
    out = []
    pat = str(R / "*" / "*" / "cf2-rotor" / "*" / B02_LABEL / "*" / "seed_*" / "summary.json")
    for f in glob.glob(pat):
        p = Path(f)
        protocol, campaign, platform, mission, label, tag, seedname = p.parts[-8], p.parts[-7], p.parts[-6], p.parts[-5], p.parts[-4], p.parts[-3], p.parts[-2]
        seed = int(seedname.split("_")[1])
        parts = tag.split("__")
        noise = next((x[6:] for x in parts if x.startswith("noise_")), "none")
        dist = next((x[5:] for x in parts if x.startswith("dist_")), "none")
        sel = int(protocol == "development_only" and campaign == "a2_dev" and noise == "moderate" and seed in (1, 2))
        out.append(flatten_summary(p, platform=platform, mission=mission, seed=seed, noise_level=noise,
                                   disturbance_level=dist, label="cmg_pes_gated", selection_flag=sel))
    return out


def relabel(rows):
    out = []
    for r in rows:
        r = dict(r)
        if r["platform"] == "cf2-rotor" and r["label"] == "cmg_pes_gated":
            r["label"] = "cmg_pes_gated_b05"
        r.setdefault("used_for_selection", 0)
        out.append(r)
    return out


def write(path, rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


a2 = a2_rows()
by = {"nominal": [], "noise": [], "disturbance": []}
for r in a2:
    if r["disturbance_level"] != "none":
        by["disturbance"].append(r)
    elif r["noise_level"] != "none":
        by["noise"].append(r)
    else:
        by["nominal"].append(r)
for name, src in (("nominal", "results_nominal.csv"), ("noise", "results_noise.csv"), ("disturbance", "results_disturbance.csv")):
    rows = relabel(read(R / src)) + by[name]
    write(R / f"final_{name}.csv", rows)
    n_b2 = sum(1 for r in rows if r["platform"] == "cf2-rotor" and r["label"] == "cmg_pes_gated")
    print(f"final_{name}.csv: {len(rows)} rows ({len(by[name])} from A2; CF2 primary rows {n_b2})")
