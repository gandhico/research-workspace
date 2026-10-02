#!/usr/bin/env python3
"""Observe-only R3 roll DeePC integration; this program cannot send controls."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "backstepping"))

import Backstepping
import xpc

from deepc.src.r3_roll_runtime import R3RollDeePCRuntime
from run_rich_r3_roll_dualrate_xp12 import abort_reason, start_reasons, update_original
from run_rich_r3_roll_highrate_observe_xp12 import FIELDS, scalar


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--duration", type=float, default=30.0)
    p.add_argument("--io-hz", type=float, default=35.0)
    p.add_argument("--fallback-hz", type=float, default=10.0)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=49009)
    p.add_argument("--timeout-ms", type=int, default=500)
    p.add_argument("--out", type=Path, required=True)
    return p


def history_fields(prefix: str, values) -> dict[str, float]:
    return {f"{prefix}_{i}": float(value) for i, value in enumerate(values)}


def main() -> None:
    args = parser().parse_args()
    if args.duration <= 0 or args.io_hz <= 0 or args.fallback_hz <= 0:
        raise SystemExit("duration and rates must be positive")

    names = list(dict.fromkeys(item[1] for item in FIELDS))
    runtime = R3RollDeePCRuntime()
    roll = Backstepping.Backstepping(0.001, 33, 0.03)
    pitch = Backstepping.Backstepping(0.001, 39, 0.03)
    roll.SetPoint = 0.0
    pitch.SetPoint = 1.3
    rows = []
    period = 1.0 / args.io_hz
    fallback_period = 1.0 / args.fallback_hz
    started = next_io = next_fallback = time.monotonic()
    bias = None
    fallback_roll = fallback_pitch = 0.0
    safety_latched = False
    safety_reason = ""

    with xpc.XPlaneConnect(xpHost=args.host, xpPort=args.port, timeout=args.timeout_ms) as client:
        while time.monotonic() - started < args.duration:
            now = time.monotonic()
            if now < next_io:
                time.sleep(min(0.001, next_io - now))
                continue
            scheduled = next_io
            next_io += period
            reply = client.getDREFs(names)
            acquired = time.monotonic()
            values = dict(zip(names, reply))
            measured = {field: scalar(values[dref], index) for field, dref, index in FIELDS}
            measured["dynamic_pressure_pa"] = 0.5 * measured["air_density_kg_m3"] * measured["tas_m_s"] ** 2
            elapsed = now - started

            if bias is None:
                bias = {
                    "p": measured["p_deg_s"],
                    "total_roll": measured["total_roll_ratio"],
                    "yoke_roll": measured["yoke_roll_ratio"],
                    "yoke_pitch": measured["yoke_pitch_ratio"],
                }
                initial_reasons = start_reasons(measured)
                print("Observe start gate PASS" if not initial_reasons else "Observe start state: " + "; ".join(initial_reasons))

            fallback_update = now >= next_fallback
            if fallback_update:
                while next_fallback <= now:
                    next_fallback += fallback_period
                fallback_roll = bias["yoke_roll"] + update_original(
                    roll, measured["roll_deg"], measured["yoke_roll_ratio"] - bias["yoke_roll"]
                )
                fallback_pitch = bias["yoke_pitch"] + update_original(
                    pitch, measured["pitch_deg"], measured["yoke_pitch_ratio"] - bias["yoke_pitch"]
                )

            reason = abort_reason(measured)
            if reason and not safety_latched:
                safety_latched = True
                safety_reason = reason

            p_error = measured["p_deg_s"] - bias["p"]
            pre_u = runtime.u_history.copy()
            pre_p = runtime.p_history.copy()
            runtime_started = time.perf_counter()
            result = runtime.update(p_error)
            runtime_ms = (time.perf_counter() - runtime_started) * 1000.0
            hypothetical_command = 0.0 if safety_latched or result["fallback_required"] else result["command"]
            selected_mode = "BACKSTEPPING_FALLBACK" if safety_latched or result["fallback_required"] else "DEEPC"

            row = {
                "sample": len(rows),
                "t_s": elapsed,
                "dt_s": now - (rows[-1]["_tick"] if rows else started),
                "deadline_lateness_s": now - scheduled,
                "acquisition_s": acquired - now,
                "runtime_ms": runtime_ms,
                "fallback_update": int(fallback_update),
                "p_bias_deg_s": bias["p"],
                "p_error_deg_s": p_error,
                "total_roll_bias": bias["total_roll"],
                "yoke_roll_bias": bias["yoke_roll"],
                "yoke_pitch_bias": bias["yoke_pitch"],
                "deepc_command": result["command"],
                "hypothetical_selected_perturbation": hypothetical_command,
                "deepc_converged": int(result["converged"]),
                "deepc_iterations": result["iterations"],
                "deepc_fallback_required": int(result["fallback_required"]),
                "deepc_fallback_reason": result["reason"],
                "safety_latched": int(safety_latched),
                "safety_reason": safety_reason,
                "hypothetical_mode": selected_mode,
                "fallback_roll_command": fallback_roll,
                "fallback_pitch_command": fallback_pitch,
                "engaged": 0,
                "controls_sent": 0,
                "ownership_requested": 0,
                **history_fields("pre_u_history", pre_u),
                **history_fields("pre_p_history", pre_p),
                **history_fields("post_u_history", runtime.u_history),
                **history_fields("post_p_history", runtime.p_history),
                "_tick": now,
                **measured,
            }
            if not all(math.isfinite(float(row[key])) for key in ("runtime_ms", "deepc_command", "p_error_deg_s")):
                raise RuntimeError("non-finite observe-only runtime value")
            rows.append(row)

    for row in rows:
        row.pop("_tick")
    if not rows:
        raise SystemExit("no samples captured")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} observe-only DeePC samples: {args.out.resolve()}")


if __name__ == "__main__":
    main()
