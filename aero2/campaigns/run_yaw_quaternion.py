"""Quaternion yaw control on the QLabs Aero2 twin — 360-degree / wrap-aware yaw.

Motivation
----------
The naive yaw error ``e = psi_ref - psi`` breaks at the +/-180 deg boundary: when
the setpoint flips from +170 to -170 deg, the naive error is -340 deg and the
controller drives the LONG way around (or winds up). A **unit quaternion**
representation of the yaw rotation gives the *shortest-path* error on the circle,
so the same setpoint switch is a +20 deg hop across 180 deg — and continuous
360 deg+ references become trackable. (For this single yaw axis the quaternion
reduces to SO(2) wrapping, but the formulation generalizes directly to full 3D
attitude for QDrone/QArm later.)

This runner regulates pitch to 0 and drives a yaw setpoint schedule that crosses
+/-180 deg, running the SAME PD twice: naive error vs quaternion error, and
reports how each handles the wrap. Requires QLabs Aero2 open on localhost:18950.

Run:  conda run -n hyperlif python C:\\Research\\aero2\\campaigns\\run_yaw_quaternion.py
"""
from __future__ import annotations

import csv
import os
import sys
import time
from datetime import datetime

REPO = r"C:\Research\aero2"
QPY = r"C:\Users\gandhico\Documents\Quanser\0_libraries\python"
os.environ.setdefault("QUANSER_PYTHON", QPY)
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
sys.path.insert(0, REPO)

import numpy as np  # noqa: E402
from aero2.config import gains, params  # noqa: E402
from aero2.execution.virtual_twin import VirtualTwinBackend  # noqa: E402

OUT = os.path.join(REPO, "results_twin_campaign")
os.makedirs(OUT, exist_ok=True)


# --- quaternion helpers (yaw about +z) -------------------------------------
def quat_from_yaw(psi: float) -> np.ndarray:
    return np.array([np.cos(psi / 2.0), 0.0, 0.0, np.sin(psi / 2.0)])  # [w,x,y,z]


def quat_conj(q: np.ndarray) -> np.ndarray:
    return np.array([q[0], -q[1], -q[2], -q[3]])


def quat_mul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    w1, x1, y1, z1 = a
    w2, x2, y2, z2 = b
    return np.array([
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
    ])


def yaw_error_quaternion(psi_ref: float, psi_meas: float) -> float:
    """Shortest-path yaw error via the error quaternion, in (-pi, pi].

    The unit quaternion double-covers SO(3): q and -q are the same rotation.
    Canonicalizing to the qw>=0 hemisphere makes 2*atan2(qz, qw) the
    SHORTEST-path angle (otherwise it can return the long way, up to +/-2pi).
    """
    qe = quat_mul(quat_from_yaw(psi_ref), quat_conj(quat_from_yaw(psi_meas)))
    if qe[0] < 0.0:
        qe = -qe                      # shortest-path hemisphere
    return 2.0 * np.arctan2(qe[3], qe[0])


# --- yaw setpoint schedule (crosses +/-180 deg) ----------------------------
AMP = np.deg2rad(170.0)


def yaw_ref(t: float) -> float:
    if t < 3.0:
        return 0.0
    if t < 9.0:
        return +AMP
    if t < 15.0:
        return -AMP        # +170 -> -170: shortest path is +20 deg across 180 deg
    return +AMP            # -170 -> +170: shortest path is -20 deg across 180 deg


