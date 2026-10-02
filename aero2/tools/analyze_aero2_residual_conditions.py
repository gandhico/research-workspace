#!/usr/bin/env python3
"""
Compare Aero2 residual-ablation conditions (none / shadow_gate / gate / always_on /
shuffled_gate) from multiple run CSVs produced by runners/run_aero2_residual.py.

Outputs under analysis/aero2_residual_comparison_YYYYMMDD_HHMMSS/:
  condition_summary.csv, demand_binned_metrics.csv, comparison_report.md,
  overlay_<condition>.png (per run), condition_comparison.png,
  demand_binned_activity.png, demand_binned_error.png, residual_energy.png

Decision logic: gate quiet at low demand; gate active during pitch/yaw transitions or
perturbations; gate uses less residual energy than always_on; shuffled_gate tests timing.

Usage:
  python tools/analyze_aero2_residual_conditions.py --log A.csv --log B.csv ...
  python tools/analyze_aero2_residual_conditions.py --demo     # offline pipeline self-test
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
BIN_EDGES = [0.0, 0.20, 0.40, 0.70, 1.0001]
BIN_LABELS = ["low", "medium", "high", "near_saturation"]
HIGH_DEMAND_MIN = 0.40


def read_log(path):
    with Path(path).open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise SystemExit(f"No rows in {path}")
    out = {}
    for k in rows[0]:
        vals = [r.get(k) for r in rows]
        try:
            out[k] = np.array([float(x) if x not in ("", None) else np.nan for x in vals], dtype=float)
        except ValueError:
            out[k] = np.array(vals, dtype=object)
    return out


def col(d, name, default=0.0):
    n = len(d.get("t", d.get("time_s", [])))
    return d[name] if name in d else np.full(n, default, dtype=float)


def active_mask(d):
    cm = d.get("control_mode")
    if cm is None:
        return np.ones(len(col(d, "t")), dtype=bool)
    return np.array([str(x) == "active" for x in cm], dtype=bool)


def label_of(d, path):
    rm = d.get("residual_mode")
    if rm is not None and len(rm) and len({str(x) for x in rm}) == 1:
        return str(rm[0])
    return Path(path).stem


def chan_applied_mag(d):
    lr = np.abs(col(d, "left_residual_applied"))
    rr = np.abs(col(d, "right_residual_applied"))
    return np.maximum(lr, rr)


def summarize(d):
    m = active_mask(d)
    if not m.any():
        m = np.ones(len(col(d, "t")), dtype=bool)
    pe = np.degrees(np.abs(col(d, "pitch_error")))
    ye = np.degrees(np.abs(col(d, "yaw_error")))
    ul = np.abs(col(d, "total_left_voltage"))
    ur = np.abs(col(d, "total_right_voltage"))
    demand = col(d, "combined_demand_score")
    res_active = col(d, "residual_active_flag")
    applied_active = col(d, "applied_residual_active_flag")
    mag = chan_applied_mag(d)
    hi = m & (demand >= HIGH_DEMAND_MIN)
    lo = m & (demand < BIN_EDGES[1])
    dd, mm = demand[m], mag[m]
    corr = float(np.corrcoef(dd, mm)[0, 1]) if (dd.size > 2 and np.std(dd) > 1e-9 and np.std(mm) > 1e-9) else float("nan")
    invalid = int(np.sum([str(x) == "invalid_sensor" for x in d["control_mode"]])) if "control_mode" in d else 0
    return {
        "n_rows": int(len(col(d, "t"))), "n_active_rows": int(m.sum()),
        "mean_abs_pitch_err_deg": float(np.nanmean(pe[m])), "p95_abs_pitch_err_deg": float(np.nanpercentile(pe[m], 95)),
        "max_abs_pitch_err_deg": float(np.nanmax(pe[m])),
        "mean_abs_yaw_err_deg": float(np.nanmean(ye[m])), "p95_abs_yaw_err_deg": float(np.nanpercentile(ye[m], 95)),
        "max_abs_yaw_err_deg": float(np.nanmax(ye[m])),
        "mean_abs_left_v": float(np.nanmean(ul[m])), "max_abs_left_v": float(np.nanmax(ul[m])),
        "mean_abs_right_v": float(np.nanmean(ur[m])), "max_abs_right_v": float(np.nanmax(ur[m])),
        "saturation_ratio": float(np.nanmean(col(d, "channel_saturated")[m])),
        "residual_active_fraction": float(np.nanmean(res_active[m])),
        "applied_active_fraction": float(np.nanmean(applied_active[m])),
        "applied_residual_energy": float(np.nansum(col(d, "applied_residual_energy"))),
        "low_demand_applied_active_fraction": float(np.nanmean(applied_active[lo])) if lo.any() else float("nan"),
        "high_demand_applied_active_fraction": float(np.nanmean(applied_active[hi])) if hi.any() else float("nan"),
        "high_demand_mean_abs_pitch_err_deg": float(np.nanmean(pe[hi])) if hi.any() else float("nan"),
        "high_demand_mean_abs_yaw_err_deg": float(np.nanmean(ye[hi])) if hi.any() else float("nan"),
        "corr_demand_vs_applied_mag": corr,
        "invalid_sensor_rows": invalid,
    }


def demand_binned(d, cond):
    m = active_mask(d)
    demand = col(d, "combined_demand_score")
    pe = np.degrees(np.abs(col(d, "pitch_error")))
    ye = np.degrees(np.abs(col(d, "yaw_error")))
    applied_active = col(d, "applied_residual_active_flag")
    applied_e = col(d, "applied_residual_energy")
    out = []
    for i, lbl in enumerate(BIN_LABELS):
        sel = m & (demand >= BIN_EDGES[i]) & (demand < BIN_EDGES[i + 1])
        out.append({
            "condition": cond, "demand_bin": lbl, "n_rows": int(sel.sum()),
            "mean_abs_pitch_err_deg": float(np.nanmean(pe[sel])) if sel.any() else float("nan"),
            "mean_abs_yaw_err_deg": float(np.nanmean(ye[sel])) if sel.any() else float("nan"),
            "applied_active_fraction": float(np.nanmean(applied_active[sel])) if sel.any() else float("nan"),
            "applied_residual_energy": float(np.nansum(applied_e[sel])) if sel.any() else 0.0,
        })
    return out


# ---------------------------------------------------------------- plots
def fig_overlay(d, cond, outdir):
    t = col(d, "t")
    fig, ax = plt.subplots(5, 1, figsize=(12, 12), sharex=True)
    ax[0].plot(t, np.degrees(col(d, "theta")), label="theta"); ax[0].plot(t, np.degrees(col(d, "theta_ref")), "--", label="ref"); ax[0].set_ylabel("pitch (deg)"); ax[0].legend(fontsize=7)
    ax[1].plot(t, np.degrees(col(d, "psi")), label="psi"); ax[1].plot(t, np.degrees(col(d, "psi_ref")), "--", label="ref"); ax[1].set_ylabel("yaw (deg)"); ax[1].legend(fontsize=7)
    ax[2].plot(t, col(d, "total_left_voltage"), label="left"); ax[2].plot(t, col(d, "total_right_voltage"), label="right"); ax[2].set_ylabel("motor V"); ax[2].legend(fontsize=7)
    ax[3].plot(t, col(d, "combined_demand_score"), color="#d62728", label="demand"); ax[3].plot(t, col(d, "gate_state"), color="#2ca02c", label="gate"); ax[3].set_ylabel("demand/gate"); ax[3].set_ylim(-0.02, 1.02); ax[3].legend(fontsize=7)
    ax[4].plot(t, col(d, "pitch_residual_applied"), label="pitch res"); ax[4].plot(t, col(d, "yaw_residual_applied"), label="yaw res"); ax[4].set_ylabel("applied res (V)"); ax[4].set_xlabel("time (s)"); ax[4].legend(fontsize=7)
    for a in ax:
        a.grid(alpha=0.3)
    fig.suptitle(f"Aero2 condition: {cond}")
    fig.tight_layout(rect=[0, 0, 1, 0.98])
    fig.savefig(outdir / f"overlay_{cond}.png", dpi=150)
    plt.close(fig)


def _bar(ax, conds, vals, title):
    ax.bar(range(len(conds)), vals, color="#4c72b0", edgecolor="black", linewidth=0.5)
    ax.set_xticks(range(len(conds))); ax.set_xticklabels(conds, rotation=20, ha="right", fontsize=8)
    ax.set_title(title, fontsize=10); ax.grid(axis="y", alpha=0.3)
    for i, v in enumerate(vals):
        if v == v:
            ax.text(i, v, f"{v:.3g}", ha="center", va="bottom", fontsize=7)


def fig_comparison(summ, outdir):
    conds = list(summ)
    metrics = [("mean_abs_pitch_err_deg", "mean |pitch err| (deg)"),
               ("mean_abs_yaw_err_deg", "mean |yaw err| (deg)"),
               ("high_demand_mean_abs_pitch_err_deg", "high-demand |pitch err| (deg)"),
               ("mean_abs_left_v", "mean |left V|"),
               ("applied_active_fraction", "applied active fraction"),
               ("applied_residual_energy", "applied residual energy")]
    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    for ax, (k, ttl) in zip(axes.flat, metrics):
        _bar(ax, conds, [summ[c].get(k, float("nan")) for c in conds], ttl)
    fig.suptitle("Aero2 residual condition comparison (active control)")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(outdir / "condition_comparison.png", dpi=150); plt.close(fig)


def fig_binned(binned, outdir):
    conds = sorted({b["condition"] for b in binned})
    # activity
    for metric, fname, title in [("applied_active_fraction", "demand_binned_activity.png", "Applied active fraction by demand bin"),
                                 ("mean_abs_pitch_err_deg", "demand_binned_error.png", "Mean |pitch err| (deg) by demand bin")]:
        fig, ax = plt.subplots(figsize=(11, 5))
        w = 0.8 / max(1, len(conds))
        for i, c in enumerate(conds):
            vals = [next((b[metric] for b in binned if b["condition"] == c and b["demand_bin"] == lb), float("nan")) for lb in BIN_LABELS]
            ax.bar(np.arange(len(BIN_LABELS)) + (i - (len(conds) - 1) / 2) * w, vals, w, label=c)
        ax.set_xticks(range(len(BIN_LABELS))); ax.set_xticklabels(BIN_LABELS)
        ax.set_title(title); ax.grid(axis="y", alpha=0.3); ax.legend(fontsize=8)
        fig.tight_layout(); fig.savefig(outdir / fname, dpi=150); plt.close(fig)


def fig_energy(summ, outdir):
    conds = list(summ)
    fig, ax = plt.subplots(figsize=(9, 5))
    _bar(ax, conds, [summ[c]["applied_residual_energy"] for c in conds], "Total applied residual energy (V^2 s)")
    fig.tight_layout(); fig.savefig(outdir / "residual_energy.png", dpi=150); plt.close(fig)


def write_report(summ, outdir, sources):
    L = ["# Aero2 residual condition comparison", "", f"- Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
         f"- Conditions: {', '.join(summ)}", "", "## Per-condition summary (active control)"]
    keys = ["mean_abs_pitch_err_deg", "p95_abs_pitch_err_deg", "max_abs_pitch_err_deg",
            "mean_abs_yaw_err_deg", "high_demand_mean_abs_pitch_err_deg", "mean_abs_left_v", "max_abs_left_v",
            "saturation_ratio", "residual_active_fraction", "applied_active_fraction",
            "low_demand_applied_active_fraction", "high_demand_applied_active_fraction",
            "applied_residual_energy", "corr_demand_vs_applied_mag", "invalid_sensor_rows"]
    L.append("| condition | " + " | ".join(keys) + " |")
    L.append("|" + "---|" * (len(keys) + 1))
    for c, s in summ.items():
        L.append("| " + c + " | " + " | ".join(f"{s[k]:.4g}" if isinstance(s.get(k), float) else str(s.get(k)) for k in keys) + " |")
    L += ["", "## Decision logic (selectivity + timing + cost)"]

    def hp(c):
        return summ.get(c, {}).get("high_demand_mean_abs_pitch_err_deg", float("nan"))
    if "gate" in summ:
        L.append(f"- gate low-demand applied activity = {summ['gate'].get('low_demand_applied_active_fraction', float('nan')):.3g} "
                 f"(should be ~0 -> selective/dormant at low demand).")
        L.append(f"- gate high-demand applied activity = {summ['gate'].get('high_demand_applied_active_fraction', float('nan')):.3g} "
                 f"(should be > low-demand -> activates on transients/perturbations).")
    if "gate" in summ and "shuffled_gate" in summ:
        dd = hp("shuffled_gate") - hp("gate")
        L.append(f"- gate vs shuffled_gate (high-demand |pitch err|): shuffled={hp('shuffled_gate'):.3g}, gate={hp('gate'):.3g}, "
                 f"gate-better-by={dd:+.3g} deg -> **{'TIMING MATTERS' if dd > 1e-6 else 'timing weak (gate ~ shuffled)'}**.")
    if "gate" in summ and "always_on" in summ:
        eg, ea = summ["gate"]["applied_residual_energy"], summ["always_on"]["applied_residual_energy"]
        L.append(f"- gate vs always_on (cost): applied energy gate={eg:.3g} vs always_on={ea:.3g} "
                 f"({'gating saves actuation' if eg < ea else 'no saving'}); high-demand |pitch err| "
                 f"gate={hp('gate'):.3g} vs always_on={hp('always_on'):.3g}.")
    L += ["", "> Rules: gate quiet at low demand + active in high-demand bins => selective/demand-triggered. "
          "gate < shuffled in high-demand error => timing matters. gate ~ always_on error at lower energy => "
          "selectivity earns its place. Classical controller remains the stability anchor in all conditions.",
          "", "## Sources"] + [f"- {c}: `{p}`" for c, p in sources.items()]
    (outdir / "comparison_report.md").write_text("\n".join(L), encoding="utf-8")


def run_compare(logs):
    ts = time.strftime("%Y%m%d_%H%M%S")
    outdir = PROJECT_ROOT / "analysis" / f"aero2_residual_comparison_{ts}"
    outdir.mkdir(parents=True, exist_ok=True)
    summ, binned, sources = {}, [], {}
    for p in logs:
        d = read_log(p)
        c = label_of(d, p); base, k = c, 2
        while c in summ:
            c = f"{base}_{k}"; k += 1
        summ[c] = summarize(d); binned += demand_binned(d, c); sources[c] = str(p)
        fig_overlay(d, c, outdir)
    with (outdir / "condition_summary.csv").open("w", newline="", encoding="utf-8") as f:
        keys = list(next(iter(summ.values())).keys())
        w = csv.writer(f); w.writerow(["condition"] + keys)
        for c, s in summ.items():
            w.writerow([c] + [s[k] for k in keys])
    with (outdir / "demand_binned_metrics.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(binned[0].keys())); w.writeheader(); w.writerows(binned)
    fig_comparison(summ, outdir); fig_binned(binned, outdir); fig_energy(summ, outdir)
    write_report(summ, outdir, sources)
    print(f"Comparison written to: {outdir}")
    for c, s in summ.items():
        print(f"  {c:14s} pitch|err|={s['mean_abs_pitch_err_deg']:.2f}deg  "
              f"applied_active={s['applied_active_fraction']:.3f}  energy={s['applied_residual_energy']:.4g}  "
              f"low_demand_active={s['low_demand_applied_active_fraction']:.3f}")
    return outdir


# ---------------------------------------------------------------- demo
def make_demo_logs():
    """Synthesize one CSV per condition with the REAL Aero2GateResidual + the runner's apply
    logic over a scripted pitch profile. TOY (no closed-loop feedback): error identical across
    conditions by construction -> validates the comparison PIPELINE and the activity/energy
    metrics, not the control science (hardware provides the closed-loop response)."""
    sys.path.insert(0, str(PROJECT_ROOT))
    from aero2_residual.residual_gate import Aero2GateResidual
    fs, dt, dur = 250.0, 1 / 250.0, 30.0
    n = int(dur * fs); vlim, cap = 24.0, 0.5
    out = PROJECT_ROOT / "results" / "residual"; out.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    fns = ["t", "control_mode", "theta", "theta_ref", "pitch_error", "theta_rate", "psi", "psi_ref",
           "yaw_error", "psi_rate", "total_left_voltage", "total_right_voltage", "base_left_voltage",
           "base_right_voltage", "combined_demand_score", "pitch_demand_score", "yaw_demand_score",
           "gate_state", "residual_active_flag", "applied_residual_active_flag", "applied_residual_energy",
           "pitch_residual_applied", "yaw_residual_applied", "left_residual_applied", "right_residual_applied",
           "channel_saturated", "residual_mode", "residual_max_voltage"]

    def pitch_deg(t):  # square-wave transitions + 2 manual-perturbation bumps
        sq = 12.0 if (0.05 * t - math.floor(0.05 * t)) >= 0.5 else -12.0
        bump = sum(8.0 * math.sin(math.pi * (t - tp) / 0.8) for tp in (12.0, 22.0) if tp <= t < tp + 0.8)
        return 0.15 * sq + bump  # mostly near-equilibrium with transitions + bumps

    paths = []
    for mode in ("none", "shadow_gate", "gate", "always_on", "shuffled_gate"):
        g = Aero2GateResidual("adaptive_hyperlif", dt, 0.15, 0.20, cap)
        buf = deque(maxlen=int(5.0 * fs))
        p = out / f"aero2_DEMO_{mode}_{stamp}.csv"
        prev = math.radians(pitch_deg(0))
        with p.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fns); w.writeheader()
            for i in range(n):
                t = i * dt
                th = math.radians(pitch_deg(t)); thr = 0.0
                pe = thr - th; pr = (th - prev) / dt; prev = th
                u_pitch = float(np.clip(-12.0 * pe - 1.0 * pr, -vlim, vlim))
                base_left, base_right = u_pitch, 0.0  # direct mapping, pitch->ch0
                pd, yd, cd, sat = g.demand_scores(pe, pr, 0.0, 0.0, u_pitch, 0.0, vlim)
                gg = g.step_gate(cd); pc, yc, cp, cy = g.candidates(gg["gate_state"], cd, pe, 0.0)
                pr_app = 0.0
                active = t >= 1.0
                if mode in ("gate", "always_on", "shuffled_gate") and active:
                    if mode == "gate":
                        vp = pc
                    elif mode == "always_on":
                        vp = cap * cp
                    else:
                        gs_, ds_ = (buf[0] if len(buf) == buf.maxlen else (0.0, 0.0)); buf.append((gg["gate_state"], cd))
                        vp = cap * cp * gs_ * ds_
                    pr_app = float(np.clip(vp, -cap, cap))
                elif mode == "shuffled_gate":
                    buf.append((gg["gate_state"], cd))
                total_left = float(np.clip(base_left + pr_app, -vlim, vlim)); total_right = base_right
                lre = total_left - base_left
                w.writerow({"t": t, "control_mode": "active" if active else "startup", "theta": th, "theta_ref": thr,
                            "pitch_error": pe, "theta_rate": pr, "psi": 0.0, "psi_ref": 0.0, "yaw_error": 0.0, "psi_rate": 0.0,
                            "total_left_voltage": total_left, "total_right_voltage": total_right,
                            "base_left_voltage": base_left, "base_right_voltage": base_right,
                            "combined_demand_score": cd, "pitch_demand_score": pd, "yaw_demand_score": yd,
                            "gate_state": gg["gate_state"], "residual_active_flag": gg["residual_active_flag"],
                            "applied_residual_active_flag": 1.0 if abs(lre) > 1e-3 else 0.0,
                            "applied_residual_energy": lre ** 2 * dt, "pitch_residual_applied": pr_app,
                            "yaw_residual_applied": 0.0, "left_residual_applied": lre, "right_residual_applied": 0.0,
                            "channel_saturated": int(abs(total_left) >= vlim - 1e-9), "residual_mode": mode,
                            "residual_max_voltage": cap})
        paths.append(p); print(f"[demo] wrote {p.name}")
    return paths


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", action="append", type=Path)
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args(argv)
    logs = list(a.log or [])
    if a.demo:
        logs = make_demo_logs() + logs
    if not logs:
        ap.error("provide --log <csv> (repeatable) or --demo")
    run_compare(logs)


if __name__ == "__main__":
    main()
