"""Supervised QArm bench test: hold pose, then small wrist position steps.

Stages
  hold   enable position mode and command every joint to its measured pose
         (elbow clamped into the documented command range); no intended motion.
  steps  same hold for the base joints, plus a zero-mean multilevel wrist
         sequence (|delta| <= 0.10 rad) for runbook step 2 identification.

Safety: gentle trajectory profiles, per-sample monitors (non-wrist drift,
wrist tracking, current, temperature, finite data, loop overrun) that abort to
a hold of the measured pose, then the board is closed. Channel map and ranges:
QUARC doc quarc/doc/qarm_usb.html. Run only with an operator at the E-stop.
"""
from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

import numpy as np
from quanser.hardware import HIL, HILError, Clock

JOINTS = ["yaw", "shoulder", "elbow", "wrist", "gripper"]
POS_IN = np.array([1000, 1001, 1002, 1003, 1004], dtype=np.uint32)
VEL_IN = np.array([3000, 3001, 3002, 3003, 3004], dtype=np.uint32)
TEMP_IN = np.array([10000, 10001, 10002, 10003, 10004], dtype=np.uint32)
PWM_IN = np.array([11000, 11001, 11002, 11003, 11004], dtype=np.uint32)
CUR_IN = np.array([5, 6, 7, 8, 9], dtype=np.uint32)
POS_OUT = np.array([1000, 1001, 1002, 1003, 1004], dtype=np.uint32)
# Quanser PAL LIMITS_MIN/MAX (gripper 0.1-0.9 as PAL). The servos enforce these
# in firmware: a command outside is driven to the limit (verified 2026-09-27; the
# rest pose shoulder -1.558 / elbow +1.404 lies outside, so enabling torque
# lifts the arm ~4-5 deg to -17pi/36 / +15pi/36).
CMD_LO = np.array([-17 * np.pi / 18, -17 * np.pi / 36, -19 * np.pi / 36, -8 * np.pi / 9, 0.1])
CMD_HI = np.array([17 * np.pi / 18, 17 * np.pi / 36, 15 * np.pi / 36, 8 * np.pi / 9, 0.9])
CUR_RANGE = np.array([4.4, 8.8, 4.4, 2.3, 1.4])

WRIST = 3
# Servo position-loop P (128-131), I (133-136), D (138-141) gains that Quanser PAL
# (pal/products/qarm.py) writes on every hardware open.
QUANSER_GAIN_PROPS = np.array([128, 129, 130, 131, 133, 134, 135, 136, 138, 139, 140, 141], dtype=np.int32)
QUANSER_GAIN_VALUES = np.array([8.89] * 4 + [0.012] * 4 + [10.23] * 4, dtype=np.float64)
STEP_LEVELS = [0.0, 0.05, -0.05, 0.10, -0.10, 0.03, -0.08, 0.08, -0.03, 0.10,
               -0.10, 0.05, 0.0, -0.05, 0.08, -0.08, 0.0]
STEP_HOLD_S = 1.5

# Abort thresholds
# Shoulder/elbow settle ~0.05 rad off their hold command under load (hold test
# 2026-09-27), so bound motion after settling tightly and the offset loosely.
MAX_DRIFT_OTHERS = 0.02     # rad, yaw/shoulder/elbow motion after SETTLE_S
MAX_OFFSET_OTHERS = 0.08    # rad, yaw/shoulder/elbow vs. their hold command
# A commanded step makes |q - cmd| equal the step (up to 0.20 rad) for a sample,
# so bound the wrist by an envelope plus a settling requirement instead.
WRIST_ENVELOPE = max(abs(d) for d in STEP_LEVELS) + 0.05   # rad about the hold pose
WRIST_SETTLE_S = 1.0        # s after each step
WRIST_SETTLE_ERR = 0.03     # rad
MAX_CUR_FRAC = 0.5          # fraction of documented current range
MAX_TEMP_C = 60.0
SETTLE_S = 1.5              # grace period for the elbow clamp move


def options_string(vel_default=0.5, acc_default=0.5, vel_wrist=1.0, acc_wrist=1.0):
    parts = []
    for j in range(4):
        v, a = (vel_wrist, acc_wrist) if j == WRIST else (vel_default, acc_default)
        parts += [f"j{j}_mode=0", f"j{j}_profile_config=0",
                  f"j{j}_profile_velocity={v}", f"j{j}_profile_acceleration={a}"]
    # gripper_profile_velocity/_acceleration are in the doc but rejected by the
    # 2026 driver (fw 3.3), verified 2026-09-27; the gripper is only held anyway.
    parts += ["gripper_mode=0", "gripper_profile_config=0"]
    return ";".join(parts) + ";"


