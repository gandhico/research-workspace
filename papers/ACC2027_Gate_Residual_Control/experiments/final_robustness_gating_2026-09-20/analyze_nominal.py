"""Nominal-campaign analysis: H1 (Hardstep gate) and H2 (CF2 authority), plus the regression check.

Reads results/final_nominal.csv (written by run_campaign.py) and prints / saves:
  * per-cell mean true error for each arm and the reduction versus PD+ff (rho=3)
  * geometric means over the five missions (paper convention)
  * Hardstep: mean, slew, settled error, settling time, rotor saturation, share of samples gated
  * regression: the ungated table-beta arm must equal the validation run bit for bit
"""
from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE / "results" / "final_nominal.csv"
VAL = HERE / "results_validation" / "validation_report.csv"
OUT = HERE / "analysis"
OUT.mkdir(exist_ok=True)
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
ARMS = ("pdff_rho3", "cmg_pes_table", "cmg_pes_b05_ungated", "cmg_pes_gated_b05", "cmg_pes_gated")   # CF2: gated_b05 = beta .5, gated = beta .2 (A2)
PLATFORMS = ("x2", "cf2-rotor")


def gmean(xs):
    return math.exp(sum(math.log(x) for x in xs) / len(xs))


def red(base, x):
    return 100.0 * (1.0 - x / base)


def main() -> None:
    rows = list(csv.DictReader(RES.open()))
    cell = {(r["platform"], r["mission"], r["label"]): r for r in rows}
    f = lambda p, m, a, k: float(cell[(p, m, a)][k])

    print("=== regression: ungated table-beta arm vs the validation run (bit-identical expected)")
    val = {(r["platform"], r["mission"], r["arm"]): float(r["new_rad"]) for r in csv.DictReader(VAL.open())}
    worst = 0.0
    for p in PLATFORMS:
        for m in MISSIONS:
            for arm, varm in (("pdff_rho3", "pdff_rho3"), ("cmg_pes_table", "cmg_pes")):
                new = f(p, m, arm, "qerr_true_mean_rad")
                worst = max(worst, abs(new - val[(p, m, varm)]) / val[(p, m, varm)])
    print(f"    worst relative deviation {worst:.2e}  ->  {'OK' if worst < 1e-12 else 'CHECK'}")

    print("\n=== mean true quaternion error [mrad] and reduction vs PD+ff rho=3 [%]")
    table = []
    for p in PLATFORMS:
        print(f"\n  {p}")
        print(f"  {'mission':9s}{'PD+ff':>10s}" + "".join(f"{a[:16]:>24s}" for a in ARMS[1:]))
        geo = {a: [] for a in ARMS}
        for m in MISSIONS:
            base = f(p, m, "pdff_rho3", "qerr_true_mean_rad")
            line = f"  {m:9s}{base*1e3:10.3f}"
            geo["pdff_rho3"].append(base)
            for a in ARMS[1:]:
                if (p, m, a) not in cell:
                    line += f"{'--':>24s}"
                    continue
                v = f(p, m, a, "qerr_true_mean_rad")
                geo[a].append(v)
                line += f"{v*1e3:12.3f} ({red(base, v):+7.1f}%)"
                table.append(dict(platform=p, mission=m, arm=a, mean_mrad=v * 1e3, base_mrad=base * 1e3,
                                  reduction_pct=red(base, v)))
            print(line)
        gb = gmean(geo["pdff_rho3"])
        line = f"  {'geo-mean':9s}{gb*1e3:10.3f}"
        for a in ARMS[1:]:
            if len(geo[a]) == len(MISSIONS):
                line += f"{gmean(geo[a])*1e3:12.3f} ({red(gb, gmean(geo[a])):+7.1f}%)"
                table.append(dict(platform=p, mission="geo", arm=a, mean_mrad=gmean(geo[a]) * 1e3,
                                  base_mrad=gb * 1e3, reduction_pct=red(gb, gmean(geo[a]))))
            else:
                line += f"{'--':>24s}"
        print(line)

    print("\n=== Hardstep (H1): mean, slew, settled [deg], settling to 5 deg [s], saturation, gated share")
    hs = []
    for p in PLATFORMS:
        print(f"\n  {p}")
        print(f"  {'arm':22s}{'mean':>8s}{'slew':>8s}{'settled':>9s}{'t_settle':>10s}{'rotorSat':>10s}{'boxSat':>8s}{'gated':>8s}")
        for a in ARMS:
            if (p, "hardstep", a) not in cell:
                continue
            r = cell[(p, "hardstep", a)]
            d = lambda k: math.degrees(float(r[k])) if r[k] not in ("", "None") else float("nan")
            print(f"  {a:22s}{d('qerr_true_mean_rad'):8.2f}{d('hardstep_slew_mean_rad'):8.2f}"
                  f"{d('hardstep_settled_mean_rad'):9.3f}{float(r['hardstep_settling_time_5deg_s']):10.3f}"
                  f"{float(r['rotor_sat_fraction']):10.3f}{float(r['torque_box_sat_fraction']):8.3f}"
                  f"{float(r['gate_blocked_fraction']):8.3f}")
            hs.append(dict(platform=p, arm=a, mean_deg=d('qerr_true_mean_rad'), slew_deg=d('hardstep_slew_mean_rad'),
                           settled_deg=d('hardstep_settled_mean_rad'), t_settle_s=float(r['hardstep_settling_time_5deg_s']),
                           rotor_sat=float(r['rotor_sat_fraction']), box_sat=float(r['torque_box_sat_fraction']),
                           gated=float(r['gate_blocked_fraction'])))
        b = cell[(p, "hardstep", "pdff_rho3")]
        g = cell[(p, "hardstep", "cmg_pes_gated")]
        dm = red(float(b["qerr_true_mean_rad"]), float(g["qerr_true_mean_rad"]))
        ds = red(float(b["hardstep_settling_time_5deg_s"]), float(g["hardstep_settling_time_5deg_s"]))
        print(f"  -> gated vs PD+ff: mean error {dm:+.2f} %   settling time {ds:+.2f} %")

    print("\n=== gate activity (share of samples with any axis blocked), gated arm")
    for p in PLATFORMS:
        print("  " + p + "  " + "  ".join(f"{m}:{float(cell[(p, m, 'cmg_pes_gated')]['gate_blocked_fraction']):.4f}" for m in MISSIONS))

    for name, data in (("nominal_reductions.csv", table), ("hardstep_gate.csv", hs)):
        if data:
            with (OUT / name).open("w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(data[0]))
                w.writeheader()
                w.writerows(data)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    sys.exit(main())
