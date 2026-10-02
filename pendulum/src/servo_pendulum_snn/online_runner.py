from __future__ import annotations

import argparse
import csv
import json
import math
import signal
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

from .controllers import (
    QUBE3_BALANCE_GAIN,
    BalanceControllerConfig,
    HyperLIFResidualBalanceController,
    QuanserBalanceController,
)
from .filters import DerivativeFilter
from .qube_io import DEFAULT_QUANSER_PYTHON, ensure_quanser_python, get_qube_class, read_state, safe_stop_qube
from .types import QubeCommand


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Qube Servo 3 online/virtual-twin pendulum runner.")
    parser.add_argument("--mode", choices=["sensor_check", "balance", "hyperlif_residual"], default="sensor_check")
    parser.add_argument("--version", type=int, choices=[2, 3], default=3)
    parser.add_argument("--id", type=int, default=0)
    parser.add_argument("--hardware", type=int, choices=[0, 1], default=0, help="0=virtual twin, 1=physical Qube.")
    parser.add_argument("--pendulum", type=int, choices=[0, 1], default=1)
    parser.add_argument("--sample-rate", type=float, default=500.0)
    parser.add_argument("--duration", type=float, default=20.0)
    parser.add_argument("--armed", action="store_true", help="Required for any nonzero motor voltage.")
    parser.add_argument("--voltage-limit", type=float, default=5.0)
    parser.add_argument("--capture-angle-deg", type=float, default=10.0)
    parser.add_argument("--command-angle-deg", type=float, default=0.0)
    parser.add_argument("--balance-gains", type=float, nargs=4, default=QUBE3_BALANCE_GAIN.tolist())
    parser.add_argument("--residual-limit", type=float, default=0.75)
    parser.add_argument("--residual-blend", type=float, default=0.25)
    parser.add_argument("--current-bias", type=float, default=0.0)
    parser.add_argument("--current-gain", type=float, default=3.5)
    parser.add_argument("--gate-gain", type=float, default=1.0)
    parser.add_argument("--no-tachometer", action="store_true", help="Use filtered position derivatives instead of tachometer channels.")
    parser.add_argument("--quanser-python", type=Path, default=DEFAULT_QUANSER_PYTHON)
    parser.add_argument("--log-root", type=Path, default=PROJECT_ROOT / "results" / "online")
    parser.add_argument("--log-prefix", type=str, default="qube3")
    parser.add_argument(
        "--led-test",
        action="store_true",
        help="Cycle the Qube's RGB LED through a fixed color sequence at zero motor "
        "voltage, then exit. Ignores --mode/--duration/--armed.",
    )
    parser.add_argument("--led-hold-s", type=float, default=1.0, help="Seconds to hold each LED color during --led-test.")
    return parser.parse_args(argv)


LED_TEST_COLORS: list[tuple[str, np.ndarray]] = [
    ("red", np.array([1.0, 0.0, 0.0])),
    ("green", np.array([0.0, 1.0, 0.0])),
    ("blue", np.array([0.0, 0.0, 1.0])),
    ("yellow", np.array([1.0, 1.0, 0.0])),
    ("cyan", np.array([0.0, 1.0, 1.0])),
    ("magenta", np.array([1.0, 0.0, 1.0])),
    ("white", np.array([1.0, 1.0, 1.0])),
    ("off", np.array([0.0, 0.0, 0.0])),
]


def run_led_test(qube: Any, hold_s: float) -> None:
    print("LED test: motor voltage stays at 0 V throughout.")
    for name, rgb in LED_TEST_COLORS:
        print(f"  LED -> {name:8s} {rgb.tolist()}")
        qube.write_voltage(0.0)
        qube.write_led(rgb)
        time.sleep(max(hold_s, 0.0))


def build_controller(args: argparse.Namespace):
    base = QuanserBalanceController(
        BalanceControllerConfig(
            gains=np.asarray(args.balance_gains, dtype=float),
            voltage_limit=float(args.voltage_limit),
            capture_angle_deg=float(args.capture_angle_deg),
            command_angle_deg=float(args.command_angle_deg),
        )
    )
    if args.mode == "balance":
        return base
    if args.mode == "hyperlif_residual":
        return HyperLIFResidualBalanceController(
            base=base,
            residual_limit=float(args.residual_limit),
            residual_blend=float(args.residual_blend),
            current_bias=float(args.current_bias),
            current_gain=float(args.current_gain),
            gate_gain=float(args.gate_gain),
        )
    return None


def zero_command(control_mode: str) -> QubeCommand:
    return QubeCommand(voltage=0.0, baseline_voltage=0.0, control_mode=control_mode)


