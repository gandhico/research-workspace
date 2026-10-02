"""CMG neuron states, fixed decoder vs online PES, side by side.

Reads the full-rate (2 kHz) neural archives of the matched neuron-family
campaign, not trace.csv: in the fixed-decoder runs trace.csv logs the gate r
as 0.0 at every sample, while the archive holds the true r (it satisfies
a = clip(1e5 r, 0, 1) exactly). See GATE_NOTE.md.

Per platform x mission: one figure, fixed on the left, PES on the right,
rows shared in y. Gate r is on a log axis: at rest r = sigmoid(-12.5)
= 3.7e-6, and the 1e5 output gain makes that the activity floor a = 0.37.

Also writes neuron_compare_summary.csv / .md.

Run:  python compare_fixed_pes.py
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / "neuron_family_matched_45s"
PLATFORMS = ("x2", "cf2-rotor")
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
MODES = (("nengo-cmg-fixed", "CMG, fixed decoder"), ("nengo-nef-pes", "CMG + online PES"))
LABELS = ("+x", "+y", "+z", "-x", "-y", "-z")
COLORS = plt.cm.tab10(np.linspace(0, 1, 6))          # as in the paper's neuron figure
AXIS_COLORS = ("#d62728", "#2ca02c", "#9467bd")
R_REST = 1.0 / (1.0 + np.exp(12.5))                  # alpha*(v_rest_eq - v_th) = 50*(0.75-1)
R_FLOOR = 1e-7
OPEN = 0.5
STEP = 2                                             # plot at 1 ms; tau_r = 5 ms


def load(run: Path) -> dict:
    z = np.load(run / "neural_trace_full_rate.npz")
    return {k: z[k] for k in ("t", "voltage", "gate", "activity", "residual_torque", "weights")}


def qerr_mean(run: Path) -> float:
    return json.loads((run / "summary.json").read_text(encoding="utf-8"))["qerr_mean_rad"]


def stats(d: dict) -> dict:
    r, a, W = d["gate"], d["activity"], d["weights"]
    return {
        "r_median": float(np.median(r)),
        "gate_open_unit_time": float(np.mean(r > OPEN)),
        "gate_open_any_time": float(np.mean((r > OPEN).any(axis=1))),
        "activity_mean": float(a.mean()),
        "activity_at_1": float(np.mean(a >= 1.0 - 1e-12)),
        "residual_rms_Nm": float(np.sqrt(np.mean(np.sum(d["residual_torque"] ** 2, axis=1)))),
        "decoder_drift_fro": float(np.linalg.norm(W[-1] - W[0])),
    }


def figure(platform: str, mission: str, data: dict, meta: dict) -> Path:
    fig, axes = plt.subplots(5, 2, figsize=(16, 12.5), sharex=True, sharey="row")
    for col, (ctrl, label) in enumerate(MODES):
        d = data[ctrl]
        s = slice(None, None, STEP)
        t = d["t"][s]
        ax = axes[:, col]
        for i, u in enumerate(LABELS):
            ax[0].plot(t, d["voltage"][s, i], color=COLORS[i], lw=0.9, label=u)
            ax[1].plot(t, np.maximum(d["gate"][s, i], R_FLOOR), color=COLORS[i], lw=0.9, label=u)
            ax[2].plot(t, d["activity"][s, i], color=COLORS[i], lw=0.9, label=u)
        ax[1].set_yscale("log")
        ax[1].set_ylim(R_FLOOR / 2, 2.0)
        ax[1].axhline(R_REST, color="0.35", ls=":", lw=1.0,
                      label=r"rest: $\sigma(-12.5)=3.7\times10^{-6}$")
        ax[1].axhline(OPEN, color="0.35", ls="--", lw=0.8, label=f"open: r > {OPEN}")
        for k, (name, c) in enumerate(zip(("roll/x", "pitch/y", "yaw/z"), AXIS_COLORS)):
            ax[3].plot(t, d["residual_torque"][s, k], color=c, lw=1.0, label=name)
        W = d["weights"][s]
        for k, name in enumerate(("x decoder", "y decoder", "z decoder")):
            ax[4].plot(t, np.linalg.norm(W[:, k, :], axis=1), lw=1.0, label=name)
        m = meta[ctrl]
        ax[0].set_title(f"{label}\nmean error {np.degrees(m['qerr']):.3g} deg "
                        f"({m['imp']:+.1f}% vs PD); gates open {100 * m['open_any']:.1f}% of time",
                        fontsize=10)
        ax[4].set_xlabel("Time [s]")
        for a in ax:
            a.grid(True, alpha=0.2)
    axes[0, 0].set_ylabel("Membrane v")
    axes[1, 0].set_ylabel("Gate r (log)")
    axes[2, 0].set_ylabel("Activity a = min(1, 1e5 r)")
    axes[3, 0].set_ylabel("Applied residual [N m]")
    axes[4, 0].set_ylabel(r"Decoder row $\|W_i\|_2$")
    axes[0, 1].legend(ncol=6, fontsize=8, loc="lower right")
    handles, labels = axes[1, 1].get_legend_handles_labels()
    axes[1, 1].legend(handles[-2:], labels[-2:], fontsize=8, loc="center right")
    axes[3, 1].legend(ncol=3, fontsize=8, loc="upper right")
    axes[4, 1].legend(ncol=3, fontsize=8, loc="upper right")
    fig.suptitle(f"{platform} — {mission}: CMG neuron states, fixed decoder vs online PES "
                 f"(quaternion PD baseline, beta 0.5, full-rate archive)", y=0.995)
    fig.tight_layout()
    path = HERE / f"{platform}_{mission}_fixed_vs_pes.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def main() -> None:
    rows = []
    for platform in PLATFORMS:
        for mission in MISSIONS:
            pd_mean = qerr_mean(ROOT / platform / mission / "classical")
            data, meta = {}, {}
            for ctrl, _ in MODES:
                run = ROOT / platform / mission / ctrl
                d = load(run)
                st = stats(d)
                q = qerr_mean(run)
                imp = 100.0 * (pd_mean - q) / pd_mean
                data[ctrl] = d
                meta[ctrl] = {"qerr": q, "imp": imp, "open_any": st["gate_open_any_time"]}
                rows.append({"platform": platform, "mission": mission,
                             "decoder": "fixed" if "fixed" in ctrl else "pes",
                             "qerr_mean_rad": q, "improvement_vs_pd_pct": imp, **st})
            print(f"wrote {figure(platform, mission, data, meta)}")
            del data

    with (HERE / "neuron_compare_summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    cols = ("improvement_vs_pd_pct", "gate_open_any_time", "gate_open_unit_time",
            "activity_mean", "residual_rms_Nm", "decoder_drift_fro")
    head = ("| platform | mission | decoder | improvement vs PD | any gate open | "
            "unit-time open | mean activity | residual RMS [N m] | decoder drift |")
    lines = [head, "|" + "---|" * 9]
    for r in rows:
        lines.append(f"| {r['platform']} | {r['mission']} | {r['decoder']} | "
                     f"{r['improvement_vs_pd_pct']:+.2f}% | {100 * r['gate_open_any_time']:.1f}% | "
                     f"{100 * r['gate_open_unit_time']:.1f}% | {r['activity_mean']:.3f} | "
                     f"{r['residual_rms_Nm']:.3g} | {r['decoder_drift_fro']:.3f} |")
    (HERE / "neuron_compare_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
