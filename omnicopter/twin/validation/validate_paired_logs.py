"""Compare synchronized physical and MuJoCo Omnicopter logs in common frames."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np


REQUIRED = ("time_s", "x_m", "y_m", "z_m", "q_w", "q_x", "q_y", "q_z",
            "wx_rad_s", "wy_rad_s", "wz_rad_s")


def load(path):
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    missing = [name for name in REQUIRED if name not in rows[0]]
    if missing:
        raise ValueError(f"{path}: missing columns {missing}")
    motor_columns = tuple(f"thrust_{index}_N" for index in range(1, 9))
    numeric = tuple(REQUIRED) + tuple(name for name in motor_columns if name in rows[0])
    columns = {name: np.asarray([float(row[name]) for row in rows]) for name in numeric}
    if np.any(np.diff(columns["time_s"]) <= 0):
        raise ValueError(f"{path}: time_s must be strictly increasing")
    return columns


def continuous_quaternions(q):
    q = q.copy()
    q /= np.linalg.norm(q, axis=1, keepdims=True)
    for index in range(1, len(q)):
        if q[index] @ q[index-1] < 0:
            q[index] *= -1
    return q


def interpolate(source, query):
    output = {}
    for name, values in source.items():
        output[name] = np.interp(query, source["time_s"], values)
    q = continuous_quaternions(np.column_stack(
        [output[name] for name in ("q_w", "q_x", "q_y", "q_z")]))
    for index, name in enumerate(("q_w", "q_x", "q_y", "q_z")):
        output[name] = q[:, index]
    return output


def metrics(physical, twin, time_offset, warmup):
    times = physical["time_s"]
    keep = ((times >= times[0]+warmup)
            & (times+time_offset >= twin["time_s"][0])
            & (times+time_offset <= twin["time_s"][-1]))
    if np.count_nonzero(keep) < 10:
        raise ValueError("Insufficient overlap after time alignment and warmup")
    physical = {key: value[keep] for key, value in physical.items()}
    aligned = interpolate(twin, times[keep]+time_offset)
    position_error = np.linalg.norm(
        np.column_stack([physical[a]-aligned[a] for a in ("x_m", "y_m", "z_m")]), axis=1)
    q_physical = continuous_quaternions(np.column_stack(
        [physical[name] for name in ("q_w", "q_x", "q_y", "q_z")]))
    q_twin = np.column_stack([aligned[name] for name in ("q_w", "q_x", "q_y", "q_z")])
    attitude_error = np.rad2deg(2*np.arccos(np.clip(
        np.abs(np.sum(q_physical*q_twin, axis=1)), 0., 1.)))
    rate_error = np.linalg.norm(np.column_stack(
        [physical[a]-aligned[a] for a in ("wx_rad_s", "wy_rad_s", "wz_rad_s")]), axis=1)
    result = {"samples": int(len(position_error)), "time_offset_s": float(time_offset)}
    for name, error in (("position_m", position_error),
                        ("attitude_deg", attitude_error), ("rate_rad_s", rate_error)):
        result[f"{name}_RMSE"] = float(np.sqrt(np.mean(error**2)))
        result[f"{name}_median"] = float(np.median(error))
        result[f"{name}_p95"] = float(np.percentile(error, 95))
        result[f"{name}_peak"] = float(np.max(error))
    motor_columns = [f"thrust_{index}_N" for index in range(1, 9)]
    if all(name in physical and name in aligned for name in motor_columns):
        error = np.column_stack([physical[name]-aligned[name] for name in motor_columns])
        result["motor_command_RMSE_N"] = float(np.sqrt(np.mean(error**2)))
        result["motor_command_peak_N"] = float(np.max(np.abs(error)))
    return result


def diagnostic_offset(physical, twin, span):
    candidates = np.linspace(-span, span, 401)
    values = []
    for offset in candidates:
        try:
            values.append(metrics(physical, twin, offset, 0.)["rate_rad_s_RMSE"])
        except ValueError:
            values.append(np.inf)
    index = int(np.argmin(values))
    return float(candidates[index]), float(values[index])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("physical", type=Path)
    parser.add_argument("twin", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--time-offset-s", type=float, default=0.,
                        help="Known synchronized t_twin - t_physical offset")
    parser.add_argument("--warmup-s", type=float, default=0.)
    parser.add_argument("--gates", type=Path, help="Optional JSON metric upper limits")
    parser.add_argument("--diagnostic-offset-search-s", type=float, default=0.,
                        help="Post-hoc diagnostic only; never use for confirmatory timing")
    args = parser.parse_args()
    physical, twin = load(args.physical), load(args.twin)
    result = metrics(physical, twin, args.time_offset_s, args.warmup_s)
    result.update({
        "physical_log": str(args.physical.resolve()), "twin_log": str(args.twin.resolve()),
        "frame_requirement": "both logs already expressed in MuJoCo world/body frames",
        "timing_requirement": "confirmatory offset supplied by clock synchronization, not outcome fitting",
    })
    if args.diagnostic_offset_search_s > 0:
        offset, score = diagnostic_offset(physical, twin, args.diagnostic_offset_search_s)
        result["diagnostic_fitted_offset_s"] = offset
        result["diagnostic_fitted_rate_RMSE_rad_s"] = score
        result["diagnostic_only"] = True
    gates = json.loads(args.gates.read_text(encoding="utf-8")) if args.gates else {}
    result["gates"] = gates
    result["failed_gates"] = [key for key, limit in gates.items()
                              if key not in result or result[key] > limit]
    result["status"] = "not_gated" if not gates else (
        "pass" if not result["failed_gates"] else "fail")
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output/"validation.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    lines = ["# Physical--virtual paired-log validation", "",
             f"Status: **{result['status']}**; samples: {result['samples']}; "
             f"known time offset: {result['time_offset_s']:.6f} s.", "",
             "| Quantity | RMSE | Median | 95th percentile | Peak |", "|---|---:|---:|---:|---:|",
             f"| Position [m] | {result['position_m_RMSE']:.6f} | {result['position_m_median']:.6f} | {result['position_m_p95']:.6f} | {result['position_m_peak']:.6f} |",
             f"| Attitude [deg] | {result['attitude_deg_RMSE']:.4f} | {result['attitude_deg_median']:.4f} | {result['attitude_deg_p95']:.4f} | {result['attitude_deg_peak']:.4f} |",
             f"| Angular rate [rad/s] | {result['rate_rad_s_RMSE']:.6f} | {result['rate_rad_s_median']:.6f} | {result['rate_rad_s_p95']:.6f} | {result['rate_rad_s_peak']:.6f} |", "",
             "This report compares prediction, not parameter identity. Acceptance gates must be frozen before viewing confirmatory results."]
    (args.output/"REPORT.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    print(args.output.resolve())


if __name__ == "__main__":
    main()
