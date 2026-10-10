"""Verify the exact one-step rotor-force box and command inversion."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from hifi.rotor_response import RotorResponse  # noqa: E402


def main():
    audit = json.loads((ROOT / "docs" / "TWIN_L0_AUDIT_2026-10-06.json").read_text())
    result = {}
    for platform, scale in (("x2", 1.0), ("cf2_design_P5_1p5x", 1.5)):
        entry = audit["models"]["x2" if platform == "x2" else "cf2_design"]
        fmax = np.array([x[1] for x in entry["rotor_force_ctrl_ranges_N"]]) * scale
        hover = float(entry["hover_force_per_rotor_N"])
        dt, tau = 0.0005, 0.03  # synthetic tau, study clock
        rotor = RotorResponse(fmax, np.full(4, tau), np.full(4, hover))
        lo, hi = rotor.reachable_force_interval(dt)
        target = 0.5 * (lo + hi)
        command = rotor.command_for_next_force(target, dt)
        realized = rotor.step(command, dt)
        np.testing.assert_allclose(realized, target, rtol=0, atol=1e-14)
        assert np.all(lo <= target) and np.all(target <= hi)
        assert np.all((command >= 0) & (command <= fmax))
        try:
            rotor.command_for_next_force(hi + 0.01 * fmax, dt)
        except ValueError:
            pass
        else:
            raise AssertionError("unreachable force accepted")
        result[platform] = {
            "fmax_N_each": float(fmax[0]), "hover_N_each": hover,
            "tau_s_synthetic": tau, "dt_s": dt,
            "next_force_min_N_each": float(lo[0]),
            "next_force_max_N_each": float(hi[0]),
            "next_force_span_pct_hover": float(100 * (hi[0] - lo[0]) / hover),
            "static_tilt_limit_for_nonnegative_vertical_accel_deg":
                float(np.degrees(np.arccos(hover / fmax[0]))),
            "next_sample_tilt_limit_for_nonnegative_vertical_accel_deg":
                float(np.degrees(np.arccos(hover / hi[0]))),
            "inverse_error_max_N": float(np.max(np.abs(realized - target))),
        }
    out = ROOT / "docs" / "TWIN_L1_REACHABILITY_2026-10-06.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
