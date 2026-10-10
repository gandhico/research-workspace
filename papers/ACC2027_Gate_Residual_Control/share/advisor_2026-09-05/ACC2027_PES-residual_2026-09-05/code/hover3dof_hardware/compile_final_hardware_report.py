"""Final compilation of the real 3DOF Hover hardware campaign (PD baseline vs
Nengo CMG-PES), across every mission that produced a completed matched pair.
Two figures per mission (tracking+error, mechanism/neurons), plus a summary
table -- reads trace.csv/summary.json only, no hardware touched.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

# --- portable paths (added for distribution) ---
import sys as _sys, pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from acc2027_paths import HOVER_FINAL, out_dir  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = HOVER_FINAL
OUT = out_dir("hover3dof_hardware_plots")

PAIRS = {
    "hover": ("pd_hover_none_armed_20260901_192613", "nengo-pes_hover_none_armed_20260901_192626"),
    "roll": ("pd_roll_none_armed_20260901_192641", "nengo-pes_roll_none_armed_20260901_192654"),
    "full3": ("pd_full3_none_armed_20260901_192715", "nengo-pes_full3_none_armed_20260901_192733"),
    "hard45": ("pd_hard45_none_armed_20260901_192812", "nengo-pes_hard45_none_armed_20260901_192844"),
    "hardstep": ("pd_hardstep_none_armed_20260901_192904", "nengo-pes_hardstep_none_armed_20260901_192922"),
    "yaw360": ("pd_yaw360_none_armed_20260901_193849", "nengo-pes_yaw360_none_armed_20260901_193929"),
}
YAW360_PD_ONLY = None


def load_trace(run_dir: Path) -> dict[str, np.ndarray]:
    with (run_dir / "trace.csv").open() as f:
        rows = list(csv.DictReader(f))
    cols = rows[0].keys()
    out = {}
    for k in cols:
        try:
            out[k] = np.array([float(r[k]) for r in rows])
        except ValueError:
            pass
    return out


def plot_tracking(mission: str, c: dict, n: dict, c_s: dict, n_s: dict, out_path: Path) -> None:
    fig, axes = plt.subplots(5, 1, figsize=(10, 12), sharex=True,
                              gridspec_kw={"height_ratios": [1.4, 1.4, 1.4, 1.3, 1.3]})
    for i, axis in enumerate(["yaw", "pitch", "roll"]):
        ax = axes[i]
        ax.plot(c["t"], c[f"{axis}_ref_deg"], "k--", lw=1.1, label="reference")
        ax.plot(c["t"], c[f"{axis}_deg"], color="tab:blue", lw=0.9, alpha=0.85, label="PD (baseline)")
        ax.plot(n["t"], n[f"{axis}_deg"], color="tab:red", lw=0.9, alpha=0.85, label="CMG-PES")
        ax.set_ylabel(f"{axis} (deg)")
        ax.legend(loc="upper right", fontsize=7, ncol=3)
        ax.grid(alpha=0.3)
    axes[0].set_title(f"REAL HARDWARE -- 3DOF Hover, mission: {mission} -- yaw/pitch/roll vs reference",
                       fontsize=10, loc="left", fontweight="bold")

    ax = axes[3]
    c_err = np.sqrt(c["yaw_error_wrapped_deg"]**2 + c["pitch_error_deg"]**2 + c["roll_error_deg"]**2)
    n_err = np.sqrt(n["yaw_error_wrapped_deg"]**2 + n["pitch_error_deg"]**2 + n["roll_error_deg"]**2)
    ax.plot(c["t"], c_err, color="tab:blue", lw=0.9, label=f"PD (mean {c_s['angle_err_mean_deg']:.2f} deg)")
    ax.plot(n["t"], n_err, color="tab:red", lw=0.9, label=f"CMG-PES (mean {n_s['angle_err_mean_deg']:.2f} deg)")
    ax.set_ylabel("|angle error| (deg)")
    ax.legend(loc="upper right", fontsize=7)
    ax.grid(alpha=0.3)
    ax.set_title("ERROR -- combined yaw/pitch/roll angle error magnitude", fontsize=10, loc="left", fontweight="bold")

    ax = axes[4]
    for m, col, lbl in zip(["Vf_written", "Vb_written", "Vl_written", "Vr_written"],
                            ["tab:blue", "tab:orange", "tab:green", "tab:purple"],
                            ["front", "back", "left", "right"]):
        ax.plot(n["t"], n[m], lw=0.6, color=col, label=f"{lbl} (CMG-PES)")
    ax.set_ylabel("motor V")
    ax.set_xlabel("time (s)")
    ax.legend(loc="upper right", fontsize=6, ncol=4)
    ax.grid(alpha=0.3)
    ax.set_title("INPUTS -- written motor voltages [front,back,left,right] (CMG-PES)",
                 fontsize=10, loc="left", fontweight="bold")

    imp = 100 * (c_s["angle_err_mean_deg"] - n_s["angle_err_mean_deg"]) / max(1e-9, c_s["angle_err_mean_deg"])
    fig.suptitle(f"Real 3DOF Hover hardware -- mission: {mission}\nCMG-PES improvement: {imp:+.2f}%", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(out_path, dpi=125)
    plt.close(fig)
    print(f"wrote {out_path}")


def plot_mechanism(mission: str, n: dict, out_path: Path) -> None:
    fig, axes = plt.subplots(4, 1, figsize=(10, 10), sharex=True,
                              gridspec_kw={"height_ratios": [1.3, 1.3, 1.3, 1.3]})

    ax = axes[0]
    for ch, col in zip(["requested_delta_tau_yaw", "requested_delta_tau_pitch", "requested_delta_tau_roll"],
                        ["tab:blue", "tab:orange", "tab:green"]):
        ax.plot(n["t"], n[ch], lw=0.7, color=col, label=ch.replace("requested_delta_tau_", ""))
    ax.set_ylabel("residual\ntorque (Nm)")
    ax.legend(loc="upper right", fontsize=7, ncol=3)
    ax.grid(alpha=0.3)
    ax.set_title(f"REAL HARDWARE -- {mission}: CMG-PES requested residual torque [yaw,pitch,roll]",
                 fontsize=10, loc="left", fontweight="bold")

    ax = axes[1]
    for i in range(6):
        ax.plot(n["t"], n[f"neuron_v_{i}"], lw=0.5, alpha=0.7, label=f"unit {i}" if i < 2 else None)
    ax.set_ylabel("membrane v")
    ax.legend(loc="upper right", fontsize=7)
    ax.grid(alpha=0.3)
    ax.set_title("MECHANISM -- CMG membrane potential (6 units, 3 channels)", fontsize=10, loc="left", fontweight="bold")

    ax = axes[2]
    for i in range(6):
        ax.plot(n["t"], n[f"neuron_activity_{i}"], lw=0.5, alpha=0.7)
    ax.set_ylabel("activity")
    ax.grid(alpha=0.3)
    ax.set_title("MECHANISM -- CMG gate-derived activity (6 units)", fontsize=10, loc="left", fontweight="bold")

    ax = axes[3]
    decoder_cols = [c for c in n if c.startswith("decoder_w_")]
    decoder_norm = np.sqrt(sum(n[c]**2 for c in decoder_cols)) if decoder_cols else None
    if decoder_norm is not None:
        ax.plot(n["t"], decoder_norm, color="tab:red", lw=1, label="||W|| (PES decoder)")
    for ch, col in zip(["pes_error_yaw", "pes_error_pitch", "pes_error_roll"],
                        ["tab:blue", "tab:orange", "tab:green"]):
        if ch in n:
            ax.plot(n["t"], n[ch], lw=0.5, alpha=0.6, color=col, label=ch.replace("pes_error_", "pes_err_"))
    ax.set_ylabel("PES / decoder")
    ax.set_xlabel("time (s)")
    ax.legend(loc="upper right", fontsize=6, ncol=4)
    ax.grid(alpha=0.3)
    ax.set_title("MECHANISM -- PES decoder weight norm and per-channel PES error", fontsize=10, loc="left", fontweight="bold")

    fig.suptitle(f"Real 3DOF Hover hardware -- mission: {mission} -- CMG-PES mechanism", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(out_path, dpi=125)
    plt.close(fig)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    rows_summary = []
    for mission, (pd_dir, cmg_dir) in PAIRS.items():
        c_dir, n_dir = ROOT / pd_dir, ROOT / cmg_dir
        c, n = load_trace(c_dir), load_trace(n_dir)
        c_s = json.loads((c_dir / "summary.json").read_text())
        n_s = json.loads((n_dir / "summary.json").read_text())
        plot_tracking(mission, c, n, c_s, n_s, OUT / f"{mission}_hardware_tracking.png")
        plot_mechanism(mission, n, OUT / f"{mission}_hardware_mechanism.png")
        imp = 100 * (c_s["angle_err_mean_deg"] - n_s["angle_err_mean_deg"]) / max(1e-9, c_s["angle_err_mean_deg"])
        rows_summary.append({
            "mission": mission, "pd_mean_deg": c_s["angle_err_mean_deg"], "cmg_mean_deg": n_s["angle_err_mean_deg"],
            "improvement_pct": imp, "pd_max_deg": c_s["angle_err_max_deg"], "cmg_max_deg": n_s["angle_err_max_deg"],
        })

    print("\n=== FINAL REAL-HARDWARE SUMMARY (matched PD vs CMG-PES, 3DOF Hover, direct-Nengo no-GUI path) ===")
    print(f"{'mission':<10}{'pd mean(deg)':>14}{'cmg mean(deg)':>15}{'improvement':>13}{'pd max':>10}{'cmg max':>10}")
    for r in rows_summary:
        print(f"{r['mission']:<10}{r['pd_mean_deg']:>14.3f}{r['cmg_mean_deg']:>15.3f}"
              f"{r['improvement_pct']:>12.2f}%{r['pd_max_deg']:>10.3f}{r['cmg_max_deg']:>10.3f}")
    if YAW360_PD_ONLY is not None:
        yaw_s = json.loads((ROOT / YAW360_PD_ONLY / "summary.json").read_text())
        print(f"{'yaw360':<10}{yaw_s['angle_err_mean_deg']:>14.3f}{'N/A (safety-aborted, CMG not run)':>15}")

    (OUT / "summary_table.json").write_text(json.dumps({"matched_pairs": rows_summary}, indent=2))
    print(f"\nwrote {OUT / 'summary_table.json'}")
