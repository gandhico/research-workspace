"""Curated result tables for the GitHub release (results/*.csv), computed from the run outputs; never edits a source.

Every value is read from a campaign table or a run summary.json; reductions are 100 (1 - CMG / baseline) and 5-mission
values are reductions of geometric means, exactly as in the paper and reproduce/verify_acc2027_claims.py.

    .venv\\Scripts\\python.exe tools\\release\\build_release_results.py <release_root>
"""
from __future__ import annotations

import csv
import json
import math
import statistics as st
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
E = REPO / "experiments"
FR, NB, BR = E / "final_robustness_gating_2026-09-20", E / "neuron_basis_decisive_2026-09-24", E / "baseline_restatement_2026-09-16"
M = ["roll", "full3", "hard45", "hardstep", "yaw360"]
P = {"x2": "x2", "cf2-rotor": "cf2"}
gm = lambda xs: math.exp(sum(math.log(x) for x in xs) / len(xs))
red = lambda b, c: 100.0 * (1.0 - c / b)
r4 = lambda x: None if x is None else float(f"{x:.6g}")


def rows(path):
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write(path, header, data):
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(data)
    print(f"{path.name}: {len(data)} rows")


def main(root: Path):
    out = root / "results"
    out.mkdir(parents=True, exist_ok=True)

    # 1. primary nominal ------------------------------------------------------------------------------------------
    nom = rows(FR / "results" / "final_nominal.csv") + rows(FR / "results" / "results_a2_nominal_gated_b02.csv")
    arm = {"pdff_rho3": "PD+ff (rho=3)", "cmg_pes_gated": "PD+ff + gated CMG-PES", "cmg_pes_table": "PD+ff + ungated CMG-PES",
           "cmg_pes_gated_b05": "PD+ff + gated CMG-PES", "cmg_pes_b05_ungated": "PD+ff + ungated CMG-PES",
           "cmg_pes_gated_b02": "PD+ff + gated CMG-PES"}
    primary = lambda r: (r["platform"] == "x2" and r["label"] == "cmg_pes_gated") or r["label"] == "cmg_pes_gated_b02"
    seen = set()
    data = []
    for r in nom:
        key = (r["platform"], r["mission"], r["label"], r["beta"], r["output_gate"])
        if key in seen:
            continue
        seen.add(key)
        base = next(x for x in nom if x["platform"] == r["platform"] and x["mission"] == r["mission"] and x["label"] == "pdff_rho3")
        q = float(r["qerr_true_mean_rad"])
        data.append([P[r["platform"]], r["mission"], arm[r["label"]], r["beta"], r4(q * 1e3), r4(math.degrees(float(r["qerr_true_max_rad"]))),
                     None if r["label"] == "pdff_rho3" else round(red(float(base["qerr_true_mean_rad"]), q), 2),
                     r4(float(r["residual_normalized_rms"])), r4(float(r["gate_blocked_fraction"])),
                     r4(float(r["torque_box_sat_fraction"])), r4(float(r["rotor_sat_fraction"])),
                     "yes" if primary(r) else ""])
    write(out / "01_primary_nominal.csv", ["platform", "mission", "controller", "beta", "mean_error_mrad", "max_error_deg",
                                            "reduction_vs_pdff_pct", "residual_effort_rms", "gate_blocked_fraction",
                                            "torque_box_saturated_fraction", "rotor_saturated_fraction",
                                            "paper_primary_result"], data)

    # 2. noise ------------------------------------------------------------------------------------------------------
    nz = rows(FR / "results" / "final_noise.csv")
    groups = {}
    for r in nz:
        groups.setdefault((P[r["platform"]], r["noise_level"], r["mission"], r["label"]), []).append(float(r["qerr_true_mean_rad"]))
    data = []
    for (p, lv, m, lab), v in sorted(groups.items()):
        if lab not in ("pdff_rho3", "cmg_pes_gated"):
            continue
        b = groups.get((p, lv, m, "pdff_rho3"))
        data.append([p, lv, m, arm[lab], len(v), r4(st.mean(v) * 1e3), r4((st.stdev(v) if len(v) > 1 else 0.0) * 1e3),
                     None if lab == "pdff_rho3" else round(st.mean(red(bi, ci) for bi, ci in zip(b, v)), 2)])
    write(out / "02_measurement_noise.csv", ["platform", "noise_level", "mission", "controller", "seeds", "mean_error_mrad",
                                              "sd_across_seeds_mrad", "mean_paired_reduction_pct"], data)

    # 3. disturbance ------------------------------------------------------------------------------------------------
    ds = rows(FR / "results" / "final_disturbance.csv")
    data = [[P[r["platform"]], r["disturbance_level"], arm[r["label"]], r4(float(r["qerr_true_mean_rad"]) * 1e3),
             r4(float(r["disturbance_active_mean_rad"]) * 1e3) if r["disturbance_active_mean_rad"] else None,
             r4(float(r["disturbance_quiet_mean_rad"]) * 1e3) if r["disturbance_quiet_mean_rad"] else None,
             r4(float(r["rotor_sat_fraction"]))] for r in ds]
    write(out / "03_torque_bursts.csv", ["platform", "burst_level", "controller", "mean_error_mrad", "burst_phase_error_mrad",
                                          "quiet_phase_error_mrad", "rotor_saturated_fraction"], data)

    # 4. controller families (A5) --------------------------------------------------------------------------------------
    a5 = json.loads((FR / "results" / "a5_numbers.json").read_text(encoding="utf-8"))["families"]
    label = {"backstepping": "PD+ff (computed-torque form)", "pid": "PID+ff", "lqr": "LQR", "smc": "SMC", "mpc": "MPC", "nmpc": "NMPC"}
    data = []
    for fam, d in a5.items():
        for p in ("x2", "cf2-rotor"):
            v = d[p]
            for i, m in enumerate(M):
                data.append([label[fam], P[p], m, r4(v["baseline_mrad"][i]), r4(v["cmg_mrad"][i]), round(v["red_pct"][i], 2)])
            data.append([label[fam], P[p], "5-mission (geometric)", r4(v["geo_baseline_mrad"]), r4(v["geo_cmg_mrad"]), round(v["geo_red_pct"], 2)])
    write(out / "04_controller_families.csv", ["nominal_controller", "platform", "mission", "nominal_mrad", "with_cmg_pes_mrad",
                                               "reduction_pct"], data)

    # 5. neuron families and non-neural bases (strict exact-rate protocol) --------------------------------------------
    SE = NB / "results" / "strict_exact"
    kind = {"cmg": "CMG (this work)", "lif": "spiking neuron", "alif": "spiking neuron", "izhikevich": "spiking neuron",
            "lifrate": "rate neuron", "paired-current": "non-neural basis", "constant-one": "non-neural basis"}
    data = []
    for p in ("x2", "cf2-rotor"):
        base = {m: json.loads((SE / p / m / "classical" / "summary.json").read_text())["metrics"]["qerr_true_mean_rad"] for m in M}
        for fam in ("cmg", "lif", "alif", "lifrate", "izhikevich", "paired-current", "constant-one"):
            errs = []
            for m in M:
                d = SE / p / m / fam
                s = json.loads((d / "summary.json").read_text())
                q = s["metrics"]["qerr_true_mean_rad"]; errs.append(q)
                occ = mean_a = None
                npz = d / "neural_trace_full_rate.npz"
                if npz.exists():
                    with np.load(npz) as z:
                        if "activity" in z.files:
                            a = z["activity"]; occ, mean_a = float(np.mean(a > 1e-6)), float(np.mean(a))
                data.append([fam, kind[fam], P[p], m, r4(base[m] * 1e3), r4(q * 1e3), round(red(base[m], q), 2),
                             r4(s["metrics"]["realized_residual_normalized_rms"]), r4(occ), r4(mean_a)])
            data.append([fam, kind[fam], P[p], "5-mission (geometric)", r4(gm(list(base.values())) * 1e3), r4(gm(errs) * 1e3),
                         round(red(gm(list(base.values())), gm(errs)), 2), None, None, None])
    write(out / "05_neuron_and_nonneural_bases.csv", ["basis", "kind", "platform", "mission", "pdff_mrad", "with_residual_mrad",
                                                      "reduction_pct", "residual_effort_rms", "activity_occupancy",
                                                      "mean_activity"], data)

    # 6. baseline ladder (Table II middle/lower blocks) ------------------------------------------------------------------
    mt = rows(BR / "master_table.csv")
    data = [[r["platform"], r["mission"], r4(float(r["PD"]) * 1e3), r4(float(r["CMG_on_PD"]) * 1e3), round(float(r["CMGonPD_vs_PD_pct"]), 2),
             r4(float(r["PDff_1x"]) * 1e3), r4(float(r["CMG_on_PDff_1x"]) * 1e3), round(float(r["CMGonff1x_vs_ff1x_pct"]), 2),
             r4(float(r["PDff_3x"]) * 1e3), r4(float(r["CMG_on_PDff_3x"]) * 1e3), round(float(r["CMGonff3x_vs_ff3x_pct"]), 2)] for r in mt]
    write(out / "06_baseline_ladder.csv", ["platform", "mission", "fixed_PD_mrad", "fixed_PD_plus_cmg_mrad", "reduction_fixed_PD_pct",
                                           "PDff_rho1_mrad", "PDff_rho1_plus_cmg_mrad", "reduction_PDff_rho1_pct", "PDff_rho3_mrad",
                                           "PDff_rho3_plus_cmg_mrad", "reduction_PDff_rho3_pct"], data)

    # 7. CMG activity per mission (recordings of the primary runs, MATCH-verified) ---------------------------------------
    REC = REPO / "reproduce" / "recordings"
    data = []
    for p in ("x2", "cf2"):
        for m in M:
            d = REC / f"{p}_{m}_cmg"
            with np.load(d / "neural_trace_full_rate.npz") as z:
                a, t, mask = z["activity"], z["t"], z["output_gate_mask"]
                rr = z["realized_residual_torque"]
            lim = np.array(json.loads((d / "summary.json").read_text())["actuation"]["torque_limits_Nm"])
            beta = 0.5 if p == "x2" else 0.2
            latched = a > 0.99
            first = [float(t[np.argmax(latched[:, j])]) if latched[:, j].any() else None for j in range(6)]
            data.append([p, m, r4(float(np.mean(a))), r4(float(np.mean(latched))), sum(x is not None for x in first),
                         ";".join("-" if x is None else f"{x:.2f}" for x in first), r4(float(np.mean((mask == 0).any(1)))),
                         r4(float(np.sqrt(np.mean((rr / (beta * lim)) ** 2))))])
    write(out / "07_cmg_activity_by_mission.csv", ["platform", "mission", "mean_activity", "latched_fraction(a>0.99)",
                                                   "units_latched_of_6", "first_latch_time_s(+x;+y;+z;-x;-y;-z)",
                                                   "gate_blocked_fraction", "residual_rms_over_bound"], data)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
