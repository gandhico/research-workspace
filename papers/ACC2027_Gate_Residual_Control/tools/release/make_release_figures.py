"""Figures for the GitHub release, from the MATCH-verified recordings (reproduce/recordings) and results/*.csv.

  figures/missions/<mission>.png    reference, error, CMG membrane v, gate r, activity a, residual, decoder W (X2 | CF2)
  figures/missions/activity_regimes.png   mean activity and latched fraction per mission and platform
  figures/benchmark/*.png           controller families, neuron and non-neural bases, ladder, noise

    .venv\\Scripts\\python.exe tools\\release\\make_release_figures.py <release_root>
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from gra_control.math3d import reference_euler  # noqa: E402

REC = REPO / "reproduce" / "recordings"
M = [("roll", "Roll"), ("full3", "Full3"), ("hard45", "Hard45"), ("hardstep", "Hardstep"), ("yaw360", "Yaw360")]
PL = [("x2", "Skydio X2", 0.5), ("cf2", "Crazyflie 2 (1.5x rotors)", 0.2)]
AXC = ["#d62728", "#2ca02c", "#1f5fd6"]
plt.rcParams.update({"font.size": 8, "axes.grid": True, "grid.alpha": 0.25, "axes.spines.top": False,
                     "axes.spines.right": False})


def rows(p):
    with Path(p).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def mission_figure(mission, name, out):
    fig, ax = plt.subplots(7, 2, figsize=(11, 13), sharex=True)
    for c, (p, label, beta) in enumerate(PL):
        d = REC / f"{p}_{mission}_cmg"
        z = np.load(d / "neural_trace_full_rate.npz")
        s = slice(None, None, 20)
        t = z["t"][s]
        lim = np.array(json.loads((d / "summary.json").read_text())["actuation"]["torque_limits_Nm"])
        base = rows(REC / f"{p}_{mission}_pdff" / "trace.csv")
        bt = np.array([float(r["t"]) for r in base]); be = np.degrees([float(r["qerr_true_rad"]) for r in base])
        ref = np.degrees(np.array([reference_euler(x, mission, 45.0) for x in t]))
        for i, lab in enumerate(("roll", "pitch", "yaw")):
            ax[0, c].plot(t, ref[:, i], color=AXC[i], lw=1, label=lab)
        ax[0, c].set_ylabel("reference\n(deg)"); ax[0, c].legend(ncol=3, fontsize=7, loc="upper right")
        ax[0, c].set_title(label, fontsize=10, fontweight="bold")
        e = np.degrees(z["qerr_true_rad"][s])
        ax[1, c].semilogy(bt, np.maximum(be, 1e-5), color="0.55", lw=0.9, label=f"PD+ff  (mean {np.mean(be):.3f} deg)")
        ax[1, c].semilogy(t, np.maximum(e, 1e-5), color="tab:blue", lw=0.9, label=f"+ CMG-PES  (mean {np.mean(e):.3f} deg)")
        ax[1, c].set_ylabel("attitude error\n(deg)"); ax[1, c].legend(fontsize=7, loc="upper right")
        for j in range(6):
            sty = dict(color=AXC[j % 3], ls="-" if j < 3 else "--", lw=0.9)
            ax[2, c].plot(t, z["voltage"][s, j], **sty)
            ax[3, c].plot(t, z["gate"][s, j], **sty)
            ax[4, c].plot(t, z["activity"][s, j], **sty)
        ax[2, c].axhline(1.0, color="k", lw=0.6, ls=":"); ax[2, c].set_ylabel("membrane v_j")
        ax[3, c].set_yscale("symlog", linthresh=1e-5); ax[3, c].set_ylim(0, 1.5); ax[3, c].set_ylabel("gate r_j\n(symlog)")
        ax[4, c].set_ylim(-0.05, 1.08); ax[4, c].set_ylabel("activity a_j")
        ax[4, c].text(0.01, 0.06, "solid +x +y +z   dashed -x -y -z", transform=ax[4, c].transAxes, fontsize=7)
        rr = z["realized_residual_torque"][s] / (beta * lim[None, :])
        blk = (z["output_gate_mask"][s] == 0).any(1)
        if blk.any():
            ax[5, c].fill_between(t, -1.05, 1.05, where=blk, color="orange", alpha=0.25, lw=0, label="gate blocking")
        for i in range(3):
            ax[5, c].plot(t, rr[:, i], color=AXC[i], lw=0.9)
        ax[5, c].set_ylim(-1.05, 1.05); ax[5, c].set_ylabel("residual /\n(beta l)")
        W = z["weights"][s].reshape(len(t), 18)
        for k in range(18):
            ax[6, c].plot(t, W[:, k], color=AXC[k // 6], lw=0.7, alpha=0.8)
        ax[6, c].set_ylabel("decoder W\n(18 weights)"); ax[6, c].set_xlabel("time (s)")
    fig.suptitle(f"{name}: what the CMG-PES residual does during the mission (primary runs, rho = 3, gated)", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.985))
    fig.savefig(out, dpi=130); plt.close(fig)


def bar_group(ax, labels, series, colors, ylabel):
    x = np.arange(len(labels)); w = 0.8 / len(series)
    for i, (name, vals) in enumerate(series):
        b = ax.bar(x + (i - (len(series) - 1) / 2) * w, vals, w, label=name, color=colors[i])
        for xi, v in zip(x + (i - (len(series) - 1) / 2) * w, vals):
            ax.text(xi, v + (0.6 if v >= 0 else -2.2), f"{v:.1f}", ha="center", fontsize=7)
    ax.set_xticks(x); ax.set_xticklabels(labels); ax.axhline(0, color="k", lw=0.6); ax.set_ylabel(ylabel); ax.legend()


def main(root: Path):
    fm = root / "figures" / "missions"; fb = root / "figures" / "benchmark"
    fm.mkdir(parents=True, exist_ok=True); fb.mkdir(parents=True, exist_ok=True)
    for m, name in M:
        mission_figure(m, name, fm / f"{m}.png"); print("mission", m)

    act = rows(root / "results" / "07_cmg_activity_by_mission.csv")
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.4))
    for k, (col, lab) in enumerate((("mean_activity", "mean activity a"), ("latched_fraction(a>0.99)", "fraction of unit-samples latched"))):
        bar_group(ax[k], [n for _, n in M], [(pl, [float(r[col]) for r in act if r["platform"] == p]) for p, pl, _ in PL],
                  ["#1f77b4", "#ff7f0e"], lab)
        ax[k].set_ylim(0, 1.15)
    ax[0].axhline(0.3727, color="0.4", ls=":", lw=1); ax[0].text(4.45, 0.40, "rest 0.373", fontsize=7, ha="right")
    fig.tight_layout(); fig.savefig(fm / "activity_regimes.png", dpi=140); plt.close(fig)

    cf = rows(root / "results" / "04_controller_families.csv")
    fams = ["PD+ff (computed-torque form)", "PID+ff", "LQR", "SMC", "MPC", "NMPC"]
    geo = lambda fam, p: float(next(r for r in cf if r["nominal_controller"] == fam and r["platform"] == p
                                    and r["mission"].startswith("5-mission"))["reduction_pct"])
    fig, ax = plt.subplots(figsize=(9, 3.4))
    bar_group(ax, ["PD+ff", "PID+ff", "LQR", "SMC", "MPC", "NMPC"], [("X2", [geo(f, "x2") for f in fams]),
              ("CF2", [geo(f, "cf2") for f in fams])], ["#1f77b4", "#ff7f0e"], "5-mission error reduction (%)")
    ax.set_title("Same residual on six nominal controllers (no retuning)")
    fig.tight_layout(); fig.savefig(fb / "controller_families.png", dpi=140); plt.close(fig)

    # per-mission heatmap of controller families
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.2))
    for k, (p, pl, _) in enumerate(PL):
        A = np.array([[float(next(r for r in cf if r["nominal_controller"] == f and r["platform"] == p and r["mission"] == m)["reduction_pct"])
                       for m, _ in M] for f in fams])
        im = ax[k].imshow(A, cmap="RdBu", vmin=-80, vmax=80, aspect="auto")
        ax[k].set_xticks(range(5)); ax[k].set_xticklabels([n for _, n in M]); ax[k].set_yticks(range(6))
        ax[k].set_yticklabels(["PD+ff", "PID+ff", "LQR", "SMC", "MPC", "NMPC"]); ax[k].set_title(pl); ax[k].grid(False)
        for i in range(6):
            for j in range(5):
                ax[k].text(j, i, f"{A[i, j]:.0f}", ha="center", va="center", fontsize=7)
    fig.colorbar(im, ax=ax, label="reduction (%)", shrink=0.9)
    fig.savefig(fb / "controller_families_by_mission.png", dpi=140, bbox_inches="tight"); plt.close(fig)

    nb = rows(root / "results" / "05_neuron_and_nonneural_bases.csv")
    bases = [("cmg", "CMG"), ("lif", "LIF"), ("alif", "ALIF"), ("lifrate", "LIFRate"), ("izhikevich", "Izhikevich"),
             ("paired-current", "static paired"), ("constant-one", "constant 1")]
    g = lambda b, p: float(next(r for r in nb if r["basis"] == b and r["platform"] == p and r["mission"].startswith("5-mission"))["reduction_pct"])
    fig, ax = plt.subplots(figsize=(10, 3.6))
    bar_group(ax, [n for _, n in bases], [("X2", [g(b, "x2") for b, _ in bases]), ("CF2", [g(b, "cf2") for b, _ in bases])],
              ["#1f77b4", "#ff7f0e"], "5-mission error reduction (%)")
    ax.axvspan(0.5, 4.5, color="0.9", zorder=-1); ax.axvspan(4.5, 6.5, color="#fff4e0", zorder=-1)
    ax.text(2.5, ax.get_ylim()[1] * 0.92, "conventional neuron families", ha="center", fontsize=8)
    ax.text(5.5, ax.get_ylim()[1] * 0.92, "non-neural bases", ha="center", fontsize=8)
    ax.set_title("Same interface, same PES rule (exact-rate normalization): which basis carries the residual?")
    fig.tight_layout(); fig.savefig(fb / "neuron_and_nonneural_bases.png", dpi=140); plt.close(fig)

    lad = rows(root / "results" / "06_baseline_ladder.csv")
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.4))
    for k, p in enumerate(("x2", "cf2")):
        r_ = [r for r in lad if r["platform"] == p]
        vals = [[float(r[c]) for r in r_] for c in ("reduction_fixed_PD_pct", "reduction_PDff_rho1_pct", "reduction_PDff_rho3_pct")]
        bar_group(ax[k], [r["mission"] for r in r_], [("fixed PD", vals[0]), ("PD+ff, rho=1", vals[1]), ("PD+ff, rho=3", vals[2])],
                  ["#9ecae1", "#4292c6", "#08519c"], "reduction (%)")
        ax[k].set_title({"x2": "Skydio X2", "cf2": "Crazyflie 2"}[p])
    fig.suptitle("The residual's gain shrinks as the nominal controller gets stronger (Table II ladder)")
    fig.tight_layout(); fig.savefig(fb / "baseline_ladder.png", dpi=140); plt.close(fig)
    print("figures written")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
