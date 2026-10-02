"""FIRST POWERED TEST, 3 DOF Gyroscope: blue gimbal only, disc not spinning.

Command chain replicated from Quanser's q_3dgyro_lqr.mdl ("HIL Interfacing"):
    AO voltage = 2 V/A * current  (AMPAQ-L4 0.5 A/V);  AO0 disc, AO1 BLUE, AO2 red, AO3 gray
    DO0-3 = amplifier enables, active-low; DO4 = 1 while running. Running [0 0 0 0 1],
    final/watchdog [1 1 1 1 0] (= disabled).
Only AO1 is ever non-zero here. Encoders: enc0 disc, enc1 blue, enc2 red, enc3 gray (2*pi/4000 rad/count).

Stages: (1) enable with all outputs 0 for 0.5 s; (2) sign test: +current pulses 0.3 s, escalating
0.15 -> 0.6 A until blue moves >= 2 deg; (3) PD position moves to +20, -20, 0 deg (|i| <= 0.4 A), with
the sign from stage 2. Aborts: blue beyond +/-40 deg, red/gray beyond +/-30 deg, blue faster than 3 rad/s,
or no sign found. Every exit writes 0 V and disables the amplifiers; the Q8 hardware watchdog does the same
if this process stalls for WATCHDOG_S.
"""
from __future__ import annotations

import csv
import json
import time
from pathlib import Path

import numpy as np
from quanser.hardware import HIL, HILError, DigitalState

AO = np.array([0, 1, 2, 3], dtype=np.uint32)
DO = np.array([0, 1, 2, 3, 4], dtype=np.uint32)
ENC = np.array([0, 1, 2, 3], dtype=np.uint32)
V_PER_A = 2.0
KT = 0.115
RUN_DO = np.array([0, 0, 0, 0, 1], dtype=np.int8)
SAFE_DO = np.array([1, 1, 1, 1, 0], dtype=np.int8)
RAD_PER_COUNT = 2 * np.pi / 4000
WATCHDOG_S = 0.1
RATE = 200.0

BLUE_LIMIT = np.radians(40)
OTHER_LIMIT = np.radians(30)
SPEED_LIMIT = 3.0
I_MAX_PD = 0.4
PULSES = [0.15, 0.25, 0.35, 0.45, 0.6]
MOVE_MIN = np.radians(2)
KP, KD = 0.39, 0.062          # N m/rad, N m s/rad: wn ~ 10 rad/s, zeta ~ 0.8 with Jx = 0.0039


