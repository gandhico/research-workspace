"""Safe launcher for the live Nengo/Quanser 3DOF Hover dashboard."""
from __future__ import annotations

import argparse
import os
import sys
import warnings
from pathlib import Path


HERE = Path(__file__).resolve().parent
CONTROLLERS = (
    "pd", "nengo-pes", "nengo-nef-pes", "nengo-cmg-fixed",
    "nengo-lif-fixed", "nengo-lif-pes",
    "nengo-alif-fixed", "nengo-alif-pes",
    "nengo-izhikevich-fixed", "nengo-izhikevich-pes",
    "nengo-lifrate-fixed", "nengo-lifrate-pes",
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--io", choices=("emulated", "q8"), default="emulated")
    parser.add_argument("--armed", action="store_true")
    parser.add_argument("--confirm-hardware-review", action="store_true")
    parser.add_argument("--controller", choices=CONTROLLERS, default="pd")
    parser.add_argument("--mission", choices=("hover", "roll", "full3", "hard45", "hardstep", "yaw360"), default="hover")
    parser.add_argument("--duration", type=float, default=5.0)
    parser.add_argument("--stop-after", type=float)
    parser.add_argument("--reference-scale", type=float, default=1.0)
    parser.add_argument("--hardstep-transition-s", type=float, default=0.0)
    parser.add_argument("--beta", type=float, default=0.5)
    parser.add_argument("--motor-residual-cap-volts", type=float, default=0.3)
    parser.add_argument("--learning-rate", type=float, default=8e-4)
    parser.add_argument("--k-error", type=float, default=8.0)
    parser.add_argument("--k-rate", type=float, default=0.0)
    parser.add_argument("--residual-slew-v-per-s", type=float, default=4.0)
    parser.add_argument("--allocation-policy", choices=("fixed-bias", "stability-priority"), default="fixed-bias")
    parser.add_argument("--motor-floor-volts", type=float, default=2.0)
    parser.add_argument("--expected-raw-home-yaw-deg", type=float)
    parser.add_argument("--raw-home-yaw-tolerance-deg", type=float, default=5.0)
    parser.add_argument("--max-encoder-step-deg", type=float, default=5.0)
    parser.add_argument("--max-abs-pitch-deg", type=float, default=55.0)
    parser.add_argument("--max-abs-roll-deg", type=float, default=55.0)
    parser.add_argument("--max-consecutive-deadline-misses", type=int, default=20)
    parser.add_argument("--gui-heartbeat-timeout", type=float, default=0.5)
    parser.add_argument("--port", type=int, default=8081)
    parser.add_argument(
        "--gui-password",
        help="Optional local Nengo GUI password (avoids the one-time-token login flow).",
    )
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--auto-shutdown", type=float, default=2.0)
    parser.add_argument("--disturbance", choices=("none", "hard-pulses"), default="none")
    parser.add_argument("--disturbance-scale", type=float, default=1.0)
    parser.add_argument("--fast-emulation", action="store_true", help="Run emulation without wall-clock sleeping; not useful for live viewing.")
    parser.add_argument("--output-root", type=Path, help="Optional result root for this GUI session.")
    args = parser.parse_args()

    if args.armed and args.io != "q8":
        parser.error("--armed requires --io q8")
    if args.armed and not args.confirm_hardware_review:
        parser.error("--armed requires --confirm-hardware-review after the lab runbook")
    if args.armed and args.controller not in ("pd", "nengo-pes"):
        parser.error(
            "only qualified pd and nengo-pes controllers may be armed; "
            "all other neuron families are emulation or zero-output shadow only"
        )
    if args.gui_heartbeat_timeout < 0.2:
        parser.error("--gui-heartbeat-timeout must be at least 0.2 s")

    values = {
        "HOVER_NENGO_IO": args.io,
        "HOVER_NENGO_ARMED": int(args.armed),
        "HOVER_NENGO_CONFIRMED": int(args.confirm_hardware_review),
        "HOVER_NENGO_CONTROLLER": args.controller,
        "HOVER_NENGO_MISSION": args.mission,
        "HOVER_NENGO_DURATION": args.duration,
        "HOVER_NENGO_STOP_AFTER": "" if args.stop_after is None else args.stop_after,
        "HOVER_NENGO_REFERENCE_SCALE": args.reference_scale,
        "HOVER_NENGO_HARDSTEP_TRANSITION": args.hardstep_transition_s,
        "HOVER_NENGO_BETA": args.beta,
        "HOVER_NENGO_MOTOR_CAP": args.motor_residual_cap_volts,
        "HOVER_NENGO_LEARNING_RATE": args.learning_rate,
        "HOVER_NENGO_K_ERROR": args.k_error,
        "HOVER_NENGO_K_RATE": args.k_rate,
        "HOVER_NENGO_RESIDUAL_SLEW": args.residual_slew_v_per_s,
        "HOVER_NENGO_ALLOCATION": args.allocation_policy,
        "HOVER_NENGO_MOTOR_FLOOR": args.motor_floor_volts,
        "HOVER_NENGO_EXPECTED_HOME_YAW": "" if args.expected_raw_home_yaw_deg is None else args.expected_raw_home_yaw_deg,
        "HOVER_NENGO_HOME_TOLERANCE": args.raw_home_yaw_tolerance_deg,
        "HOVER_NENGO_MAX_ENCODER_STEP_DEG": args.max_encoder_step_deg,
        "HOVER_NENGO_MAX_PITCH": args.max_abs_pitch_deg,
        "HOVER_NENGO_MAX_ROLL": args.max_abs_roll_deg,
        "HOVER_NENGO_MAX_MISSES": args.max_consecutive_deadline_misses,
        "HOVER_NENGO_HEARTBEAT_TIMEOUT": args.gui_heartbeat_timeout,
        "HOVER_NENGO_DISTURBANCE": args.disturbance,
        "HOVER_NENGO_DISTURBANCE_SCALE": args.disturbance_scale,
        "HOVER_NENGO_EMULATION_REALTIME": int(not args.fast_emulation),
    }
    if args.output_root is not None:
        values["HOVER_NENGO_OUTPUT_ROOT"] = args.output_root.resolve()
    for key, value in values.items():
        os.environ[key] = str(value)

    os.chdir(HERE)
    sys.path.insert(0, str(HERE))
    gui_args = [
        "nengo_gui",
        "--backend", "nengo_gui_backend_50hz",
        "--port", str(args.port),
        "--auto-shutdown", str(args.auto_shutdown),
    ]
    if args.gui_password:
        gui_args.extend(("--password", args.gui_password))
    if args.no_browser:
        gui_args.append("--no-browser")
    gui_args.append(str(HERE / "hover_nengo_hil_gui.py"))
    sys.argv = gui_args
    warnings.filterwarnings("ignore", message="Install the jedi module.*")

    print(
        f"Preparing GUI: io={args.io} armed={args.armed} controller={args.controller} "
        f"mission={args.mission}. Control begins only when the browser loads the model."
    )
    import nengo_gui

    try:
        nengo_gui.main()
    except KeyboardInterrupt:
        print("Nengo GUI stopped by operator; shutdown hooks force Q8 output to zero.")


if __name__ == "__main__":
    main()
