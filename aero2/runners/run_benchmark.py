"""run_benchmark.py — sweep controllers offline, emit the Table-IV-style comparison.

Reproduces the linear-vs-nonlinear controller ranking (Ref 3, Table IV) on the
offline plant. Absolute numbers differ from hardware (no real-time timing/noise),
but the RANKING and the yaw weakness should carry over.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from aero2.applications.reference_tracking import SquareWaveTracking
from aero2.benchmarking.metrics import tracking_metrics
from aero2.control import make_controller
from aero2.execution.offline import OfflineBackend
from aero2.models import make_model

VARIANTS = [
    ("PD baseline", "pd", {}),
    ("LQR", "lqr", {}),
    ("LQG", "lqg", {}),
    ("Linear MPC", "mpc", {}),
    ("Backstepping", "backstepping", {}),
    ("Backstepping yawboost", "backstepping", {"yawboost": True}),
    ("SMC", "smc", {}),
    ("SMC yawboost", "smc", {"yawboost": True}),
    ("NMPC realtime", "nmpc", {}),
]


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="helicopter_2dof")
    p.add_argument("--duration", type=float, default=30.0)
    p.add_argument("--dt", type=float, default=0.005)
    p.add_argument("--save", action="store_true")
    p.add_argument("--out", default="results")
    args = p.parse_args(argv)

    print(f"Offline benchmark | {args.model} | {args.duration:.0f}s @ {1/args.dt:.0f} Hz")
    print(f"{'Controller':<22} {'PitchRMS':>8} {'YawRMS':>7} {'TailP':>7} {'TailY':>7} {'PitchSat':>8}")
    print("-" * 64)
    rows = []
    for label, name, kw in VARIANTS:
        backend = OfflineBackend(make_model(args.model), dt=args.dt)
        app = SquareWaveTracking(duration_s=args.duration, nominal_hz=1.0 / args.dt)
        m = tracking_metrics(app.run(backend, make_controller(name, **kw)))
        rows.append({"label": label, "controller": name, "kwargs": kw, **m})
        print(f"{label:<22} {m['pitch_rms']:8.4f} {m['yaw_rms']:7.4f} "
              f"{m['tail_pitch_mae']:7.4f} {m['tail_yaw_mae']:7.4f} {m['pitch_sat_frac']:8.3f}")

    if args.save:
        out_dir = REPO / args.out
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = f"benchmark_{args.model}_offline_{stamp}"
        csv_path = out_dir / f"{stem}.csv"
        json_path = out_dir / f"{stem}.json"
        csv_fields = [
            "label",
            "controller",
            "kwargs",
            "n",
            "duration_s",
            "realized_hz",
            "pitch_rms",
            "yaw_rms",
            "tail_pitch_mae",
            "tail_yaw_mae",
            "pitch_sat_frac",
            "yaw_sat_frac",
            "theta_range",
            "psi_range",
        ]
        with csv_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=csv_fields)
            writer.writeheader()
            for row in rows:
                writer.writerow({key: row.get(key) for key in csv_fields})
        json_path.write_text(
            json.dumps(
                {
                    "config": {
                        "model": args.model,
                        "execution_mode": "offline",
                        "duration_s": args.duration,
                        "dt": args.dt,
                    },
                    "rows": rows,
                },
                indent=2,
                default=str,
            )
        )
        print(f"Saved CSV: {display_path(csv_path)}")
        print(f"Saved JSON: {display_path(json_path)}")


if __name__ == "__main__":
    main()
