#!/usr/bin/env python3
"""
Compare Qube residual-ablation conditions (none / shadow_gate / gate / shuffled_gate /
always_on) from multiple run CSVs.

Outputs under analysis/qube_residual_comparison_YYYYMMDD_HHMMSS/:
  - condition_summary.csv          per-condition global metrics
  - demand_binned_metrics.csv      per-condition x demand-bin metrics
  - comparison_report.md           ranked tables + H1/H2 decision logic
  - overlay_<condition>.png        per-run time overlay
  - condition_comparison.png       grouped bars across conditions

Decision logic (printed in the report):
  * gate should reduce high-demand error/recovery vs none, without raising low-demand activity.
  * shuffled_gate tests whether TIMING matters (H1): gate < shuffled in high-demand bins -> timing matters.
  * always_on tests whether demand gating saves actuation/event cost (H2): gate ~ always_on on
    high-demand error but with lower applied energy / active fraction -> gating earns its place.

Usage:
  python tools/compare_qube_residual_conditions.py --log A.csv --log B.csv ...
  python tools/compare_qube_residual_conditions.py --demo     # offline pipeline self-test
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
import time
from collections import deque
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# demand-score bin edges and labels
BIN_EDGES = [0.0, 0.20, 0.40, 0.70, 1.0001]
BIN_LABELS = ["low", "medium", "high", "near_saturation"]
HIGH_DEMAND_MIN = 0.40  # 'high' + 'near_saturation'


# ---------------------------------------------------------------- IO
def read_log(path: Path) -> dict[str, np.ndarray]:
    with Path(path).open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise SystemExit(f"No rows in {path}")
    cols = {k: [] for k in rows[0]}
    for r in rows:
        for k, v in r.items():
            cols[k].append(v)
    out = {}
    for k, vals in cols.items():
        try:
            out[k] = np.array([float(x) if x not in ("", None) else np.nan for x in vals], dtype=float)
        except ValueError:
            out[k] = np.array(vals, dtype=object)
    return out


def col(data, name, default=0.0):
    n = len(data.get("time_s", []))
    return data[name] if name in data else np.full(n, default, dtype=float)


def active_mask(data):
    cm = data.get("control_mode")
    if cm is None:
        return np.ones(len(data["time_s"]), dtype=bool)
    return np.array([str(x) == "simulink_balance" for x in cm], dtype=bool)


def condition_label(data, path: Path) -> str:
    rm = data.get("residual_mode")
    if rm is not None and len(rm):
        vals = {str(x) for x in rm}
        if len(vals) == 1:
            return next(iter(vals))
    return path.stem


# ---------------------------------------------------------------- metrics
def summarize(data) -> dict:
    m = active_mask(data)
    if not m.any():
        m = np.ones(len(data["time_s"]), dtype=bool)
    err = np.degrees(np.abs(col(data, "alpha_control_rad")))
    utot = np.abs(col(data, "u_total_command")) if "u_total_command" in data else np.abs(col(data, "command_voltage"))
    demand = col(data, "demand_score")
    applied_active = col(data, "applied_residual_active_flag")
    res_active = col(data, "residual_active_flag")
    hi = m & (demand >= HIGH_DEMAND_MIN)
    lo = m & (demand < BIN_EDGES[1])
    return {
        "n_rows": int(len(data["time_s"])),
        "n_active_rows": int(m.sum()),
        "mean_abs_err_deg": float(np.nanmean(err[m])),
        "max_abs_err_deg": float(np.nanmax(err[m])),
        "mean_abs_u_total": float(np.nanmean(utot[m])),
        "max_abs_u_total": float(np.nanmax(utot[m])),
        "residual_active_fraction": float(np.nanmean(res_active[m])),
        "applied_active_fraction": float(np.nanmean(applied_active[m])),
        "applied_residual_energy": float(np.nansum(col(data, "applied_residual_energy"))),
        "candidate_residual_energy": float(np.nansum(col(data, "residual_energy"))),
        "high_demand_mean_abs_err_deg": float(np.nanmean(err[hi])) if hi.any() else float("nan"),
        "high_demand_max_abs_err_deg": float(np.nanmax(err[hi])) if hi.any() else float("nan"),
        "high_demand_rows": int(hi.sum()),
        "low_demand_applied_active_fraction": float(np.nanmean(applied_active[lo])) if lo.any() else float("nan"),
        "amplifier_fault_count": int(np.nansum(col(data, "amplifier_fault") > 0)),
    }


def demand_binned(data, condition: str) -> list[dict]:
    m = active_mask(data)
    demand = col(data, "demand_score")
    err = np.degrees(np.abs(col(data, "alpha_control_rad")))
    utot = np.abs(col(data, "u_total_command")) if "u_total_command" in data else np.abs(col(data, "command_voltage"))
    applied_active = col(data, "applied_residual_active_flag")
    applied_e = col(data, "applied_residual_energy")
    out = []
    for i, lbl in enumerate(BIN_LABELS):
        sel = m & (demand >= BIN_EDGES[i]) & (demand < BIN_EDGES[i + 1])
        out.append({
            "condition": condition, "demand_bin": lbl, "n_rows": int(sel.sum()),
            "mean_abs_err_deg": float(np.nanmean(err[sel])) if sel.any() else float("nan"),
            "max_abs_err_deg": float(np.nanmax(err[sel])) if sel.any() else float("nan"),
            "mean_abs_u_total": float(np.nanmean(utot[sel])) if sel.any() else float("nan"),
            "applied_active_fraction": float(np.nanmean(applied_active[sel])) if sel.any() else float("nan"),
            "applied_residual_energy": float(np.nansum(applied_e[sel])) if sel.any() else 0.0,
        })
    return out


# ---------------------------------------------------------------- plots
def fig_overlay(data, condition, outdir):
    t = col(data, "time_s")
    fig, ax = plt.subplots(5, 1, figsize=(12, 11), sharex=True)
    ax[0].plot(t, np.degrees(col(data, "alpha_control_rad")), color="#1f77b4"); ax[0].set_ylabel("pend err\n(deg)")
    ax[1].plot(t, col(data, "u_total_command"), color="#7f7f7f"); ax[1].set_ylabel("u_total (V)")
    ax[2].plot(t, col(data, "demand_score"), color="#d62728"); ax[2].set_ylabel("demand"); ax[2].set_ylim(-0.02, 1.02)
    ax[3].plot(t, col(data, "gate_state"), color="#2ca02c"); ax[3].set_ylabel("gate"); ax[3].set_ylim(-0.02, 1.02)
    ax[4].plot(t, col(data, "u_residual_applied"), color="#9467bd"); ax[4].set_ylabel("applied\nresidual (V)")
    ax[4].set_xlabel("time (s)")
    for a in ax:
        a.grid(alpha=0.3)
    fig.suptitle(f"Condition: {condition}")
    fig.tight_layout(rect=[0, 0, 1, 0.98])
    fig.savefig(outdir / f"overlay_{condition}.png", dpi=150)
    plt.close(fig)


def fig_comparison(summaries: dict[str, dict], outdir):
    conds = list(summaries.keys())
    metrics = [
        ("mean_abs_err_deg", "mean |err| (deg)"),
        ("max_abs_err_deg", "max |err| (deg)"),
        ("high_demand_mean_abs_err_deg", "high-demand mean |err| (deg)"),
        ("mean_abs_u_total", "mean |u_total| (V)"),
        ("applied_active_fraction", "applied active fraction"),
        ("applied_residual_energy", "applied residual energy (V^2 s)"),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    for ax, (key, title) in zip(axes.flat, metrics):
        vals = [summaries[c].get(key, float("nan")) for c in conds]
        ax.bar(range(len(conds)), vals, color="#4c72b0", edgecolor="black", linewidth=0.5)
        ax.set_xticks(range(len(conds)))
        ax.set_xticklabels(conds, rotation=20, ha="right", fontsize=8)
        ax.set_title(title, fontsize=10)
        ax.grid(axis="y", alpha=0.3)
        for i, v in enumerate(vals):
            if v == v:  # not NaN
                ax.text(i, v, f"{v:.3g}", ha="center", va="bottom", fontsize=7)
    fig.suptitle("Residual condition comparison (active balance)")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(outdir / "condition_comparison.png", dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------- report
def write_report(summaries, binned_rows, outdir, sources):
    lines = ["# Qube residual condition comparison", ""]
    lines.append(f"- Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- Conditions: {', '.join(summaries)}")
    lines.append("")
    lines.append("## Per-condition summary (active balance)")
    keys = ["mean_abs_err_deg", "max_abs_err_deg", "high_demand_mean_abs_err_deg",
            "high_demand_max_abs_err_deg", "mean_abs_u_total", "max_abs_u_total",
            "residual_active_fraction", "applied_active_fraction",
            "low_demand_applied_active_fraction", "applied_residual_energy", "amplifier_fault_count"]
    lines.append("| condition | " + " | ".join(keys) + " |")
    lines.append("|" + "---|" * (len(keys) + 1))
    for c, s in summaries.items():
        lines.append("| " + c + " | " + " | ".join(
            (f"{s[k]:.4g}" if isinstance(s.get(k), float) else str(s.get(k))) for k in keys) + " |")
    lines.append("")

    # decision logic
    lines.append("## Decision logic (H1 timing, H2 event/actuation cost)")

    def hd(c):  # high-demand mean abs error
        return summaries.get(c, {}).get("high_demand_mean_abs_err_deg", float("nan"))

    if "gate" in summaries and "none" in summaries:
        d = hd("none") - hd("gate")
        lines.append(f"- gate vs none (high-demand mean |err|): none={hd('none'):.3g}, gate={hd('gate'):.3g}, "
                     f"improvement={d:+.3g} deg "
                     f"({'gate helps' if d > 0 else 'no improvement'}).")
    if "gate" in summaries and "shuffled_gate" in summaries:
        d = hd("shuffled_gate") - hd("gate")
        verdict = ("TIMING MATTERS (gate beats shuffled)" if d > 1e-6 else
                   "timing weak (gate ~ shuffled)")
        lines.append(f"- gate vs shuffled_gate (high-demand mean |err|): shuffled={hd('shuffled_gate'):.3g}, "
                     f"gate={hd('gate'):.3g}, gate-better-by={d:+.3g} deg -> **{verdict}**.")
    if "gate" in summaries and "always_on" in summaries:
        e_gate = summaries["gate"]["applied_residual_energy"]
        e_alw = summaries["always_on"]["applied_residual_energy"]
        f_gate = summaries["gate"]["applied_active_fraction"]
        f_alw = summaries["always_on"]["applied_active_fraction"]
        lines.append(f"- gate vs always_on (cost): applied energy gate={e_gate:.3g} vs always_on={e_alw:.3g}; "
                     f"applied active fraction gate={f_gate:.3g} vs always_on={f_alw:.3g}. "
                     f"gate err={hd('gate'):.3g} vs always_on err={hd('always_on'):.3g}. "
                     f"({'gating saves actuation at similar error' if (e_gate < e_alw) else 'no cost saving'}).")
    lines.append("")
    lines.append("> Interpretation rules: gate < shuffled in high-demand bins => demand-triggered "
                 "timing is doing the work (H1). gate ~ always_on on high-demand error but with lower "
                 "applied energy/active fraction => demand gating earns its place (H2). gate ~ shuffled "
                 "=> timing claim is weak and should not be made.")
    lines.append("")
    lines.append("## Sources")
    for c, p in sources.items():
        lines.append(f"- {c}: `{p}`")
    (outdir / "comparison_report.md").write_text("\n".join(lines), encoding="utf-8")


def run_compare(logs: list[Path]) -> Path:
    ts = time.strftime("%Y%m%d_%H%M%S")
    outdir = PROJECT_ROOT / "analysis" / f"qube_residual_comparison_{ts}"
    outdir.mkdir(parents=True, exist_ok=True)
    summaries, all_binned, sources = {}, [], {}
    for p in logs:
        data = read_log(p)
        c = condition_label(data, p)
        # de-duplicate condition labels if needed
        base, k = c, 2
        while c in summaries:
            c = f"{base}_{k}"; k += 1
        summaries[c] = summarize(data)
        all_binned.extend(demand_binned(data, c))
        sources[c] = str(p)
        fig_overlay(data, c, outdir)

    with (outdir / "condition_summary.csv").open("w", newline="", encoding="utf-8") as f:
        keys = list(next(iter(summaries.values())).keys())
        w = csv.writer(f); w.writerow(["condition"] + keys)
        for c, s in summaries.items():
            w.writerow([c] + [s[k] for k in keys])
    with (outdir / "demand_binned_metrics.csv").open("w", newline="", encoding="utf-8") as f:
        fns = list(all_binned[0].keys())
        w = csv.DictWriter(f, fieldnames=fns); w.writeheader(); w.writerows(all_binned)

    fig_comparison(summaries, outdir)
    write_report(summaries, all_binned, outdir, sources)
    print(f"Comparison written to: {outdir}")
    for c, s in summaries.items():
        print(f"  {c:14s} mean|err|={s['mean_abs_err_deg']:.3f}deg  "
              f"hi-demand|err|={s['high_demand_mean_abs_err_deg']:.3f}  "
              f"applied_active={s['applied_active_fraction']:.3f}  "
              f"applied_energy={s['applied_residual_energy']:.4g}")
    return outdir


# ---------------------------------------------------------------- demo (offline pipeline test)
def make_demo_logs() -> list[Path]:
    """Synthesize one CSV per condition by driving the REAL ShadowGateResidual + the runner's
    apply logic over a scripted perturbation. TOY plant with NO closed-loop feedback, so the
    pendulum-error profile is identical across conditions by construction: this validates the
    comparison PIPELINE and the actuation/energy/activity metrics, NOT the control science.
    Real hardware provides the closed-loop error response."""
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    from servo_pendulum_snn.simulink_balance_runner import ShadowGateResidual

    fs, dt, duration = 250.0, 1.0 / 250.0, 30.0
    n = int(duration * fs)
    vlim, cap = 5.0, 0.10
    pulses = [10.0, 15.0, 20.0]

    def alpha_deg(t):
        base = 0.5 * math.sin(2 * math.pi * 0.3 * t)
        bump = sum(9.5 * math.sin(math.pi * (t - tp) / 0.8) for tp in pulses if tp <= t < tp + 0.8)
        return base + bump

    out_dir = PROJECT_ROOT / "results" / "online"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    fns = ["time_s", "control_mode", "alpha_control_rad", "command_voltage", "u0_command",
           "u_residual_candidate", "u_residual_applied", "u_total_command", "demand_score",
           "saturation_proximity", "gate_state", "event_activity", "residual_active_flag",
           "applied_residual_active_flag", "residual_energy", "applied_residual_energy",
           "amplifier_fault", "residual_mode"]
    paths = []
    for mode in ("none", "gate", "shuffled_gate", "always_on"):
        gate = ShadowGateResidual("adaptive_hyperlif", dt, 0.15, 0.20, cap, math.radians(12.0))
        delay = int(5.0 * fs)
        buf = deque(maxlen=delay)  # in-run delay buffer for shuffled (offset 5 s), like the runner
        p = out_dir / f"qube3_DEMO_{mode}_{stamp}.csv"
        prev = math.radians(alpha_deg(0.0))
        with p.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fns); w.writeheader()
            for i in range(n):
                t = i * dt
                ac = math.radians(alpha_deg(t))
                adot = (ac - prev) / dt; prev = ac
                u0 = float(np.clip(-30.0 * ac - 2.0 * adot, -vlim, vlim))
                d = gate.demand_score(ac, adot, 0.0, u0, vlim)
                res = gate.step_gate(d, ac)
                applied = 0.0
                if mode in ("gate", "shuffled_gate", "always_on"):  # active balance assumed throughout
                    if mode == "gate":
                        base = res["u_residual_candidate"]
                    elif mode == "always_on":
                        base = cap * res["corrective"]
                    else:  # shuffled_gate, in-run delayed gate/demand (deque[0] == 'delay' steps ago)
                        sg, sd = (buf[0] if len(buf) == buf.maxlen else (0.0, 0.0))
                        buf.append((res["gate_state"], d))
                        base = cap * res["corrective"] * sg * sd
                    applied = float(np.clip(base, -cap, cap))
                utot = float(np.clip(u0 + applied, -vlim, vlim))
                w.writerow({
                    "time_s": t, "control_mode": "simulink_balance", "alpha_control_rad": ac,
                    "command_voltage": u0, "u0_command": u0,
                    "u_residual_candidate": res["u_residual_candidate"], "u_residual_applied": applied,
                    "u_total_command": utot, "demand_score": d,
                    "saturation_proximity": min(1.0, abs(u0) / vlim), "gate_state": res["gate_state"],
                    "event_activity": res["event_activity"], "residual_active_flag": res["residual_active_flag"],
                    "applied_residual_active_flag": 1.0 if abs(applied) > 1e-3 else 0.0,
                    "residual_energy": res["u_residual_candidate"] ** 2 * dt,
                    "applied_residual_energy": applied ** 2 * dt, "amplifier_fault": 0.0,
                    "residual_mode": mode,
                })
        paths.append(p)
        print(f"[demo] wrote {p}")
    return paths


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", action="append", type=Path, help="run CSV (repeatable)")
    ap.add_argument("--demo", action="store_true", help="offline pipeline self-test (no hardware)")
    args = ap.parse_args(argv)
    logs = list(args.log or [])
    if args.demo:
        logs = make_demo_logs() + logs
    if not logs:
        ap.error("provide one or more --log <csv>, or --demo")
    run_compare(logs)


if __name__ == "__main__":
    main()
