"""Noise (H3) and disturbance (H4) analysis against PD + feedforward at rho = 3.

Paired by construction: within (noise level, platform, mission, seed) every arm sees the identical noise
stream, so reductions are computed seed by seed and only then summarised.

Primary metric: TRUE quaternion-angle error.  Corrupted-feedback error is reported as a secondary column
because the paper's earlier noise rows used it.
"""
from __future__ import annotations

import csv
import math
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
OUT = HERE / "analysis"
OUT.mkdir(exist_ok=True)
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
PLATFORMS = ("x2", "cf2-rotor")
ARMS = ("cmg_pes_table", "cmg_pes_gated_b05", "cmg_pes_gated")   # CF2: gated_b05 = beta .5, gated = beta .2 (A2); X2 has no gated_b05


def gmean(xs):
    return math.exp(sum(math.log(x) for x in xs) / len(xs))


def red(b, x):
    return 100.0 * (1.0 - x / b)


def noise() -> None:
    path = RES / "final_noise.csv"
    if not path.exists():
        print("no noise results yet")
        return
    rows = list(csv.DictReader(path.open()))
    idx = {(r["noise_level"], r["platform"], r["mission"], int(r["seed"]), r["label"]): r for r in rows}
    levels = sorted({r["noise_level"] for r in rows}, key=lambda s: 0 if s == "moderate" else 1)
    out = []
    for key in ("qerr_true_mean_rad", "qerr_feedback_mean_rad"):
        print(f"\n######## NOISE, metric = {key}")
        for lvl in levels:
            seeds = sorted({int(r["seed"]) for r in rows if r["noise_level"] == lvl})
            for arm in ARMS:
                print(f"\n  level={lvl}  arm={arm}  seeds={len(seeds)}")
                print(f"  {'platform':10s}{'mission':10s}{'PD+ff [mrad]':>14s}{'reduction mean':>16s}{'sd':>7s}{'min':>8s}{'#pos':>6s}")
                for p in PLATFORMS:
                    per_seed_geo_b, per_seed_geo_c = [], []
                    for m in MISSIONS:
                        rr, bs = [], []
                        for s in seeds:
                            b = idx.get((lvl, p, m, s, "pdff_rho3"))
                            c = idx.get((lvl, p, m, s, arm))
                            if b is None or c is None:
                                continue
                            bs.append(float(b[key]))
                            rr.append(red(float(b[key]), float(c[key])))
                        if not rr:
                            continue
                        sd = st.stdev(rr) if len(rr) > 1 else float("nan")
                        print(f"  {p:10s}{m:10s}{st.mean(bs)*1e3:14.3f}{st.mean(rr):16.2f}{sd:7.2f}{min(rr):8.2f}{sum(x > 0 for x in rr):4d}/{len(rr)}")
                        out.append(dict(metric=key, level=lvl, arm=arm, platform=p, mission=m, n=len(rr),
                                        base_mrad=st.mean(bs) * 1e3, red_mean=st.mean(rr), red_sd=sd,
                                        red_min=min(rr), n_pos=sum(x > 0 for x in rr)))
                    # geometric mean over missions, per seed
                    gr = []
                    for s in seeds:
                        try:
                            b = [float(idx[(lvl, p, m, s, "pdff_rho3")][key]) for m in MISSIONS]
                            c = [float(idx[(lvl, p, m, s, arm)][key]) for m in MISSIONS]
                        except KeyError:
                            continue
                        gr.append(red(gmean(b), gmean(c)))
                    if gr:
                        sd = st.stdev(gr) if len(gr) > 1 else float("nan")
                        print(f"  {p:10s}{'geo (5)':10s}{'':14s}{st.mean(gr):16.2f}{sd:7.2f}{min(gr):8.2f}{sum(x > 0 for x in gr):4d}/{len(gr)}")
                        out.append(dict(metric=key, level=lvl, arm=arm, platform=p, mission="geo", n=len(gr),
                                        base_mrad=float("nan"), red_mean=st.mean(gr), red_sd=sd, red_min=min(gr),
                                        n_pos=sum(x > 0 for x in gr)))
    if out:
        with (OUT / "noise_summary.csv").open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(out[0]))
            w.writeheader()
            w.writerows(out)


def disturbance() -> None:
    path = RES / "final_disturbance.csv"
    if not path.exists():
        print("no disturbance results yet")
        return
    rows = list(csv.DictReader(path.open()))
    idx = {(r["platform"], r["disturbance_level"], r["label"]): r for r in rows}
    print("\n######## DISTURBANCE (Hover, intermittent bursts)")
    out = []
    for p in PLATFORMS:
        for lvl in sorted({r["disturbance_level"] for r in rows}, key=lambda s: float(s[1:])):
            b = idx.get((p, lvl, "pdff_rho3"))
            if b is None:
                continue
            print(f"\n  {p}  amplitude {lvl}   PD+ff: whole {float(b['qerr_true_mean_rad'])*1e3:8.3f}  burst "
                  f"{math.degrees(float(b['disturbance_active_mean_rad'])):7.3f} deg  quiet "
                  f"{math.degrees(float(b['disturbance_quiet_mean_rad'])):7.3f} deg")
            for arm in ("cmg_pes_table", "cmg_pes_b05_ungated", "cmg_pes_gated_b05", "cmg_pes_gated"):
                c = idx.get((p, lvl, arm))
                if c is None:
                    continue
                rw = red(float(b["qerr_true_mean_rad"]), float(c["qerr_true_mean_rad"]))
                ra = red(float(b["disturbance_active_mean_rad"]), float(c["disturbance_active_mean_rad"]))
                rq = red(float(b["disturbance_quiet_mean_rad"]), float(c["disturbance_quiet_mean_rad"]))
                print(f"    {arm:22s} whole {float(c['qerr_true_mean_rad'])*1e3:8.3f} ({rw:+6.1f}%)  burst "
                      f"{math.degrees(float(c['disturbance_active_mean_rad'])):7.3f} deg ({ra:+6.1f}%)  quiet "
                      f"{math.degrees(float(c['disturbance_quiet_mean_rad'])):7.3f} deg ({rq:+6.1f}%)  "
                      f"effort {float(c['residual_normalized_rms']):.3f}  rotorSat {float(c['rotor_sat_fraction']):.3f}")
                out.append(dict(platform=p, level=lvl, arm=arm, whole_red=rw, burst_red=ra, quiet_red=rq,
                                base_burst_deg=math.degrees(float(b["disturbance_active_mean_rad"])),
                                cmg_burst_deg=math.degrees(float(c["disturbance_active_mean_rad"])),
                                base_quiet_deg=math.degrees(float(b["disturbance_quiet_mean_rad"])),
                                cmg_quiet_deg=math.degrees(float(c["disturbance_quiet_mean_rad"])),
                                effort=float(c["residual_normalized_rms"])))
    if out:
        with (OUT / "disturbance_summary.csv").open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(out[0]))
            w.writeheader()
            w.writerows(out)


if __name__ == "__main__":
    noise()
    disturbance()
    print(f"\nwrote {OUT}")
    sys.exit(0)
