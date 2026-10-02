"""Finite-difference regression for analytic mission reference kinematics."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from missions import AXES, MISSIONS, reference_kinematics


def main():
    q0 = np.array([np.sqrt(.5), 0., np.sqrt(.5), 0.])
    h = 1e-5
    max_linear = max_angular = 0.
    samples = 0
    for mission in MISSIONS:
        for t in np.linspace(2.1, 2 + mission.move_s - .1, 9):
            p, v, a, _, omega, alpha, _ = reference_kinematics(mission, t, q0)
            before = reference_kinematics(mission, t-h, q0)
            after = reference_kinematics(mission, t+h, q0)
            velocity_fd = (after[0] - before[0]) / (2*h)
            acceleration_fd = (after[1] - before[1]) / (2*h)
            omega_fd = np.deg2rad(after[6] - before[6]) / (2*h) * AXES[mission.axis]
            alpha_fd = (after[4] - before[4]) / (2*h)
            max_linear = max(max_linear, np.linalg.norm(v-velocity_fd),
                             np.linalg.norm(a-acceleration_fd))
            max_angular = max(max_angular, np.linalg.norm(omega-omega_fd),
                              np.linalg.norm(alpha-alpha_fd))
            samples += 1
    result = {"samples": samples,
              "max_linear_derivative_error": float(max_linear),
              "max_angular_derivative_error": float(max_angular),
              "tolerance": 1e-7,
              "passed": bool(max(max_linear, max_angular) < 1e-7)}
    output = Path(__file__).resolve().parent / "output" / "reference_validation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
