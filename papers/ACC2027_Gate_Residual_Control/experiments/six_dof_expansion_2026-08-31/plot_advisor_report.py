"""Complete advisor-report figure set: quaternion/Euler detail tracking and
3D trajectories (PCA-chosen best viewing angle) for every mission and every
controller/neuron-family we have real data for -- X2 (classical/CMG-PES/
CMG-eprop_anneal, 4 missions), CF2 (classical/CMG-PES, 4 missions), and the
neuron-family ablation (LIF/ALIF/Izhikevich/LIFRate/CMG-PES/classical,
full6_stress only -- the only mission that family sweep was run on).
Reads trace.csv only, no re-simulation. Research phase closed; this is
figure generation from existing data.
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT/"results"/"plots"/"advisor_report"
OUT.mkdir(parents=True, exist_ok=True)
MISSIONS = ["hover3d", "waypoint_step", "circle_xy", "full6_stress"]


def load(d: Path) -> dict[str, np.ndarray]:
    with (d/"trace.csv").open() as f:
        rows = list(csv.DictReader(f))
    return {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}


def quat_mul(p, q):
    p0, p1, p2, p3 = p; q0, q1, q2, q3 = q
    return np.array([p0*q0-p1*q1-p2*q2-p3*q3, p0*q1+p1*q0+p2*q3-p3*q2,
                      p0*q2-p1*q3+p2*q0+p3*q1, p0*q3+p1*q2-p2*q1+p3*q0])


def quat_to_euler(q):
    w, x, y, z = q
    roll = np.arctan2(2*(w*x+y*z), 1-2*(x*x+y*y))
    pitch = np.arcsin(np.clip(2*(w*y-z*x), -1.0, 1.0))
    yaw = np.arctan2(2*(w*z+x*y), 1-2*(y*y+z*z))
    return np.array([roll, pitch, yaw])


def recover_q_meas(trace: dict) -> np.ndarray:
    n = len(trace["t"])
    q_meas = np.zeros((n, 4))
    for i in range(n):
        eq = np.array([trace["eq_x"][i], trace["eq_y"][i], trace["eq_z"][i]])
        qe0 = np.sqrt(max(0.0, 1.0-np.dot(eq, eq)))
        qe_conj = np.array([qe0, -eq[0], -eq[1], -eq[2]])
        q_des = np.array([trace["qdes_w"][i], trace["qdes_x"][i], trace["qdes_y"][i], trace["qdes_z"][i]])
        q_meas[i] = quat_mul(qe_conj, q_des)
    return q_meas


def best_view(xyz_list: list[np.ndarray]) -> tuple[float, float]:
    """PCA over all trajectories combined; view along the least-variance
    (flattest) principal axis so the trajectory's main plane of motion is
    shown face-on rather than foreshortened. Falls back to a standard
    3/4 view if the motion is too small/degenerate to have a clear axis."""
    pts = np.vstack(xyz_list)
    pts = pts-pts.mean(axis=0)
    spread = pts.std(axis=0)
    if np.max(spread) < 1e-3:
        return 22.0, -55.0
    cov = np.cov(pts.T)
    eigvals, eigvecs = np.linalg.eigh(cov)
    normal = eigvecs[:, 0]
    if normal[2] < 0:
        normal = -normal
    elev = float(np.degrees(np.arcsin(np.clip(normal[2], -1.0, 1.0))))
    azim = float(np.degrees(np.arctan2(normal[1], normal[0])))
    elev = float(np.clip(elev, 12.0, 75.0))
    return elev, azim


def plot_3d(traces: dict, ref: dict, colors: dict, title: str, out_path: Path) -> None:
    fig = plt.figure(figsize=(10, 9))
    ax = fig.add_subplot(111, projection="3d")
    if "x_ref" in ref:
        ax.plot(ref["x_ref"], ref["y_ref"], ref["z_ref"], "k--", lw=1.3, label="reference")
    all_pts = []
    for name, tr in traces.items():
        ax.plot(tr["x"], tr["y"], tr["z"], color=colors[name], lw=1.3, alpha=0.85, label=name)
        ax.scatter([tr["x"][0]], [tr["y"][0]], [tr["z"][0]], color=colors[name], marker="o", s=40)
        ax.scatter([tr["x"][-1]], [tr["y"][-1]], [tr["z"][-1]], color=colors[name], marker="^", s=50)
        all_pts.append(np.column_stack([tr["x"], tr["y"], tr["z"]]))
    elev, azim = best_view(all_pts)
    ax.view_init(elev=elev, azim=azim)
    ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)"); ax.set_zlabel("z (m)")
    ax.set_title(f"{title}\n(o = start, ^ = end; view auto-chosen via PCA)", fontsize=11)
    ax.legend(loc="upper left", fontsize=7.5)
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
    print(f"wrote {out_path}")


def plot_quat_detail(traces: dict, q_des_euler: np.ndarray, ref_t: np.ndarray,
                      colors: dict, ref_controller: str, title: str, out_path: Path) -> None:
    q_meas = {name: recover_q_meas(t) for name, t in traces.items()}
    euler = {name: np.array([quat_to_euler(q) for q in qm]) for name, qm in q_meas.items()}
    fig, axes = plt.subplots(4, 2, figsize=(14, 11), sharex=True)
    qlabels = ["w", "x", "y", "z"]
    for row in range(4):
        ax = axes[row, 0]
        ax.plot(ref_t, traces[ref_controller][f"qdes_{qlabels[row]}"], "k--", lw=1, label="q_des")
        for name, tr in traces.items():
            ax.plot(tr["t"], q_meas[name][:, row], color=colors[name], lw=0.7, alpha=0.85, label=name)
        ax.set_ylabel(f"q_{qlabels[row]}")
        if row == 0:
            ax.legend(loc="upper right", fontsize=7, ncol=len(traces)+1)
            ax.set_title("QUATERNION TRACKING", fontsize=10, loc="left", fontweight="bold")
    eulerlabels = ["roll", "pitch", "yaw"]
    for row in range(3):
        ax = axes[row, 1]
        ax.plot(ref_t, np.rad2deg(q_des_euler[:, row]), "k--", lw=1, label="reference")
        for name, tr in traces.items():
            ax.plot(tr["t"], np.rad2deg(euler[name][:, row]), color=colors[name], lw=0.7, alpha=0.85, label=name)
        ax.set_ylabel(f"{eulerlabels[row]} (deg)")
        if row == 0:
            ax.legend(loc="upper right", fontsize=7, ncol=len(traces)+1)
            ax.set_title("EULER ANGLE TRACKING", fontsize=10, loc="left", fontweight="bold")
    for name, tr in traces.items():
        axes[3, 1].plot(tr["t"], tr["pos_err"], color=colors[name], lw=0.8, label=name)
    axes[3, 1].set_ylabel("|pos err| (m)")
    axes[3, 1].legend(loc="upper right", fontsize=7)
    axes[3, 1].set_xlabel("time (s)")
    axes[3, 0].set_xlabel("time (s)")
    for ax in axes.flat:
        ax.grid(alpha=0.3)
    fig.suptitle(f"{title}\nmeasured q recovered via q_meas = conj(qe) (x) q_des", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(out_path, dpi=125)
    plt.close(fig)
    print(f"wrote {out_path}")


# =========================================================================
# Group 1 & 2: X2 and CF2 missions (classical / CMG-PES [/ CMG-eprop_anneal])
# =========================================================================
def run_platform_group(platform_label: str, dirs: dict, colors: dict):
    for mission in MISSIONS:
        try:
            traces = {name: load(fn(mission)) for name, fn in dirs.items()}
        except FileNotFoundError as e:
            print(f"SKIP {platform_label}/{mission}: {e}")
            continue
        ref_controller = next(iter(traces))
        ref = traces[ref_controller]
        q_des_euler = np.array([quat_to_euler(np.array([ref["qdes_w"][i], ref["qdes_x"][i],
                                                          ref["qdes_y"][i], ref["qdes_z"][i]]))
                                 for i in range(len(ref["t"]))])
        plot_quat_detail(traces, q_des_euler, ref["t"], colors, ref_controller,
                          f"{platform_label} 6-DOF cascade -- {mission}: quaternion + Euler detail tracking",
                          OUT/f"{platform_label}_{mission}_quaternion_detail.png")
        plot_3d(traces, ref, colors, f"3D TRAJECTORY -- {platform_label}, {mission}",
                OUT/f"{platform_label}_{mission}_trajectory_3d.png")


X2_DIRS = {
    "classical": lambda m: ROOT/"results"/"optionA"/f"{m}_classical",
    "CMG-PES": lambda m: ROOT/"results"/"optionA"/f"{m}_pes",
    "CMG-eprop_anneal": lambda m: ROOT/"results"/"eprop_x2"/m,
}
X2_COLORS = {"classical": "tab:blue", "CMG-PES": "tab:red", "CMG-eprop_anneal": "tab:brown"}

CF2_DIRS = {
    "classical": lambda m: ROOT/"results"/"optionA_cf2"/f"{m}_classical",
    "CMG-PES": lambda m: ROOT/"results"/"optionA_cf2"/f"{m}_pes",
}
CF2_COLORS = {"classical": "tab:blue", "CMG-PES": "tab:red"}

run_platform_group("X2", X2_DIRS, X2_COLORS)
run_platform_group("CF2", CF2_DIRS, CF2_COLORS)


# =========================================================================
# Group 3: neuron-family ablation (full6_stress only -- the only mission
# this sweep was run on; no eq_x/qdes columns logged for these runs, so
# quaternion/Euler detail isn't recoverable -- 3D trajectory + error
# tracking only, honestly scoped to what the data supports).
# =========================================================================
FAMILY_DIRS = {
    "classical": ROOT/"results"/"optionA"/"full6_stress_classical",
    "CMG-PES": ROOT/"results"/"optionA"/"full6_stress_pes",
    "LIFRate-PES": ROOT/"results"/"nengo_families"/"x2_lifrate_full6_stress",
    "ALIF-PES": ROOT/"results"/"nengo_families"/"x2_alif_full6_stress",
    "LIF-PES": ROOT/"results"/"nengo_families"/"x2_lif_full6_stress",
    "Izhikevich-PES": ROOT/"results"/"nengo_families"/"x2_izhikevich_full6_stress",
}
FAMILY_COLORS = {"classical": "gray", "CMG-PES": "tab:red", "LIFRate-PES": "tab:orange",
                  "ALIF-PES": "tab:green", "LIF-PES": "tab:blue", "Izhikevich-PES": "tab:purple"}

family_traces = {name: load(d) for name, d in FAMILY_DIRS.items()}
ref_fam = family_traces["classical"]

plot_3d(family_traces, ref_fam, FAMILY_COLORS,
        "3D TRAJECTORY -- X2, full6_stress: neuron-family ablation",
        OUT/"neuron_family_full6_stress_trajectory_3d.png")

fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
for name, tr in family_traces.items():
    axes[0].plot(tr["t"], tr["pos_err"], color=FAMILY_COLORS[name], lw=1, alpha=0.85, label=name)
    axes[1].plot(tr["t"], np.rad2deg(tr["qerr"]), color=FAMILY_COLORS[name], lw=1, alpha=0.85, label=name)
axes[0].set_ylabel("|pos error| (m)")
axes[0].legend(loc="upper right", fontsize=8, ncol=3)
axes[0].grid(alpha=0.3)
axes[0].set_title("NEURON-FAMILY ABLATION -- X2, full6_stress: position error", fontsize=11, loc="left", fontweight="bold")
axes[1].set_ylabel("attitude error (deg)")
axes[1].set_xlabel("time (s)")
axes[1].legend(loc="upper right", fontsize=8, ncol=3)
axes[1].grid(alpha=0.3)
axes[1].set_title("attitude (quaternion angle) error", fontsize=11, loc="left", fontweight="bold")
fig.suptitle("Neuron-family ablation, X2 full6_stress -- classical vs CMG-PES vs LIF/ALIF/Izhikevich/LIFRate\n"
             "(only mission this sweep was run on; no per-axis quaternion detail logged for these runs)", fontsize=12)
fig.tight_layout(rect=[0, 0, 1, 0.92])
fig.savefig(OUT/"neuron_family_full6_stress_error_tracking.png", dpi=125)
plt.close(fig)
print(f"wrote {OUT/'neuron_family_full6_stress_error_tracking.png'}")
