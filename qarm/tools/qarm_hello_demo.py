"""Supervised QArm motion demo: sleep -> home -> base wave -> wrist twist -> gripper -> sleep.

Joint-space waypoints only (Quanser PAL HOME_POSE / SLEEP_POSE), gentle servo
trajectory profiles, Quanser PAL servo gains, and per-sample monitors
(current, temperature, finite data) plus an arrival check at every waypoint.
On any fault the arm is frozen at its measured pose and the board is closed.
Run only with the workspace clear and an operator at the E-stop.
"""
from __future__ import annotations

import csv
import json
import time
from pathlib import Path

import numpy as np
from quanser.hardware import HIL, HILError

POS_IN = np.array([1000, 1001, 1002, 1003, 1004], dtype=np.uint32)
TEMP_IN = np.array([10000, 10001, 10002, 10003, 10004], dtype=np.uint32)
CUR_IN = np.array([5, 6, 7, 8, 9], dtype=np.uint32)
OUT = np.array([1000, 1001, 1002, 1003, 1004, 11005, 11006, 11007], dtype=np.uint32)
CUR_RANGE = np.array([4.4, 8.8, 4.4, 2.3, 1.4])

# Quanser PAL limits (enforced by servo firmware) and poses.
LO = np.array([-17 * np.pi / 18, -17 * np.pi / 36, -19 * np.pi / 36, -8 * np.pi / 9, 0.1])
HI = np.array([17 * np.pi / 18, 17 * np.pi / 36, 15 * np.pi / 36, 8 * np.pi / 9, 0.9])
HOME = [0.0, 0.0, 0.0, 0.0]
SLEEP = [0.0, -17 * np.pi / 36, 15 * np.pi / 36, 0.0]
GAIN_PROPS = np.array([128, 129, 130, 131, 133, 134, 135, 136, 138, 139, 140, 141], dtype=np.int32)
GAIN_VALUES = np.array([8.89] * 4 + [0.012] * 4 + [10.23] * 4, dtype=np.float64)

VEL, ACC = 0.6, 0.6          # rad/s, rad/s^2 (PAL default 1.5708 / 1.0472)
RATE = 50.0
ARRIVE_TOL = np.array([0.03, 0.03, 0.03, 0.03, 0.05])
ARRIVE_TIMEOUT = 8.0         # s per waypoint
CUR_FRAC, CUR_PERSIST = 0.75, 0.3
MAX_TEMP = 60.0

GREEN, BLUE, RED = [0, 1, 0], [0, 0, 1], [1, 0, 0]
# (label, [yaw, shoulder, elbow, wrist], gripper, LED, dwell_s)
SEQUENCE = [
    ("home", HOME, 0.1, GREEN, 1.0),
    ("base left", [0.5, 0, 0, 0], 0.1, GREEN, 0.5),
    ("base right", [-0.5, 0, 0, 0], 0.1, GREEN, 0.5),
    ("base centre", HOME, 0.1, GREEN, 0.5),
    ("wrist +", [0, 0, 0, 0.8], 0.1, BLUE, 0.3),
    ("wrist -", [0, 0, 0, -0.8], 0.1, BLUE, 0.3),
    ("wrist centre", HOME, 0.1, BLUE, 0.5),
    ("gripper close", HOME, 0.7, BLUE, 1.0),
    ("gripper open", HOME, 0.1, GREEN, 1.0),
    ("sleep", SLEEP, 0.1, RED, 1.0),
]


def options():
    parts = []
    for j in range(4):
        parts += [f"j{j}_mode=0", f"j{j}_profile_config=0",
                  f"j{j}_profile_velocity={VEL}", f"j{j}_profile_acceleration={ACC}"]
    return ";".join(parts + ["gripper_mode=0", "gripper_profile_config=0"]) + ";"


def main():
    out_dir = Path(__file__).resolve().parents[1] / "hw_logs"
    tag = time.strftime("%Y%m%d_%H%M%S") + "_hello_demo"
    card = HIL()
    card.open("qarm_usb", "0")
    pos, temp, cur = np.zeros(5), np.zeros(5), np.zeros(5)
    rows, events, fault = [], [], None
    t0 = time.perf_counter()

    def read():
        card.read_other(np.concatenate([POS_IN, TEMP_IN]), 10, buf := np.zeros(10))
        card.read_analog(CUR_IN, 5, cur)
        pos[:], temp[:] = buf[:5], buf[5:]

    def write(q5, led):
        cmd = np.clip(np.asarray(q5, dtype=np.float64), LO, HI)
        card.write_other(OUT, 8, np.concatenate([cmd, np.asarray(led, dtype=np.float64)]))
        return cmd

    try:
        card.set_card_specific_options(options(), len(options()) + 1)
        card.set_double_property(GAIN_PROPS, len(GAIN_PROPS), GAIN_VALUES)
        read()
        events.append({"label": "start", "pos": pos.round(4).tolist()})
        over_since = None
        for label, joints, grip, led, dwell in SEQUENCE:
            target = np.array([*joints, grip])
            print(f"-> {label:14s} target {np.round(target, 3).tolist()}", flush=True)
            seg_t0 = time.perf_counter()
            arrived_at = None
            while True:
                tick = time.perf_counter()
                cmd = write(target, led)
                read()
                t = tick - t0
                rows.append([t, label, *cmd, *pos, *cur, *temp])
                if not np.all(np.isfinite(np.concatenate([pos, cur, temp]))):
                    fault = "non-finite reading"
                elif np.any(temp > MAX_TEMP):
                    fault = f"temperature {temp.round(1).tolist()}"
                else:
                    over = np.any(np.abs(cur) > CUR_FRAC * CUR_RANGE)
                    over_since = (over_since or tick) if over else None
                    if over_since and tick - over_since > CUR_PERSIST:
                        fault = f"current {cur.round(2).tolist()}"
                if fault:
                    break
                err = np.abs(pos - cmd)
                if arrived_at is None and np.all(err < ARRIVE_TOL):
                    arrived_at = tick
                    events.append({"label": label, "arrive_s": round(tick - seg_t0, 2),
                                   "err": err.round(4).tolist(), "cur": cur.round(2).tolist()})
                if arrived_at is not None and tick - arrived_at >= dwell:
                    break
                if arrived_at is None and tick - seg_t0 > ARRIVE_TIMEOUT:
                    fault = f"'{label}' not reached: err {err.round(3).tolist()}"
                    break
                time.sleep(max(0.0, 1.0 / RATE - (time.perf_counter() - tick)))
            if fault:
                print("FAULT:", fault, "- freezing at measured pose", flush=True)
                write(pos.copy(), RED)
                time.sleep(0.5)
                break
    finally:
        card.close()

    with (out_dir / f"{tag}.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["time_s", "segment"] + [f"cmd{i}" for i in range(5)] + [f"pos{i}" for i in range(5)]
                   + [f"cur{i}" for i in range(5)] + [f"temp{i}" for i in range(5)])
        w.writerows(rows)
    a = np.array([r[2:] for r in rows], dtype=float)
    summary = {"fault": fault, "duration_s": round(rows[-1][0], 1), "events": events,
               "max_abs_current_A": np.abs(a[:, 10:15]).max(axis=0).round(2).tolist(),
               "max_temp_C": a[:, 15:20].max(axis=0).round(1).tolist(),
               "final_pos": a[-1, 5:10].round(4).tolist(), "log": str(out_dir / f"{tag}.csv")}
    (out_dir / f"{tag}_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    try:
        main()
    except HILError as e:
        print("HIL ERROR:", e.get_error_message())
        raise SystemExit(2)
