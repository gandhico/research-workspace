"""Export downsampled trace data (all 4 missions x 3 controllers) as one
compact JSON for the interactive dashboard artifact. Downsamples to ~400
points/run to keep the artifact well under size limits while preserving
the shape of every curve.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
MISSIONS = ["hover3d", "waypoint_step", "circle_xy", "full6_stress"]
DIRS = {
    "classical": lambda m: ROOT/"results"/"optionA"/f"{m}_classical",
    "CMG-PES": lambda m: ROOT/"results"/"optionA"/f"{m}_pes",
    "CMG-eprop_anneal": lambda m: ROOT/"results"/"eprop_x2"/m,
}
POINTS = 400


def load(d: Path) -> dict[str, np.ndarray]:
    with (d/"trace.csv").open() as f:
        rows = list(csv.DictReader(f))
    return {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}


def down(arr: np.ndarray, n: int) -> list:
    idx = np.linspace(0, len(arr)-1, n).astype(int)
    return [round(float(v), 5) for v in arr[idx]]


def quat_mul(p, q):
    p0, p1, p2, p3 = p; q0, q1, q2, q3 = q
    return np.array([p0*q0-p1*q1-p2*q2-p3*q3, p0*q1+p1*q0+p2*q3-p3*q2,
                      p0*q2-p1*q3+p2*q0+p3*q1, p0*q3+p1*q2-p2*q1+p3*q0])


def quat_to_euler_deg(q):
    w, x, y, z = q
    roll = np.degrees(np.arctan2(2*(w*x+y*z), 1-2*(x*x+y*y)))
    pitch = np.degrees(np.arcsin(np.clip(2*(w*y-z*x), -1.0, 1.0)))
    yaw = np.degrees(np.arctan2(2*(w*z+x*y), 1-2*(y*y+z*z)))
    return roll, pitch, yaw


if __name__ == "__main__":
    out = {}
    for mission in MISSIONS:
        out[mission] = {"controllers": {}}
        for name, fn in DIRS.items():
            tr = load(fn(mission))
            n = len(tr["t"])
            idx = np.linspace(0, n-1, POINTS).astype(int)
            roll, pitch, yaw = [], [], []
            for i in idx:
                eq = np.array([tr["eq_x"][i], tr["eq_y"][i], tr["eq_z"][i]])
                qe0 = np.sqrt(max(0.0, 1.0-np.dot(eq, eq)))
                qe_conj = np.array([qe0, -eq[0], -eq[1], -eq[2]])
                q_des = np.array([tr["qdes_w"][i], tr["qdes_x"][i], tr["qdes_y"][i], tr["qdes_z"][i]])
                q_meas = quat_mul(qe_conj, q_des)
                r, p, y = quat_to_euler_deg(q_meas)
                roll.append(round(r, 3)); pitch.append(round(p, 3)); yaw.append(round(y, 3))
            out[mission]["controllers"][name] = {
                "t": down(tr["t"], POINTS),
                "x": down(tr["x"], POINTS), "y": down(tr["y"], POINTS), "z": down(tr["z"], POINTS),
                "pos_err": down(tr["pos_err"], POINTS), "qerr_deg": [round(np.degrees(v), 3) for v in down(tr["qerr"], POINTS)],
                "tau_x": down(tr["tau_x"], POINTS), "tau_y": down(tr["tau_y"], POINTS), "tau_z": down(tr["tau_z"], POINTS),
                "residual_norm": down(tr["residual_norm"], POINTS),
                "gate_mean": down(tr["gate_mean"], POINTS) if "gate_mean" in tr else [],
                "activity_mean": down(tr["activity_mean"], POINTS),
                "roll": roll, "pitch": pitch, "yaw": yaw,
            }
        out[mission]["reference"] = {
            "x": down(load(DIRS["classical"](mission))["x_ref"], POINTS),
            "y": down(load(DIRS["classical"](mission))["y_ref"], POINTS),
            "z": down(load(DIRS["classical"](mission))["z_ref"], POINTS),
        }

    (ROOT/"results"/"plots"/"dashboard_data.json").write_text(json.dumps(out))
    sz = (ROOT/"results"/"plots"/"dashboard_data.json").stat().st_size
    print(f"wrote dashboard_data.json ({sz/1024:.1f} KB)")
