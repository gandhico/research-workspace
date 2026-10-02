"""Generate an offline diagnostic plot; no hardware access."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

RESULTS = Path(r"C:\Research\hover3dof\results\hardware")
OUT = Path(__file__).resolve().parents[1] / "plots" / "yaw_duration_and_set_k.png"
DOCUMENTED_EXTERNAL_TOUCH = "online-pes-adaptive_armed_20260828_112330"


def smooth_yaw(t: np.ndarray, duration: float) -> np.ndarray:
    s = np.clip(t / duration, 0.0, 1.0)
    return np.rad2deg(2.0 * np.pi * (3.0 * s**2 - 2.0 * s**3))


def matched_yaw_runs() -> list[tuple[str, dict]]:
    selected: list[tuple[str, dict]] = []
    for path in RESULTS.glob("*/summary.json"):
        item = json.loads(path.read_text(encoding="utf-8"))
        if item.get("mission") != "yaw360" or item.get("duration") != 30.0:
            continue
        is_classical = item.get("controller") == "classical"
        is_k = (
            item.get("controller") == "online-pes-adaptive"
            and item.get("beta") == 0.4
            and item.get("max_residual_volts") == 3.0
            and item.get("learning_rate") == 0.0003
            and item.get("k_error") == 2.0
            and item.get("k_rate") == 0.0
        )
        if is_classical or is_k:
            label = "Classical" if is_classical else "Set K"
            selected.append((f"{label}\n{path.parent.name[-6:]}", item))
    return sorted(selected, key=lambda pair: pair[1]["trace"])


def main() -> None:
    t = np.linspace(0.0, 30.0, 1000)
    data = matched_yaw_runs()

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4))
    axes[0].plot(t, smooth_yaw(t, 25.0), label="25 s: peak 21.6 deg/s", linewidth=2)
    axes[0].plot(t, smooth_yaw(t, 30.0), label="30 s: peak 18.0 deg/s", linewidth=2)
    axes[0].set(xlabel="time [s]", ylabel="yaw reference [deg]", title="Duration changes yaw360 difficulty")
    axes[0].grid(alpha=0.25)
    axes[0].legend()

    labels = [item[0] for item in data]
    means = [item[1]["angle_err_mean_deg"] for item in data]
    peaks = [item[1]["angle_err_max_deg"] for item in data]
    x = np.arange(len(labels))
    clean = np.array([item[1]["trace"].split("\\")[-2] != DOCUMENTED_EXTERNAL_TOUCH for item in data])
    axes[1].scatter(x[clean], np.asarray(means)[clean], s=70, label="mean error (clean)", zorder=3)
    axes[1].scatter(x[clean], np.asarray(peaks)[clean], s=70, marker="x", label="peak error (clean)", zorder=3)
    if np.any(~clean):
        axes[1].scatter(x[~clean], np.asarray(means)[~clean], s=100, facecolors="none", edgecolors="crimson", linewidths=2, label="external-touch run", zorder=4)
        axes[1].scatter(x[~clean], np.asarray(peaks)[~clean], s=100, marker="x", color="crimson", linewidths=2, zorder=4)
    axes[1].set_xticks(x, labels, rotation=0, ha="center")
    axes[1].set(ylabel="combined Euler error [deg]", title="Set K must use the 30 s baseline")
    axes[1].grid(axis="y", alpha=0.25)
    axes[1].legend()

    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=180, bbox_inches="tight")
    print(OUT)


if __name__ == "__main__":
    main()
