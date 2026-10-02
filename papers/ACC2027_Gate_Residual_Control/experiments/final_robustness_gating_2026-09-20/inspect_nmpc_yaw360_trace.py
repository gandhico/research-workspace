import csv
from pathlib import Path

BASE = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\final_robustness_gating_2026-09-20\results\a5_controllers\nmpc\x2\yaw360")


def load(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


for arm in ("classical", "nengo-nef-pes"):
    rows = load(BASE / arm / "trace.csv")
    n = len(rows)
    qerr = [float(r["qerr_true_rad"]) for r in rows]
    print(f"\n=== {arm} ===  rows={n}")
    tail = qerr[-max(1, n // 10):]
    print("qerr_true_rad: mean=%.6f  max=%.6f  last-10%%-mean=%.6f" % (
        sum(qerr) / n, max(qerr), sum(tail) / len(tail)))

    win = [r for r in rows if float(r["t"]) < 0.2]
    print("tau0_z first 200ms (period should look like a 10ms staircase, log period 5ms):")
    for r in win:
        print(f"  t={float(r['t']):.4f}  tau0_z={float(r['tau0_z']):+.6f}")

    if arm == "nengo-nef-pes":
        print("\ngated_residual_z / decoder_w_0..2 / pes_error_z, same window:")
        for r in win:
            print(f"  t={float(r['t']):.4f}  gres_z={float(r['gated_residual_z']):+.6f}  "
                  f"w0={float(r['decoder_w_0']):+.4f}  w1={float(r['decoder_w_1']):+.4f}  "
                  f"w2={float(r['decoder_w_2']):+.4f}  pes_err_z={float(r['pes_error_z']):+.6f}")
        wcols = [k for k in rows[0].keys() if k.startswith("decoder_w_")]
        print("\ndecoder_w_* range over full run:")
        for c in wcols:
            vals = [float(r[c]) for r in rows]
            print(f"  {c}: min={min(vals):+.4f} max={max(vals):+.4f} final={vals[-1]:+.4f}")
        gres = [float(r["gated_residual_z"]) for r in rows]
        mean_g = sum(gres) / n
        std_g = (sum((v - mean_g) ** 2 for v in gres) / n) ** 0.5
        print("\ngated_residual_z stats: mean=%.6f std=%.6f min=%.6f max=%.6f" % (
            mean_g, std_g, min(gres), max(gres)))
