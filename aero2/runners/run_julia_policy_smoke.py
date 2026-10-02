"""Validate the first Aero2 Julia policy path against Python PD.

This is a parity smoke, not the real-time bridge. The live controller path should
use PythonCall/juliacall or exported Julia-trained weights; a Julia subprocess per
control step would be inappropriate for the 200 Hz loop.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from aero2.control.base import Reference
from aero2.control.linear.pd import PD2DOF


def run_julia_policy(args) -> np.ndarray:
    julia = shutil.which(args.julia)
    if julia is None:
        raise RuntimeError(f"Julia executable not found: {args.julia!r}")

    script = REPO / "julia" / "aero2_policy_smoke.jl"
    cmd = [
        julia,
        "--startup-file=no",
        str(script),
        str(args.theta),
        str(args.theta_rate_f),
        str(args.psi),
        str(args.psi_rate_f),
        str(args.ref_theta),
        str(args.ref_psi),
        str(args.dt),
    ]
    result = subprocess.run(cmd, cwd=REPO, text=True, capture_output=True, check=True, timeout=args.timeout)
    values = [float(part) for part in result.stdout.strip().split(",")]
    return np.asarray(values, dtype=float)


def run_python_policy(args) -> np.ndarray:
    controller = PD2DOF()
    controller.reset()
    controller.pitch_filter.x2 = float(args.theta_rate_f) / controller.pitch_filter.wn
    controller.yaw_filter.x2 = float(args.psi_rate_f) / controller.yaw_filter.wn
    x = np.array([args.theta, 0.0, args.psi, 0.0], dtype=float)
    ref = Reference(theta=args.ref_theta, psi=args.ref_psi)
    return np.asarray(controller.compute(x, ref, args.dt), dtype=float)


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description="Compare Julia and Python Aero2 PD policy outputs.")
    p.add_argument("--theta", type=float, default=0.10)
    p.add_argument("--theta-rate-f", type=float, default=0.02)
    p.add_argument("--psi", type=float, default=-0.20)
    p.add_argument("--psi-rate-f", type=float, default=-0.03)
    p.add_argument("--ref-theta", type=float, default=0.20)
    p.add_argument("--ref-psi", type=float, default=0.10)
    p.add_argument("--dt", type=float, default=0.005)
    p.add_argument("--atol", type=float, default=1e-9)
    p.add_argument("--julia", default="julia")
    p.add_argument("--timeout", type=float, default=30.0)
    args = p.parse_args(argv)

    py_u = run_python_policy(args)
    jl_u = run_julia_policy(args)
    diff = np.abs(py_u - jl_u)
    print(f"python_u={py_u.tolist()}")
    print(f"julia_u={jl_u.tolist()}")
    print(f"max_abs_diff={float(diff.max()):.3e}")
    if not np.allclose(py_u, jl_u, atol=args.atol, rtol=0.0):
        raise SystemExit(f"Julia/Python policy mismatch exceeds atol={args.atol}")


if __name__ == "__main__":
    main()
