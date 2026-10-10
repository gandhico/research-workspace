"""Figure: hover hold under intermittent disturbance, PD versus CMG-PES."""
from __future__ import annotations

import csv
import io
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
RES = HERE / "results" / "hover_intermittent_2026-09-05"
WARMUP, ON, OFF = 5.0, 5.0, 5.0
PD_C, CMG_C = "#3569A8", "#B5482A"


def load(run):
    with io.open(RES / run / "trace.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return {c: np.array([float(r[c]) for r in rows]) for c in rows[0]}


def bursts(tmax):
    out, e = [], WARMUP
    while e < tmax:
        out.append((e, min(e + ON, tmax)))
        e += ON + OFF
    return out


def main():
    pd_, cmg = load("pd_disturbed"), load("cmg_disturbed")
    t = pd_["t"]
    fig, ax = plt.subplots(3, 1, figsize=(7.0, 6.2), sharex=True,
                           gridspec_kw={"height_ratios": [2.1, 1.5, 1.3]})

    for a in ax:
        for s0, s1 in bursts(t[-1]):
            a.axvspan(s0, s1, color="0.85", zorder=0, lw=0)

    ax[0].plot(t, np.degrees(pd_["qerr"]), color=PD_C, lw=1.0, label="quaternion PD")
    ax[0].plot(t, np.degrees(cmg["qerr"]), color=CMG_C, lw=1.0, label="CMG--PES")
    ax[0].set_ylabel(r"$\theta_q$  [deg]")
    ax[0].legend(loc="upper right", fontsize=8, framealpha=0.9)
    ax[0].set_title("X2 hover hold, intermittent 0.15 N·m disturbance "
                    "(shaded = disturbance active)", fontsize=10)

    res = np.linalg.norm(np.c_[cmg["residual_x"], cmg["residual_y"],
                               cmg["residual_z"]], axis=1)
    ax[1].plot(t, res, color=CMG_C, lw=0.9)
    ax[1].set_ylabel(r"$\|\beta\ell\odot s_k\|$" "\n[N·m]")
    ax[1].set_yscale("log")

    W = np.c_[[cmg[f"decoder_w_{i}"] for i in range(18)]].T
    ax[2].plot(t, np.linalg.norm(W - W[0], axis=1), color="0.25", lw=0.9)
    ax[2].set_ylabel(r"$\|W_k-W_0\|_F$")
    ax[2].set_xlabel("time [s]")

    for a in ax:
        a.grid(alpha=0.25, lw=0.5)
        a.set_xlim(0, t[-1])
    fig.tight_layout(pad=0.6)
    for ext in ("png", "pdf"):
        fig.savefig(RES / f"hover_intermittent.{ext}", dpi=200,
                    bbox_inches="tight")
    print(f"wrote {RES / 'hover_intermittent.png'}")

    # numbers quoted in the caption
    ph_burst = np.zeros_like(t, dtype=bool)
    for s0, s1 in bursts(t[-1]):
        ph_burst |= (t >= s0) & (t < s1)
    ph_sil = (t >= WARMUP) & ~ph_burst
    for nm, m in (("burst", ph_burst), ("silence", ph_sil)):
        a, b = pd_["qerr"][m].mean(), cmg["qerr"][m].mean()
        print(f"  {nm:8s} PD {np.degrees(a):.3f} deg   CMG {np.degrees(b):.3f} deg"
              f"   reduction {100 * (1 - b / a):.1f}%")
    print(f"  decoder drift at 45 s: {np.linalg.norm(W[-1] - W[0]):.4f}")


if __name__ == "__main__":
    main()
