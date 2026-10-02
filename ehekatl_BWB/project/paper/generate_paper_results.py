#!/usr/bin/env python3
"""Generate the paper-facing tables and figures from frozen registered evidence."""
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper" / "generated"
DIRECT = {
    "DeePC": ROOT / "logs/direct_deepc_20260810_150657.csv",
    "LQR": ROOT / "logs/direct_lqr_20260810_151244.csv",
}


def load_csv(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def values(rows, name):
    return np.asarray([float(row[name]) for row in rows], dtype=float)


def direct_metrics(name, path):
    rows = load_csv(path)
    t = values(rows, "t_s")
    p_error = values(rows, "p_deg_s") - values(rows, "p_bias_deg_s")
    command = values(rows, "sent_roll_perturbation")
    final = t >= 25.0
    runtime = values(rows, "runtime_ms") if "runtime_ms" in rows[0] else None
    dt = np.diff(t)
    result = {
        "controller": name,
        "source": str(path.relative_to(ROOT)),
        "rows": len(rows),
        "effective_hz": float(1.0 / np.mean(dt)),
        "maximum_gap_ms": float(1000.0 * np.max(dt)),
        "integral_abs_delta_p_deg": float(np.trapezoid(np.abs(p_error), t)),
        "rms_delta_p_deg_s": float(np.sqrt(np.mean(p_error**2))),
        "peak_abs_delta_p_deg_s": float(np.max(np.abs(p_error))),
        "final_5s_max_abs_delta_p_deg_s": float(np.max(np.abs(p_error[final]))),
        "peak_abs_command": float(np.max(np.abs(command))),
        "maximum_command_slew": float(np.max(np.abs(np.diff(np.r_[0.0, command])))),
        "control_energy": float(np.trapezoid(command**2, t)),
        "fallback_latched": bool(any(int(row["fallback_latched"]) for row in rows)),
        "axes_restored": bool(
            rows[-1]["restored_roll_override"] == "0"
            and rows[-1]["restored_pitch_override"] == "0"
            and abs(float(rows[-1]["restored_roll_yoke_error"])) <= 1e-12
            and abs(float(rows[-1]["restored_pitch_yoke_error"])) <= 1e-12
        ),
    }
    if runtime is not None:
        result["runtime_ms_median"] = float(np.median(runtime))
        result["runtime_ms_p95"] = float(np.percentile(runtime, 95))
        result["runtime_ms_max"] = float(np.max(runtime))
    return result, (t, p_error, command, values(rows, "disturbance_command"))


def write_metrics(metrics):
    (OUT / "direct_demonstration_metrics.json").write_text(
        json.dumps({"claim_boundary": "Unmatched direct demonstrations; descriptive only.", "runs": metrics}, indent=2) + "\n"
    )
    fields = sorted({key for row in metrics for key in row})
    with (OUT / "direct_demonstration_metrics.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(metrics)


def plot_direct(series):
    colors = {"LQR": "#0072B2", "DeePC": "#D55E00"}
    fig, axes = plt.subplots(3, 1, figsize=(7.2, 7.2), sharex=True)
    for name in ("LQR", "DeePC"):
        t, p_error, command, disturbance = series[name]
        axes[0].plot(t, p_error, lw=1.1, color=colors[name], label=name)
        axes[1].plot(t, command * 1e5, lw=1.1, color=colors[name], label=name)
        axes[2].plot(t, disturbance * 1e5, lw=1.1, color=colors[name], label=name)
    axes[0].set_ylabel(r"$\Delta P$ [deg/s]")
    axes[1].set_ylabel(r"Roll command [$10^{-5}$]")
    axes[2].set_ylabel(r"Pulse [$10^{-5}$]")
    axes[2].set_xlabel("Time [s]")
    for ax in axes:
        ax.grid(True, alpha=0.3)
    axes[0].legend(ncol=2, frameon=False)
    fig.suptitle("Direct R3 controller demonstrations (separate reloads)")
    fig.tight_layout()
    fig.savefig(OUT / "direct_controller_demonstrations.png", dpi=240)
    fig.savefig(OUT / "direct_controller_demonstrations.pdf")
    plt.close(fig)


def plot_offline_and_power():
    replay = json.loads((ROOT / "configs/rich_R3_deepc_uncertainty_replay.json").read_text())
    ratios = np.asarray([case["integral_ratio"] for case in replay["cases"]])
    separate = json.loads((ROOT / "configs/rich_R3_deepc_separate_power.json").read_text())
    paired = json.loads((ROOT / "configs/rich_R3_deepc_paired_iae_power.json").read_text())
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.6))
    axes[0].hist(ratios, bins=18, color="#009E73", edgecolor="white")
    axes[0].axvline(0.9, color="black", ls="--", lw=1, label="Frozen gate")
    axes[0].set_xlabel("Offline DeePC/LQR integral ratio")
    axes[0].set_ylabel("Uncertainty cases")
    axes[0].legend(frameon=False)
    xs = [x["pulses_each_controller"] for x in separate["curve"]]
    ys = [x["power_upper_bound_below_one"] for x in separate["curve"]]
    xp = [x["paired_pulses_each_controller"] for x in paired["curve"]]
    yp = [x["power_upper_bound_below_one"] for x in paired["curve"]]
    axes[1].plot(xs, ys, "o-", label="Separate reloads")
    axes[1].plot(xp, yp, "s-", label="Paired IAE")
    axes[1].axhline(0.8, color="black", ls="--", lw=1, label="Required power")
    axes[1].set_xlabel("Pulses per controller")
    axes[1].set_ylabel("Prospective power")
    axes[1].set_ylim(0.25, 1.0)
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "offline_robustness_and_power.png", dpi=240)
    fig.savefig(OUT / "offline_robustness_and_power.pdf")
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    metrics, series = [], {}
    for name, path in DIRECT.items():
        metric, datum = direct_metrics(name, path)
        metrics.append(metric)
        series[name] = datum
    write_metrics(metrics)
    plot_direct(series)
    plot_offline_and_power()
    print(json.dumps(metrics, indent=2))
    print(f"Generated paper artifacts in {OUT}")


if __name__ == "__main__":
    main()
