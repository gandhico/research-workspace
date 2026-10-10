from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
VALID = ROOT/"results/validation"
OUT = ROOT/"results/reports"
OUT.mkdir(parents=True, exist_ok=True)

RUNS = [
    ("X2", "classical", VALID/"x2_45s_dt0005/classical"),
    ("X2", "CMG fixed decoder, fixed conductance", VALID/"x2_residual_beta05/fixed-residual"),
    ("X2", "CMG fixed decoder, adaptive conductance", VALID/"x2_residual_beta05/adaptive-residual"),
    ("X2", "CMG-PES, fixed conductance", VALID/"x2_online_additive/beta_0.5_fixed_conductance"),
    ("X2", "CMG-PES, adaptive conductance", VALID/"x2_online_additive/beta_0.5"),
    ("CF2 stock XML", "classical", VALID/"cf2_45s_model/classical"),
    ("CF2 stock XML", "CMG fixed decoder, fixed conductance", VALID/"cf2_45s_model/fixed-residual"),
    ("CF2 stock XML", "CMG fixed decoder, adaptive conductance", VALID/"cf2_45s_model/adaptive-residual"),
    ("CF2 rotor design 1.5x", "classical", VALID/"cf2_rotor_45s_scale15/classical"),
    ("CF2 rotor design 1.5x", "CMG fixed decoder, fixed conductance", VALID/"cf2_rotor_45s_scale15/fixed-residual"),
    ("CF2 rotor design 1.5x", "CMG fixed decoder, adaptive conductance", VALID/"cf2_rotor_45s_scale15/adaptive-residual"),
    ("CF2 rotor design 1.5x", "CMG-PES, fixed conductance", VALID/"cf2_rotor_45s_scale15/online-pes-fixed"),
    ("CF2 rotor design 1.5x", "CMG-PES, adaptive conductance", VALID/"cf2_rotor_45s_scale15/online-pes-adaptive"),
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_trace(path: Path) -> dict[str, np.ndarray]:
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    return {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}


records = []
baselines: dict[str, float] = {}
for platform, controller, folder in RUNS:
    summary = load_json(folder/"summary.json")
    score = (summary["qerr_mean_rad"] + 0.02*summary["tau_mean_Nm"]
             + 0.20*summary["saturation_fraction"] + 0.05*summary["z_std_m"])
    if controller == "classical":
        baselines[platform] = summary["qerr_mean_rad"]
    records.append({
        "platform": platform, "controller": controller,
        "qerr_mean_rad": summary["qerr_mean_rad"],
        "qerr_max_rad": summary["qerr_max_rad"],
        "score": score,
        "saturation_fraction": summary["saturation_fraction"],
        "z_std_m": summary["z_std_m"],
        "actuator_scale": summary.get("actuator_scale", 1.0),
    })
for row in records:
    base = baselines[row["platform"]]
    row["qerr_improvement_percent"] = 100*(base-row["qerr_mean_rad"])/base

with (OUT/"validation_summary.csv").open("w", newline="", encoding="utf-8") as stream:
    writer = csv.DictWriter(stream, fieldnames=list(records[0]))
    writer.writeheader(); writer.writerows(records)

lines = [
    "# Validated Hard45 summary", "",
    "| Platform | Controller | qerr mean | Improvement | Score | Saturation |",
    "|---|---|---:|---:|---:|---:|",
]
for r in records:
    lines.append(
        f"| {r['platform']} | {r['controller']} | {r['qerr_mean_rad']:.6f} | "
        f"{r['qerr_improvement_percent']:+.2f}% | {r['score']:.6f} | "
        f"{100*r['saturation_fraction']:.2f}% |"
    )
(OUT/"validation_summary.md").write_text("\n".join(lines)+"\n", encoding="utf-8")

colors = {
    "classical": "#1f77b4",
    "CMG fixed decoder, fixed conductance": "#2ca02c",
    "CMG fixed decoder, adaptive conductance": "#ff7f0e",
    "CMG-PES, fixed conductance": "#9467bd",
    "CMG-PES, adaptive conductance": "#d62728",
}
for platform, prefix in [("X2", "x2"), ("CF2 rotor design 1.5x", "cf2_rotor")]:
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    for p, controller, folder in RUNS:
        if p != platform:
            continue
        tr = read_trace(folder/"trace.csv")
        ax.plot(tr["t"], tr["qerr"], lw=1.0, label=controller, color=colors[controller])
    ax.set(xlabel="Time [s]", ylabel="Quaternion error [rad]", title=f"{platform}: Hard45")
    ax.grid(alpha=.25); ax.legend(ncol=2, fontsize=8); fig.tight_layout()
    fig.savefig(OUT/f"{prefix}_hard45_qerr.png", dpi=220)
    fig.savefig(OUT/f"{prefix}_hard45_qerr.pdf")
    plt.close(fig)

sweep_root = VALID/"cf2_authority_sweep_5s"
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.0, 5.5), sharex=True)
for controller, label, color in [
    ("classical", "Classical", "#1f77b4"),
    ("online-pes-adaptive", "Online PES residual", "#d62728"),
]:
    xs, errors, sats = [], [], []
    for scale_dir in sorted(sweep_root.glob("scale_*"), key=lambda p: float(p.name.split("_")[1])):
        s = load_json(scale_dir/controller/"summary.json")
        xs.append(float(scale_dir.name.split("_")[1]))
        errors.append(s["qerr_mean_rad"]); sats.append(100*s["saturation_fraction"])
    ax1.plot(xs, errors, "o-", label=label, color=color)
    ax2.plot(xs, sats, "o-", label=label, color=color)
ax1.set_ylabel("Mean q-error [rad]"); ax2.set_ylabel("Rotor saturation [%]")
ax2.set_xlabel("Per-rotor maximum-thrust scale")
for ax in (ax1, ax2): ax.grid(alpha=.25); ax.legend(fontsize=8)
fig.suptitle("CF2 rotor-authority design sweep (5 s screening)"); fig.tight_layout()
fig.savefig(OUT/"cf2_authority_sweep.png", dpi=220)
fig.savefig(OUT/"cf2_authority_sweep.pdf")
plt.close(fig)

print(f"Wrote report and figures to {OUT}")
