"""Find the commandable gripper range of the QArm Mini, then return the arm to rest.

Background (demo run 20260927_202751): commanding gripper 0.05 (raw 1.787) from 0.95 gave no
motion and zero load, which is the signature of a Dynamixel goal rejected for being outside the
servo's firmware position limits. The hand-measured open end (raw 1.666) lies beyond what
the servo may be driven to.

The arm joints hold their measured pose. The gripper is stepped open 0.1 at a time; a step
that produces no motion within STEP_TIMEOUT is recorded as rejected (not a fault). The
gripper then opens to the most-open accepted value, closes to 0.7, reopens, and the arm
returns to REST. Same monitors as qarm_mini_hello_demo.py (error flags, load/current,
temperature, desync, speed).
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from quanser.hardware import HIL, HILError

import qarm_mini_calibration as cal
import qarm_mini_hello_demo as demo

# Rest pose the arm sat in at the start of run 20260927_202751 (elbow clamped to PAL min).
REST = np.radians([-10.73, 191.29, -150.0, 27.33])
STEP_TIMEOUT = 4.0
MOVE_EPS = 0.02       # gripper fraction change that counts as "it moved"


def main(board_id: str):
    out = Path(__file__).resolve().parents[1] / "hw_logs"
    card = HIL()
    card.open("qarm_mini", board_id)
    other, analog = np.zeros(len(demo.OTHER_IN)), np.zeros(5)
    flags = np.zeros(25, dtype=np.int8)
    report = {"steps": [], "fault": None}

    def read():
        analog[:] = np.nan
        card.read(demo.ANALOG_IN, 5, None, 0, demo.DIGITAL_IN, 25, demo.OTHER_IN, len(demo.OTHER_IN),
                  analog, None, flags, other)
        raw = other[:5].copy()
        return raw, np.concatenate([cal.raw_to_joint(raw[:4]), [cal.raw_to_gripper(raw[4])]]), \
            other[5:10].copy(), analog.copy(), flags.copy()

    def write(q5, grip_raw=None):
        raw_g = cal.gripper_to_raw(q5[4]) if grip_raw is None else grip_raw
        raw = np.concatenate([cal.joint_to_raw(q5[:4]), [raw_g]])
        card.write_other(np.concatenate([demo.POS_OUT, demo.PWM_OUT]), 10, np.concatenate([raw, np.zeros(5)]))

    last = {"q": None, "t": None}

    def check(q, temp, an, fl):
        last["flag_run"] = last.get("flag_run", 0) + 1 if fl.any() else 0
        if last["flag_run"] >= demo.FLAG_DEBOUNCE:
            return "servo error flags " + str(np.flatnonzero(fl).tolist())
        if not np.all(np.isfinite(np.concatenate([q, temp]))):
            return "non-finite read"
        if last["q"] is not None:
            dq = np.max(np.abs(q[:4] - last["q"][:4]))
            if dq > demo.JUMP_MAX:
                return f"position jump {dq:.3f} (desync?)"
            if dq / max(time.perf_counter() - last["t"], 1e-3) > demo.SPEED_MAX:
                return "joint speed above limit"
        if np.any(temp > demo.TEMP_MAX):
            return "temperature"
        if np.nanmax(np.abs(an[[0, 4]])) > demo.LOAD_MAX_PCT or np.nanmax(np.abs(an[1:4])) > demo.CUR_MAX_A:
            return f"load/current {np.round(an, 2).tolist()}"
        last["q"], last["t"] = q.copy(), time.perf_counter()
        return None

    def go(target, timeout, tol=demo.TOL, dwell=0.3):
        """Drive to target; return (reached, final q). Joint faults raise."""
        t0 = time.perf_counter(); arrived = None
        while True:
            write(target)
            _, q, temp, an, fl = read()
            f = check(q, temp, an, fl)
            if f:
                raise RuntimeError(f)
            if arrived is None and np.all(np.abs(q - target) < tol):
                arrived = time.perf_counter()
            if arrived is not None and time.perf_counter() - arrived >= dwell:
                return True, q
            if time.perf_counter() - t0 > timeout:
                return False, q
            time.sleep(0.02)

    try:
        opts = demo.options()
        card.set_card_specific_options(opts, len(opts) + 1)
        card.set_double_property(demo.GAIN_PROPS, len(demo.GAIN_PROPS), demo.GAIN_VALUES)
        samples = []
        for _ in range(5):
            samples.append(read()[1]); time.sleep(0.02)
        samples = np.array(samples)
        if np.max(np.ptp(samples, axis=0)) > 0.02:
            raise SystemExit("start reads disagree; not moving")
        start = np.median(samples, axis=0)
        report["start_deg"] = np.degrees(start[:4]).round(2).tolist()
        report["start_gripper"] = round(float(start[4]), 3)
        hold = np.clip(start[:4], cal.JOINT_MIN, cal.JOINT_MAX)
        g = float(np.clip(start[4], cal.GRIPPER_CMD_MIN, cal.GRIPPER_CMD_MAX))
        go(np.array([*hold, g]), 3.0)

        accepted_min = g
        for frac in np.arange(round(g - 0.1, 2), 0.04, -0.1):
            _, q_before = read()[:2]
            ok, q = go(np.array([*hold, frac]), STEP_TIMEOUT, tol=np.array([*demo.TOL[:4], 0.04]))
            moved = abs(q[4] - q_before[4]) > MOVE_EPS
            report["steps"].append({"cmd": round(float(frac), 2), "raw_cmd": round(cal.gripper_to_raw(frac), 4),
                                    "reached": bool(ok), "moved": bool(moved), "final": round(float(q[4]), 3)})
            print(report["steps"][-1], flush=True)
            if not moved:
                break
            accepted_min = float(q[4])
        report["gripper_open_limit_fraction"] = round(accepted_min, 3)
        report["gripper_open_limit_raw"] = round(cal.GRIPPER_RAW_OPEN
                                                 + accepted_min * (cal.GRIPPER_RAW_CLOSED - cal.GRIPPER_RAW_OPEN), 4)
        lo = accepted_min + 0.02
        for label, frac in (("open", lo), ("close 70%", 0.7), ("open", lo)):
            ok, q = go(np.array([*hold, frac]), 6.0, tol=np.array([*demo.TOL[:4], 0.04]))
            print(f"-> gripper {label} {frac:.2f}: reached={ok} final={q[4]:.3f}", flush=True)
        ok, q = go(np.array([*REST, lo]), 15.0, dwell=1.0)
        report["back_to_rest"] = {"reached": bool(ok), "final_deg": np.degrees(q[:4]).round(2).tolist()}
        print("-> back to rest:", report["back_to_rest"], flush=True)
    except RuntimeError as e:
        report["fault"] = str(e)
        print("FAULT:", e, "- freezing", flush=True)
        if last["q"] is not None:
            write(last["q"])
            time.sleep(0.5)
    finally:
        card.close()
    path = out / (time.strftime("%Y%m%d_%H%M%S") + "_mini_gripper_sweep.json")
    path.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    try:
        main(ap.parse_args().id)
    except HILError as e:
        print("HIL ERROR:", e.get_error_message())
        raise SystemExit(2)
