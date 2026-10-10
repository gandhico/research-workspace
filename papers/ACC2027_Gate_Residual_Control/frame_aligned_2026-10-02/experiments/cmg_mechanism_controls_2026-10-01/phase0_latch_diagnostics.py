"""Phase 0: per-unit latch/saturation diagnostics from the archived strict_exact CMG runs.

No simulation.  Reads the ten full-rate CMG neural archives of
neuron_basis_decisive_2026-09-24/results/strict_exact and writes

- analysis/phase0/latch_diagnostics.csv   one row per platform/mission/unit
- analysis/phase0/mission_summary.csv     one row per platform/mission
- analysis/phase0/cmg_latch_schedule.json latch times consumed by the latch-replay basis
- analysis/phase0/activity_timecourses.png
- analysis/phase0/log_r_histograms.png
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
STRICT = REPO / "experiments" / "neuron_basis_decisive_2026-09-24" / "results" / "strict_exact"
OUT = HERE / "analysis" / "phase0"
PLATFORMS = ("x2", "cf2-rotor")
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
UNITS = ("+x", "+y", "+z", "-x", "-y", "-z")  # paired encoder order [max(u,0), max(-u,0)]
ETA = 8e-4
LATCH_R = 0.5          # gate on the upper branch
SAT_A = 1.0 - 1e-9     # readout clipped at 1
GRADED_EPS = 1e-6      # 0 < a < 1 strictly


def load(platform: str, mission: str) -> dict[str, np.ndarray]:
    z = np.load(STRICT / platform / mission / "cmg" / "neural_trace_full_rate.npz")
    return {k: z[k] for k in ("t", "gate", "activity", "voltage", "current")}


def first_crossing(t: np.ndarray, x: np.ndarray, level: float) -> float | None:
    hit = np.flatnonzero(x > level)
    return float(t[hit[0]]) if hit.size else None


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    unit_rows, mission_rows, schedule, traces = [], [], {}, {}
    for platform in PLATFORMS:
        schedule[platform] = {}
        for mission in MISSIONS:
            d = load(platform, mission)
            t, r, a, v = d["t"], d["gate"], d["activity"], d["voltage"]
            dt = float(np.median(np.diff(t)))
            latch_times = []
            for j, name in enumerate(UNITS):
                tl = first_crossing(t, r[:, j], LATCH_R)
                released = bool(tl is not None and np.any(r[t >= tl, j] < LATCH_R))
                after = t >= (tl if tl is not None else np.inf)
                unit_rows.append({
                    "platform": platform, "mission": mission, "unit": j, "unit_name": name,
                    "latch_time_s": tl, "released_after_latch": released,
                    "frac_a_saturated": float(np.mean(a[:, j] >= SAT_A)),
                    "frac_a_graded": float(np.mean((a[:, j] > GRADED_EPS) & (a[:, j] < SAT_A))),
                    "a_mean": float(a[:, j].mean()),
                    "a_min_after_0p5s": float(a[t > 0.5, j].min()),
                    "r_min_after_0p5s": float(r[t > 0.5, j].min()),
                    "r_median": float(np.median(r[:, j])),
                    "v_min_after_latch": float(v[after, j].min()) if after.any() else None,
                    "v_max": float(v[:, j].max()),
                })
                latch_times.append(tl)
            schedule[platform][mission] = latch_times
            norm2 = np.sum(a ** 2, axis=1)
            corner = ETA * norm2 / dt
            mission_rows.append({
                "platform": platform, "mission": mission,
                "units_latched": int(sum(x is not None for x in latch_times)),
                "any_release": any(row["released_after_latch"] for row in unit_rows[-6:]),
                "a_norm2_mean": float(norm2.mean()),
                "a_norm2_final": float(norm2[-1]),
                "pes_corner_rad_s_mean": float(corner.mean()),
                "pes_corner_rad_s_final": float(corner[-1]),
                "frac_samples_all_units_saturated": float(np.mean(np.all(a >= SAT_A, axis=1))),
            })
            traces[(platform, mission)] = (t, a, r)

    for name, rows in (("latch_diagnostics.csv", unit_rows), ("mission_summary.csv", mission_rows)):
        with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    (OUT / "cmg_latch_schedule.json").write_text(json.dumps({
        "source": str(STRICT.relative_to(REPO)).replace("\\", "/"),
        "definition": f"first full-rate sample with gate r > {LATCH_R}; null = never latched",
        "unit_order": list(UNITS),
        "latch_time_s": schedule,
    }, indent=2) + "\n", encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(len(MISSIONS), 2, figsize=(10, 11), sharex=True, sharey=True)
    for c, platform in enumerate(PLATFORMS):
        for m, mission in enumerate(MISSIONS):
            t, a, _ = traces[(platform, mission)]
            ax = axes[m, c]
            for j, name in enumerate(UNITS):
                ax.plot(t[::20], a[::20, j], lw=1.0, label=name)
            ax.set_title(f"{platform} / {mission}", fontsize=9)
            ax.set_ylim(0.3, 1.05)
            ax.grid(alpha=0.3)
    axes[0, 0].legend(ncol=6, fontsize=7, loc="lower right")
    for ax in axes[-1]:
        ax.set_xlabel("t [s]")
    for ax in axes[:, 0]:
        ax.set_ylabel("activity a")
    fig.suptitle("Archived strict_exact CMG activity per unit (rest ~0.373, latched = 1)")
    fig.tight_layout()
    fig.savefig(OUT / "activity_timecourses.png", dpi=140)
    plt.close(fig)

    fig, axes = plt.subplots(2, len(MISSIONS), figsize=(14, 5), sharey=True)
    bins = np.linspace(-8, 0, 81)
    for c, platform in enumerate(PLATFORMS):
        for m, mission in enumerate(MISSIONS):
            _, _, r = traces[(platform, mission)]
            ax = axes[c, m]
            for j, name in enumerate(UNITS):
                ax.hist(np.log10(np.clip(r[:, j], 1e-8, 1.0)), bins=bins, histtype="step", label=name)
            ax.axvline(-5, color="k", ls="--", lw=0.8)
            ax.set_yscale("log")
            ax.set_title(f"{platform} / {mission}", fontsize=8)
    axes[0, 0].legend(fontsize=6)
    for ax in axes[-1]:
        ax.set_xlabel("log10 r  (dashed: a saturates for r > 1/G = 1e-5)")
    fig.tight_layout()
    fig.savefig(OUT / "log_r_histograms.png", dpi=140)
    plt.close(fig)

    for row in mission_rows:
        print(row)


if __name__ == "__main__":
    main()
