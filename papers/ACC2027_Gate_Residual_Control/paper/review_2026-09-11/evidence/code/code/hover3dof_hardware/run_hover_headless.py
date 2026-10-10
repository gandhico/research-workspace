"""Headless Hover runner; Q8 mode is deliberately zero-output and unarmed."""
from __future__ import annotations

import argparse
import os
from pathlib import Path


HERE = Path(__file__).resolve().parent
CONTROLLERS = (
    "pd", "nengo-pes", "nengo-nef-pes", "nengo-cmg-fixed",
    "nengo-lif-fixed", "nengo-lif-pes",
    "nengo-alif-fixed", "nengo-alif-pes",
    "nengo-izhikevich-fixed", "nengo-izhikevich-pes",
    "nengo-lifrate-fixed", "nengo-lifrate-pes",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--io", choices=("emulated", "q8"), default="emulated")
    parser.add_argument("--controller", choices=CONTROLLERS, required=True)
    parser.add_argument("--mission", choices=("hover", "roll", "full3", "hard45", "hardstep", "yaw360"), required=True)
    parser.add_argument("--duration", type=float, default=25.0)
    parser.add_argument("--disturbance", choices=("none", "hard-pulses"), default="none")
    parser.add_argument("--disturbance-scale", type=float, default=1.0)
    parser.add_argument("--output-root", type=Path, default=HERE / "results" / "disturbance_campaign")
    parser.add_argument("--reference-scale", type=float, default=1.0)
    parser.add_argument("--hardstep-transition-s", type=float, default=0.0)
    parser.add_argument("--allocation-policy", choices=("fixed-bias", "stability-priority"), default="fixed-bias")
    parser.add_argument("--beta", type=float, default=0.2)
    parser.add_argument("--motor-residual-cap-volts", type=float, default=0.2)
    parser.add_argument("--learning-rate", type=float, default=0.0002)
    parser.add_argument("--k-error", type=float, default=2.0)
    parser.add_argument("--k-rate", type=float, default=0.0)
    parser.add_argument("--residual-slew-v-per-s", type=float, default=1.0)
    parser.add_argument("--max-abs-pitch-deg", type=float, default=55.0)
    parser.add_argument("--max-abs-roll-deg", type=float, default=55.0)
    args = parser.parse_args()
    if args.io == "q8" and args.disturbance != "none":
        parser.error("Q8 dry-run mode does not inject emulated disturbances")
    if args.io == "q8" and args.controller not in ("pd", "nengo-pes"):
        print(
            "Connected neuron-family shadow: Q8 outputs remain hard-coded zero; "
            "this is interface/telemetry validation, not closed-loop tracking."
        )
    values = {
        "HOVER_NENGO_IO": args.io,
        "HOVER_NENGO_ARMED": "0",
        "HOVER_NENGO_CONFIRMED": "0",
        "HOVER_NENGO_CONTROLLER": args.controller,
        "HOVER_NENGO_MISSION": args.mission,
        "HOVER_NENGO_DURATION": args.duration,
        "HOVER_NENGO_STOP_AFTER": "",
        "HOVER_NENGO_DISTURBANCE": args.disturbance,
        "HOVER_NENGO_DISTURBANCE_SCALE": args.disturbance_scale,
        "HOVER_NENGO_EMULATION_REALTIME": "0" if args.io == "emulated" else "1",
        "HOVER_NENGO_OUTPUT_ROOT": str(args.output_root.resolve()),
        "HOVER_NENGO_REFERENCE_SCALE": args.reference_scale,
        "HOVER_NENGO_HARDSTEP_TRANSITION": args.hardstep_transition_s,
        "HOVER_NENGO_ALLOCATION": args.allocation_policy,
        "HOVER_NENGO_BETA": args.beta,
        "HOVER_NENGO_MOTOR_CAP": args.motor_residual_cap_volts,
        "HOVER_NENGO_LEARNING_RATE": args.learning_rate,
        "HOVER_NENGO_K_ERROR": args.k_error,
        "HOVER_NENGO_K_RATE": args.k_rate,
        "HOVER_NENGO_RESIDUAL_SLEW": args.residual_slew_v_per_s,
        "HOVER_NENGO_MAX_PITCH": args.max_abs_pitch_deg,
        "HOVER_NENGO_MAX_ROLL": args.max_abs_roll_deg,
    }
    os.environ.update({key: str(value) for key, value in values.items()})
    import hover_nengo_hil_gui as experiment

    if args.io == "q8":
        print(
            "Q8 sensor/dry-run mode: armed=False is hard-coded; all four DAC "
            "outputs are written as zero on every step and again in finally."
        )
    experiment.WORKER._run()
    if experiment.WORKER.output_dir is None:
        raise SystemExit("run produced no output directory")
    print(f"OUTPUT={experiment.WORKER.output_dir}")


if __name__ == "__main__":
    main()
