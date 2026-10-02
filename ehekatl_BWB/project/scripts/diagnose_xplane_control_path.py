#!/usr/bin/env python3
"""Read-only snapshot of X-Plane control ownership and realized surfaces."""

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
XPC_DIR = ROOT / "scripts"
if str(XPC_DIR) not in sys.path:
    sys.path.insert(0, str(XPC_DIR))

import xpc


SCALARS = (
    "sim/time/paused",
    "sim/time/sim_speed",
    "sim/operation/prefs/replay_mode",
    "sim/cockpit/switches/art_stab_on",
    "sim/joystick/artstab_roll_ratio",
    "sim/cockpit2/controls/torque_tube_split_roll",
    "sim/operation/failures/rel_conlock",
    "sim/operation/failures/rel_fcon_ailn_1_lft_lock",
    "sim/operation/failures/rel_fcon_ailn_1_rgt_lock",
    "sim/operation/failures/rel_fcon_ailn_2_lft_lock",
    "sim/operation/failures/rel_fcon_ailn_2_rgt_lock",
    "sim/operation/failures/rel_fcon_ailn_1_lft_cntr",
    "sim/operation/failures/rel_fcon_ailn_1_rgt_cntr",
    "sim/operation/failures/rel_fcon_ailn_2_lft_cntr",
    "sim/operation/failures/rel_fcon_ailn_2_rgt_cntr",
    "sim/operation/override/override_joystick",
    "sim/operation/override/override_joystick_roll",
    "sim/operation/override/override_joystick_pitch",
    "sim/operation/override/override_joystick_heading",
    "sim/operation/override/override_flightcontrol",
    "sim/operation/override/override_control_surfaces",
    "sim/joystick/yoke_roll_ratio",
    "sim/joystick/yoke_pitch_ratio",
    "sim/joystick/yoke_heading_ratio",
    "sim/joystick/FC_roll",
    "sim/joystick/FC_ptch",
    "sim/joystick/FC_hdng",
    "sim/cockpit2/controls/total_roll_ratio",
    "sim/cockpit2/controls/total_pitch_ratio",
    "sim/cockpit2/controls/total_heading_ratio",
)

SURFACE_ARRAYS = (
    "sim/flightmodel/controls/ail1_def",
    "sim/flightmodel/controls/ail2_def",
    "sim/flightmodel/controls/elv1_def",
    "sim/flightmodel/controls/elv2_def",
    "sim/flightmodel/controls/rudd_def",
)


def flat(value):
    if isinstance(value, (list, tuple)):
        if len(value) == 1 and isinstance(value[0], (list, tuple)):
            return flat(value[0])
        return [float(item) for item in value]
    return [float(value)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=49009)
    parser.add_argument("--timeout-ms", type=int, default=2000)
    parser.add_argument("--surface-threshold-deg", type=float, default=1e-6)
    args = parser.parse_args()

    with xpc.XPlaneConnect(xpHost=args.host, xpPort=args.port, timeout=args.timeout_ms) as client:
        print("getCTRL:", tuple(float(value) for value in client.getCTRL()))
        values = client.getDREFs(list(SCALARS) + list(SURFACE_ARRAYS))

    for name, value in zip(SCALARS, values[: len(SCALARS)]):
        sequence = flat(value)
        print(f"{name}: {sequence[0] if sequence else 'MISSING'}")

    for name, value in zip(SURFACE_ARRAYS, values[len(SCALARS) :]):
        sequence = flat(value)
        active = [(index, item) for index, item in enumerate(sequence) if abs(item) > args.surface_threshold_deg]
        print(f"{name}: length={len(sequence)} nonzero={active}")


if __name__ == "__main__":
    main()
