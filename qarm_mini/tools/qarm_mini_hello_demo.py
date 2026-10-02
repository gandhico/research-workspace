"""Supervised QArm Mini motion demo: rest -> home -> base wave -> wrist twist -> gripper -> rest.

Uses qarm_mini_calibration.py (PAL joint bias map, confirmed against the physical rest
pose; gripper map measured by hand on this unit), gentle servo profiles (0.6 rad/s),
PAL's servo gains, and per-sample monitors: 25 servo error flags, load/current, temperature,
finite data, bus desync (a position jump > 0.25 rad in one sample, or an all-zero read),
and arrival at every waypoint. On any fault it freezes at the last good pose and closes.
It ends at the measured start (rest) pose, so nothing is preloaded when torque drops.
Board id = COM port number; the FTDI latency timer must be 2 ms (see RUNNERS.md).
Run only with the 0.5 m workspace clear and a hand on the power switch.
"""
from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

import numpy as np
from quanser.hardware import HIL, HILError

import qarm_mini_calibration as cal

OTHER_IN = np.array([1000, 1001, 1002, 1003, 1004, 10000, 10001, 10002, 10003, 10004], dtype=np.uint32)
ANALOG_IN = np.arange(5, dtype=np.uint32)          # 0,4 load %; 1-3 current A
DIGITAL_IN = np.arange(25, dtype=np.uint32)        # servo error flags
POS_OUT = np.array([1000, 1001, 1002, 1003, 1004], dtype=np.uint32)
PWM_OUT = np.array([11000, 11001, 11002, 11003, 11004], dtype=np.uint32)  # held at 0, as PAL does
ERR_NAMES = ["input_voltage", "overheating", "motor_encoder", "electrical_shock", "overload"]
NAMES = ["yaw", "shoulder", "elbow", "wrist", "gripper"]

# PAL QArmMini gains: P, I, D, FF-vel, FF-acc for yaw..gripper (-1 = servo default).
GAIN_PROPS = np.arange(128, 153, dtype=np.int32)
GAIN_VALUES = np.array([5, 10, 10, 10, 20, -1, 0.036, 0.036, -1, -1, 200, 0, 0, 0, 0,
                        -1, -1, -1, -1, -1, -1, -1, -1, -1, -1], dtype=np.float64)

VEL, ACC = 0.6, 0.6
RATE = 50.0
TOL = np.array([0.04, 0.04, 0.04, 0.04, 0.08])     # rad x4, gripper fraction
TIMEOUT = 10.0
LOAD_MAX_PCT, CUR_MAX_A, PERSIST = 80.0, 2.0, 0.3
TEMP_MAX = 60.0
JUMP_MAX = 0.25
SPEED_MAX = 1.0   # rad/s; the profiles request 0.6 (the servos actually ran ~0.3)
# A bad sample (error flags, all-zero/non-finite, impossible jump) must persist this many consecutive
# samples to be a fault. On 2026-09-27 single-sample glitches were seen twice: ALL five flags on yaw and
# gripper (sweep), and an all-joint -2..-3.3 rad "jump" (demo 2), each clearing on the next sample. Real
# Dynamixel hardware errors latch until reboot, and a real disconnect persists. A 3-sample glitch
# (elbow, under load) still tripped a debounce of 3, so it is 10 (200 ms); commands are fixed
# waypoints, so dropped reads do not change what the arm is told to do.
FLAG_DEBOUNCE = 10
START_GATE_DEG = 10.0         # must start within this of cal.REST_POSE on every joint
SAFE_RETURN_TIMEOUT = 25.0    # s to reach rest under torque after a fault

HOME = [0.0, np.pi / 2, -np.pi / 2, np.pi / 2]


def options() -> str:
    # This driver REJECTS jX_profile_config / gripper_profile_config (the doc lists them) and
    # ACCEPTS gripper_profile_velocity/_acceleration; the QArm is the opposite (verified 2026-09-27).
    # The profile base is therefore the servo default, assumed velocity-based (PAL passes 6.2832 = 2*pi
    # rad/s). SPEED_MAX and the at-rest profile check below verify that on the hardware.
    parts = []
    for j in range(4):
        parts += [f"j{j}_mode=0", f"j{j}_profile_velocity={VEL}", f"j{j}_profile_acceleration={ACC}"]
    parts += ["gripper_mode=0", f"gripper_profile_velocity={VEL}", f"gripper_profile_acceleration={ACC}"]
    return ";".join(parts) + ";"


