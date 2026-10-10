"""Turn the final sweep into the tables and figures the paper needs."""
from __future__ import annotations

import csv
import io
import json
import statistics as st
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE / "results" / "final_sweep_2026-09-05"
OUT = ROOT / "compiled"
PLATFORMS = ("x2", "cf2-rotor")
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
LEVELS = (("n0_clean", (1,)), ("n1_moderate", (7, 8)), ("n2_realistic", (7, 8)))
PD_C, CMG_C = "#3569A8", "#B5482A"


def q(plat, mis, ctl, level, seed):
    p = ROOT / "A_noise" / plat / mis / ctl / f"{level}_s{seed}" / "summary.json"
    return json.loads(p.read_text())["qerr_mean_rad"] if p.is_file() else None


# --------------------------------------------------------------------------
def table_noise():
    rows = []
    for plat in PLATFORMS:
        for mis in MISSIONS:
            rec = {"platform": plat, "mission": mis}
            for level, seeds in LEVELS:
                pd_ = [q(plat, mis, "classical", level, s) for s in seeds]
                cm = [q(plat, mis, "nengo-nef-pes", level, s) for s in seeds]
                if any(v is None for v in pd_ + cm):
                    continue
                red = [100 * (1 - c / p) for p, c in zip(pd_, cm)]
                rec[f"{level}_pd"] = st.mean(pd_)
                rec[f"{level}_cmg"] = st.mean(cm)
                rec[f"{level}_red"] = st.mean(red)
                rec[f"{level}_red_sd"] = st.stdev(red) if len(red) > 1 else 0.0
            rows.append(rec)

    with io.open(OUT / "noise_sensitivity.csv", "w", encoding="utf-8",
                 newline="") as f:
        w = csv.DictWriter(f, fieldnames=sorted({k for r in rows for k in r}))
        w.writeheader()
        w.writerows(rows)

    print(f"\n{'platform':11s}{'mission':10s}{'clean':>9s}{'moderate':>11s}"
          f"{'realistic':>11s}{'seed SD':>10s}")
    print("-" * 62)
    for r in rows:
        if "n2_realistic_red" not in r:
            continue
        print(f"{r['platform']:11s}{r['mission']:10s}"
              f"{r['n0_clean_red']:8.2f}%{r['n1_moderate_red']:10.2f}%"
              f"{r['n2_realistic_red']:10.2f}%"
              f"{r['n2_realistic_red_sd']:9.3f}%")
    return rows


def latex_table(rows):
    lines = [
        r"\begin{table}[t]",
        r"\caption{Mean quaternion-angle-error reduction versus PD under "
        r"measurement noise. Clean reproduces Table~\ref{tab:mujoco}; "
        r"moderate is $0.010$ rad / $0.025$ rad\,s$^{-1}$ and realistic is "
        r"$0.020$ rad / $0.050$ rad\,s$^{-1}$ on the attitude and rate "
        r"estimates. Noisy entries are the mean of two seeds; the seed "
        r"standard deviation is given for the realistic level.}",
        r"\label{tab:noise}\centering\small",
        r"\begin{tabular}{llrrr@{\,}l}",
        r"\toprule",
        r"Model&Mission&Clean&Moderate&\multicolumn{2}{c}{Realistic}\\\midrule",
    ]
    for i, r in enumerate(rows):
        if "n2_realistic_red" not in r:
            continue
        plat = {"x2": "X2", "cf2-rotor": "CF2"}[r["platform"]]
        name = plat if i % len(MISSIONS) == 0 else ""
        if name and i:
            lines.append(r"\midrule")
        lines.append(
            f"{name}&{r['mission'].capitalize()}&"
            f"{r['n0_clean_red']:.1f}\\%&{r['n1_moderate_red']:.1f}\\%&"
            f"{r['n2_realistic_red']:.1f}\\%&"
            f"$\\pm${r['n2_realistic_red_sd']:.2f}\\\\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    (OUT / "table_noise.tex").write_text("\n".join(lines), encoding="utf-8")
    print(f"\nwrote {OUT / 'table_noise.tex'}")


def fig_noise(rows):
    fig, ax = plt.subplots(figsize=(7.0, 3.0))
    x = np.arange(len(rows))
    for k, (lvl, lab, c) in enumerate((("n0_clean", "clean", "#9BB7D4"),
                                       ("n1_moderate", "moderate", "#5E8CBE"),
                                       ("n2_realistic", "realistic", "#2F4F73"))):
        vals = [r.get(f"{lvl}_red", np.nan) for r in rows]
        ax.bar(x + (k - 1) * 0.27, vals, 0.26, label=lab, color=c)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{'X2' if r['platform'] == 'x2' else 'CF2'}\n"
                        f"{r['mission']}" for r in rows], fontsize=7)
    ax.set_ylabel("mean-error reduction vs PD [%]")
    ax.axhline(0, color="0.3", lw=0.8)
    ax.legend(title="measurement noise", fontsize=8, title_fontsize=8)
    ax.grid(axis="y", alpha=0.3, lw=0.5)
    fig.tight_layout(pad=0.5)
    for e in ("png", "pdf"):
        fig.savefig(OUT / f"noise_sensitivity.{e}", dpi=200, bbox_inches="tight")
    print(f"wrote {OUT / 'noise_sensitivity.png'}")


