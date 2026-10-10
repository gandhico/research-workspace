from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from gra_control.platforms.drone import run_drone
from gra_control.platforms.hardware import HARDWARE, hardware_status
from gra_control.platforms.surrogate import run_surrogate


ROOT = Path(__file__).resolve().parents[2]
CONTROLLERS = [
    "classical", "fixed-residual", "adaptive-residual", "legacy-blend",
    "online-pes", "online-pes-fixed", "online-pes-adaptive",
]


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="CMG residual augmentation experiment launcher")
    sub = p.add_subparsers(dest="command", required=True)
    sim = sub.add_parser("simulate", help="run one MuJoCo experiment")
    sim.add_argument("--platform", choices=["cf2", "cf2-rotor", "x2", "pendulum", "hover3dof", "qcar"], required=True)
    sim.add_argument("--controller", choices=CONTROLLERS, default="classical")
    sim.add_argument("--mission", choices=["hover", "roll", "full3", "hard45", "hardstep", "yaw360"], default="hard45")
    sim.add_argument("--duration", type=float, default=5.0)
    sim.add_argument("--dt", type=float, default=0.001)
    sim.add_argument("--beta", type=float, default=0.20)
    sim.add_argument("--learning-rate", type=float, default=8e-4)
    sim.add_argument("--k-error", type=float, default=8.0)
    sim.add_argument("--k-rate", type=float, default=0.0)
    sim.add_argument("--torque-policy", choices=["model", "inertia", "legacy-learned"], default="model")
    sim.add_argument("--actuator-scale", type=float, default=1.0,
                     help="Declared rotor maximum-thrust multiplier; rotor platforms only.")
    sim.add_argument("--initial-angle-deg", type=float, default=0.0)
    sim.add_argument("--disturbance-torque", type=float, default=0.0,
                     help="Sinusoidal body-disturbance torque amplitude in N m.")
    sim.add_argument("--attitude-noise-std", type=float, default=0.0,
                     help="Per-axis attitude measurement noise standard deviation in rad.")
    sim.add_argument("--rate-noise-std", type=float, default=0.0,
                     help="Per-axis angular-rate noise standard deviation in rad/s.")
    sim.add_argument("--seed", type=int, default=1)
    sim.add_argument("--output", type=Path)

    hw = sub.add_parser("hardware-status", help="show safe hardware integration status; never arms hardware")
    hw.add_argument("--platform", choices=sorted(HARDWARE), required=True)
    return p


def main() -> None:
    args = parser().parse_args()
    if args.command == "hardware-status":
        print(json.dumps(hardware_status(args.platform), indent=2))
        return

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = args.output or ROOT/"results"/"runs"/f"{stamp}_{args.platform}_{args.controller}"
    if args.platform in {"cf2", "cf2-rotor", "x2"}:
        result = run_drone(args.platform, args.controller, args.mission, args.duration, args.dt,
                           args.beta, args.torque_policy, args.learning_rate, args.k_error,
                           args.k_rate, args.actuator_scale, args.initial_angle_deg,
                           args.disturbance_torque, args.attitude_noise_std,
                           args.rate_noise_std, args.seed, output)
    else:
        result = run_surrogate(args.platform, args.controller, args.duration, args.dt, args.beta, output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
