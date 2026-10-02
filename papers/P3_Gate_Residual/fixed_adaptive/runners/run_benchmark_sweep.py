"""
Benchmark sweep: run multiple controllers x missions and compare.

Usage:
    python runners/run_benchmark_sweep.py --preset smoke --missions roll,hard45 --sim-time 20

    python runners/run_benchmark_sweep.py --preset full --missions hard45 --sim-time 45 --activity-mode gate --direct-scale control --gate-gain 100000 --blend 0.50

Presets:
    smoke   : classical + direct_lif + direct_hyperlif
    quick   : + nengo_lifrate + direct_adaptive_hyperlif
    full    : all body-torque controllers
    rotor   : classical + rotor_residual controllers (Skydio X2 only)
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path


_HERE    = Path(__file__).resolve().parent
_PROJECT = _HERE.parent
_RUNNER  = _HERE / "run_rotor_level.py"

PRESETS = {
    "smoke": ["classical", "direct_lif", "direct_hyperlif"],
    "quick": ["classical", "direct_lif", "direct_hyperlif",
              "direct_adaptive_hyperlif", "nengo_lifrate"],
    "full":  ["classical", "direct_lif", "direct_hyperlif",
              "direct_adaptive_hyperlif", "direct_izhikevich",
              "nengo_lifrate", "nengo_lif", "nengo_adaptive_lif"],
    "rotor": ["classical", "rotor_residual_hyperlif",
              "rotor_residual_adaptive_hyperlif"],
}


def run_case(args, quad: str, controller: str, mission: str) -> dict:
    cmd = [
        sys.executable, str(_RUNNER),
        "--quad",       quad,
        "--controller", controller,
        "--mission",    mission,
        "--sim-time",   str(args.sim_time),
        "--dt",         str(args.dt),
        "--z-ref",      str(args.z_ref),
        "--seed",       str(args.seed),
        "--save-csv",
    ]
    if controller.startswith("direct_"):
        cmd += ["--blend",         str(args.blend),
                "--activity-mode", args.activity_mode,
                "--direct-scale",  args.direct_scale,
                "--gate-gain",     str(args.gate_gain)]
    if controller.startswith("rotor_residual"):
        cmd += ["--residual-blend", str(args.residual_blend),
                "--gate-gain",      str(args.gate_gain)]
    if controller.startswith("nengo_"):
        cmd += ["--n-neurons", str(args.n_neurons),
                "--radius",    str(args.radius),
                "--synapse",   str(args.synapse)]

    print(f"\n--- {quad} | {controller} | {mission} ---")
    print("  " + " ".join(cmd))
    result = subprocess.run(cmd, cwd=str(_PROJECT), capture_output=False)

    row = {
        "quad":       quad,
        "controller": controller,
        "mission":    mission,
        "returncode": result.returncode,
    }

    # Try to read latest summary
    summary_files = sorted(
        (_PROJECT / "results" / "logs").glob(f"{quad}_{mission}_{controller}_*_summary.json"),
        key=lambda p: p.stat().st_mtime
    )
    if summary_files:
        try:
            with summary_files[-1].open() as f:
                data = json.load(f)
            row.update({k: v for k, v in data.items() if isinstance(v, (int, float, str))})
        except Exception:
            pass

    return row


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--preset", choices=list(PRESETS), default="smoke")
    p.add_argument("--quad", default="skydio_x2")
    p.add_argument("--missions", default="roll")
    p.add_argument("--sim-time", type=float, default=20.0)
    p.add_argument("--dt", type=float, default=0.0005)
    p.add_argument("--z-ref", type=float, default=1.0)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--blend", type=float, default=0.20)
    p.add_argument("--activity-mode", choices=["voltage","gate","events"], default="voltage")
    p.add_argument("--direct-scale", choices=["paper","control"], default="paper")
    p.add_argument("--gate-gain", type=float, default=1.0)
    p.add_argument("--residual-blend", type=float, default=0.10)
    p.add_argument("--n-neurons", type=int, default=400)
    p.add_argument("--radius", type=float, default=1.5)
    p.add_argument("--synapse", type=float, default=0.002)
    args = p.parse_args()

    missions     = [m.strip() for m in args.missions.split(",") if m.strip()]
    controllers  = PRESETS[args.preset]
    quads        = [args.quad]

    rows = []
    for q in quads:
        for mission in missions:
            for ctrl in controllers:
                rows.append(run_case(args, q, ctrl, mission))

    # Save aggregate CSV
    out = _PROJECT / "results" / "logs" / (
        f"benchmark_sweep_{args.preset}_{args.quad}"
        f"_m{args.missions.replace(',','-')}"
        f"_T{args.sim_time:g}"
        f"_scale{args.direct_scale}_act{args.activity_mode}_gg{args.gate_gain:g}.csv"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({k for r in rows for k in r})
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nAggregate benchmark CSV: {out}")

    # Print comparison table
    table_keys = ["quad","controller","mission","qerr_mean","qerr_max","rmse_euler_mean","score","z_std"]
    header = " | ".join(f"{k:30s}" if len(k) > 12 else f"{k:14s}" for k in table_keys)
    print("\n" + "-"*len(header))
    print(header)
    print("-"*len(header))
    for row in rows:
        vals = []
        for k in table_keys:
            v = row.get(k, "N/A")
            if isinstance(v, float):
                vals.append(f"{v:14.6f}")
            else:
                vals.append(f"{str(v):14s}")
        print(" | ".join(vals))
    print("-"*len(header))


if __name__ == "__main__":
    main()