# --------------------------------------------------------------------------
def fig_long_hover():
    def load(ctl):
        p = ROOT / "B_long_hover" / ctl / "trace.csv"
        if not p.is_file():
            return None
        rows = list(csv.DictReader(io.open(p, encoding="utf-8", newline="")))
        return {c: np.array([float(r[c]) for r in rows]) for c in rows[0]}

    pd_, cmg = load("classical"), load("nengo-nef-pes")
    if pd_ is None or cmg is None:
        print("long-hover traces missing, skipping")
        return
    t = pd_["t"]
    W = np.c_[[cmg[f"decoder_w_{i}"] for i in range(18)]].T
    drift = np.linalg.norm(W - W[0], axis=1)

    fig, ax = plt.subplots(2, 1, figsize=(7.0, 4.4), sharex=True,
                           gridspec_kw={"height_ratios": [1.6, 1.3]})
    e = 5.0
    while e < t[-1]:
        for a in ax:
            a.axvspan(e, min(e + 5, t[-1]), color="0.88", zorder=0, lw=0)
        e += 10.0
    ax[0].plot(t, np.degrees(pd_["qerr"]), color=PD_C, lw=0.7, label="quaternion PD")
    ax[0].plot(t, np.degrees(cmg["qerr"]), color=CMG_C, lw=0.7, label="CMG--PES")
    ax[0].set_ylabel(r"$\theta_q$ [deg]")
    ax[0].legend(fontsize=8, loc="upper right")
    ax[0].set_title("X2 hover hold, 180 s, sixteen disturbance bursts", fontsize=10)
    ax[1].plot(t, drift, color="0.25", lw=0.8)
    ax[1].set_ylabel(r"$\|W_k-W_0\|_F$")
    ax[1].set_xlabel("time [s]")
    for a in ax:
        a.grid(alpha=0.25, lw=0.5)
        a.set_xlim(0, t[-1])
    fig.tight_layout(pad=0.6)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"long_hover_retention.{ext}", dpi=200,
                    bbox_inches="tight")
    print(f"wrote {OUT / 'long_hover_retention.png'}")

    # does retention converge? report the silence-floor per episode
    floors = []
    e = 10.0
    while e + 5 <= t[-1]:
        m = (t >= e) & (t < e + 5)
        if m.any():
            floors.append(float(drift[m][-1]))
        e += 10.0
    print("\nsilence-floor drift per episode:")
    print("  " + "  ".join(f"{v:.3f}" for v in floors))
    if len(floors) >= 6:
        first, last = st.mean(floors[:3]), st.mean(floors[-3:])
        growth = 100 * (last - first) / first if first else float("nan")
        print(f"  first three {first:.3f} -> last three {last:.3f} "
              f"({growth:+.1f}%)")
        print("  VERDICT:", "converging / saturated" if abs(growth) < 15
              else "still accumulating")
    json.dump({"silence_floor_drift": floors},
              (OUT / "retention.json").open("w"), indent=2)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    rows = table_noise()
    latex_table(rows)
    fig_noise(rows)
    fig_long_hover()
    print(f"\ncompiled into {OUT}")
