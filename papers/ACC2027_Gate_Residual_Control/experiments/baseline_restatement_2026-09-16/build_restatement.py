"""Baseline restatement analysis (2026-09-16): tables + figures for the PD / PD+ff / tuned-PD+ff ladder.

Read-only over existing result folders; nothing canonical is modified.
Sources
  A rate_ff_summary.csv      PD, PID(0.05), CMG|PD, PD+ff(1x), CMG|PD+ff(1x)   (pid_baseline_2026-09-10)
  B cmg_beta_summary.csv     PD+ff(3x) and CMG on it at the selected beta       (baselines_2026-09-10)
  C tune/pdff{,_noise}/bw*/  bandwidth sweep, noise-free and realistic noise    (baselines_2026-09-10)
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ACC = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control")
RES = ACC / "experiments/nengo_nef_replication_2026-08-29/results"
A = RES / "pid_baseline_2026-09-10/rate_ff_summary.csv"
B = RES / "baselines_2026-09-10/cmg_beta_summary.csv"
TUNE = RES / "baselines_2026-09-10/tune"
OUT = ACC / "experiments/baseline_restatement_2026-09-16"

PLATFORMS = (("x2", "Skydio X2"), ("cf2-rotor", "Crazyflie 2 (1.5x rotors)"))
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
MLABEL = {"roll": "Roll", "full3": "Full3", "hard45": "Hard45", "hardstep": "Hardstep", "yaw360": "Yaw360"}
BWS = (0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0)
# dataviz reference palette, light mode, documented slot order (slots 1-3 validate all-pairs)
C1, C2, C3, C4, C5 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"
INK, INK2 = "#0b0b0b", "#52514e"


def rows(p: Path):
    with p.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_master():
    a = {(r["platform"], r["mission"]): r for r in rows(A)}
    b = {(r["platform"], r["mission"]): r for r in rows(B) if r["family"] == "pdff"}
    out = []
    for p, _ in PLATFORMS:
        for m in MISSIONS:
            ra, rb = a[(p, m)], b[(p, m)]
            rec = {
                "platform": p, "mission": m,
                "PD": float(ra["PD"]), "PID_005": float(ra["PID_0.05"]), "CMG_on_PD": float(ra["CMG_on_PD"]),
                "PDff_1x": float(ra["PD_ff"]), "CMG_on_PDff_1x": float(ra["CMG_on_PD_ff"]),
                "PDff_3x": float(rb["family_alone"]), "CMG_on_PDff_3x": float(rb["CMG_on_family"]),
                "beta_sel": float(rb["beta"]),
                "sat_PD": float(ra["sat_PD"]), "sat_PDff_1x": float(ra["sat_PD_ff"]),
                "sat_CMG_on_PDff_3x": float(rb["sat_CMG"]),
                "residual_CMG_on_PD": float(ra["residual_CMG_on_PD"]),
                "residual_CMG_on_PDff_1x": float(ra["residual_CMG_on_PD_ff"]),
                "residual_CMG_on_PDff_3x": float(rb["residual_mean_Nm"]),
            }
            rec["ff1x_vs_PD_pct"] = 100 * (1 - rec["PDff_1x"] / rec["PD"])
            rec["tuned_vs_PD_pct"] = 100 * (1 - rec["PDff_3x"] / rec["PD"])
            rec["CMGonPD_vs_PD_pct"] = 100 * (1 - rec["CMG_on_PD"] / rec["PD"])
            rec["CMGonff1x_vs_ff1x_pct"] = 100 * (1 - rec["CMG_on_PDff_1x"] / rec["PDff_1x"])
            rec["CMGonff3x_vs_ff3x_pct"] = 100 * (1 - rec["CMG_on_PDff_3x"] / rec["PDff_3x"])
            rec["tuned_over_CMGonPD"] = rec["PDff_3x"] / rec["CMG_on_PD"]
            out.append(rec)
    with (OUT / "master_table.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    return {(r["platform"], r["mission"]): r for r in out}


def build_sweep():
    recs = []
    for noise, sub in (("none", "pdff"), ("realistic", "pdff_noise")):
        for p, _ in PLATFORMS:
            for m in MISSIONS:
                for bw in BWS:
                    d = TUNE / sub / f"bw{bw:g}" / f"{p.replace('-', '_')}_{m}_classical" / "summary.json"
                    if not d.exists():
                        continue
                    s = json.loads(d.read_text(encoding="utf-8"))
                    recs.append({"noise": noise, "platform": p, "mission": m, "bw": bw,
                                 "qerr_mean_rad": s["qerr_mean_rad"],
                                 "saturation_fraction": s["saturation_fraction"]})
    with (OUT / "bandwidth_sweep.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(recs[0]))
        w.writeheader()
        w.writerows(recs)
    return recs


def style(ax):
    ax.set_axisbelow(True)
    ax.grid(axis="y", alpha=0.25, lw=0.7)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#bbbbb8")
    ax.tick_params(colors=INK2, labelsize=8.5)


def fig_ladder(M):
    series = [("PD", "PD (Table V)", C1, None), ("CMG_on_PD", "CMG | PD", C1, "///"),
              ("PDff_1x", "PD+ff, Table V bandwidth", C2, None),
              ("CMG_on_PDff_1x", "CMG | PD+ff (1x)", C2, "///"),
              ("PDff_3x", "PD+ff, tuned bandwidth (3x)", C3, None),
              ("CMG_on_PDff_3x", "CMG | PD+ff (3x)", C3, "///")]
    fig, axes = plt.subplots(1, 2, figsize=(13.2, 5.0), constrained_layout=True)
    x = np.arange(len(MISSIONS))
    w = 0.14
    for ax, (p, name) in zip(axes, PLATFORMS):
        for i, (key, lab, col, hatch) in enumerate(series):
            v = [M[(p, m)][key] for m in MISSIONS]
            ax.bar(x + (i - 2.5) * w, v, w * 0.92, color=col, hatch=hatch, edgecolor="white", linewidth=0.8,
                   label=lab if ax is axes[0] else None)
        ax.set_yscale("log")
        ax.set_ylim(3e-5, 2.0)
        ax.set_xticks(x)
        ax.set_xticklabels([MLABEL[m] for m in MISSIONS], fontsize=9.5, color=INK)
        ax.set_title(name, fontsize=10.5, color=INK)
        style(ax)
        for j, m in enumerate(MISSIONS):          # selective labels: only the contested pair
            ax.annotate(f"{M[(p, m)]['CMG_on_PD']:.4f}", (x[j] - 1.5 * w, M[(p, m)]["CMG_on_PD"]),
                        textcoords="offset points", xytext=(0, 3), ha="center", fontsize=6.6,
                        color=INK2, rotation=90)
            ax.annotate(f"{M[(p, m)]['PDff_3x']:.4f}", (x[j] + 1.5 * w, M[(p, m)]["PDff_3x"]),
                        textcoords="offset points", xytext=(0, 3), ha="center", fontsize=6.6,
                        color=INK2, rotation=90)
    axes[0].set_ylabel("mean quaternion-angle error [rad], log scale", fontsize=9.5, color=INK)
    axes[0].legend(fontsize=8.2, ncol=3, loc="upper left", framealpha=0.95, labelcolor=INK2)
    fig.suptitle("Baseline ladder: what the residual is compared against "
                 "(45 s, noise-free; hatched = with CMG-PES; labels = CMG|PD vs tuned PD+ff)",
                 fontsize=11, color=INK)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"fig1_baseline_ladder.{ext}", dpi=190)
    plt.close(fig)


def fig_bandwidth(S):
    cols = (C1, C2, C3, C4, C5)
    fig, axes = plt.subplots(2, 2, figsize=(12.4, 7.2), sharex=True, sharey=True, constrained_layout=True)
    for r, (noise, nlabel) in enumerate((("none", "noise-free"), ("realistic", "realistic measurement noise"))):
        for c, (p, name) in enumerate(PLATFORMS):
            ax = axes[r, c]
            for k, m in enumerate(MISSIONS):
                pts = sorted([(x["bw"], x["qerr_mean_rad"]) for x in S
                              if x["noise"] == noise and x["platform"] == p and x["mission"] == m])
                if not pts:
                    continue
                bw, q = zip(*pts)
                ax.plot(bw, q, color=cols[k], lw=2, marker="o", ms=4.5,
                        label=MLABEL[m] if (r == 0 and c == 0) else None)
            ax.axvline(3.0, color="#888888", lw=1.1, ls="--")
            ax.set_xscale("log")
            ax.set_yscale("log")
            ax.set_xticks(BWS)
            ax.set_xticklabels([f"{b:g}x" for b in BWS])
            ax.set_title(f"{name} - {nlabel}", fontsize=10, color=INK)
            style(ax)
            if r == 1:
                ax.set_xlabel("bandwidth factor on the Table V natural frequency", fontsize=9.5, color=INK)
            if c == 0:
                ax.set_ylabel("mean quaternion-angle error [rad]", fontsize=9.5, color=INK)
    axes[0, 0].legend(fontsize=8.5, ncol=5, loc="lower left", framealpha=0.95, labelcolor=INK2)
    for ax in (axes[0, 0], axes[0, 1]):
        ax.annotate("selected 3x", xy=(3.0, 1.0), xycoords=("data", "axes fraction"), xytext=(4, -11),
                    textcoords="offset points", fontsize=8, color=INK2, ha="left")
    fig.suptitle("PD+ff bandwidth sweep: the optimum is interior at 3x on both airframes, "
                 "noise-free and under the paper's noise model", fontsize=11, color=INK)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"fig2_bandwidth_sweep.{ext}", dpi=190)
    plt.close(fig)


def fig_cmg_gain(M):
    series = [("CMGonPD_vs_PD_pct", "on PD (the paper's pairing)", C1),
              ("CMGonff1x_vs_ff1x_pct", "on PD+ff (Table V bandwidth)", C2),
              ("CMGonff3x_vs_ff3x_pct", "on PD+ff (tuned 3x)", C3)]
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.6), constrained_layout=True)
    x = np.arange(len(MISSIONS))
    w = 0.26
    for ax, (p, name) in zip(axes, PLATFORMS):
        for i, (key, lab, col) in enumerate(series):
            v = [M[(p, m)][key] for m in MISSIONS]
            ax.bar(x + (i - 1) * w, v, w * 0.9, color=col, edgecolor="white", linewidth=0.8,
                   label=lab if ax is axes[0] else None)
            if key.endswith("ff3x_pct"):        # label only the series the reader has not seen before
                for j, val in enumerate(v):
                    ax.annotate(f"{val:+.0f}%", (x[j] + (i - 1) * w, val), textcoords="offset points",
                                xytext=(0, 3 if val >= 0 else -12), ha="center", fontsize=8, color=INK2)
        ax.axhline(0, color="#555555", lw=1.0)
        ax.set_xticks(x)
        ax.set_xticklabels([MLABEL[m] for m in MISSIONS], fontsize=9.5, color=INK)
        ax.set_ylim(-30, 100)
        ax.set_title(f"{name}   (beta = {M[(p, 'roll')]['beta_sel']:g} on the tuned baseline)",
                     fontsize=10, color=INK)
        style(ax)
    axes[0].set_ylabel("error reduction by CMG-PES vs its own baseline [%]", fontsize=9.5, color=INK)
    axes[0].legend(fontsize=8.5, loc="upper right", framealpha=0.95, labelcolor=INK2)
    fig.suptitle("What CMG-PES adds as the baseline gets stronger (positive = the residual helps)",
                 fontsize=11, color=INK)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"fig3_cmg_gain_vs_baseline.{ext}", dpi=190)
    plt.close(fig)


def geo(vals):
    return float(np.exp(np.mean([np.log(v) for v in vals])))


def write_tables(M, S):
    L = ["# Auto-generated tables (build_restatement.py)", "",
         "Mean quaternion-angle error, rad, 45 s, dt 0.5 ms, one deterministic run per cell.", ""]
    L += ["## T1. The baseline ladder", "",
          "| platform | mission | PD (Table V) | CMG \\| PD (Table V) | PD+ff (1x) | CMG \\| PD+ff (1x) | "
          "PD+ff (tuned 3x) | CMG \\| PD+ff (3x) |", "|---|---|---|---|---|---|---|---|"]
    keys = ("PD", "CMG_on_PD", "PDff_1x", "CMG_on_PDff_1x", "PDff_3x", "CMG_on_PDff_3x")
    for p, name in PLATFORMS:
        for m in MISSIONS:
            r = M[(p, m)]
            L.append(f"| {p} | {MLABEL[m]} | " + " | ".join(f"{r[k]:.5f}" for k in keys) + " |")
        L.append(f"| **{p}** | **geo-mean** | " +
                 " | ".join(f"**{geo([M[(p, m)][k] for m in MISSIONS]):.5f}**" for k in keys) + " |")
    L += ["", "## T2. Derived comparisons (%, positive = better than the stated reference)", "",
          "| platform | mission | ff(1x) vs PD | tuned(3x) vs PD | CMG\\|PD vs PD (paper headline) | "
          "CMG vs ff(1x) | CMG vs ff(3x) | tuned PD+ff / CMG\\|PD |", "|---|---|---|---|---|---|---|---|"]
    for p, _ in PLATFORMS:
        for m in MISSIONS:
            r = M[(p, m)]
            L.append(f"| {p} | {MLABEL[m]} | {r['ff1x_vs_PD_pct']:.1f} | {r['tuned_vs_PD_pct']:.1f} | "
                     f"{r['CMGonPD_vs_PD_pct']:.1f} | {r['CMGonff1x_vs_ff1x_pct']:.1f} | "
                     f"{r['CMGonff3x_vs_ff3x_pct']:.1f} | {r['tuned_over_CMGonPD']:.3f} |")
    L += ["", "## T3. Effort and saturation", "",
          "| platform | mission | sat PD | sat PD+ff (1x) | sat CMG\\|PD+ff (3x) | residual CMG\\|PD [N m] | "
          "residual CMG\\|ff(1x) [N m] | residual CMG\\|ff(3x) [N m] |", "|---|---|---|---|---|---|---|---|"]
    for p, _ in PLATFORMS:
        for m in MISSIONS:
            r = M[(p, m)]
            L.append(f"| {p} | {MLABEL[m]} | {r['sat_PD']:.4f} | {r['sat_PDff_1x']:.4f} | "
                     f"{r['sat_CMG_on_PDff_3x']:.4f} | {r['residual_CMG_on_PD']:.5f} | "
                     f"{r['residual_CMG_on_PDff_1x']:.5f} | {r['residual_CMG_on_PDff_3x']:.5f} |")
    L += ["", "## T4. PD+ff bandwidth sweep, geometric mean over the five missions", "",
          "| platform | noise | " + " | ".join(f"{b:g}x" for b in BWS) + " |", "|---|---|" + "---|" * len(BWS)]
    for p, _ in PLATFORMS:
        for noise in ("none", "realistic"):
            cells = []
            for b in BWS:
                v = [x["qerr_mean_rad"] for x in S if x["platform"] == p and x["noise"] == noise and x["bw"] == b]
                cells.append(f"{geo(v):.5f}" if len(v) == len(MISSIONS) else "-")
            L.append(f"| {p} | {noise} | " + " | ".join(cells) + " |")
    (OUT / "TABLES.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


M = build_master()
S = build_sweep()
write_tables(M, S)
fig_ladder(M)
fig_bandwidth(S)
fig_cmg_gain(M)
print("master rows", len(M), "sweep rows", len(S))
for p, _ in PLATFORMS:
    def g(k, p=p):
        return float(np.exp(np.mean([np.log(M[(p, m)][k]) for m in MISSIONS])))
    print(p, "geo: PD %.5f  CMG|PD %.5f  PD+ff1x %.5f  CMG|ff1x %.5f  PD+ff3x %.5f  CMG|ff3x %.5f"
          % (g("PD"), g("CMG_on_PD"), g("PDff_1x"), g("CMG_on_PDff_1x"), g("PDff_3x"), g("CMG_on_PDff_3x")))
