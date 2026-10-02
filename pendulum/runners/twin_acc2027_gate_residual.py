"""ACC 2027 gate-state residual experiments on the QLabs QUBE Servo 3 twin.

This runner deliberately imports the canonical ``GateStateAugmentor`` from the
ACC 2027 repository.  It therefore exercises the same fixed-conductance,
adaptive-conductance, and online-PES implementations used by the MuJoCo drone
experiments instead of maintaining a pendulum-specific copy.

Only the upright balance controller is augmented.  Energy swing-up remains
classical.  Except for the explicitly labelled ``legacy-blend`` ablation, the
command is baseline preserving::

    v = sat(v_lqr + v_res, +/- V_bal)
    |v_res| <= residual_cap_v

QLabs is selected with ``hardware=0``.  This file never opens physical QUBE
hardware.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import socket
import sys
import time

import numpy as np


HERE = Path(__file__).resolve()
PENDULUM_ROOT = HERE.parents[1]
DEFAULT_ACC_ROOT = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control")
DEFAULT_PYTHON = Path(
    r"C:\Users\gandhico\AppData\Local\miniconda3\envs\hyperlif\python.exe"
)


def _first_existing(candidates: list[Path]) -> Path | None:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def configure_imports(acc_root: Path, pal_path: Path | None) -> Path:
    """Add the portable local source roots and return the PAL path in use."""
    acc_src = acc_root / "src"
    if not (acc_src / "gra_control" / "gate.py").exists():
        raise FileNotFoundError(
            f"ACC controller source not found at {acc_src}. Use --acc-root."
        )
    sys.path.insert(0, str(acc_src))

    selected = pal_path or _first_existing(
        [
            Path(os.environ["QUANSER_PAL_PYTHON"])
            if os.environ.get("QUANSER_PAL_PYTHON")
            else Path("__not_set__"),
            Path.home()
            / "Documents"
            / "Quanser_Academic_Resources_tmp"
            / "0_libraries"
            / "python",
            Path(r"C:\Quanser\0_libraries\python"),
        ]
    )
    if selected is None or not (selected / "pal" / "products" / "qube.py").exists():
        raise FileNotFoundError(
            "Quanser PAL qube.py was not found. Set QUANSER_PAL_PYTHON or use --pal-path."
        )
    sys.path.insert(0, str(selected))
    return selected.resolve()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def wrap_to_pi(value: float) -> float:
    return float((value + np.pi) % (2.0 * np.pi) - np.pi)


def scalar(value: object) -> float:
    return float(np.asarray(value, dtype=float).reshape(-1)[0])


def port_open(host: str = "127.0.0.1", port: int = 18923) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


def settle_and_reference(
    qube: object,
    dt: float,
    timeout_s: float = 30.0,
    window_s: float = 1.5,
    position_span_deg: float = 0.5,
) -> tuple[float, bool, float]:
    """Find the hanging reference from position stability, not tachometer bias."""
    samples: list[tuple[float, float]] = []
    started = time.perf_counter()
    while time.perf_counter() - started < timeout_s:
        qube.read_outputs()
        qube.write_voltage(0.0)
        now = time.perf_counter()
        raw = scalar(qube.pendulumPosition)
        samples.append((now, raw))
        samples = [(t, a) for t, a in samples if now - t <= window_s]
        # The sliding-window prune occurs before this test, so demanding exactly
        # ``window_s`` can be impossible under normal scheduler jitter.  Two
        # samples of tolerance preserves the physical test while avoiding a
        # false timeout at 500 Hz.
        if len(samples) > 50 and now - samples[0][0] >= window_s - 2.0 * dt:
            angles = np.unwrap(np.asarray([a for _, a in samples]))
            if np.ptp(angles) <= np.radians(position_span_deg):
                return wrap_to_pi(float(np.median(angles))), True, now - started
        time.sleep(dt)
    return wrap_to_pi(scalar(qube.pendulumPosition)), False, time.perf_counter() - started


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the canonical ACC 2027 residual controller on the QLabs QUBE twin."
    )
    parser.add_argument(
        "--controller",
        choices=[
            "classical",
            "fixed-residual",
            "adaptive-residual",
            "online-pes-fixed",
            "online-pes-adaptive",
            "legacy-blend",
        ],
        default="classical",
    )
    parser.add_argument("--duration", type=float, default=30.0)
    parser.add_argument(
        "--balance-duration",
        type=float,
        help="If set, stop after this many accumulated balance seconds instead of a fixed wall duration.",
    )
    parser.add_argument(
        "--max-duration",
        type=float,
        default=90.0,
        help="Wall-time safety timeout when --balance-duration is used.",
    )
    parser.add_argument("--frequency", type=int, default=500)
    parser.add_argument("--voltage-limit", type=float, default=5.0)
    parser.add_argument("--residual-cap-v", type=float, default=0.35)
    parser.add_argument("--learning-rate", type=float, default=8e-4)
    parser.add_argument("--k-error", type=float, default=1.0)
    parser.add_argument("--k-rate", type=float, default=0.30)
    parser.add_argument("--gate-gain", type=float, default=1e5)
    parser.add_argument("--current-bias", type=float, default=0.75)
    parser.add_argument("--current-gain", type=float, default=1.25)
    parser.add_argument("--acc-root", type=Path, default=DEFAULT_ACC_ROOT)
    parser.add_argument("--pal-path", type=Path)
    parser.add_argument("--output-root", type=Path, default=PENDULUM_ROOT / "results" / "acc2027_twin")
    parser.add_argument("--label", default="nominal")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.duration <= 0 or args.frequency <= 0 or args.max_duration <= 0:
        raise ValueError("duration and frequency must be positive")
    if args.balance_duration is not None and args.balance_duration <= 0:
        raise ValueError("balance-duration must be positive")
    if not 0.0 <= args.residual_cap_v <= args.voltage_limit:
        raise ValueError("residual-cap-v must be in [0, voltage-limit]")

    pal_path = configure_imports(args.acc_root.resolve(), args.pal_path)
    from gra_control.gate import GateStateAugmentor, HyperLIFConfig
    from pal.products.qube import QubeServo3

    dt = 1.0 / args.frequency
    voltage_limit = float(args.voltage_limit)
    beta = float(args.residual_cap_v / voltage_limit)
    gains = np.array([-1.000, 26.72, -0.8269, 2.214], dtype=float)
    capture_rad = np.radians(20.0)
    capture_rate = 6.0
    capture_arm = np.radians(110.0)
    hold_rad = np.radians(35.0)

    # QUBE 3 energy swing-up parameters retained from the validated July twin.
    mu, swing_limit, center_gain = 100.0, 10.0, 1.0
    resistance, torque_constant = 7.5, 0.0422
    arm_mass, arm_radius = 0.095, 0.085
    pend_mass, pend_length, gravity = 0.024, 0.129, 9.81
    pend_com = pend_length / 2.0
    pend_inertia = pend_mass * pend_length**2 / 12.0
    upright_energy = 2.0 * pend_mass * gravity * pend_com
    max_accel = (torque_constant * 10.0 / resistance) / (arm_mass * arm_radius)
    accel_to_voltage = arm_mass * arm_radius * resistance / torque_constant

    mode = "blend" if args.controller == "legacy-blend" else (
        "online_pes" if args.controller.startswith("online-pes") else "residual"
    )
    adaptive = args.controller in {"adaptive-residual", "online-pes-adaptive"}
    augmentor = None
    if args.controller != "classical":
        config = HyperLIFConfig(
            gate_gain=args.gate_gain,
            current_bias=args.current_bias,
            current_gain=args.current_gain,
        )
        augmentor = GateStateAugmentor(
            channels=1,
            limits=np.array([voltage_limit]),
            mode=mode,
            adaptive_conductance=adaptive,
            beta=beta,
            learning_rate=args.learning_rate,
            cfg=config,
        )

    print("=" * 78)
    print(
        f"QLABS QUBE3 ACC2027 | {args.controller} | duration={args.duration:g}s | "
        f"residual_cap={args.residual_cap_v:g} V"
    )
    print("=" * 78)
    print(f"PAL: {pal_path}")
    print(f"ACC source: {args.acc_root.resolve()}")
    print(f"TCP preflight 127.0.0.1:18923 = {port_open()}")

    qube = QubeServo3(
        id=0, hardware=0, frequency=args.frequency, pendulum=1, readMode=1
    )
    if not qube.card.is_valid():
        qube.terminate()
        raise RuntimeError("QLabs virtual card is invalid. Start the QUBE3 pendulum scene.")

    yellow = np.array([1.0, 1.0, 0.0])
    blue = np.array([0.0, 0.0, 1.0])
    red = np.array([1.0, 0.0, 0.0])
    qube.write_led(yellow)
    rest_raw, settled, settle_s = settle_and_reference(qube, dt)
    print(
        f"reference: raw_hanging={rest_raw:+.5f} rad, settled={settled}, "
        f"settle_time={settle_s:.2f}s"
    )
    if not settled:
        qube.terminate()
        raise RuntimeError("Pendulum did not settle; run aborted before applying voltage.")

    rows: list[dict[str, float | int | str]] = []
    previous_mode = -1
    capture_time: float | None = None
    longest_hold = 0
    hold_samples = 0
    balance_samples_total = 0
    started = time.perf_counter()
    previous_t = started
    next_t = started + dt

    try:
        while True:
            qube.read_outputs()
            now = time.perf_counter()
            elapsed = now - started
            wall_limit = args.max_duration if args.balance_duration is not None else args.duration
            if elapsed >= wall_limit:
                break
            if (
                args.balance_duration is not None
                and balance_samples_total >= int(args.balance_duration * args.frequency)
            ):
                break
            measured_dt = now - previous_t
            previous_t = now

            theta = scalar(qube.motorPosition)
            alpha = wrap_to_pi(scalar(qube.pendulumPosition) - rest_raw - np.pi)
            theta_rate = scalar(qube.motorSpeed)
            alpha_rate = scalar(qube.pendulumSpeed)

            captured = (
                abs(alpha) <= capture_rad
                and abs(alpha_rate) <= capture_rate
                and abs(theta) <= capture_arm
            )
            balancing = captured or (previous_mode == 1 and abs(alpha) <= hold_rad)
            baseline = residual = command = 0.0
            target = gate_mean = gate_std = activity_mean = activity_std = np.nan

            if balancing:
                mode_now = 1
                hold_samples += 1
                balance_samples_total += 1
                longest_hold = max(longest_hold, hold_samples)
                if capture_time is None:
                    capture_time = elapsed
                state = np.array([theta, alpha, theta_rate, alpha_rate])
                baseline = float(np.clip(gains @ state, -voltage_limit, voltage_limit))
                command = baseline
                if augmentor is not None:
                    # Positive alpha requires positive voltage for the validated gain
                    # convention.  The normalized target is therefore sign-consistent
                    # with the classical stabilizing action.
                    target = float(
                        np.clip(
                            args.k_error * alpha / capture_rad
                            + args.k_rate * alpha_rate / capture_rate,
                            -1.0,
                            1.0,
                        )
                    )
                    output = augmentor.step(
                        np.array([baseline]), dt, np.array([target])
                    )
                    command = float(output.command[0])
                    residual = float(output.residual[0])
                    gate_mean = float(np.mean(output.gate))
                    gate_std = float(np.std(output.gate))
                    activity_mean = float(np.mean(output.activity))
                    activity_std = float(np.std(output.activity))
                error_ratio = float(np.clip(abs(alpha) / capture_rad, 0.0, 1.0))
                led = np.array([error_ratio, 1.0 - error_ratio, 0.0])
            else:
                mode_now = 0
                hold_samples = 0
                energy = (
                    0.5 * pend_inertia * alpha_rate**2
                    + pend_mass * gravity * pend_com * (1.0 + np.cos(alpha))
                )
                acceleration = float(
                    np.clip(
                        mu * (energy - upright_energy) * np.sign(alpha_rate * np.cos(alpha))
                        - center_gain * theta,
                        -max_accel,
                        max_accel,
                    )
                )
                baseline = float(np.clip(accel_to_voltage * acceleration, -swing_limit, swing_limit))
                command = baseline
                led = blue

            qube.write_voltage(command)
            if mode_now != previous_mode or mode_now == 1:
                qube.write_led(led)
            previous_mode = mode_now

            rows.append(
                {
                    "t": elapsed,
                    "dt": measured_dt,
                    "phase": "balance" if mode_now else "swingup",
                    "mode": mode_now,
                    "theta_rad": theta,
                    "alpha_rad": alpha,
                    "theta_rate_rad_s": theta_rate,
                    "alpha_rate_rad_s": alpha_rate,
                    "baseline_v": baseline,
                    "residual_v": residual,
                    "command_v": command,
                    "learning_target": target,
                    "gate_mean": gate_mean,
                    "gate_std": gate_std,
                    "activity_mean": activity_mean,
                    "activity_std": activity_std,
                    "motor_current_a": scalar(qube.motorCurrent),
                    "amplifier_fault": int(scalar(qube.amplifierFault)),
                    "stall_detected": int(scalar(qube.motorStallDetected)),
                }
            )
            remaining = next_t - time.perf_counter()
            if remaining > 0:
                time.sleep(remaining)
            next_t += dt
    finally:
        qube.write_voltage(0.0)
        qube.write_led(red)
        qube.terminate()
        print("shutdown: 0 V, LED red, virtual amplifier disabled, card closed")

    if not rows:
        raise RuntimeError("No samples were recorded")
    balance_rows = [row for row in rows if row["mode"] == 1]
    tail_count = min(len(rows), int(5.0 * args.frequency))
    tail_rows = rows[-tail_count:]
    tail_balance = [row for row in tail_rows if row["mode"] == 1]

    def rms(values: list[float]) -> float | None:
        return float(np.sqrt(np.mean(np.square(values)))) if values else None

    alpha_tail = [float(row["alpha_rad"]) for row in tail_balance]
    command_balance = [float(row["command_v"]) for row in balance_rows]
    residual_balance = [float(row["residual_v"]) for row in balance_rows]
    activity_std_values = [
        float(row["activity_std"])
        for row in balance_rows
        if np.isfinite(float(row["activity_std"]))
    ]
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    run_dir = args.output_root.resolve() / f"{timestamp}_{args.label}_{args.controller}"
    run_dir.mkdir(parents=True, exist_ok=False)
    csv_path = run_dir / "trace.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    gate_source = args.acc_root.resolve() / "src" / "gra_control" / "gate.py"
    summary = {
        "status": "valid" if capture_time is not None else "no_capture",
        "platform": "Quanser QUBE Servo 3 QLabs virtual twin",
        "hardware_flag": 0,
        "controller": args.controller,
        "architecture": mode if augmentor is not None else "classical_lqr",
        "adaptive_conductance": adaptive if augmentor is not None else None,
        "online_decoder_adaptation": args.controller.startswith("online-pes"),
        "requested_wall_duration_s": args.duration if args.balance_duration is None else None,
        "requested_balance_duration_s": args.balance_duration,
        "max_wall_duration_s": args.max_duration if args.balance_duration is not None else args.duration,
        "actual_wall_duration_s": float(rows[-1]["t"]),
        "actual_balance_duration_s": len(balance_rows) / args.frequency,
        "target_frequency_hz": args.frequency,
        "realized_frequency_hz": float(1.0 / np.mean(np.diff([float(r["t"]) for r in rows]))),
        "settled_before_run": settled,
        "settle_time_s": settle_s,
        "hanging_reference_raw_rad": rest_raw,
        "first_capture_s": capture_time,
        "longest_balance_hold_s": longest_hold / args.frequency,
        "balance_fraction_total": len(balance_rows) / len(rows),
        "balance_fraction_tail_5s": len(tail_balance) / len(tail_rows),
        "alpha_rms_tail_deg": None if not alpha_tail else float(np.degrees(rms(alpha_tail))),
        "alpha_abs_mean_tail_deg": None if not alpha_tail else float(np.degrees(np.mean(np.abs(alpha_tail)))),
        "alpha_abs_max_tail_deg": None if not alpha_tail else float(np.degrees(np.max(np.abs(alpha_tail)))),
        "command_rms_balance_v": rms(command_balance),
        "residual_rms_balance_v": rms(residual_balance),
        "command_saturation_fraction_balance": (
            None
            if not command_balance
            else float(np.mean(np.abs(command_balance) >= voltage_limit - 1e-9))
        ),
        "activity_std_mean_balance": (
            None if not activity_std_values else float(np.mean(activity_std_values))
        ),
        "decoder_weights_final": None if augmentor is None else augmentor.W.tolist(),
        "amplifier_fault_samples": int(sum(int(r["amplifier_fault"]) for r in rows)),
        "stall_samples": int(sum(int(r["stall_detected"]) for r in rows)),
        "voltage_limit_v": voltage_limit,
        "residual_cap_v": args.residual_cap_v,
        "beta": beta,
        "learning_rate": args.learning_rate,
        "k_error": args.k_error,
        "k_rate": args.k_rate,
        "gate_gain": args.gate_gain,
        "current_bias": args.current_bias,
        "current_gain": args.current_gain,
        "lqr_gains": gains.tolist(),
        "pal_path": str(pal_path),
        "acc_root": str(args.acc_root.resolve()),
        "controller_source": str(gate_source),
        "controller_source_sha256": sha256(gate_source),
        "runner_source_sha256": sha256(HERE),
        "python_executable": sys.executable,
        "trace": str(csv_path),
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"saved: {run_dir}")


if __name__ == "__main__":
    main()
