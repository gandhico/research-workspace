"""Motor map and thrust-direction test for the 6DoF (reversible DShot-3D) Omnidrone.

Uses MAV_CMD_DO_MOTOR_TEST in **PWM mode around 1500 us** (1500 = stop, >1500 one
direction, <1500 the other).  Never use a PERCENT motor test on reversible outputs:
ArduPilot 4.7.1 maps percent to 1000 + 10*percent us (ArduCopter/motor_test.cpp), so
"10 %" is 1100 us = about 80 % REVERSE, and "0 %" (e.g. motor_test_1.py's emergency
stop) is 1000 us = FULL reverse (AP_HAL_ChibiOS/RCOutput.cpp DShot-3D mapping).

    python motor_test_6dof.py                     # props OFF: which physical rotor is MotorK?
    python motor_test_6dof.py --props-on          # props ON, vehicle restrained: thrust direction
    python motor_test_6dof.py --motors 3,5 --delta 30

Each motor runs 1500+delta, pauses, then 1500-delta.  You answer which twin rotor
(1-8, as labelled on the frame) moved and, with props on, whether the +delta pulse pushed
along that rotor's +Z (the blue axis in the twin viewer).  The result is saved and the
--motor-map for make_6dof_mixer.py and any SERVO_BLH_RVMASK bits are printed.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path
import sys
import time

from pymavlink import mavutil

from ap_link import connect, is_armed

HERE = Path(__file__).resolve().parent
MAV_CMD_DO_MOTOR_TEST = 209
THROTTLE_PWM = 1
STOP_PWM = 1500


def read_param(link, name, timeout_s=3.0):
    for _ in range(3):
        link.tx.mav.param_request_read_send(link.target_system, link.target_component, name.encode(), -1)
        end = time.time() + timeout_s / 3
        while time.time() < end:
            m = link.rx.recv_match(type="PARAM_VALUE", blocking=True, timeout=0.2)
            if m is not None:
                pid = m.param_id.decode() if isinstance(m.param_id, bytes) else m.param_id
                if pid.rstrip("\x00") == name:
                    return m.param_value
    return None


def motor_test(link, motor, pwm, seconds):
    """Returns the MAV_RESULT name (or 'NO_ACK')."""
    while link.rx.recv_match(type="COMMAND_ACK", blocking=False):
        pass
    link.send_heartbeat()
    link.tx.mav.command_long_send(link.target_system, link.target_component, MAV_CMD_DO_MOTOR_TEST, 0,
                                  motor, THROTTLE_PWM, pwm, seconds, 1, 0, 0)
    end = time.time() + 2.0
    while time.time() < end:
        m = link.rx.recv_match(type=["COMMAND_ACK", "STATUSTEXT"], blocking=True, timeout=0.25)
        if m is None:
            continue
        if m.get_type() == "STATUSTEXT":
            print("   CUBE:", m.text)
        elif m.command == MAV_CMD_DO_MOTOR_TEST:
            entry = mavutil.mavlink.enums["MAV_RESULT"].get(m.result)
            return entry.name if entry else str(m.result)
    return "NO_ACK"


def stop_all(link):
    for motor in range(1, 9):
        link.tx.mav.command_long_send(link.target_system, link.target_component, MAV_CMD_DO_MOTOR_TEST, 0,
                                      motor, THROTTLE_PWM, STOP_PWM, 0.1, 1, 0, 0)
    link.tx.mav.command_long_send(link.target_system, link.target_component,
                                  mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 0, 0, 0, 0, 0, 0, 0)


def ask(prompt, valid):
    while True:
        answer = input(prompt).strip().lower()
        if answer in valid:
            return answer
        print(f"   answer one of: {', '.join(sorted(valid))}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--props-on", action="store_true", help="direction test with props, vehicle RESTRAINED")
    parser.add_argument("--motors", default="1,2,3,4,5,6,7,8", help="ArduPilot motor numbers to test")
    parser.add_argument("--delta", type=int, default=40, help="PWM offset from 1500 us (40 = ~8%% thrust)")
    parser.add_argument("--seconds", type=float, default=2.0)
    parser.add_argument("--pico-ip", default=None)
    parser.add_argument("--port", type=int, default=14550, help="UDP port the Pico sends telemetry to")
    parser.add_argument("--pico-port", type=int, default=None, help="UDP port the Pico listens on (default --port)")
    args = parser.parse_args()
    if not 10 <= args.delta <= (60 if args.props_on else 100):
        parser.error("--delta must be 10..100 (props off) or 10..60 (props on)")
    motors = [int(m) for m in args.motors.split(",")]

    print("6DoF MOTOR TEST (PWM mode around 1500 us).")
    if args.props_on:
        print("PROPS ON: the vehicle must be RESTRAINED (tether/fixture), people clear, E-stop in hand.")
        if input("Type PROPS ON RESTRAINED to continue: ").strip().upper() != "PROPS ON RESTRAINED":
            sys.exit("cancelled")
    elif input("Type YES to confirm ALL propellers are removed: ").strip().upper() != "YES":
        sys.exit("cancelled")

    link = connect(port=args.port, pico_ip=args.pico_ip, pico_port=args.pico_port)
    reversible_confirmed = False          # only then is 1500 us a stop command
    rows = []
    try:
        if is_armed(link.heartbeat):
            sys.exit("vehicle is ARMED: disarm first")
        frame = read_param(link, "FRAME_CLASS")
        mask = read_param(link, "SERVO_BLH_3DMASK")
        print(f"FRAME_CLASS={frame}, SERVO_BLH_3DMASK={mask}")
        if frame != 16 or mask is None or (int(mask) & 0xFF) != 0xFF:
            sys.exit("Refusing: this test is only for the 6DoF frame (FRAME_CLASS 16) with SERVO_BLH_3DMASK "
                     "covering outputs 1-8. On a normal DShot output, 1500 us is ~50% thrust. Nothing was sent.")
        reversible_confirmed = True

        for motor in motors:
            print(f"\n=== ArduPilot Motor{motor} ===")
            choice = ask(f"Run Motor{motor}? [r]un / [s]kip / [q]uit: ", {"r", "s", "q"})
            if choice == "q":
                break
            if choice == "s":
                continue
            entry = {"ap_motor": motor}
            for sign, label in ((+1, "plus"), (-1, "minus")):
                pwm = STOP_PWM + sign * args.delta
                print(f"   {label}: {pwm} us for {args.seconds:.1f} s ...", flush=True)
                result = motor_test(link, motor, pwm, args.seconds)
                print(f"   ack: {result}")
                if result != "MAV_RESULT_ACCEPTED":
                    stop_all(link)
                    sys.exit("motor test rejected: check Messages in Mission Planner (safety, RC, arming checks)")
                time.sleep(args.seconds + 0.8)
                if sign > 0:
                    entry["twin_rotor"] = int(ask("   Which twin rotor (1-8, as labelled) spun? ",
                                                  {str(i) for i in range(1, 9)}))
                    if args.props_on:
                        entry["plus_pushes_along_plusZ"] = ask(
                            "   Did +delta push the vehicle along that rotor's +Z (air leaving along -Z)? [y/n] ",
                            {"y", "n"}) == "y"
                else:
                    entry["minus_reversed"] = ask("   Did -delta spin it the OTHER way? [y/n] ", {"y", "n"}) == "y"
            rows.append(entry)
    except KeyboardInterrupt:
        print("\nCtrl+C")
    finally:
        if reversible_confirmed:
            stop_all(link)
            print("stop (1500 us) and disarm sent")
        link.close()

    if not rows:
        return
    out = HERE / "audits" / datetime.now().strftime("motor_test_%Y%m%d_%H%M%S.csv")
    out.parent.mkdir(exist_ok=True)
    keys = sorted({k for r in rows for k in r})
    with out.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved {out}")
    by_motor = {r["ap_motor"]: r.get("twin_rotor") for r in rows}
    if sorted(by_motor) == list(range(1, 9)) and sorted(by_motor.values()) == list(range(1, 9)):
        motor_map = ",".join(str(by_motor[m]) for m in range(1, 9))
        print(f"Motor map: --motor-map {motor_map}"
              + ("  (identity: the generated mixer already matches)" if motor_map == "1,2,3,4,5,6,7,8" else
                 "\n  -> python make_6dof_mixer.py --motor-map " + motor_map + "  then re-upload the .lua"))
    else:
        print("Motor map incomplete or duplicated: test all 8 motors once each.")
    not_reversing = [r["ap_motor"] for r in rows if r.get("minus_reversed") is False]
    if not_reversing:
        print(f"Motors {not_reversing} did NOT reverse: ESC 3D mode is not working on them. Do not fly.")
    wrong = [r["ap_motor"] for r in rows if r.get("plus_pushes_along_plusZ") is False]
    if wrong:
        bits = sum(1 << (m - 1) for m in wrong)
        print(f"Motors {wrong} push the wrong way: add {bits} to SERVO_BLH_RVMASK (bits = output numbers), "
              "reboot, and repeat this test.")


if __name__ == "__main__":
    main()