def run(args: argparse.Namespace) -> Path:
    ensure_quanser_python(args.quanser_python)
    qube_cls = get_qube_class(args.version)

    sample_rate = float(args.sample_rate)
    sample_time = 1.0 / sample_rate
    args.log_root.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_path = args.log_root / f"{args.log_prefix}_{args.mode}_{timestamp}.csv"

    controller = build_controller(args)
    if controller is not None:
        controller.reset()

    stop_requested = False

    def request_stop(_signum: int | None = None, _frame: Any = None) -> None:
        nonlocal stop_requested
        stop_requested = True
        print("\nStop requested. Sending zero voltage and closing Qube...")

    signal.signal(signal.SIGINT, request_stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, request_stop)

    if args.mode != "sensor_check" and not args.armed:
        print("\nWARNING: closed-loop mode requested without --armed.")
        print("The runner will log sensors and computed states but command zero voltage.\n")

    print("Starting Qube Servo pendulum runner.")
    print(f"Mode: {args.mode}")
    print(f"Hardware flag: {args.hardware} (0=virtual, 1=physical)")
    print(f"Armed: {args.armed}")
    print(f"Log: {log_path}")
    print("Press Ctrl+C to stop safely.")

    fieldnames = [
        "time_s",
        "mode",
        "armed",
        "hardware",
        "control_mode",
        "theta_rad",
        "theta_dot_rad_s",
        "alpha_rad",
        "alpha_dot_rad_s",
        "motor_current_a",
        "amplifier_fault",
        "motor_stall_detected",
        "motor_stall_error",
        "command_voltage",
        "baseline_voltage",
        "residual_voltage",
        "gate_pos",
        "gate_neg",
        "state_json",
        "controller_info_json",
    ]

    qube = None
    theta_filter = DerivativeFilter(bandwidth_rad_s=50.0, sample_time_s=sample_time)
    alpha_filter = DerivativeFilter(bandwidth_rad_s=100.0, sample_time_s=sample_time)

    try:
        qube = qube_cls(
            id=args.id,
            hardware=args.hardware,
            frequency=int(round(sample_rate)),
            pendulum=args.pendulum,
            readMode=1,
        )
        qube.write_voltage(0.0)

        if args.led_test:
            run_led_test(qube, args.led_hold_s)
            safe_stop_qube(qube)
            print("LED test finished safely.")
            return log_path

        with log_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            start = time.time()
            last_loop = start

            while not stop_requested:
                loop_start = time.time()
                elapsed = loop_start - start
                if elapsed > float(args.duration):
                    break

                dt = max(loop_start - last_loop, sample_time)
                last_loop = loop_start

                state = read_state(
                    qube,
                    time_s=elapsed,
                    theta_filter=theta_filter,
                    alpha_filter=alpha_filter,
                    sample_time_s=sample_time,
                    use_tachometer=not args.no_tachometer,
                )

                has_fault = bool(state.amplifier_fault or state.motor_stall_detected or state.motor_stall_error)
                if args.mode == "sensor_check":
                    command = zero_command("sensor_check_zero")
                elif not args.armed:
                    command = zero_command("not_armed_zero_output")
                elif has_fault:
                    command = zero_command("fault_zero_output")
                else:
                    command = controller.compute(state, dt)

                voltage = float(np.clip(command.voltage, -args.voltage_limit, args.voltage_limit))
                qube.write_voltage(voltage)

                writer.writerow(
                    {
                        "time_s": elapsed,
                        "mode": args.mode,
                        "armed": int(bool(args.armed)),
                        "hardware": int(args.hardware),
                        "control_mode": command.control_mode,
                        "theta_rad": state.theta_rad,
                        "theta_dot_rad_s": state.theta_dot_rad_s,
                        "alpha_rad": state.alpha_rad,
                        "alpha_dot_rad_s": state.alpha_dot_rad_s,
                        "motor_current_a": state.motor_current_a,
                        "amplifier_fault": state.amplifier_fault,
                        "motor_stall_detected": state.motor_stall_detected,
                        "motor_stall_error": state.motor_stall_error,
                        "command_voltage": voltage,
                        "baseline_voltage": command.baseline_voltage,
                        "residual_voltage": command.residual_voltage,
                        "gate_pos": command.gate_pos,
                        "gate_neg": command.gate_neg,
                        "state_json": json.dumps(asdict(state)),
                        "controller_info_json": json.dumps(command.info, default=str),
                    }
                )

                print(
                    f"t={elapsed:5.2f}s | {command.control_mode:24s} | "
                    f"theta={state.theta_rad:+.3f} | alpha={math.degrees(state.alpha_rad):+6.2f} deg | "
                    f"V={voltage:+.3f} | res={command.residual_voltage:+.3f}",
                    end="\r",
                    flush=True,
                )

                sleep_time = sample_time - (time.time() - loop_start)
                if sleep_time > 0.0:
                    time.sleep(sleep_time)

    finally:
        print("\nCommanding Qube to zero voltage...")
        safe_stop_qube(qube)
        print(f"Finished safely. Log saved to: {log_path}")

    return log_path


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    run(args)


if __name__ == "__main__":
    main()
