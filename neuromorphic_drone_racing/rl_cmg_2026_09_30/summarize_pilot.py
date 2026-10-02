"""Rebuild descriptive pilot table and figures; no statistical inference."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE / "results"
OUT = ROOT / "final_pilot_analysis"
MODES = ("mlp", "graded", "crossing", "reset_gate", "reset_spike")
COLORS = {"teacher": "#111827", "mlp": "#64748b", "graded": "#00867a",
          "crossing": "#d97706", "reset_gate": "#2563eb", "reset_spike": "#7c3aed"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows, traces = [], {}
    for mode in MODES:
        folder = ROOT / f"final_x2_{mode}_seed1"
        summary = json.loads((folder / "summary.json").read_text())
        d = dict(np.load(folder / "eval.npz"))
        traces[mode] = d
        rates = np.asarray(summary["eval_spikes_per_unit_hz"])
        rows.append(dict(mode=mode, bc_samples=summary["bc_samples"],
                         ppo_rollouts=summary["ppo_rollouts"],
                         ppo_simulator_steps=sum(x["simulator_steps"] for x in summary["training"]),
                         eval_duration_s=round(len(d["t"]) * summary["policy_dt"], 3),
                         gates=summary["eval_gates"], collisions=summary["eval_collisions"],
                         termination=summary["eval_termination_reason"],
                         return_sum=round(summary["eval_return"], 4),
                         mean_position_error_m=round(summary["eval_position_error_mean_m"], 4),
                         mean_event_rate_hz=round(float(rates.mean()), 3),
                         active_event_units=int(np.count_nonzero(rates > 1)),
                         total_units=len(rates)))
    teacher = dict(np.load(ROOT / "teacher_12s.npz"))
    oracle = dict(np.load(ROOT / "oracle_12s.npz"))
    with (OUT / "pilot_comparison.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    with plt.rc_context({"font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "figure.dpi": 140}):
        fig, ax = plt.subplots(2, 1, figsize=(8.4, 6.0), sharex=True, constrained_layout=True)
        for name, d in [("teacher", teacher), ("oracle", oracle), *traces.items()]:
            label = "Geometric teacher" if name == "teacher" else (
                    "Oracle through RL interface" if name == "oracle" else name)
            color = COLORS.get(name, "#334155")
            style = "--" if name == "oracle" else "-"
            ax[0].plot(d["t"] - 7.0, d["pos_error"], label=label,
                       color=color, linestyle=style, lw=1.6 if name != "teacher" else 2.2)
            ax[1].step(d["t"] - 7.0, d["gates"], where="post", label=label,
                       color=color, linestyle=style, lw=1.6 if name != "teacher" else 2.2)
        ax[0].set_ylabel("Position error to reference (m)")
        ax[1].set_ylabel("Gates passed in order")
        ax[1].set_xlabel("Time since race start (s)")
        ax[0].set_ylim(bottom=0)
        ax[1].set_ylim(-0.1, 4.5)
        ax[0].legend(loc="upper left", ncol=2, fontsize=8)
        for a in ax:
            a.grid(alpha=0.2)
        fig.savefig(OUT / "pilot_tracking.png", bbox_inches="tight")
        fig.savefig(OUT / "pilot_tracking.pdf", bbox_inches="tight")
        plt.close(fig)

        fig, axs = plt.subplots(3, 1, figsize=(8.4, 6.5), sharex=True, constrained_layout=True)
        for mode in ("graded", "crossing", "reset_gate", "reset_spike"):
            d = traces[mode]
            t = d["t"] - 7.0
            axs[0].plot(t, d["activity"][:, :4].mean(axis=1), color=COLORS[mode], label=mode)
            axs[1].plot(t, d["gate"][:, :4].mean(axis=1), color=COLORS[mode], label=mode)
            event_delta = np.diff(d["events"][:, :4], axis=0, prepend=np.zeros((1, 4)))
            axs[2].plot(t, event_delta.sum(axis=1) / 4.0, color=COLORS[mode],
                        lw=0.8, label=mode)
        axs[0].set_ylabel("Activity (first four units)")
        axs[1].set_ylabel("Gate state (first four)")
        axs[2].set_ylabel("Events / 20 ms / unit")
        axs[2].set_xlabel("Time since race start (s)")
        axs[0].legend(loc="best", ncol=3, fontsize=8)
        for a in axs:
            a.grid(alpha=0.2)
        fig.savefig(OUT / "cmg_activity_events.png", bbox_inches="tight")
        fig.savefig(OUT / "cmg_activity_events.pdf", bbox_inches="tight")
        plt.close(fig)
    (OUT / "summary.json").write_text(json.dumps(dict(rows=rows,
        teacher=dict(duration_s=len(teacher["t"]) * 0.02, gates=int(teacher["gates"][-1]),
                     collisions=int(teacher["collisions"][-1])),
        oracle=dict(duration_s=len(oracle["t"]) * 0.02, gates=int(oracle["gates"][-1]),
                    collisions=int(oracle["collisions"][-1])),
        warning="Single seed, short BC+PPO budget, variable survival times; no family ranking justified"), indent=2))
    print(OUT)
    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