class Arm:
    def __init__(self, card):
        self.card = card
        self.other_ch = np.concatenate([POS_IN, VEL_IN, TEMP_IN, PWM_IN])
        self.other = np.zeros(len(self.other_ch))
        self.cur = np.zeros(5)

    def read(self):
        self.card.read_other(self.other_ch, len(self.other_ch), self.other)
        self.card.read_analog(CUR_IN, 5, self.cur)
        o = self.other
        return o[0:5].copy(), o[5:10].copy(), o[10:15].copy(), o[15:20].copy(), self.cur.copy()

    def read_task(self, task):
        """Block until the next hardware-clocked sample (ERROR_ON_OVERFLOW: a late loop raises)."""
        self.card.task_read(task, 1, self.cur, None, None, self.other)
        o = self.other
        return o[0:5].copy(), o[5:10].copy(), o[10:15].copy(), o[15:20].copy(), self.cur.copy()

    def command(self, q):
        q = np.clip(np.asarray(q, dtype=np.float64), CMD_LO, CMD_HI)
        self.card.write_other(POS_OUT, 5, q)
        return q


def run(stage, rate_hz, hold_s, out_dir: Path, clock="hw", gains="quanser"):
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = time.strftime("%Y%m%d_%H%M%S") + f"_{stage}_{clock}_{gains}"
    card = HIL()
    card.open("qarm_usb", "0")
    arm = Arm(card)
    rows, abort_reason, overruns, task = [], None, 0, None
    try:
        q0, *_ = arm.read()
        hold = np.clip(q0, CMD_LO, CMD_HI)
        opts = options_string()
        card.set_card_specific_options(opts, len(opts) + 1)
        if gains == "quanser":
            card.set_double_property(QUANSER_GAIN_PROPS, len(QUANSER_GAIN_PROPS), QUANSER_GAIN_VALUES)

        if stage == "hold":
            schedule = [(hold_s, 0.0)]
        else:
            schedule = [(2.0, 0.0)] + [(STEP_HOLD_S, d) for d in STEP_LEVELS]
        seg_ends = np.cumsum([s for s, _ in schedule])
        total = float(seg_ends[-1])

        def seg_start(i):
            return 0.0 if i == 0 else float(seg_ends[i - 1])

        period = 1.0 / rate_hz
        if clock == "hw":
            task = card.task_create_reader(int(rate_hz), CUR_IN, len(CUR_IN), None, 0, None, 0,
                                           arm.other_ch, len(arm.other_ch))
            card.task_start(task, Clock.HARDWARE_CLOCK_0, rate_hz, 2**32 - 1)
        t0 = time.perf_counter()
        k = 0
        settled_ref = None
        while True:
            if clock == "hw":
                # Sample k is taken by the board clock at exactly k/rate; the command
                # for that instant is written right after it arrives.
                t = k * period
                if t >= total:
                    break
                q, qd, temp, pwm, cur = arm.read_task(task)
                host = time.perf_counter() - t0
                seg = int(np.searchsorted(seg_ends, t, side="right"))
                cmd = hold.copy()
                cmd[WRIST] = hold[WRIST] + schedule[seg][1]
                cmd = arm.command(cmd)
            else:
                target = t0 + k * period
                now = time.perf_counter()
                if now - target > period:
                    overruns += 1
                while time.perf_counter() < target:
                    pass
                t = time.perf_counter() - t0
                if t >= total:
                    break
                seg = int(np.searchsorted(seg_ends, t, side="right"))
                cmd = hold.copy()
                cmd[WRIST] = hold[WRIST] + schedule[seg][1]
                cmd = arm.command(cmd)
                q, qd, temp, pwm, cur = arm.read()
                host = t
            rows.append([t, *cmd, *q, *qd, *temp, *pwm, *cur, host])

            if settled_ref is None and t > SETTLE_S:
                settled_ref = q.copy()
            vals = np.concatenate([q, qd, temp, pwm, cur])
            if not np.all(np.isfinite(vals)):
                abort_reason = "non-finite reading"
            elif t > SETTLE_S and np.max(np.abs((q - cmd)[:3])) > MAX_OFFSET_OTHERS:
                abort_reason = f"non-wrist offset {np.round(q - cmd, 3).tolist()}"
            elif t > SETTLE_S and settled_ref is not None and np.max(np.abs((q - settled_ref)[:3])) > MAX_DRIFT_OTHERS:
                abort_reason = f"non-wrist drift since settle {np.round(q - settled_ref, 3).tolist()}"
            elif abs(q[WRIST] - hold[WRIST]) > WRIST_ENVELOPE:
                abort_reason = f"wrist left envelope {q[WRIST] - hold[WRIST]:.3f}"
            elif t - seg_start(seg) > WRIST_SETTLE_S and abs(q[WRIST] - cmd[WRIST]) > WRIST_SETTLE_ERR:
                abort_reason = f"wrist not settled {q[WRIST] - cmd[WRIST]:.3f} at t={t:.2f}"
            elif np.any(np.abs(cur) > MAX_CUR_FRAC * CUR_RANGE):
                abort_reason = f"current {np.round(cur, 3).tolist()}"
            elif np.any(temp > MAX_TEMP_C):
                abort_reason = f"temperature {temp.tolist()}"
            if abort_reason:
                arm.command(q)  # freeze at the last measured pose
                break
            k += 1
        # Return the wrist to its start pose before releasing.
        if not abort_reason:
            end = time.perf_counter() + 1.5
            while time.perf_counter() < end:
                arm.command(hold)
                time.sleep(0.02)
    finally:
        if task is not None:
            card.task_stop(task)
            card.task_delete(task)
        card.close()

    header = (["time_s"] + [f"cmd_{j}" for j in JOINTS] + [f"pos_{j}" for j in JOINTS]
              + [f"vel_{j}" for j in JOINTS] + [f"temp_{j}" for j in JOINTS]
              + [f"pwm_{j}" for j in JOINTS] + [f"cur_{j}" for j in JOINTS] + ["host_s"])
    full = out_dir / f"{tag}_full.csv"
    with full.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    a = np.array(rows)
    summary = {"stage": stage, "clock": clock, "gains": gains,
               "abort_reason": abort_reason, "samples": len(rows),
               "overruns": overruns, "options": opts, "start_pose": q0.tolist(),
               "hold_cmd": hold.tolist(), "log": str(full)}
    if len(rows):
        dt = np.diff(a[:, 0])
        host_dt = np.diff(a[:, 31])
        cmd, pos, cur = a[:, 1:6], a[:, 6:11], a[:, 26:31]
        settled = a[:, 0] > SETTLE_S
        summary.update({
            "dt_mean_ms": float(dt.mean() * 1e3), "dt_max_ms": float(dt.max() * 1e3),
            "jitter_pct": float(dt.std() / dt.mean() * 100),
            "host_dt_max_ms": float(host_dt.max() * 1e3),
            "host_dt_max_rel_dev_pct": float(np.max(np.abs(host_dt - period)) / period * 100),
            "max_abs_err_settled": dict(zip(JOINTS, np.abs(pos - cmd)[settled].max(axis=0).round(4).tolist()))
            if settled.any() else None,
            "max_abs_current_A": dict(zip(JOINTS, np.abs(cur).max(axis=0).round(3).tolist())),
            "mean_current_A": dict(zip(JOINTS, cur.mean(axis=0).round(3).tolist())),
            "final_pos": dict(zip(JOINTS, pos[-1].round(4).tolist())),
        })
        if stage == "steps":
            ident = out_dir / f"{tag}_wrist_ident.csv"
            with ident.open("w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["time_s", "command", "position"])
                w.writerows(zip(a[:, 0], a[:, 1 + WRIST], a[:, 6 + WRIST]))
            summary["ident_log"] = str(ident)
    (out_dir / f"{tag}_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("stage", choices=["hold", "steps"])
    p.add_argument("--rate", type=float, default=100.0)
    p.add_argument("--hold-seconds", type=float, default=5.0)
    p.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "hw_logs")
    p.add_argument("--clock", choices=["hw", "host"], default="hw",
                   help="hw: board HARDWARE_CLOCK_0 reader task (as Quanser PAL); host: busy-wait")
    p.add_argument("--gains", choices=["quanser", "firmware"], default="quanser",
                   help="quanser: PAL's servo PID gains; firmware: leave servo defaults")
    args = p.parse_args()
    try:
        run(args.stage, args.rate, args.hold_seconds, args.out, args.clock, args.gains)
    except HILError as e:
        print("HIL ERROR:", e.get_error_message())
        raise SystemExit(2)