def main():
    out = Path(__file__).resolve().parents[1] / "hw_logs"
    tag = time.strftime("%Y%m%d_%H%M%S") + "_blue_first_motion"
    card = HIL()
    card.open("q8_usb", "0")
    enc = np.zeros(4, dtype=np.int32)
    rows, events, fault = [], [], None
    t0 = time.perf_counter()

    def safe_outputs():
        card.write_analog(AO, 4, np.zeros(4))
        card.write_digital(DO, 5, SAFE_DO)

    def read():
        card.read_encoder(ENC, 4, enc)
        return enc.astype(float) * RAD_PER_COUNT

    def command(i_blue):
        i_blue = float(np.clip(i_blue, -0.6, 0.6))
        card.write_analog(AO, 4, np.array([0.0, V_PER_A * i_blue, 0.0, 0.0]))
        card.watchdog_reload()
        return i_blue

    try:
        # Outputs and watchdog expiry to the safe state BEFORE enabling anything.
        card.set_digital_directions(None, 0, DO, 5)
        safe_outputs()
        card.watchdog_set_analog_expiration_state(AO, 4, np.zeros(4))
        card.watchdog_set_digital_expiration_state(
            DO, 5, np.array([DigitalState.HIGH] * 4 + [DigitalState.LOW], dtype=np.int32))
        card.watchdog_start(WATCHDOG_S)
        q0 = read().copy()
        events.append({"stage": "start", "enc_rad": q0.round(4).tolist()})

        prev = {"q": q0.copy(), "t": time.perf_counter()}

        def step(i_cmd, stage):
            nonlocal fault
            tick = time.perf_counter()
            i = command(i_cmd)
            q = read() - q0
            dt = max(tick - prev["t"], 1e-3)
            speed = abs(q[1] - prev["q"][1]) / dt
            prev["q"], prev["t"] = q.copy(), tick
            rows.append([tick - t0, stage, i, *q])
            if abs(q[1]) > BLUE_LIMIT:
                fault = f"blue beyond {np.degrees(BLUE_LIMIT):.0f} deg ({np.degrees(q[1]):.1f})"
            elif np.max(np.abs(q[[2, 3]])) > OTHER_LIMIT:
                fault = f"red/gray moved {np.degrees(q[[2, 3]]).round(1).tolist()} deg"
            elif speed > SPEED_LIMIT and prev.get("warm"):
                fault = f"blue speed {speed:.2f} rad/s"
            prev["warm"] = True
            time.sleep(max(0.0, 1.0 / RATE - (time.perf_counter() - tick)))
            return q

        # (1) enable, zero current
        card.write_digital(DO, 5, RUN_DO)
        end = time.perf_counter() + 0.5
        while time.perf_counter() < end and not fault:
            q = step(0.0, "enable_zero")
        events.append({"stage": "enable_zero", "blue_deg": round(float(np.degrees(q[1])), 2)})

        # (2) sign test
        sign = None
        for amp in PULSES:
            if fault:
                break
            base = step(0.0, "pre_pulse")[1]
            end = time.perf_counter() + 0.3
            while time.perf_counter() < end and not fault:
                q = step(amp, f"pulse_{amp}")
            end = time.perf_counter() + 0.4
            while time.perf_counter() < end and not fault:
                q = step(0.0, "post_pulse")
            moved = q[1] - base
            events.append({"stage": "pulse", "amps": amp, "blue_moved_deg": round(float(np.degrees(moved)), 2)})
            print(f"pulse +{amp:.2f} A -> blue moved {np.degrees(moved):+.2f} deg", flush=True)
            if abs(moved) >= MOVE_MIN:
                sign = float(np.sign(moved))
                break
        if sign is None and not fault:
            fault = "no blue motion up to 0.6 A: check amp power/enable/cabling"

        # (3) PD moves: current = sign * (KP e - KD qdot) / KT
        if not fault:
            events.append({"stage": "sign", "encoder_sign_for_positive_current": sign})
            for target_deg in (20.0, -20.0, 0.0):
                tgt = np.radians(target_deg)
                print(f"-> blue to {target_deg:+.0f} deg", flush=True)
                end = time.perf_counter() + 3.0
                last_q, last_t = None, None
                while time.perf_counter() < end and not fault:
                    q = prev["q"]
                    qd = 0.0 if last_q is None else (q[1] - last_q) / max(time.perf_counter() - last_t, 1e-3)
                    last_q, last_t = q[1], time.perf_counter()
                    tau = KP * (tgt - q[1]) - KD * qd
                    i = np.clip(sign * tau / KT, -I_MAX_PD, I_MAX_PD)
                    step(i, f"pd_{target_deg:+.0f}")
                events.append({"stage": f"pd_{target_deg:+.0f}", "blue_deg": round(float(np.degrees(prev["q"][1])), 2),
                               "red_deg": round(float(np.degrees(prev["q"][2])), 2),
                               "gray_deg": round(float(np.degrees(prev["q"][3])), 2)})
                print(f"   reached blue {np.degrees(prev['q'][1]):+.1f} deg (red {np.degrees(prev['q'][2]):+.1f}, "
                      f"gray {np.degrees(prev['q'][3]):+.1f})", flush=True)
    except KeyboardInterrupt:
        fault = "operator interrupt"
    finally:
        try:
            safe_outputs()
            card.watchdog_stop()
        finally:
            card.close()

    if fault:
        print("FAULT:", fault, "- outputs zeroed and amplifiers disabled", flush=True)
    with (out / f"{tag}.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t", "stage", "i_blue_A", "disc_rad", "blue_rad", "red_rad", "gray_rad"])
        w.writerows(rows)
    summary = {"fault": fault, "events": events, "samples": len(rows), "log": str(out / f"{tag}.csv")}
    (out / f"{tag}.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    try:
        main()
    except HILError as e:
        print("HIL ERROR:", e.get_error_message())
        raise SystemExit(2)
