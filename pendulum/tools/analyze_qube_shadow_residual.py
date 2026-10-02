#!/usr/bin/env python3
"""
Analyze a Qube shadow gate-state residual run.

Reads a CSV produced by run_simulink_balance.py with --residual-mode shadow_gate and
generates, under analysis/qube_shadow_residual_YYYYMMDD_HHMMSS/:

  1. overlay_timeseries.png   - pendulum error, command voltage, demand_score,
                                gate_state, u_residual_candidate vs time
  2. residual_timing.png      - demand_score vs gate_state vs event_activity vs candidate
  3. shadow_residual_summary.csv - the requested summary metrics

SAFETY CHECK: the analyzer also verifies that u_residual_applied is identically 0 and
that u_total_command == u0_command (i.e. the residual was NOT applied), and prints a
PASS/FAIL banner.

Usage:
  python tools/analyze_qube_shadow_residual.py --log results/online/<run>.csv
  python tools/analyze_qube_shadow_residual.py --demo      # offline self-test (no hardware)

stdlib csv + numpy + matplotlib.
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
import time
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------- IO helpers
def read_log(path: Path) -> dict[str, np.ndarray]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        raise SystemExit(f"No rows in {path}")
    cols: dict[str, list] = {k: [] for k in rows[0].keys()}
    for r in rows:
        for k, v in r.items():
            cols[k].append(v)
    out: dict[str, np.ndarray] = {}
    for k, vals in cols.items():
        try:
            out[k] = np.array([float(x) if x not in ("", None) else np.nan for x in vals], dtype=float)
        except ValueError:
            out[k] = np.array(vals, dtype=object)  # non-numeric (e.g. control_mode strings)
    return out


def col(data: dict[str, np.ndarray], name: str, default: float = 0.0) -> np.ndarray:
    n = len(data.get("time_s", []))
    if name in data:
        return data[name]
    return np.full(n, default, dtype=float)


def active_mask(data: dict[str, np.ndarray]) -> np.ndarray:
    cm = data.get("control_mode")
    if cm is None:
        return np.ones(len(data["time_s"]), dtype=bool)
    return np.array([str(x) == "simulink_balance" for x in cm], dtype=bool)


# ---------------------------------------------------------------- analysis
def safety_check(data: dict[str, np.ndarray]) -> tuple[bool, str]:
    applied = col(data, "u_residual_applied")
    u0 = col(data, "u0_command", np.nan)
    utot = col(data, "u_total_command", np.nan)
    max_applied = float(np.nanmax(np.abs(applied))) if applied.size else 0.0
    if np.all(np.isnan(u0)) or np.all(np.isnan(utot)):
        diff = 0.0
    else:
        diff = float(np.nanmax(np.abs(utot - u0)))
    ok = (max_applied == 0.0) and (diff <= 1e-9)
    msg = (f"max|u_residual_applied|={max_applied:.6g} ; max|u_total-u0|={diff:.6g}")
    return ok, msg


def summarize(data: dict[str, np.ndarray]) -> dict[str, float]:
    m = active_mask(data)
    if not m.any():
        m = np.ones(len(data["time_s"]), dtype=bool)
    alpha_err_deg = np.degrees(np.abs(col(data, "alpha_control_rad")))
    u0 = np.abs(col(data, "u0_command")) if "u0_command" in data else np.abs(col(data, "command_voltage"))
    cand = np.abs(col(data, "u_residual_candidate"))
    demand = col(data, "demand_score")
    active = col(data, "residual_active_flag")
    amp_fault = col(data, "amplifier_fault")
    stall = col(data, "motor_stall_detected")
    fault_zero = 0
    if "control_mode" in data:
        fault_zero = int(np.sum([str(x) == "fault_zero" for x in data["control_mode"]]))

    # correlation demand vs |candidate| (guard against constant arrays)
    d = demand[m]
    c = cand[m]
    if d.size > 2 and np.std(d) > 1e-12 and np.std(c) > 1e-12:
        corr = float(np.corrcoef(d, c)[0, 1])
    else:
        corr = float("nan")

    return {
        "n_rows": int(len(data["time_s"])),
        "n_active_balance_rows": int(m.sum()),
        "mean_abs_pendulum_error_deg_active": float(np.nanmean(alpha_err_deg[m])),
        "max_abs_pendulum_error_deg": float(np.nanmax(alpha_err_deg)),
        "mean_abs_u0_v": float(np.nanmean(u0[m])),
        "max_abs_u0_v": float(np.nanmax(u0)),
        "mean_abs_candidate_residual_v": float(np.nanmean(cand[m])),
        "max_abs_candidate_residual_v": float(np.nanmax(cand)),
        "residual_active_fraction": float(np.nanmean(active)),
        "corr_demand_vs_abs_candidate": corr,
        "amplifier_fault_count": int(np.nansum(amp_fault > 0)),
        "motor_stall_count": int(np.nansum(stall > 0)),
        "fault_zero_count": fault_zero,
    }


def fig_overlay(data, outdir: Path):
    t = col(data, "time_s")
    fig, axes = plt.subplots(5, 1, figsize=(12, 11), sharex=True)
    axes[0].plot(t, np.degrees(col(data, "alpha_control_rad")), color="#1f77b4")
    axes[0].set_ylabel("pendulum\nerror (deg)")
    axes[1].plot(t, col(data, "command_voltage"), color="#7f7f7f")
    axes[1].set_ylabel("command\nvoltage (V)")
    axes[2].plot(t, col(data, "demand_score"), color="#d62728")
    axes[2].set_ylabel("demand_score")
    axes[2].set_ylim(-0.02, 1.02)
    axes[3].plot(t, col(data, "gate_state"), color="#2ca02c")
    axes[3].set_ylabel("gate_state")
    axes[3].set_ylim(-0.02, 1.02)
    axes[4].plot(t, col(data, "u_residual_candidate"), color="#9467bd",
                 label="candidate (NOT applied)")
    axes[4].plot(t, col(data, "u_residual_applied"), color="black", lw=1.0, ls="--",
                 label="applied (=0, shadow)")
    axes[4].set_ylabel("residual (V)")
    axes[4].set_xlabel("time (s)")
    axes[4].legend(loc="upper right", fontsize=8)
    for ax in axes:
        ax.grid(alpha=0.3)
    fig.suptitle("Qube shadow gate-state residual — time overlay (residual NOT applied)")
    fig.tight_layout(rect=[0, 0, 1, 0.98])
    fig.savefig(outdir / "overlay_timeseries.png", dpi=150)
    plt.close(fig)


def fig_timing(data, outdir: Path):
    t = col(data, "time_s")
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(t, col(data, "demand_score"), label="demand_score", color="#d62728")
    ax.plot(t, col(data, "gate_state"), label="gate_state", color="#2ca02c")
    ax.plot(t, col(data, "event_activity"), label="event_activity", color="#ff7f0e")
    # scale candidate to [0,1]-ish for shared axis readability
    cand = col(data, "u_residual_candidate")
    mx = max(1e-9, float(np.nanmax(np.abs(cand))))
    ax.plot(t, np.abs(cand) / mx, label=f"|candidate| / {mx:.3f}V", color="#9467bd", ls="--")
    ax.set_xlabel("time (s)")
    ax.set_ylabel("normalized activation")
    ax.set_title("Residual timing: demand vs gate vs event vs candidate")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(outdir / "residual_timing.png", dpi=150)
    plt.close(fig)


def analyze(log_path: Path) -> Path:
    data = read_log(log_path)
    ts = time.strftime("%Y%m%d_%H%M%S")
    outdir = PROJECT_ROOT / "analysis" / f"qube_shadow_residual_{ts}"
    outdir.mkdir(parents=True, exist_ok=True)

    ok, msg = safety_check(data)
    banner = "PASS" if ok else "FAIL"
    print(f"[SHADOW SAFETY {banner}] residual not applied - {msg}")

    summ = summarize(data)
    summ_path = outdir / "shadow_residual_summary.csv"
    with summ_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value"])
        w.writerow(["source_log", str(log_path)])
        w.writerow(["shadow_safety_pass", int(ok)])
        w.writerow(["shadow_safety_detail", msg])
        for k, v in summ.items():
            w.writerow([k, v])

    fig_overlay(data, outdir)
    fig_timing(data, outdir)

    print(f"Analysis written to: {outdir}")
    print("Summary:")
    for k, v in summ.items():
        print(f"   {k}: {v}")
    return outdir


# ---------------------------------------------------------------- demo (offline self-test)
def make_demo_log() -> Path:
    """Drive the REAL ShadowGateResidual with a scripted perturbation profile and write a
    runner-compatible CSV. No hardware. Demonstrates demand->gate->candidate timing and the
    shadow safety invariant (applied == 0)."""
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    from servo_pendulum_snn.simulink_balance_runner import ShadowGateResidual

    fs = 250.0
    dt = 1.0 / fs
    duration = 30.0
    n = int(duration * fs)
    rng = np.random.default_rng(0)
    gate = ShadowGateResidual(
        neuron="adaptive_hyperlif", sample_time_s=dt, residual_threshold=0.15,
        residual_demand_threshold=0.20, residual_max_voltage=0.25,
        alpha_err_ref_rad=math.radians(12.0),
    )
    voltage_limit = 5.0
    pulses = [10.0, 15.0, 20.0]

    def alpha_deg(t):  # pendulum error profile: quiet ~0.5deg + perturbation bumps
        base = 0.5 * math.sin(2 * math.pi * 0.3 * t)
        bump = 0.0
        for tp in pulses:
            if tp <= t < tp + 0.8:
                bump += 9.5 * math.sin(math.pi * (t - tp) / 0.8)  # half-sine up to ~9.5 deg
        return base + bump

    out_dir = PROJECT_ROOT / "results" / "online"
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / f"qube3_shadow_DEMO_{time.strftime('%Y%m%d_%H%M%S')}.csv"

    fieldnames = ["time_s", "control_mode", "alpha_control_rad", "alpha_dot_sim_rad_s",
                  "theta_dot_sim_rad_s", "command_voltage", "amplifier_fault",
                  "motor_stall_detected", "motor_stall_error", "residual_mode",
                  "residual_scale", "u0_command", "u_residual_candidate", "u_residual_applied",
                  "u_total_command", "demand_score", "saturation_proximity", "gate_state",
                  "conductance_state", "event_activity", "residual_active_flag",
                  "residual_neuron", "residual_threshold"]
    prev_alpha = math.radians(alpha_deg(0.0))
    with log_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for i in range(n):
            t = i * dt
            ac = math.radians(alpha_deg(t)) + math.radians(0.05) * rng.standard_normal()
            adot = (ac - prev_alpha) / dt
            prev_alpha = ac
            tdot = 0.2 * rng.standard_normal()
            # synthetic classical command: small PD-like response to the error, clipped
            u0 = float(np.clip(-30.0 * ac - 2.0 * adot, -voltage_limit, voltage_limit))
            d = gate.demand_score(ac, adot, tdot, u0, voltage_limit)
            res = gate.step_gate(d, ac)
            sat = min(1.0, abs(u0) / voltage_limit)
            w.writerow({
                "time_s": t, "control_mode": "simulink_balance", "alpha_control_rad": ac,
                "alpha_dot_sim_rad_s": adot, "theta_dot_sim_rad_s": tdot, "command_voltage": u0,
                "amplifier_fault": 0.0, "motor_stall_detected": 0.0, "motor_stall_error": 0.0,
                "residual_mode": "shadow_gate", "residual_scale": 0.0, "u0_command": u0,
                "u_residual_candidate": res["u_residual_candidate"], "u_residual_applied": 0.0,
                "u_total_command": u0, "demand_score": d, "saturation_proximity": sat,
                "gate_state": res["gate_state"], "conductance_state": res["conductance_state"],
                "event_activity": res["event_activity"],
                "residual_active_flag": res["residual_active_flag"],
                "residual_neuron": "adaptive_hyperlif", "residual_threshold": 0.15,
            })
    print(f"[demo] wrote synthetic shadow log: {log_path}")
    return log_path


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", type=Path, help="shadow-mode CSV from run_simulink_balance.py")
    ap.add_argument("--demo", action="store_true", help="offline self-test (no hardware)")
    args = ap.parse_args(argv)
    if args.demo:
        log = make_demo_log()
        analyze(log)
        return
    if not args.log:
        ap.error("provide --log <csv> or --demo")
    analyze(args.log)


if __name__ == "__main__":
    main()
