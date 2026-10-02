"""
Generate publication-quality comparison figures: classical vs HyperLIF overlay.

Usage:
    python runners/make_comparison_figures.py --quad skydio_x2 --mission hard45

Reads the latest CSV for each controller from results/logs/ and overlays them.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

_HERE    = Path(__file__).resolve().parent
_PROJECT = _HERE.parent

COLORS = {
    "classical":              "#1f77b4",
    "direct_lif":             "#d62728",
    "direct_hyperlif":        "#2ca02c",
    "direct_adaptive_hyperlif": "#ff7f0e",
    "direct_izhikevich":      "#9467bd",
    "nengo_lifrate":          "#8c564b",
    "rotor_residual_hyperlif": "#17becf",
    "rotor_residual_adaptive_hyperlif": "#bcbd22",
}
LABELS = {
    "classical":               "Classical PD",
    "direct_lif":              "Direct LIF",
    "direct_hyperlif":         "HyperLIF (gate)",
    "direct_adaptive_hyperlif":"Adaptive HyperLIF",
    "direct_izhikevich":       "Izhikevich",
    "nengo_lifrate":           "Nengo LIF-Rate",
    "rotor_residual_hyperlif": "Rotor Residual HyperLIF",
    "rotor_residual_adaptive_hyperlif": "Rotor Residual Adaptive HyperLIF",
}


def latest_csv(logs_dir: Path, quad: str, mission: str, controller: str) -> Path | None:
    pattern = f"{quad}_{mission}_{controller}_*.csv"
    # Exclude summary and config files
    files = [f for f in logs_dir.glob(pattern)
             if "summary" not in f.name and "config" not in f.name]
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def load_csv(path: Path) -> dict[str, np.ndarray]:
    import csv
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        return {}
    arr = {}
    for k in rows[0]:
        try:
            arr[k] = np.array([float(r[k]) for r in rows])
        except (ValueError, KeyError):
            pass
    return arr


def make_comparison(quad: str, mission: str, controllers: list[str],
                    output_dir: Path, sim_time: float | None = None) -> None:
    logs_dir = _PROJECT / "results" / "logs"
    output_dir.mkdir(parents=True, exist_ok=True)

    datasets: dict[str, dict] = {}
    for ctrl in controllers:
        p = latest_csv(logs_dir, quad, mission, ctrl)
        if p is None:
            print(f"  No CSV found for {ctrl}, skipping.")
            continue
        d = load_csv(p)
        if not d:
            print(f"  Empty CSV for {ctrl}, skipping.")
            continue
        datasets[ctrl] = d
        print(f"  Loaded {ctrl}: {len(d.get('t',[])):,} rows from {p.name}")

    if len(datasets) < 2:
        print("Need at least 2 controllers. Skipping.")
        return

    t_max = sim_time
    for d in datasets.values():
        if "t" in d and t_max is None:
            t_max = float(d["t"][-1])

    # ─── Figure 1: Euler angle tracking comparison ───────────────────────────
    fig, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
    angle_keys = [("phi","phi_ref","Roll φ [°]"),
                  ("theta","theta_ref","Pitch θ [°]"),
                  ("psi","psi_ref","Yaw ψ [°]")]
    for i, (k, kref, ylabel) in enumerate(angle_keys):
        for ctrl, d in datasets.items():
            if k not in d:
                continue
            t = d["t"]
            axes[i].plot(t, np.degrees(d[k]),
                         color=COLORS.get(ctrl,"gray"),
                         linewidth=1.2, alpha=0.85,
                         label=LABELS.get(ctrl, ctrl))
        if kref in next(iter(datasets.values())):
            d0 = next(iter(datasets.values()))
            axes[i].plot(d0["t"], np.degrees(d0[kref]),
                         "k--", linewidth=1.5, alpha=0.5, label="Reference")
        axes[i].set_ylabel(ylabel, fontsize=10)
        axes[i].grid(True, alpha=0.25)
    axes[0].legend(fontsize=8, loc="upper right")
    axes[-1].set_xlabel("Time [s]", fontsize=10)
    fig.suptitle(f"Euler Angle Tracking — {quad.replace('_',' ')} | {mission}", fontsize=11)
    fig.tight_layout()
    out = output_dir / f"compare_{quad}_{mission}_euler.pdf"
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(str(out).replace(".pdf", ".png"), dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")

    # ─── Figure 2: Quaternion error angle ────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 4))
    for ctrl, d in datasets.items():
        if "qerr_angle" not in d:
            continue
        label = LABELS.get(ctrl, ctrl)
        # Compute qerr_mean
        qerr_mean = float(np.mean(d["qerr_angle"]))
        ax.plot(d["t"], d["qerr_angle"],
                color=COLORS.get(ctrl, "gray"),
                linewidth=1.2, alpha=0.85,
                label=f"{label}  (mean={qerr_mean:.4f} rad)")
    ax.set_ylabel("Quaternion error angle [rad]", fontsize=10)
    ax.set_xlabel("Time [s]", fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.25)
    ax.set_title(f"Attitude Tracking Error — {quad.replace('_',' ')} | {mission}", fontsize=11)
    fig.tight_layout()
    out = output_dir / f"compare_{quad}_{mission}_qerr.pdf"
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(str(out).replace(".pdf", ".png"), dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")

    # ─── Figure 3: Gate state dynamics (if available) ────────────────────────
    has_gate = any("gate_mean" in d and np.max(d["gate_mean"]) > 1e-8
                   for d in datasets.values())
    if has_gate:
        fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
        for ctrl, d in datasets.items():
            if "gate_mean" not in d or np.max(d["gate_mean"]) < 1e-8:
                continue
            axes[0].plot(d["t"], d["gate_mean"],
                         color=COLORS.get(ctrl, "gray"),
                         linewidth=1.0, alpha=0.85,
                         label=LABELS.get(ctrl, ctrl))
            if "voltage_mean" in d:
                axes[1].plot(d["t"], d["voltage_mean"],
                             color=COLORS.get(ctrl, "gray"),
                             linewidth=1.0, alpha=0.85,
                             label=LABELS.get(ctrl, ctrl))
        axes[0].set_ylabel("Gate state r (mean)", fontsize=10)
        axes[0].legend(fontsize=8); axes[0].grid(True, alpha=0.25)
        axes[1].set_ylabel("Membrane voltage (mean)", fontsize=10)
        axes[1].set_xlabel("Time [s]", fontsize=10); axes[1].grid(True, alpha=0.25)
        fig.suptitle(f"Neural Gate Dynamics — {quad.replace('_',' ')} | {mission}", fontsize=11)
        fig.tight_layout()
        out = output_dir / f"compare_{quad}_{mission}_gate.pdf"
        fig.savefig(out, bbox_inches="tight")
        fig.savefig(str(out).replace(".pdf", ".png"), dpi=180, bbox_inches="tight")
        plt.close(fig)
        print(f"  Saved: {out.name}")

    # ─── Figure 4: Control torques ───────────────────────────────────────────
    fig, axes = plt.subplots(3, 1, figsize=(10, 7), sharex=True)
    torque_keys = [("tau_x", "τ_x [Nm]"), ("tau_y", "τ_y [Nm]"), ("tau_z", "τ_z [Nm]")]
    for i, (k, ylabel) in enumerate(torque_keys):
        for ctrl, d in datasets.items():
            if k not in d:
                continue
            axes[i].plot(d["t"], d[k],
                         color=COLORS.get(ctrl, "gray"),
                         linewidth=1.0, alpha=0.8,
                         label=LABELS.get(ctrl, ctrl))
        axes[i].set_ylabel(ylabel, fontsize=9)
        axes[i].grid(True, alpha=0.25)
    axes[0].legend(fontsize=8, loc="upper right")
    axes[-1].set_xlabel("Time [s]", fontsize=10)
    fig.suptitle(f"Control Torques — {quad.replace('_',' ')} | {mission}", fontsize=11)
    fig.tight_layout()
    out = output_dir / f"compare_{quad}_{mission}_torques.pdf"
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(str(out).replace(".pdf", ".png"), dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")

    print(f"\nAll comparison figures saved to: {output_dir}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--quad",    default="skydio_x2")
    p.add_argument("--mission", default="hard45")
    p.add_argument("--controllers", default=None,
                   help="Comma-separated list. Default: all found in logs.")
    p.add_argument("--output-dir", type=Path, default=None)
    p.add_argument("--sim-time", type=float, default=None)
    args = p.parse_args()

    logs_dir = _PROJECT / "results" / "logs"
    if args.controllers:
        controllers = [c.strip() for c in args.controllers.split(",")]
    else:
        # Auto-discover from CSV filenames
        prefix = f"{args.quad}_{args.mission}_"
        seen: set[str] = set()
        for f in logs_dir.glob(f"{prefix}*.csv"):
            if "summary" in f.name or "config" in f.name:
                continue
            # Extract controller name: everything between mission_ and _dt
            rest = f.name[len(prefix):]
            m = re.match(r"(.+?)_dt", rest)
            if m:
                seen.add(m.group(1))
        controllers = sorted(seen)
        print(f"Auto-discovered controllers: {controllers}")

    if not controllers:
        print("No controllers found. Run simulations first.")
        return

    out_dir = args.output_dir or (_PROJECT / "results" / "figures")
    print(f"\nGenerating comparison figures:")
    print(f"  quad: {args.quad}, mission: {args.mission}")
    print(f"  controllers: {controllers}")
    make_comparison(args.quad, args.mission, controllers, out_dir, args.sim_time)


if __name__ == "__main__":
    main()
