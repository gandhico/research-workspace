"""Full comparison figures and tables: every arm x mission x platform.

Writes analysis/report/:
  activity_<platform>_<mission>.png   per-unit a_j(t) for all ten residual arms
  error_<platform>.png                true quaternion error vs time, five missions
  improvement_heatmap.png             improvement % for every arm/mission/platform
  summary_table.csv / summary_table.md
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
STRICT = HERE.parents[0] / "neuron_basis_decisive_2026-09-24" / "results" / "strict_exact"
CONFIRM = HERE / "results" / "confirm"
OUT = HERE / "analysis" / "report"
PLATFORMS = ("x2", "cf2-rotor")
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
UNITS = ("+x", "+y", "+z", "-x", "-y", "-z")
# (key, label, root): archived references first, then new arms
ARMS = (
    ("cmg", "CMG (paper, G=1e5, chi=1)", STRICT),
    ("lpf-logistic", "LPF + static logistic", CONFIRM),
    ("cmg_chi0", "CMG chi=0", CONFIRM),
    ("latch-replay", "Latch replay", CONFIRM),
    ("cmg_G1e3", "CMG G=1e3", CONFIRM),
    ("cmg_G1", "CMG G=1", CONFIRM),
    ("constant-rest", "Constant-rest (a=0.3728)", CONFIRM),
    ("constant-one", "Constant-one (archived)", STRICT),
    ("constant-one-nengo-order", "Constant-one (Nengo PES order)", CONFIRM),
    ("paired-current", "Static paired (archived)", STRICT),
)
ERROR_ARMS = ("classical", "cmg", "lpf-logistic", "latch-replay", "constant-rest", "constant-one")
ERROR_LABEL = {"classical": "Classical PD+ff", **{k: l for k, l, _ in ARMS}}
COLORS = {"classical": "#444444", "cmg": "#1f77b4", "lpf-logistic": "#d62728", "latch-replay": "#9467bd",
          "constant-rest": "#8c564b", "constant-one": "#2ca02c"}


def path(platform, mission, arm):
    root = STRICT if arm == "classical" else dict((k, r) for k, _, r in ARMS)[arm]
    return root / platform / mission / arm


def qerr_mean(platform, mission, arm):
    import json
    return json.loads((path(platform, mission, arm) / "summary.json").read_text())["metrics"]["qerr_true_mean_rad"]


def read_trace(p: Path):
    with (p / "trace.csv").open(encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        it, iq = header.index("t"), header.index("qerr_true_rad")
        rows = [(float(r[it]), float(r[iq])) for r in reader]
    a = np.array(rows)
    return a[:, 0], a[:, 1]


def activity_figures():
    for platform in PLATFORMS:
        for mission in MISSIONS:
            fig, axes = plt.subplots(2, 5, figsize=(20, 6.4), sharex=True, sharey=True)
            base = qerr_mean(platform, mission, "classical")
            for ax, (arm, label, _) in zip(axes.ravel(), ARMS):
                z = np.load(path(platform, mission, arm) / "neural_trace_full_rate.npz")
                lines = ax.plot(z["t"][::20], z["activity"][::20], lw=0.8)
                imp = 100 * (1 - qerr_mean(platform, mission, arm) / base)
                ax.set_title(f"{label}\nimprovement {imp:+.1f}%", fontsize=9)
                ax.set_ylim(-0.05, 1.05)
                ax.grid(alpha=0.25)
            for ax in axes[-1]:
                ax.set_xlabel("t [s]")
            for ax in axes[:, 0]:
                ax.set_ylabel("activity a")
            fig.legend(lines, UNITS, loc="upper right", ncol=6, fontsize=9)
            fig.suptitle(f"{platform} / {mission} — per-unit activity of every residual basis", x=0.01, ha="left")
            fig.tight_layout(rect=(0, 0, 1, 0.95))
            fig.savefig(OUT / f"activity_{platform}_{mission}.png", dpi=100)
            plt.close(fig)


def error_figures():
    for platform in PLATFORMS:
        fig, axes = plt.subplots(len(MISSIONS), 1, figsize=(12, 13), sharex=True)
        for ax, mission in zip(axes, MISSIONS):
            for arm in ERROR_ARMS:
                t, q = read_trace(path(platform, mission, arm))
                ax.semilogy(t, np.degrees(np.maximum(q, 1e-6)), lw=0.9, color=COLORS[arm],
                            label=f"{ERROR_LABEL[arm]} (mean {np.degrees(qerr_mean(platform, mission, arm)):.3f}°)")
            ax.set_title(f"{platform} / {mission}", fontsize=10)
            ax.set_ylabel("quaternion error [deg]")
            ax.grid(alpha=0.3, which="both")
            ax.legend(fontsize=7, ncol=3, loc="upper right")
        axes[-1].set_xlabel("t [s]")
        fig.tight_layout()
        fig.savefig(OUT / f"error_{platform}.png", dpi=100)
        plt.close(fig)


def tables_and_heatmap():
    rows = []
    for arm, label, _ in ARMS:
        row = {"arm": label}
        for platform in PLATFORMS:
            ratios = []
            for mission in MISSIONS:
                ratio = qerr_mean(platform, mission, arm) / qerr_mean(platform, mission, "classical")
                ratios.append(ratio)
                row[f"{platform}:{mission}"] = 100 * (1 - ratio)
                z = np.load(path(platform, mission, arm) / "neural_trace_full_rate.npz")
                a = z["activity"]
                row[f"{platform}:{mission}:frac_a_eq_1"] = float(np.mean(a >= 1 - 1e-9))
                row[f"{platform}:{mission}:a_temporal_std"] = float(np.mean(a.std(axis=0)))
            row[f"{platform}:geomean"] = 100 * (1 - float(np.exp(np.mean(np.log(ratios)))))
        rows.append(row)
    cmg = rows[0]
    for row in rows[1:]:
        f = [row[f"{p}:geomean"] / cmg[f"{p}:geomean"] for p in PLATFORMS]
        row["verdict"] = ("reproduces CMG" if all(x >= 0.9 for x in f) else
                          "fails" if all(x <= 0.5 for x in f) else "partial")
    cmg["verdict"] = "reference"
    with (OUT / "summary_table.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]) + ["verdict"] if "verdict" not in rows[0] else list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    md = ["| Arm | X2 geomean | CF2 geomean | Verdict | " + " | ".join(f"X2 {m}" for m in MISSIONS) + " | "
          + " | ".join(f"CF2 {m}" for m in MISSIONS) + " |", "|---" * 14 + "|"]
    for r in rows:
        md.append(f"| {r['arm']} | {r['x2:geomean']:.2f} | {r['cf2-rotor:geomean']:.2f} | {r['verdict']} | "
                  + " | ".join(f"{r[f'x2:{m}']:+.1f}" for m in MISSIONS) + " | "
                  + " | ".join(f"{r[f'cf2-rotor:{m}']:+.1f}" for m in MISSIONS) + " |")
    (OUT / "summary_table.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    cols = [f"{p}:{m}" for p in PLATFORMS for m in MISSIONS] + [f"{p}:geomean" for p in PLATFORMS]
    data = np.array([[r[c] for c in cols] for r in rows])
    fig, ax = plt.subplots(figsize=(15, 5.6))
    lim = np.max(np.abs(data))
    im = ax.imshow(data, cmap="RdBu", vmin=-lim, vmax=lim, aspect="auto")
    ax.set_xticks(range(len(cols)), [c.replace("cf2-rotor", "CF2").replace("x2", "X2").replace(":", "\n") for c in cols], fontsize=8)
    ax.set_yticks(range(len(rows)), [r["arm"] for r in rows], fontsize=9)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            ax.text(j, i, f"{data[i, j]:+.1f}", ha="center", va="center", fontsize=8,
                    color="white" if abs(data[i, j]) > 0.55 * lim else "black")
    ax.axvline(4.5, color="k", lw=1.5)
    ax.axvline(9.5, color="k", lw=1.5)
    fig.colorbar(im, ax=ax, label="error reduction vs classical [%]")
    ax.set_title("Tracking-error reduction vs classical PD+ff, every basis (45 s, noise-free)")
    fig.tight_layout()
    fig.savefig(OUT / "improvement_heatmap.png", dpi=120)
    plt.close(fig)
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = tables_and_heatmap()
    error_figures()
    activity_figures()
    print((OUT / "summary_table.md").read_text())


if __name__ == "__main__":
    main()