def run_mode(be: VirtualTwinBackend, mode: str, duration: float, hz: float,
             kp_yaw: float | None = None, kd_yaw: float | None = None) -> list[dict]:
    KpP, KdP = gains.PD_KP_PITCH, gains.PD_KD_PITCH
    KpY = gains.PD_KP_YAW if kp_yaw is None else kp_yaw
    KdY = gains.PD_KD_YAW if kd_yaw is None else kd_yaw
    VMAX = params.V_MAX
    use_quat = "quaternion" in mode
    be.reset(np.zeros(4))
    be.apply(np.zeros(2)); be.read()          # warm-up throwaway
    rows: list[dict] = []
    dt = 1.0 / hz
    t0 = time.perf_counter()
    nextT = t0
    while True:
        t = time.perf_counter() - t0
        if t > duration:
            break
        m = be.read()
        theta = float(m.theta); psi = float(m.psi)
        thd = float(m.theta_dot or 0.0); psd = float(m.psi_dot or 0.0)
        rpsi = yaw_ref(t)
        e_naive = rpsi - psi
        e_quat = yaw_error_quaternion(rpsi, psi)
        e_yaw = e_quat if use_quat else e_naive
        u_p = np.clip(KpP * (0.0 - theta) - KdP * thd, -VMAX, VMAX)   # regulate pitch to 0
        u_y = np.clip(KpY * e_yaw - KdY * psd, -VMAX, VMAX)
        be.apply(np.array([u_p, u_y]))
        rows.append({"t": t, "psi_ref": rpsi, "psi": psi, "theta": theta,
                     "e_naive": e_naive, "e_quat": e_quat, "u_yaw": u_y, "u_pitch": u_p})
        nextT += dt
        while time.perf_counter() < nextT and (time.perf_counter() - t0) <= duration:
            pass
    be.apply(np.zeros(2))
    time.sleep(0.2)
    return rows


def summarize(mode: str, rows: list[dict]) -> dict:
    psi = np.array([r["psi"] for r in rows])
    t = np.array([r["t"] for r in rows])
    u = np.array([r["u_yaw"] for r in rows])
    # commanded direction in the 0.5 s right after the +170 -> -170 switch (t=9 s)
    win = (t >= 9.0) & (t < 9.5)
    yaw_travel = float(np.sum(np.abs(np.diff(psi)))) if len(psi) > 1 else 0.0
    return {
        "mode": mode,
        "samples": len(rows),
        "yaw_reach_deg": float(np.rad2deg(np.max(np.abs(psi)))) if len(psi) else 0.0,
        "total_yaw_travel_deg": float(np.rad2deg(yaw_travel)),
        "u_yaw_after_switch": float(np.mean(u[win])) if win.any() else float("nan"),
        "e_yaw_after_switch_deg": float(np.rad2deg(
            np.mean([r["e_quat" if "quaternion" in mode else "e_naive"] for r, w in zip(rows, win) if w]
                    ))) if win.any() else float("nan"),
    }


def main():
    print("Connecting to QLabs Aero2 twin (quaternion yaw demo)...", flush=True)
    be = VirtualTwinBackend(aero_id="0", frequency=200.0, output_mode="mixed",
                            voltage_limit=15.0, quanser_python=QPY)
    dur, hz = 21.0, 200.0
    all_rows: dict[str, list[dict]] = {}
    summ = []
    # (label, kp_yaw, kd_yaw) — None => stock config gains
    conditions = [
        ("naive", None, None),
        ("quaternion", None, None),
        ("quaternion_damped", 8.0, 7.0),   # gentler, well-damped for clean positioning
    ]
    try:
        for mode, kpy, kdy in conditions:
            print(f"running yaw mode = {mode} (Kp={kpy or gains.PD_KP_YAW:.1f}, Kd={kdy or gains.PD_KD_YAW:.1f}) ...", flush=True)
            rows = run_mode(be, mode, dur, hz, kpy, kdy)
            all_rows[mode] = rows
            summ.append(summarize(mode, rows))
    finally:
        be.close()

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for mode, rows in all_rows.items():
        p = os.path.join(OUT, f"yaw_{mode}_{stamp}.csv")
        with open(p, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

    print("\n[Quaternion yaw demo — +/-170 deg setpoints crossing 180 deg]")
    for s in summ:
        print(f"  {s['mode']:>10}: reach={s['yaw_reach_deg']:.1f} deg  "
              f"travel={s['total_yaw_travel_deg']:.1f} deg  "
              f"u_yaw@switch={s['u_yaw_after_switch']:+.2f} V  "
              f"e@switch={s['e_yaw_after_switch_deg']:+.1f} deg")
    print("\n  Interpretation: at the +170->-170 switch, shortest path is +20 deg.")
    print("  naive commands the LONG way (large negative error/command); quaternion")
    print("  commands the SHORT +20 deg hop across 180 deg.")
    print(f"  saved -> {OUT}\\yaw_*_{stamp}.csv")


if __name__ == "__main__":
    main()
