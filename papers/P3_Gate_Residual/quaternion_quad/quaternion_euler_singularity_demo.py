"""Visualize why quaternion attitude states are better than Euler angles.

Run from the project root:

    python experiments/quaternion_quad/quaternion_euler_singularity_demo.py --show

For live updating plots:

    python experiments/quaternion_quad/quaternion_euler_singularity_demo.py --realtime

The script saves:

    results/logs/quaternion_euler_singularity_demo.csv
    results/logs/quaternion_euler_singularity_demo.npz
    results/figures/quaternion_quad/quaternion_euler_singularity_demo.png

The demonstration sweeps a ZYX Euler pitch angle through 90 degrees while roll
and yaw are nonzero. The quaternion components remain smooth, but the recovered
Euler roll/yaw coordinates jump and the Euler-rate map becomes ill-conditioned.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = PROJECT_ROOT / "results" / "logs"
FIGURES_DIR = PROJECT_ROOT / "results" / "figures" / "quaternion_quad"


def q_normalize(q: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(q)
    if n < 1e-12:
        return np.array([1.0, 0.0, 0.0, 0.0], dtype=float)
    return q / n


def euler_to_quat(phi: float, theta: float, psi: float) -> np.ndarray:
    """Convert ZYX Euler angles to quaternion [w, x, y, z]."""
    cphi, sphi = np.cos(phi / 2.0), np.sin(phi / 2.0)
    cth, sth = np.cos(theta / 2.0), np.sin(theta / 2.0)
    cpsi, spsi = np.cos(psi / 2.0), np.sin(psi / 2.0)

    return q_normalize(
        np.array(
            [
                cphi * cth * cpsi + sphi * sth * spsi,
                sphi * cth * cpsi - cphi * sth * spsi,
                cphi * sth * cpsi + sphi * cth * spsi,
                cphi * cth * spsi - sphi * sth * cpsi,
            ],
            dtype=float,
        )
    )


def quat_to_euler(q: np.ndarray) -> np.ndarray:
    """Convert quaternion [w, x, y, z] to ZYX Euler angles."""
    q = q_normalize(q)
    q0, q1, q2, q3 = q

    phi = np.arctan2(
        2.0 * (q0 * q1 + q2 * q3),
        q0 * q0 - q1 * q1 - q2 * q2 + q3 * q3,
    )

    s_theta = 2.0 * (q0 * q2 - q3 * q1)
    s_theta = np.clip(s_theta, -1.0, 1.0)
    theta = np.arcsin(s_theta)

    psi = np.arctan2(
        2.0 * (q0 * q3 + q1 * q2),
        q0 * q0 + q1 * q1 - q2 * q2 - q3 * q3,
    )

    return np.array([phi, theta, psi], dtype=float)


def wrap_to_pi(x: np.ndarray) -> np.ndarray:
    return (x + np.pi) % (2.0 * np.pi) - np.pi


def euler_rate_condition_number(phi: float, theta: float) -> float:
    """Condition number of the ZYX body-rate to Euler-rate matrix.

    For ZYX Euler angles, the map contains tan(theta) and sec(theta). It is
    singular at pitch = +/- 90 degrees.
    """
    cos_theta = np.cos(theta)
    if abs(cos_theta) < 1e-10:
        return float("inf")

    transform = np.array(
        [
            [1.0, np.sin(phi) * np.tan(theta), np.cos(phi) * np.tan(theta)],
            [0.0, np.cos(phi), -np.sin(phi)],
            [0.0, np.sin(phi) / cos_theta, np.cos(phi) / cos_theta],
        ],
        dtype=float,
    )
    return float(np.linalg.cond(transform))


def quaternion_step_angle(q_prev: np.ndarray, q_next: np.ndarray) -> float:
    """Geodesic angle between two unit quaternions."""
    dot = abs(float(np.dot(q_normalize(q_prev), q_normalize(q_next))))
    dot = np.clip(dot, -1.0, 1.0)
    return float(2.0 * np.arccos(dot))


def generate_demo(n: int = 900) -> dict[str, np.ndarray]:
    t = np.linspace(0.0, 1.0, n)

    # Nonzero roll/yaw makes the Euler singularity obvious.
    roll_ref = np.full_like(t, np.deg2rad(25.0))
    pitch_ref = np.deg2rad(-20.0 + 130.0 * t)
    yaw_ref = np.full_like(t, np.deg2rad(40.0))

    q = np.zeros((n, 4))
    euler_recovered = np.zeros((n, 3))
    cond = np.zeros(n)
    quat_step = np.zeros(n)
    euler_step = np.zeros(n)

    for i in range(n):
        q[i] = euler_to_quat(roll_ref[i], pitch_ref[i], yaw_ref[i])
        euler_recovered[i] = quat_to_euler(q[i])
        cond[i] = euler_rate_condition_number(euler_recovered[i, 0], euler_recovered[i, 1])
        if i > 0:
            quat_step[i] = quaternion_step_angle(q[i - 1], q[i])
            euler_step[i] = np.linalg.norm(wrap_to_pi(euler_recovered[i] - euler_recovered[i - 1]))

    singularity_index = int(np.argmin(np.abs(np.rad2deg(pitch_ref) - 90.0)))

    return {
        "t": t,
        "roll_ref": roll_ref,
        "pitch_ref": pitch_ref,
        "yaw_ref": yaw_ref,
        "q": q,
        "euler_recovered": euler_recovered,
        "condition_number": cond,
        "quat_step_angle": quat_step,
        "euler_step_norm": euler_step,
        "singularity_index": np.array([singularity_index], dtype=int),
    }


def save_data(data: dict[str, np.ndarray]) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = LOGS_DIR / "quaternion_euler_singularity_demo.csv"
    npz_path = LOGS_DIR / "quaternion_euler_singularity_demo.npz"

    t = data["t"]
    q = data["q"]
    e = data["euler_recovered"]
    fields = [
        "t",
        "roll_ref_rad",
        "pitch_ref_rad",
        "yaw_ref_rad",
        "q0",
        "q1",
        "q2",
        "q3",
        "roll_recovered_rad",
        "pitch_recovered_rad",
        "yaw_recovered_rad",
        "euler_rate_condition_number",
        "quat_step_angle",
        "euler_step_norm",
    ]

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for i in range(len(t)):
            writer.writerow(
                {
                    "t": t[i],
                    "roll_ref_rad": data["roll_ref"][i],
                    "pitch_ref_rad": data["pitch_ref"][i],
                    "yaw_ref_rad": data["yaw_ref"][i],
                    "q0": q[i, 0],
                    "q1": q[i, 1],
                    "q2": q[i, 2],
                    "q3": q[i, 3],
                    "roll_recovered_rad": e[i, 0],
                    "pitch_recovered_rad": e[i, 1],
                    "yaw_recovered_rad": e[i, 2],
                    "euler_rate_condition_number": data["condition_number"][i],
                    "quat_step_angle": data["quat_step_angle"][i],
                    "euler_step_norm": data["euler_step_norm"][i],
                }
            )

    np.savez(npz_path, **data)
    print(f"Saved data: {csv_path}")
    print(f"Saved data: {npz_path}")


def plot_demo(data: dict[str, np.ndarray], realtime: bool, show: bool) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    t = data["t"]
    q = data["q"]
    e = data["euler_recovered"]
    cond = data["condition_number"]
    singularity_index = int(data["singularity_index"][0])
    singularity_t = t[singularity_index]

    fig, axes = plt.subplots(4, 1, figsize=(12, 12), sharex=True)

    if realtime:
        plt.ion()
        chunk = max(5, len(t) // 180)
        for end in range(chunk, len(t) + chunk, chunk):
            end = min(end, len(t))
            for ax in axes:
                ax.clear()
            draw_panels(axes, t[:end], q[:end], e[:end], cond[:end], data, singularity_t)
            fig.canvas.draw()
            fig.canvas.flush_events()
            plt.pause(0.015)
    else:
        draw_panels(axes, t, q, e, cond, data, singularity_t)

    fig.tight_layout()
    path = FIGURES_DIR / "quaternion_euler_singularity_demo.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    print(f"Saved figure: {path}")

    if show or realtime:
        plt.show()
    else:
        plt.close(fig)


def draw_panels(
    axes: np.ndarray,
    t: np.ndarray,
    q: np.ndarray,
    e: np.ndarray,
    cond: np.ndarray,
    full_data: dict[str, np.ndarray],
    singularity_t: float,
) -> None:
    labels = ["roll", "pitch", "yaw"]
    ref = np.vstack(
        (
            full_data["roll_ref"][: len(t)],
            full_data["pitch_ref"][: len(t)],
            full_data["yaw_ref"][: len(t)],
        )
    ).T

    for i, label in enumerate(labels):
        axes[0].plot(t, np.rad2deg(ref[:, i]), "--", linewidth=1.4, label=f"{label} reference" if len(t) == len(full_data["t"]) else None)
        axes[0].plot(t, np.rad2deg(e[:, i]), linewidth=1.1, label=f"{label} recovered" if len(t) == len(full_data["t"]) else None)
    axes[0].axvline(singularity_t, color="k", linestyle=":", linewidth=1.0)
    axes[0].set_ylabel("Euler angles [deg]")
    axes[0].set_title("Euler coordinates jump near pitch = 90 deg")
    axes[0].grid(True, alpha=0.35)
    if len(t) == len(full_data["t"]):
        axes[0].legend(ncol=3, fontsize=7)

    q_labels = ["q0", "q1", "q2", "q3"]
    for i, label in enumerate(q_labels):
        axes[1].plot(t, q[:, i], linewidth=1.3, label=label)
    axes[1].axvline(singularity_t, color="k", linestyle=":", linewidth=1.0)
    axes[1].set_ylabel("Quaternion")
    axes[1].set_title("Quaternion components remain smooth")
    axes[1].grid(True, alpha=0.35)
    axes[1].legend(ncol=4, fontsize=8)

    cond_plot = np.clip(cond, 1.0, 1e4)
    axes[2].semilogy(t, cond_plot, linewidth=1.5)
    axes[2].axvline(singularity_t, color="k", linestyle=":", linewidth=1.0)
    axes[2].set_ylabel("Condition number")
    axes[2].set_title("Euler-rate map becomes ill-conditioned")
    axes[2].grid(True, which="both", alpha=0.35)

    axes[3].plot(t, full_data["quat_step_angle"][: len(t)], label="quaternion step angle", linewidth=1.4)
    axes[3].plot(t, full_data["euler_step_norm"][: len(t)], label="Euler coordinate step norm", linewidth=1.2)
    axes[3].axvline(singularity_t, color="k", linestyle=":", linewidth=1.0)
    axes[3].set_ylabel("Step size [rad]")
    axes[3].set_xlabel("Normalized sweep time")
    axes[3].set_title("Same smooth attitude path, unstable Euler coordinates")
    axes[3].grid(True, alpha=0.35)
    axes[3].legend(fontsize=8)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--show", action="store_true", help="Show the final plot window")
    parser.add_argument("--realtime", action="store_true", help="Animate the plot while generating it")
    parser.add_argument("--n", type=int, default=900, help="Number of samples")
    args = parser.parse_args()

    data = generate_demo(n=args.n)
    save_data(data)
    plot_demo(data, realtime=args.realtime, show=args.show)

    idx = int(data["singularity_index"][0])
    print("Singularity sample:")
    print(f"  pitch_ref_deg={np.rad2deg(data['pitch_ref'][idx]):.3f}")
    print(f"  condition_number={data['condition_number'][idx]}")
    print(f"  quaternion={data['q'][idx]}")
    print(f"  recovered_euler_deg={np.rad2deg(data['euler_recovered'][idx])}")


if __name__ == "__main__":
    main()
