#!/usr/bin/env python3
"""Identify a first-order pitch-rate model from EHEKATL XP12 CSV logs."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


def finite(value: float) -> bool:
    return math.isfinite(value)


def read_float(row: dict[str, str], name: str) -> float:
    try:
        return float(row[name])
    except Exception:
        return math.nan


def read_first_float(row: dict[str, str], names: tuple[str, ...]) -> float:
    for name in names:
        value = read_float(row, name)
        if finite(value):
            return value
    return math.nan


def read_log(path: Path) -> list[dict[str, float | str]]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    parsed: list[dict[str, float | str]] = []
    for row in rows:
        parsed.append(
            {
                "t": read_float(row, "elapsed_s"),
                "pitch": read_float(row, "pitch_deg"),
                "q": read_float(row, "pitch_rate_deg_s"),
                "u": read_first_float(row, ("actual_elevator_delta", "elevator_stick")),
                "ctrl0": read_float(row, "ctrl_0"),
                "ctrl1": read_float(row, "ctrl_1"),
                "engaged": row.get("engaged", ""),
                "axis": row.get("axis", ""),
                "stop_reason": row.get("stop_reason", ""),
            }
        )
    return parsed


def least_squares_2x2(samples: list[tuple[float, float, float]]) -> tuple[float, float, float]:
    """Fit y = a*x1 + b*x2 and return (a, b, rms_residual)."""
    s11 = s12 = s22 = sy1 = sy2 = 0.0
    for x1, x2, y in samples:
        s11 += x1 * x1
        s12 += x1 * x2
        s22 += x2 * x2
        sy1 += y * x1
        sy2 += y * x2

    det = s11 * s22 - s12 * s12
    if abs(det) < 1e-12:
        raise ValueError("least-squares matrix is singular; use a log with richer elevator excitation")

    a = (sy1 * s22 - sy2 * s12) / det
    b = (s11 * sy2 - s12 * sy1) / det
    err2 = [(y - (a * x1 + b * x2)) ** 2 for x1, x2, y in samples]
    rms = math.sqrt(sum(err2) / max(len(err2), 1))
    return a, b, rms


def build_pitch_rate_samples(
    rows: list[dict[str, float | str]],
    only_engaged: bool,
    max_dt: float,
) -> list[tuple[float, float, float]]:
    samples: list[tuple[float, float, float]] = []
    for prev, cur in zip(rows, rows[1:]):
        if only_engaged and (prev["engaged"] != "True" or cur["engaged"] != "True"):
            continue
        t0 = float(prev["t"])
        t1 = float(cur["t"])
        q0 = float(prev["q"])
        q1 = float(cur["q"])
        u0 = float(prev["u"])
        dt = t1 - t0
        if dt <= 1e-6 or dt > max_dt:
            continue
        if not all(finite(v) for v in (q0, q1, u0)):
            continue
        samples.append((q0, u0, (q1 - q0) / dt))
    return samples


def metric_stats(rows: list[dict[str, float | str]]) -> dict[str, float]:
    numeric = {
        "pitch": [float(r["pitch"]) for r in rows if finite(float(r["pitch"]))],
        "q": [float(r["q"]) for r in rows if finite(float(r["q"]))],
        "u": [float(r["u"]) for r in rows if finite(float(r["u"]))],
    }
    out: dict[str, float] = {"rows": float(len(rows))}
    if rows:
        out["duration_s"] = float(rows[-1]["t"]) - float(rows[0]["t"])
        out["engaged_fraction"] = sum(1 for r in rows if r["engaged"] == "True") / len(rows)
    for name, values in numeric.items():
        if not values:
            continue
        out[f"{name}_min"] = min(values)
        out[f"{name}_max"] = max(values)
        out[f"{name}_mean"] = sum(values) / len(values)
        out[f"{name}_rms"] = math.sqrt(sum(v * v for v in values) / len(values))
    if numeric["u"]:
        max_abs_u = max(abs(v) for v in numeric["u"])
        if max_abs_u > 0.0:
            out["u_saturation_fraction"] = sum(abs(v) >= 0.98 * max_abs_u for v in numeric["u"]) / len(numeric["u"])
            out["u_max_abs"] = max_abs_u
    return out


def recommended_rate_gain(a: float, b: float, tau: float) -> tuple[float, float]:
    """Return u = -kq*q with desired closed-loop q_dot = -q/tau."""
    desired_pole = -1.0 / tau
    if abs(b) < 1e-12:
        raise ValueError("identified elevator effectiveness is too small for gain recommendation")
    kq = (a - desired_pole) / b
    return kq, desired_pole


def print_report(path: Path, rows: list[dict[str, float | str]], args: argparse.Namespace) -> None:
    samples = build_pitch_rate_samples(rows, only_engaged=not args.include_waiting, max_dt=args.max_dt)
    print(f"\n=== {path} ===")
    for key, value in metric_stats(rows).items():
        print(f"{key}: {value:.6g}")
    print(f"identification_samples: {len(samples)}")

    if len(samples) < 20:
        print("model_status: insufficient samples")
        return

    a, b, rms = least_squares_2x2(samples)
    kq, desired_pole = recommended_rate_gain(a, b, args.tau)
    natural_tau = -1.0 / a if a < 0.0 else math.inf

    print("model: q_dot = a*q + b*u_e")
    print("units: q [deg/s], q_dot [deg/s^2], u_e [X-Plane elevator stick]")
    print(f"a: {a:.6g}")
    print(f"b: {b:.6g}")
    print(f"rms_qdot_residual: {rms:.6g}")
    print(f"open_loop_pitch_rate_tau_s: {natural_tau:.6g}")
    print(f"target_closed_loop_pole: {desired_pole:.6g}")
    print(f"recommended_inner_rate_gain_kq: {kq:.6g}")
    print("inner_rate_law: u_e = trim_elevator - kq * q_error")
    print(
        "note: use the sign of kq exactly with this log convention; validate with "
        "small clip and slew limits before adding attitude hold."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logs", nargs="+", type=Path)
    parser.add_argument("--tau", type=float, default=1.2, help="Desired closed-loop pitch-rate time constant.")
    parser.add_argument("--max-dt", type=float, default=0.2, help="Ignore row pairs with larger sample interval.")
    parser.add_argument("--include-waiting", action="store_true", help="Include WAIT rows in identification.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for path in args.logs:
        print_report(path, read_log(path), args)


if __name__ == "__main__":
    main()
