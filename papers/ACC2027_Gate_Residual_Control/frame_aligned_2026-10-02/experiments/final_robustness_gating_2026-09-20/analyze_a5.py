"""Amendment A5 analysis: does the bounded, gated CMG-PES residual attach cleanly to LQR/SMC/MPC/NMPC/PID, and does it
help or hurt? Reads results/a5_controllers/, plus the existing sealed pdff_rho3/cmg_pes_gated data for backstepping/pd
(proven identical, not re-run). Writes results/A5_CONTROLLERS_RESULTS.md and izh... no: a5_numbers.json.
"""
import csv
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = HERE / "results"
A5 = R / "a5_controllers"
MISSIONS = ["roll", "full3", "hard45", "hardstep", "yaw360"]
NAMES = {"roll": "Roll", "full3": "Full3", "hard45": "Hard45", "hardstep": "Hardstep", "yaw360": "Yaw360"}
PLAT = {"x2": "X2", "cf2-rotor": "CF2"}
FAMILIES = ["backstepping", "pid", "lqr", "smc", "mpc", "nmpc"]
FAM_LABEL = {"backstepping": "PD+ff (backstepping form)", "pid": "PID+ff", "lqr": "LQR", "smc": "SMC", "mpc": "MPC", "nmpc": "NMPC"}


def qerr(p: Path):
    s = json.loads(p.read_text(encoding="utf-8"))
    return s.get("qerr_mean_rad", s.get("metrics", {}).get("qerr_true_mean_rad"))


def sat(p: Path):
    s = json.loads(p.read_text(encoding="utf-8"))
    a = s.get("actuation", {})
    return a.get("rotor_saturation_fraction_any_rotor"), a.get("torque_box_saturation_fraction_any_axis")


def gm(xs):
    return math.exp(sum(math.log(x) for x in xs) / len(xs))


# backstepping now runs through the identical new pipeline as the other five families (certified bit-exact against
# the sealed run_final_robustness.py data across all 20 cells, worst relative deviation 0.00e+00 -- see
# run_campaign_a5_backstepping.py's own printed certification and REPORT_A5_CERTIFICATION_2026-09-24.md).

# nmpc reads from the CORRECTED re-run (2026-09-25): the original a5_controllers/nmpc/ row used a leftover 100 Hz
# --baseline-rate-hz hold from an unrelated older exploratory NMPC setting, while every other family (mpc included)
# ran at full rate. A two-way ablation confirmed the hold -- not NMPC's predictive machinery -- caused the X2
# anomaly (removing it fixed NMPC; imposing it on MPC broke MPC identically). See
# AUDIT_NMPC_HOLD_RATE_2026-09-25.md and run_campaign_a5_nmpc_corrected.py. The original 100Hz-hold data is kept
# on disk for the audit trail, not read here.
FAMILY_ROOT = {"nmpc": R / "a5_controllers_nmpc_corrected"}


def cell(family, plat, mission, arm):
    root = FAMILY_ROOT.get(family, A5 / family)
    p = root / plat / mission / arm / "summary.json"
    e = qerr(p)
    rs, ts = sat(p)
    return e, rs, ts


out = {"families": {}}
md = ["# Amendment A5: controller-family portability (2026-09-24, NMPC corrected 2026-09-25)\n",
      "Same missions/platforms/gate/beta/eta as the rest of this campaign; bw_scale=3 reused uniformly (not re-swept per family). "
      "PID: ki_factor=0.3, rotor-level anti-windup, undertuned (disclosed). MPC: unconstrained finite-horizon, full update rate. "
      "NMPC: grid receding-horizon, full update rate (corrected 2026-09-25 -- the original run's 100 Hz hold was a leftover "
      "unrelated setting, not a considered choice; see AUDIT_NMPC_HOLD_RATE_2026-09-25.md).\n"]

for fam in FAMILIES:
    md.append(f"\n## {FAM_LABEL[fam]}\n")
    md.append("| platform | mission | baseline [mrad] | +CMG-PES gated [mrad] | Delta [%] | CMG rotor-sat | CMG box-sat |")
    md.append("|---|---|---:|---:|---:|---:|---:|")
    fam_rows = {"x2": [], "cf2-rotor": []}
    for plat in ("x2", "cf2-rotor"):
        for m in MISSIONS:
            b, _, _ = cell(fam, plat, m, "classical")
            c, rs, ts = cell(fam, plat, m, "nengo-nef-pes")
            red = 100 * (1 - c / b)
            fam_rows[plat].append((b, c, red))
            rs_s = f"{rs:.3f}" if rs is not None else "--"
            ts_s = f"{ts:.3f}" if ts is not None else "--"
            md.append(f"| {PLAT[plat]} | {NAMES[m]} | {b*1e3:.3f} | {c*1e3:.3f} | {red:+.1f} | {rs_s} | {ts_s} |")
        bl = [r[0] for r in fam_rows[plat]]
        cl = [r[1] for r in fam_rows[plat]]
        g = 100 * (1 - gm(cl) / gm(bl))
        md.append(f"| {PLAT[plat]} | **geo** | **{gm(bl)*1e3:.3f}** | **{gm(cl)*1e3:.3f}** | **{g:+.1f}** | | |")
        out["families"].setdefault(fam, {})[plat] = {"baseline_mrad": [b * 1e3 for b in bl], "cmg_mrad": [c * 1e3 for c in cl],
                                                       "red_pct": [r[2] for r in fam_rows[plat]], "geo_red_pct": g,
                                                       "geo_baseline_mrad": gm(bl) * 1e3, "geo_cmg_mrad": gm(cl) * 1e3}

(R / "a5_numbers.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
(R / "A5_CONTROLLERS_RESULTS.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("\n".join(md))
