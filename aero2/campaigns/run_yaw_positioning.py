"""Quaternion yaw positioning vs naive PD on large / 360-deg setpoints (2DOF twin).

Runs the registered ``qpd`` (wrap-aware, rate-limited) and ``pd`` (naive error)
controllers on the ``yaw_large_setpoint`` application (0 -> +170 -> -170 -> +270
-> 0 deg) and scores yaw with a SHORTEST-PATH (wrap-aware) metric — the only
fair way to compare once the setpoints cross +/-180 deg.
Requires QLabs Aero2 (helicopter 2DOF) open on localhost:18950.
"""
from __future__ import annotations

import csv
import os
import sys
from datetime import datetime

REPO = r"C:\Research\aero2"
QPY = r"C:\Users\gandhico\Documents\Quanser\0_libraries\python"
os.environ.setdefault("QUANSER_PYTHON", QPY)
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
sys.path.insert(0, REPO)

import numpy as np  # noqa: E402
from aero2.applications import make_application  # noqa: E402
from aero2.control import make_controller  # noqa: E402
from aero2.control.quaternion_yaw import yaw_error_quaternion  # noqa: E402
from aero2.execution.virtual_twin import VirtualTwinBackend  # noqa: E402
from aero2.io import make_estimator  # noqa: E402

OUT = os.path.join(REPO, "results_twin_campaign")
os.makedirs(OUT, exist_ok=True)

# (hold_start_s, hold_end_s, target_deg) for the yaw_large_setpoint schedule
HOLDS = [(3, 9, 170), (9, 15, -170), (15, 21, 270), (21, 27, 0)]


def scored(rec):
    t = np.asarray(rec.t)
    psi = np.array([x[2] for x in rec.x_est])
    rpsi = np.array([r[2] for r in rec.ref])
    e = np.array([yaw_error_quaternion(rr, pp) for rr, pp in zip(rpsi, psi)])  # shortest-path
    out = {"wrap_rms_deg": float(np.rad2deg(np.sqrt(np.mean(e ** 2)))),
           "reach_deg": float(np.rad2deg(np.max(np.abs(psi)))),
           "travel_deg": float(np.rad2deg(np.sum(np.abs(np.diff(psi)))))}
    for (h0, h1, tgt) in HOLDS:
        win = (t >= h1 - 1.5) & (t < h1)
        out[f"settle@{tgt}deg"] = (float(np.rad2deg(np.mean(np.abs(e[win])))) if win.any()
                                   else float("nan"))
    return t, rpsi, psi, e, out


def main():
    app = make_application("yaw_large_setpoint")   # 27 s schedule
    est = make_estimator("passthrough")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summ = {}
    for name in ("pd", "qpd"):
        print(f"running {name} on yaw_large_setpoint ...", flush=True)
        be = VirtualTwinBackend(aero_id="0", frequency=200.0, output_mode="mixed",
                                voltage_limit=15.0, quanser_python=QPY)
        rec = app.run(be, make_controller(name), est)   # app.run closes the backend
        t, rpsi, psi, e, out = scored(rec)
        summ[name] = out
        with open(os.path.join(OUT, f"yawpos_{name}_{stamp}.csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["t", "psi_ref_deg", "psi_deg", "wrap_err_deg"])
            for i in range(len(t)):
                w.writerow([round(t[i], 4), round(np.rad2deg(rpsi[i]), 2),
                            round(np.rad2deg(psi[i]), 2), round(np.rad2deg(e[i]), 2)])

    print("\n[Yaw positioning — shortest-path (wrap-aware) settle error, deg]")
    hdr = "  {:>5} | wrap_rms | " + " | ".join(f"@{tgt}" for _, _, tgt in HOLDS) + " | reach | travel"
    print(hdr.format("ctrl"))
    for name in ("pd", "qpd"):
        s = summ[name]
        cells = " | ".join(f"{s[f'settle@{tgt}deg']:6.1f}" for _, _, tgt in HOLDS)
        print(f"  {name:>5} | {s['wrap_rms_deg']:8.1f} | {cells} | {s['reach_deg']:5.0f} | {s['travel_deg']:.0f}")
    print(f"saved -> {OUT}\\yawpos_*_{stamp}.csv")
    print("YAW POSITIONING DONE")


if __name__ == "__main__":
    main()
