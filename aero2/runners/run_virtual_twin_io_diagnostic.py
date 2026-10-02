"""Open-loop PAL/QLabs Aero2 I/O diagnostic.

This runner is intentionally small and direct: it bypasses controllers and sends
known voltage pulses through ``VirtualTwinBackend`` while logging angles, rates,
raw encoder counts, and motor voltages. Use it to determine whether a loaded
QLabs Aero2 asset is pitch-only or true 2-DOF.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from aero2.execution.virtual_twin import DEFAULT_QUANSER_PYTHON, VirtualTwinBackend


TESTS = {
    "pitch": ("mixed", np.array([1.0, 0.0], dtype=float)),
    "yaw": ("mixed", np.array([0.0, 1.0], dtype=float)),
    "direct0": ("direct", np.array([1.0, 0.0], dtype=float)),
    "direct1": ("direct", np.array([0.0, 1.0], dtype=float)),
    "direct_both": ("direct", np.array([1.0, 1.0], dtype=float)),
}


def pulse_value(t: float, amp: float) -> float:
    """Return a short +/0/-/0 diagnostic pulse profile."""
    if t < 0.50:
        return 0.0
    if t < 1.50:
        return amp
    if t < 2.00:
        return 0.0
    if t < 3.00:
        return -amp
    return 0.0


def vector_raw(raw: dict, key: str, size: int) -> list[float]:
    value = raw.get(key, np.zeros(size))
    arr = np.asarray(value, dtype=float).reshape(-1)
    out = np.zeros(size, dtype=float)
    out[: min(size, arr.size)] = arr[:size]
    return out.tolist()


def _summarize_flat(rows: list[dict]) -> dict:
    theta = np.array([r["theta"] for r in rows], dtype=float)
    psi = np.array([r["psi"] for r in rows], dtype=float)
    theta_dot = np.array([r["theta_dot"] for r in rows], dtype=float)
    psi_dot = np.array([r["psi_dot"] for r in rows], dtype=float)
    enc3 = np.array([r["enc3"] for r in rows], dtype=float)
    motor1 = np.array([r["motor1_v"] for r in rows], dtype=float)
    return {
        "samples": len(rows),
        "duration_s": float(rows[-1]["t"] - rows[0]["t"]) if len(rows) > 1 else 0.0,
        "theta_range_rad": float(theta.max() - theta.min()) if rows else 0.0,
        "psi_range_rad": float(psi.max() - psi.min()) if rows else 0.0,
        "theta_dot_peak_abs": float(np.max(np.abs(theta_dot))) if rows else 0.0,
        "psi_dot_peak_abs": float(np.max(np.abs(psi_dot))) if rows else 0.0,
        "yaw_encoder_count_range": float(enc3.max() - enc3.min()) if rows else 0.0,
        "motor1_command_peak_abs": float(np.max(np.abs(motor1))) if rows else 0.0,
        "pitch_motion_detected": bool((theta.max() - theta.min()) >= 0.02) if rows else False,
        "yaw_motion_detected": bool((psi.max() - psi.min()) >= 0.02 or (enc3.max() - enc3.min()) >= 2) if rows else False,
    }


def summarize(rows: list[dict]) -> dict:
    summary = _summarize_flat(rows)
    test_names = sorted({str(r.get("test")) for r in rows if r.get("test") is not None})
    if test_names:
        per_test = {
            name: _summarize_flat([r for r in rows if str(r.get("test")) == name])
            for name in test_names
        }
        summary["per_test"] = per_test
        if len(test_names) > 1:
            summary["duration_s"] = float(sum(s["duration_s"] for s in per_test.values()))
    return summary


def run_one_test(args, test_name: str, backend: VirtualTwinBackend) -> list[dict]:
    output_mode, command_axis = TESTS[test_name]
    backend.output_mode = output_mode
    rows: list[dict] = []
    dt = 1.0 / float(args.hz)
    start = time.perf_counter()
    next_tick = start

    while True:
        now = time.perf_counter()
        t = now - start
        if t > args.duration:
            break

        command = command_axis * pulse_value(t, args.voltage)
        backend.apply(command)
        meas = backend.read()
        raw = meas.raw
        motor_v = vector_raw(raw, "motor_voltage", 2)
        encoder = vector_raw(raw, "encoder_counts", 4)
        motor_speed = vector_raw(raw, "motor_speed", 2)
        rows.append(
            {
                "test": test_name,
                "t": float(t),
                "output_mode": output_mode,
                "virtual_pitch": float(command[0]),
                "virtual_yaw": float(command[1]),
                "motor0_v": motor_v[0],
                "motor1_v": motor_v[1],
                "theta": float(meas.theta),
                "psi": float(meas.psi),
                "theta_dot": float(0.0 if meas.theta_dot is None else meas.theta_dot),
                "psi_dot": float(0.0 if meas.psi_dot is None else meas.psi_dot),
                "enc0": encoder[0],
                "enc1": encoder[1],
                "enc2": encoder[2],
                "enc3": encoder[3],
                "motor0_speed": motor_speed[0],
                "motor1_speed": motor_speed[1],
            }
        )

        next_tick += dt
        sleep_s = next_tick - time.perf_counter()
        if sleep_s > 0.0:
            time.sleep(sleep_s)

    backend.apply(np.zeros(2))
    time.sleep(0.05)
    return rows


def save_outputs(rows: list[dict], summary: dict, cfg: dict) -> Path:
    out_dir = REPO / cfg.get("out", "results")
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tag = f"virtual_twin_io_{cfg['test']}_{stamp}"
    csv_path = out_dir / f"{tag}.csv"
    json_path = out_dir / f"{tag}.json"

    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    json_path.write_text(json.dumps({"config": cfg, "summary": summary, "csv": str(csv_path)}, indent=2))
    return json_path


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description="Run open-loop Aero2 PAL/QLabs I/O diagnostics.")
    p.add_argument("--test", choices=[*TESTS.keys(), "all"], default="yaw")
    p.add_argument("--duration", type=float, default=3.5)
    p.add_argument("--hz", type=float, default=200.0)
    p.add_argument("--voltage", type=float, default=3.0)
    p.add_argument("--voltage-limit", type=float, default=15.0)
    p.add_argument("--aero-id", default="0")
    p.add_argument("--read-mode", type=int, default=1)
    p.add_argument("--quanser-python", default=str(DEFAULT_QUANSER_PYTHON))
    p.add_argument("--out", default="results")
    p.add_argument("--save", action="store_true")
    args = p.parse_args(argv)

    tests = list(TESTS) if args.test == "all" else [args.test]
    backend = VirtualTwinBackend(
        aero_id=args.aero_id,
        frequency=float(args.hz),
        read_mode=int(args.read_mode),
        output_mode="mixed",
        voltage_limit=float(args.voltage_limit),
        quanser_python=args.quanser_python,
    )

    rows: list[dict] = []
    try:
        backend.reset(np.zeros(4))
        for test_name in tests:
            print(f"running {test_name} pulse diagnostic...")
            rows.extend(run_one_test(args, test_name, backend))
    finally:
        backend.close()

    summary = summarize(rows)
    cfg = {k: v for k, v in vars(args).items() if k != "save"}
    print("[Aero2 virtual-twin I/O diagnostic]")
    print(f"  tests={','.join(tests)} samples={summary['samples']} duration={summary['duration_s']:.2f}s")
    print(f"  theta_range={summary['theta_range_rad']:.4f} rad  psi_range={summary['psi_range_rad']:.4f} rad")
    print(f"  theta_dot_peak={summary['theta_dot_peak_abs']:.4f}  psi_dot_peak={summary['psi_dot_peak_abs']:.4f} rad/s")
    print(f"  yaw_encoder_count_range={summary['yaw_encoder_count_range']:.1f}")
    print(f"  pitch_motion_detected={summary['pitch_motion_detected']}  yaw_motion_detected={summary['yaw_motion_detected']}")
    if "per_test" in summary and len(summary["per_test"]) > 1:
        for name, item in summary["per_test"].items():
            print(
                f"  {name}: theta_range={item['theta_range_rad']:.4f} "
                f"psi_range={item['psi_range_rad']:.4f} "
                f"enc3_range={item['yaw_encoder_count_range']:.1f}"
            )
    if args.save:
        saved = save_outputs(rows, summary, cfg)
        print(f"  saved -> {saved.relative_to(REPO)}")


if __name__ == "__main__":
    main()
