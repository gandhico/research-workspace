"""Compile matched metrics and generate tracking/neuron figures."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
RUN_ROOT = HERE / "results" / "matched_45s"
OUT = HERE / "results" / "compiled"
PLOTS = HERE / "results" / "plots"
MISSIONS = ("hover", "roll", "full3", "hard45", "hardstep", "yaw360")
PLATFORMS = ("cf2-rotor", "x2")


def _summary(platform, mission, controller):
    label = f"{platform}_{mission}_{controller}".replace("-", "_")
    path = RUN_ROOT / label / "summary.json"
    return json.loads(path.read_text(encoding="utf-8")), path.parent


def _improvement(baseline, neural):
    if abs(baseline) < 1e-12:
        return None
    return 100.0 * (baseline - neural) / baseline


def _tracking_plot(platform, mission, bdir, ndir, row):
    b = pd.read_csv(bdir / "trace.csv", usecols=["t", "qerr"])
    n = pd.read_csv(ndir / "trace.csv", usecols=["t", "qerr"])
    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    ax.plot(b.t, np.degrees(b.qerr), lw=1.4, color="#1f4e79", label="Quaternion PD")
    ax.plot(n.t, np.degrees(n.qerr), lw=1.25, color="#c23b22", label="Nengo CMG + online PES")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Quaternion-angle error [deg]")
    improvement = row["mean_improvement_percent"]
    suffix = "zero-error hover" if improvement is None else f"mean improvement = {improvement:.2f}%"
    ax.set_title(f"{platform} — {mission}: matched 45 s tracking ({suffix})")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    path = PLOTS / f"{platform}_{mission}_tracking.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _neuron_plot(platform, mission, ndir):
    columns = ["t", "residual_x", "residual_y", "residual_z"]
    for prefix in ("voltage", "gate", "activity"):
        columns.extend([f"{prefix}_{i}" for i in range(6)])
    columns.extend([f"decoder_w_{i}" for i in range(18)])
    d = pd.read_csv(ndir / "trace.csv", usecols=columns)
    t = d.t.to_numpy()
    labels = ("+x", "+y", "+z", "-x", "-y", "-z")
    colors = plt.cm.tab10(np.linspace(0, 1, 6))
    fig, axes = plt.subplots(5, 1, figsize=(12, 12), sharex=True)
    for i, label in enumerate(labels):
        axes[0].plot(t, d[f"voltage_{i}"], color=colors[i], lw=0.9, label=label)
        axes[1].plot(t, d[f"gate_{i}"], color=colors[i], lw=0.9, label=label)
        axes[2].plot(t, d[f"activity_{i}"], color=colors[i], lw=0.9, label=label)
    axes[0].set_ylabel("Membrane v")
    axes[1].set_ylabel("Gate r")
    axes[2].set_ylabel("Activity a")
    axes[0].legend(ncol=6, fontsize=8, loc="upper right")
    for axis, name, color in zip("xyz", ("roll/x", "pitch/y", "yaw/z"), ("#d62728", "#2ca02c", "#9467bd")):
        axes[3].plot(t, d[f"residual_{axis}"], lw=1.0, label=name, color=color)
    axes[3].set_ylabel("Applied residual [N m]")
    axes[3].legend(ncol=3, fontsize=8, loc="upper right")
    W = d[[f"decoder_w_{i}" for i in range(18)]].to_numpy().reshape(-1, 3, 6)
    for i, name in enumerate(("x decoder", "y decoder", "z decoder")):
        axes[4].plot(t, np.linalg.norm(W[:, i, :], axis=1), lw=1.0, label=name)
    axes[4].set_ylabel(r"Decoder row $\|W_i\|_2$")
    axes[4].set_xlabel("Time [s]")
    axes[4].legend(ncol=3, fontsize=8, loc="upper right")
    for ax in axes:
        ax.grid(True, alpha=0.2)
    fig.suptitle(f"{platform} — {mission}: Nengo CMG states and online PES decoder", y=0.995)
    fig.tight_layout()
    path = PLOTS / f"{platform}_{mission}_neurons.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    PLOTS.mkdir(parents=True, exist_ok=True)
    rows = []
    for platform in PLATFORMS:
        for mission in MISSIONS:
            b, bdir = _summary(platform, mission, "classical")
            n, ndir = _summary(platform, mission, "nengo-nef-pes")
            row = {
                "platform": platform,
                "mission": mission,
                "duration_s": b["duration"],
                "dt_s": b["dt"],
                "baseline_mean_rad": b["qerr_mean_rad"],
                "nengo_mean_rad": n["qerr_mean_rad"],
                "mean_improvement_percent": _improvement(b["qerr_mean_rad"], n["qerr_mean_rad"]),
                "baseline_rmse_rad": b["qerr_rmse_rad"],
                "nengo_rmse_rad": n["qerr_rmse_rad"],
                "rmse_improvement_percent": _improvement(b["qerr_rmse_rad"], n["qerr_rmse_rad"]),
                "baseline_max_rad": b["qerr_max_rad"],
                "nengo_max_rad": n["qerr_max_rad"],
                "max_improvement_percent": _improvement(b["qerr_max_rad"], n["qerr_max_rad"]),
                "baseline_saturation_fraction": b["saturation_fraction"],
                "nengo_saturation_fraction": n["saturation_fraction"],
                "nengo_residual_mean_Nm": n["residual_mean_Nm"],
                "nengo_version": n["nengo_version"],
                "baseline_run": str(bdir),
                "nengo_run": str(ndir),
            }
            rows.append(row)
            _tracking_plot(platform, mission, bdir, ndir, row)
            _neuron_plot(platform, mission, ndir)

    csv_path = OUT / "matched_results.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (OUT / "matched_results.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")

    # Compact paper-facing improvement chart; zero-error Hover is intentionally omitted.
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
    missions = MISSIONS[1:]
    for ax, platform in zip(axes, PLATFORMS):
        values = [
            next(r["mean_improvement_percent"] for r in rows if r["platform"] == platform and r["mission"] == m)
            for m in missions
        ]
        bars = ax.bar(missions, values, color="#2a6f97")
        ax.axhline(0, color="black", lw=0.8)
        ax.set_title(platform)
        ax.set_ylabel("Mean error reduction [%]")
        ax.tick_params(axis="x", rotation=30)
        ax.grid(axis="y", alpha=0.25)
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, value + 1, f"{value:.1f}%", ha="center", fontsize=8)
    fig.suptitle("Nengo CMG + online PES versus matched quaternion-PD baseline")
    fig.tight_layout()
    fig.savefig(PLOTS / "all_missions_mean_improvement.png", dpi=200)
    plt.close(fig)
    print(csv_path)
    print(f"generated {2 * len(rows) + 1} plots in {PLOTS}")


if __name__ == "__main__":
    main()

