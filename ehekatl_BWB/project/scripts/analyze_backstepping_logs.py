#!/usr/bin/env python3
import argparse
import csv
import glob
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


def read_log(path):
    rows = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    def col(name, default=np.nan):
        out = []
        for r in rows:
            try:
                out.append(float(r.get(name, default)))
            except Exception:
                out.append(np.nan)
        return np.asarray(out, dtype=float)

    return {
        "t": col("t_s"),
        "pitch": col("pitch_deg"),
        "roll": col("roll_deg"),
        "alt": col("alt_m"),
        "ail": col("xpc_ctrl_aileron"),
        "ele": col("xpc_ctrl_elevator"),
        "roll_output": col("roll_output"),
        "pitch_output": col("pitch_output"),
    }


def metrics(data, pitch_sp, roll_sp):
    t = data["t"]
    if len(t) < 5:
        return {}

    duration = t[-1] - t[0]
    start_eval = max(t[0], t[-1] - min(15.0, 0.5 * duration))
    idx = t >= start_eval

    pitch_err = data["pitch"] - pitch_sp
    roll_err = data["roll"] - roll_sp

    def rms(x):
        return float(np.sqrt(np.nanmean(x * x)))

    def p2p(x):
        return float(np.nanmax(x) - np.nanmin(x))

    def maxabs(x):
        return float(np.nanmax(np.abs(x)))

    # Rough oscillation count from pitch-error zero crossings in final window
    pe = pitch_err[idx]
    tt = t[idx]
    finite = np.isfinite(pe)
    pe = pe[finite]
    tt = tt[finite]
    zero_cross = 0
    osc_hz = 0.0
    if len(pe) > 3:
        signs = np.sign(pe)
        signs[signs == 0] = 1
        zero_cross = int(np.sum(signs[1:] * signs[:-1] < 0))
        if tt[-1] > tt[0]:
            osc_hz = (zero_cross / 2.0) / (tt[-1] - tt[0])

    return {
        "duration_s": float(duration),
        "pitch_rms_final_deg": rms(pitch_err[idx]),
        "roll_rms_final_deg": rms(roll_err[idx]),
        "pitch_p2p_final_deg": p2p(data["pitch"][idx]),
        "roll_p2p_final_deg": p2p(data["roll"][idx]),
        "max_abs_aileron": maxabs(data["ail"]),
        "max_abs_elevator": maxabs(data["ele"]),
        "pitch_zero_crossings_final": zero_cross,
        "pitch_osc_hz_final": float(osc_hz),
        "final_pitch_deg": float(data["pitch"][-1]),
        "final_roll_deg": float(data["roll"][-1]),
        "final_alt_m": float(data["alt"][-1]),
    }


def plot_log(path, data, pitch_sp, roll_sp, outdir):
    name = Path(path).stem
    t = data["t"]

    fig, ax = plt.subplots(4, 1, figsize=(11, 10), sharex=True)

    ax[0].plot(t, data["pitch"], label="pitch")
    ax[0].axhline(pitch_sp, linestyle="--", label="pitch setpoint")
    ax[0].set_ylabel("Pitch [deg]")
    ax[0].grid(True)
    ax[0].legend()

    ax[1].plot(t, data["roll"], label="roll")
    ax[1].axhline(roll_sp, linestyle="--", label="roll setpoint")
    ax[1].set_ylabel("Roll [deg]")
    ax[1].grid(True)
    ax[1].legend()

    ax[2].plot(t, data["ail"], label="aileron cmd")
    ax[2].plot(t, data["ele"], label="elevator cmd")
    ax[2].set_ylabel("Stick cmd")
    ax[2].grid(True)
    ax[2].legend()

    ax[3].plot(t, data["alt"], label="altitude")
    ax[3].set_ylabel("Alt [m]")
    ax[3].set_xlabel("Time [s]")
    ax[3].grid(True)
    ax[3].legend()

    fig.suptitle(name)
    fig.tight_layout()

    out_png = outdir / f"{name}_overview.png"
    fig.savefig(out_png, dpi=160)
    plt.close(fig)
    return out_png


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("logs", nargs="+", help="CSV log path or glob, e.g. ../../logs/*.csv")
    ap.add_argument("--pitch-sp", type=float, default=6.0)
    ap.add_argument("--roll-sp", type=float, default=0.0)
    ap.add_argument("--outdir", default="../../logs/plots")
    args = ap.parse_args()

    paths = []
    for item in args.logs:
        matches = glob.glob(item)
        paths.extend(matches if matches else [item])

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    for path in sorted(set(paths)):
        p = Path(path)
        if not p.exists():
            print(f"Missing: {path}")
            continue

        data = read_log(p)
        m = metrics(data, args.pitch_sp, args.roll_sp)
        png = plot_log(p, data, args.pitch_sp, args.roll_sp, outdir)

        print("\n===", p.name, "===")
        for k, v in m.items():
            print(f"{k}: {v:.6g}" if isinstance(v, float) else f"{k}: {v}")
        print("plot:", png)


if __name__ == "__main__":
    main()
