"""Render a saved mission campaign as a Markdown report and summary figures."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("directory", type=Path)
args = parser.parse_args()
out = args.directory
results = json.loads((out / "campaign.json").read_text(encoding="utf-8"))
manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
lines = ["# Omnicopter progressive mission results", "",
         "Controller: unchanged hover PD (position 4/3.6, attitude 16/7.2), moving pose references, ideal state feedback. Model and inputs unchanged. Simulation only.", "",
         "Pass criteria were set before the runs. A failed mission stops escalation; skipped missions have not been validated.", "",
         "| Stage | Mission | Result | Peak position error (cm) | Peak attitude error (deg) | Peak input (N) | Saturated (%) | Actual signed turn (deg) |",
         "|---|---|---|---:|---:|---:|---:|---:|"]
for r in results:
    if "peak_position_error_m" not in r:
        lines.append(f"| {r['stage']} | {r['name']} | {r['status']} | - | - | - | - | - |")
        continue
    turn = "-" if r["actual_rotation_progress_deg"] is None else f"{r['actual_rotation_progress_deg']:.2f}"
    lines.append(f"| {r['stage']} | {r['name']} | {r['status']} | {100*r['peak_position_error_m']:.2f} | {r['peak_attitude_error_deg']:.2f} | {r['max_abs_input_N']:.3f} | {100*r['saturation_fraction']:.3f} | {turn} |")
lines += ["", "## Gate failures", ""]
for r in results:
    if r.get("failed_gates") or r.get("abort_reason"):
        lines.append(f"- {r['name']}: gates {r.get('failed_gates', [])}; abort {r.get('abort_reason')}.")
if not any(r.get("failed_gates") or r.get("abort_reason") for r in results):
    lines.append("None among executed missions.")
executed = [r for r in results if "peak_position_error_m" in r]
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
fig, axes = plt.subplots(1, 2, figsize=(12, max(7, len(executed)*.34)), layout="constrained", sharey=True)
y = np.arange(len(executed))
colors = ["#168485" if r["status"] == "pass" else "#bd3e48" for r in executed]
axes[0].barh(y, [100*r["peak_position_error_m"] for r in executed], color=colors)
axes[1].barh(y, [r["peak_attitude_error_deg"] for r in executed], color=colors)
axes[0].set_yticks(y, [r["name"] for r in executed])
axes[0].invert_yaxis()
axes[0].set_xlabel("Peak position error (cm)")
axes[1].set_xlabel("Peak attitude error (deg)")
axes[0].axvline(100*manifest["gates"]["peak_position_error_m"], color="#bd3e48", ls="--", lw=1)
axes[1].axvline(manifest["gates"]["peak_attitude_error_deg"], color="#bd3e48", ls="--", lw=1)
for ax in axes:
    ax.grid(axis="x", alpha=.15)
fig.suptitle("Omnicopter maneuverability | Unchanged PD baseline\nDashed lines: predeclared tracking gates; red bars: failed mission", fontsize=13)
fig.savefig(out / "campaign_summary.png", dpi=150)
plt.close(fig)
lines += ["", "![Campaign summary](campaign_summary.png)", ""]
spin_names = [r["name"] for r in executed if r["name"] == "yaw_360" or r["stage"] == 7]
if spin_names:
    fig, axes = plt.subplots(len(spin_names), 1, figsize=(10, 2.7*len(spin_names)), layout="constrained", squeeze=False)
    for ax, name in zip(axes[:, 0], spin_names):
        data = np.genfromtxt(out / name / "trace.csv", delimiter=",", names=True)
        ax.plot(data["time_s"], data["reference_rotation_deg"], "--", color="#333333", label="Requested turn")
        ax.plot(data["time_s"], data["actual_rotation_progress_deg"], color="#168485", label="Accumulated actual turn")
        ax.set_title(name)
        ax.set_ylabel("Signed angle (deg)")
        ax.grid(alpha=.15)
        ax.legend(loc="upper left", fontsize=9)
    axes[-1, 0].set_xlabel("Simulation time (s), including start and terminal holds")
    fig.suptitle("Verify the revolution, not just the final orientation", fontsize=14)
    fig.savefig(out / "rotation_progress.png", dpi=150)
    plt.close(fig)
    lines += ["![Actual rotation progress](rotation_progress.png)", ""]
lines += ["## Interpretation", "",
          "A full turn is checked using signed accumulated quaternion increments as well as attitude error. Equivalent start/end orientations alone do not count as success.", "",
          "The pose-only PD damps absolute velocity and angular rate, so moving references produce tracking lag. A quality-gate failure may occur without saturation or loss of stability. Inspect allocation residuals and saturation before attributing a failure to actuator authority.", "",
          "These ideal-model results do not validate hardware or unmodeled motor/estimator/communication dynamics."]
(out / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(out / "REPORT.md")