def main(board_id: str):
    out = Path(__file__).resolve().parents[1] / "hw_logs"
    tag = time.strftime("%Y%m%d_%H%M%S") + "_mini_hello_demo"
    card = HIL()
    card.open("qarm_mini", board_id)
    other, analog = np.zeros(len(OTHER_IN)), np.zeros(5)
    flags = np.zeros(25, dtype=np.int8)
    rows, events, fault = [], [], None
    dropped = []
    safe_return_result = None
    t0 = time.perf_counter()

    def read():
        analog[:] = np.nan
        card.read(ANALOG_IN, 5, None, 0, DIGITAL_IN, 25, OTHER_IN, len(OTHER_IN), analog, None, flags, other)
        raw = other[:5].copy()
        q = np.concatenate([cal.raw_to_joint(raw[:4]), [cal.raw_to_gripper(raw[4])]])
        return raw, q, other[5:10].copy(), analog.copy(), flags.copy()

    def write(q5):
        raw = np.concatenate([cal.joint_to_raw(q5[:4]), [cal.gripper_to_raw(q5[4])]])
        card.write_other(np.concatenate([POS_OUT, PWM_OUT]), 10, np.concatenate([raw, np.zeros(5)]))
        return np.concatenate([cal.raw_to_joint(raw[:4]), [cal.raw_to_gripper(raw[4])]])

    try:
        opts = options()
        card.set_card_specific_options(opts, len(opts) + 1)
        card.set_double_property(GAIN_PROPS, len(GAIN_PROPS), GAIN_VALUES)

        # Start pose from 5 agreeing reads (guards against a desynced first sample).
        samples = []
        for _ in range(5):
            samples.append(read()[1]); time.sleep(0.02)
        samples = np.array(samples)
        if np.max(np.ptp(samples, axis=0)) > 0.02:
            raise SystemExit(f"start reads disagree ({np.ptp(samples, axis=0).round(3).tolist()}); not moving")
        start = np.median(samples, axis=0)
        # Gate the gravity-loaded joints only; yaw turns about the vertical axis, so any yaw
        # inside its limits is a valid rest. The return target keeps the starting yaw.
        off_rest = np.degrees(np.abs(start[:4] - cal.REST_POSE))
        rest_here = np.array([start[0], *cal.REST_POSE[1:]])
        if np.max(off_rest[1:]) > START_GATE_DEG:
            raise SystemExit(f"arm is not at rest (deg off REST_POSE: {off_rest.round(1).tolist()}); "
                             "power off, fold it to rest by hand, power on, retry")
        grip_start = float(np.clip(start[4], cal.GRIPPER_CMD_MIN, cal.GRIPPER_CMD_MAX))
        events.append({"label": "start", "q_deg": np.degrees(start[:4]).round(2).tolist(), "gripper": round(start[4], 3)})

        seq = [
            ("hold rest", [*start[:4], grip_start], 1.0),
            # Profile check at rest: a small wrist move whose speed must stay <= SPEED_MAX,
            # before any large move (verifies the velocity-based profile assumption).
            ("profile check", [*start[:3], start[3] + 0.3, grip_start], 0.3),
            ("profile check back", [*start[:4], grip_start], 0.5),
            ("home", [*HOME, grip_start], 1.0),
            ("base left", [0.5, *HOME[1:], grip_start], 0.5),
            ("base right", [-0.5, *HOME[1:], grip_start], 0.5),
            ("base centre", [*HOME, grip_start], 0.5),
            ("wrist +", [*HOME[:3], HOME[3] + 0.5, grip_start], 0.3),
            ("wrist -", [*HOME[:3], HOME[3] - 0.5, grip_start], 0.3),
            ("wrist centre", [*HOME, grip_start], 0.5),
            ("gripper open", [*HOME, cal.GRIPPER_CMD_MIN], 1.0),
            ("gripper close 70%", [*HOME, 0.7], 1.0),
            ("gripper open", [*HOME, cal.GRIPPER_CMD_MIN], 1.0),
            ("back to rest", [*rest_here, grip_start], 1.0),
        ]
        last_good = start.copy()
        over_since = None
        prev_tick = None
        bad_run, dropped = 0, []
        max_speed_seen = 0.0
        prev_for_speed = {"q": start.copy(), "t": time.perf_counter()}

        def safe_return(target):
            t_s = time.perf_counter()
            arrived_at = None
            while time.perf_counter() - t_s < SAFE_RETURN_TIMEOUT:
                write(target)
                raw_r, q_r, _, _, fl_r = read()
                good = not fl_r.any() and np.all(np.isfinite(q_r)) and not np.all(raw_r == 0)
                if good and np.all(np.abs(q_r[:4] - target[:4]) < 0.06):
                    arrived_at = arrived_at or time.perf_counter()
                    if time.perf_counter() - arrived_at > 1.0:
                        return {"reached_rest": True, "s": round(time.perf_counter() - t_s, 1)}
                time.sleep(0.02)
            return {"reached_rest": False, "s": SAFE_RETURN_TIMEOUT}

        def speed_now(q):
            now = time.perf_counter()
            v = float(np.max(np.abs(q[:4] - prev_for_speed["q"][:4])) / max(now - prev_for_speed["t"], 1e-3))
            prev_for_speed["q"], prev_for_speed["t"] = q.copy(), now
            return v
        for label, target, dwell in seq:
            target = np.array(target, dtype=float)
            print(f"-> {label:18s} target deg {np.degrees(target[:4]).round(1).tolist()} grip {target[4]:.2f}", flush=True)
            seg0 = time.perf_counter(); arrived = None
            while True:
                tick = time.perf_counter()
                cmd = write(target)
                raw, q, temp, an, fl = read()
                t = tick - t0
                rows.append([t, label, *cmd, *q, *an, *temp, int(fl.any())])
                # A sample is BAD if it carries error flags, is non-finite/all-zero, or jumps more than
                # the arm can move. Commands are fixed waypoints (not computed from feedback), so a
                # single bad sample is dropped; BAD_RUN_MAX consecutive bad samples is a fault.
                bad = None
                if fl.any():
                    bad = "servo error: " + ", ".join(f"{NAMES[i // 5]}:{ERR_NAMES[i % 5]}" for i in np.flatnonzero(fl))
                elif not np.all(np.isfinite(np.concatenate([q, temp]))) or np.all(raw == 0):
                    bad = "non-finite or all-zero read"
                elif np.max(np.abs(q[:4] - last_good[:4])) > JUMP_MAX:
                    bad = f"position jump {np.round(q - last_good, 3).tolist()}"
                if bad:
                    bad_run += 1
                    dropped.append({"t": round(t, 3), "segment": label, "why": bad})
                    if bad_run >= FLAG_DEBOUNCE:
                        fault = f"{bad_run} consecutive bad samples, last: {bad}"
                        break
                    time.sleep(max(0.0, 1.0 / RATE - (time.perf_counter() - tick)))
                    continue
                bad_run = 0
                if prev_tick is not None and \
                        np.max(np.abs(q[:4] - last_good[:4])) / max(tick - prev_tick, 1e-3) > SPEED_MAX:
                    fault = (f"joint speed {np.max(np.abs(q[:4] - last_good[:4])) / (tick - prev_tick):.2f} rad/s "
                             f"> {SPEED_MAX} (profile not velocity-based?)")
                elif np.any(temp > TEMP_MAX):
                    fault = f"temperature {temp.tolist()}"
                else:
                    over = (np.nanmax(np.abs(an[[0, 4]])) > LOAD_MAX_PCT) or (np.nanmax(np.abs(an[1:4])) > CUR_MAX_A)
                    over_since = (over_since or tick) if over else None
                    if over_since and tick - over_since > PERSIST:
                        fault = f"load/current {np.round(an, 2).tolist()}"
                if fault:
                    break
                last_good = q.copy()
                prev_tick = tick
                max_speed_seen = max(max_speed_seen, speed_now(q))
                err = np.abs(q - cmd)
                if arrived is None and np.all(err < TOL):
                    arrived = tick
                    events.append({"label": label, "arrive_s": round(tick - seg0, 2), "err": err.round(4).tolist(),
                                   "analog": np.round(an, 2).tolist(), "max_speed_so_far": round(max_speed_seen, 3)})
                if arrived is not None and tick - arrived >= dwell:
                    break
                if arrived is None and tick - seg0 > TIMEOUT:
                    fault = f"'{label}' not reached: err {err.round(3).tolist()}"
                    break
                time.sleep(max(0.0, 1.0 / RATE - (time.perf_counter() - tick)))
            if fault:
                # Closing the Mini drops torque and the arm falls, so never close mid-air:
                # drive back to REST under torque first (bad reads ignored), then close.
                print("FAULT:", fault, "- returning to rest under torque before closing", flush=True)
                safe_return_result = safe_return(np.array([*rest_here, grip_start]))
                print("   safe return:", safe_return_result, flush=True)
                break
    finally:
        card.close()

    with (out / f"{tag}.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["time_s", "segment"] + [f"cmd_{n}" for n in NAMES] + [f"q_{n}" for n in NAMES]
                   + ["load_yaw_pct", "cur_shoulder_A", "cur_elbow_A", "cur_wrist_A", "load_gripper_pct"]
                   + [f"temp_{n}" for n in NAMES] + ["any_error_flag"])
        w.writerows(rows)
    a = np.array([r[2:] for r in rows], dtype=float) if rows else np.zeros((1, 26))
    summary = {"fault": fault, "options": opts, "duration_s": round(rows[-1][0], 1) if rows else 0,
               "dropped_bad_samples": len(dropped), "dropped_detail": dropped[:20],
               "samples": len(rows), "safe_return": safe_return_result,
               "events": events,
               "max_abs_analog": np.nanmax(np.abs(a[:, 10:15]), axis=0).round(2).tolist(),
               "max_temp_C": np.nanmax(a[:, 15:20], axis=0).round(1).tolist(),
               "log": str(out / f"{tag}.csv")}
    (out / f"{tag}_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True, help="COM port number, e.g. 6")
    try:
        main(ap.parse_args().id)
    except HILError as e:
        print("HIL ERROR:", e.get_error_message())
        raise SystemExit(2)
