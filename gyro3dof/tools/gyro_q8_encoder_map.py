"""Read-only encoder mapping for the 3 DOF Gyroscope (Q8-USB). Writes NOTHING to the board.

The operator turns each axis by hand in turn (gray, red, blue, disc) while encoders 0-7 are
logged; this reports which channel moved, when, by how much (counts and degrees), and in which
direction first. Counts/rev from Quanser's q_3dgyro_lqr.mdl: enc0 disc 4096, enc1-3 gimbals 4000.
"""
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
from quanser.hardware import HIL, HILError

CPR = [4096, 4000, 4000, 4000, 4000, 4000, 4000, 4000]


def main(duration=40.0, rate_hz=50.0, label="all"):
    out = Path(__file__).resolve().parents[1] / "hw_logs"
    out.mkdir(exist_ok=True)
    tag = time.strftime("%Y%m%d_%H%M%S") + f"_q8_encoder_map_{label}"
    card = HIL()
    card.open("q8_usb", "0")
    ch = np.arange(8, dtype=np.uint32)
    buf = np.zeros(8, dtype=np.int32)
    T, E = [], []
    try:
        t0 = time.perf_counter()
        for k in range(int(duration * rate_hz)):
            while time.perf_counter() < t0 + k / rate_hz:
                pass
            card.read_encoder(ch, 8, buf)
            T.append(time.perf_counter() - t0); E.append(buf.copy())
            if k % int(5 * rate_hz) == 0:
                print(f"t={T[-1]:5.1f}s counts={buf.tolist()}", flush=True)
    finally:
        card.close()
    T, E = np.array(T), np.array(E)
    with (out / f"{tag}.csv").open("w", newline="") as f:
        w = csv.writer(f); w.writerow(["t"] + [f"enc{i}" for i in range(8)]); w.writerows(np.column_stack([T, E]))
    rep = {"duration_s": float(T[-1]), "channels": {}}
    for i in range(8):
        e = E[:, i]
        moving = np.flatnonzero(np.abs(np.diff(e)) > 0)
        if len(moving) == 0:
            rep["channels"][f"enc{i}"] = {"moved": False}
            continue
        first_dir = int(np.sign(e[moving[0] + 1] - e[moving[0]]))
        rep["channels"][f"enc{i}"] = {
            "moved": True, "active_from_s": round(float(T[moving[0]]), 1), "active_to_s": round(float(T[moving[-1] + 1]), 1),
            "min": int(e.min()), "max": int(e.max()), "span_counts": int(e.max() - e.min()),
            "span_deg": round((e.max() - e.min()) * 360.0 / CPR[i], 1),
            "final_counts": int(e[-1]), "final_deg": round(e[-1] * 360.0 / CPR[i], 1), "first_direction": first_dir}
    order = sorted([k for k, v in rep["channels"].items() if v["moved"]], key=lambda k: rep["channels"][k]["active_from_s"])
    rep["order_moved"] = order
    # Motion bursts per channel (gaps > 1.5 s split bursts), to separate "one axis at a time" moves.
    bursts = []
    for i in range(8):
        idx = np.flatnonzero(np.abs(np.diff(E[:, i])) > 0)
        if len(idx) == 0:
            continue
        start = prev = idx[0]
        for j in list(idx[1:]) + [None]:
            if j is None or T[j] - T[prev] > 1.5:
                seg = E[start:prev + 2, i]
                if seg.max() - seg.min() >= 5:   # ignore 1-4 count jitter/knocks
                    bursts.append({"enc": i, "from_s": round(float(T[start]), 1), "to_s": round(float(T[prev + 1]), 1),
                                   "span_counts": int(seg.max() - seg.min()),
                                   "span_deg": round((seg.max() - seg.min()) * 360.0 / CPR[i], 1)})
                if j is not None:
                    start = j
            if j is not None:
                prev = j
    rep["bursts_in_time_order"] = sorted(bursts, key=lambda b: b["from_s"])
    rep["log"] = str(out / f"{tag}.csv")
    (out / f"{tag}.json").write_text(json.dumps(rep, indent=2))
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    try:
        # usage: gyro_q8_encoder_map.py [seconds] [axis-label, e.g. gray|red|blue|disc]
        main(duration=float(sys.argv[1]) if len(sys.argv) > 1 else 40.0,
             label=sys.argv[2] if len(sys.argv) > 2 else "all")
    except HILError as e:
        print("HIL ERROR:", e.get_error_message()); sys.exit(2)
