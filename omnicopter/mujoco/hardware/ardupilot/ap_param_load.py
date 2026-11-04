"""Write a .param file to the Cube through the Pico W link, reading back every value.

    python ap_param_load.py config\\stage1_optitrack_ekf.param

1. Reads the Cube's current value of every parameter in the file.
2. Shows current -> new, and lists parameters the Cube does not have yet (e.g. VISO_* before
   VISO_TYPE=1 and a reboot).
3. Asks you to type WRITE, writes only the changed values, and reads each one back.
4. Offers a reboot (the Cube must be disarmed).  Run the same command again after the reboot
   until it reports nothing missing and nothing to change.

Stage-2 values (FRAME_CLASS 16, SERVO_BLH_3DMASK) also require typing ESC 3D CONFIRMED.
Mission Planner must not be connected on UDP 14550 (USB is fine).  Its parameter table is a
cached copy: press Refresh Params there afterwards.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path
import sys
import time

from pymavlink import mavutil

from ap_link import connect, is_armed


def parse(path: Path) -> dict[str, float]:
    values = {}
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        text = line.split("#", 1)[0].strip()
        if not text:
            continue
        parts = [p for p in text.replace("\t", ",").replace(" ", ",").split(",") if p]
        if len(parts) != 2:
            sys.exit(f"{path}:{number}: expected NAME,VALUE, got {line!r}")
        values[parts[0]] = float(parts[1])
    return values


def param_id(message):
    raw = message.param_id
    return (raw.decode("utf-8", "ignore") if isinstance(raw, bytes) else str(raw)).rstrip("\x00")


def same(a, b):
    return math.isclose(a, b, rel_tol=1e-5, abs_tol=1e-6)


def read(link, name, timeout_s=1.0, tries=3):
    for _ in range(tries):
        link.tx.mav.param_request_read_send(link.target_system, link.target_component, name.encode(), -1)
        end = time.time() + timeout_s
        while time.time() < end:
            m = link.rx.recv_match(type="PARAM_VALUE", blocking=True, timeout=0.2)
            if m is not None and param_id(m) == name:
                return m.param_value, m.param_type
    return None, None


def write(link, name, value, param_type, tries=3):
    for _ in range(tries):
        link.tx.mav.param_set_send(link.target_system, link.target_component, name.encode(), value, param_type)
        end = time.time() + 1.5
        while time.time() < end:
            m = link.rx.recv_match(type="PARAM_VALUE", blocking=True, timeout=0.2)
            if m is not None and param_id(m) == name and same(m.param_value, value):
                return True
    got, _ = read(link, name)
    return got is not None and same(got, value)


def reboot(link):
    link.tx.mav.command_long_send(link.target_system, link.target_component,
                                  mavutil.mavlink.MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN, 0, 1, 0, 0, 0, 0, 0, 0)
    m = link.rx.recv_match(type="COMMAND_ACK", blocking=True, timeout=3)
    return m is not None and m.result == mavutil.mavlink.MAV_RESULT_ACCEPTED


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("param_file", type=Path)
    parser.add_argument("--port", type=int, default=14550)
    parser.add_argument("--pico-ip", default=None)
    parser.add_argument("--pico-port", type=int, default=None)
    args = parser.parse_args()
    wanted = parse(args.param_file)
    print(f"{args.param_file.name}: {len(wanted)} parameters")

    link = connect(port=args.port, pico_ip=args.pico_ip, pico_port=args.pico_port)
    try:
        if is_armed(link.heartbeat):
            sys.exit("The Cube is ARMED: disarm before changing parameters. Nothing was written.")
        changes, missing, unchanged = [], [], []
        for name, value in wanted.items():
            current, param_type = read(link, name)
            if current is None:
                missing.append(name)
            elif same(current, value):
                unchanged.append(name)
            else:
                changes.append((name, current, value, param_type))
        print(f"\n{'parameter':22s} {'current':>12s}    {'new':>12s}")
        for name, current, value, _ in changes:
            print(f"{name:22s} {current:12.6g} -> {value:12.6g}")
        for name in unchanged:
            print(f"{name:22s} {wanted[name]:12.6g}    (already set)")
        for name in missing:
            print(f"{name:22s} {'(not on the Cube yet)':>12s}")
        if not changes:
            if missing:
                print("\nNothing to write now. The missing parameters appear only after the ones that enable them "
                      "are set and the Cube reboots. If you have already rebooted, their enabling parameter is "
                      "not set: check the lines above.")
            else:
                print("\nEverything in this file is already set on the Cube.")
            return
        gated = [n for n, _, v, _ in changes
                 if (n == "FRAME_CLASS" and v == 16) or (n == "SERVO_BLH_3DMASK" and v != 0)]
        if gated:
            print("\nThis enables the 6DoF frame / reversible DShot-3D outputs. Only continue if all 8 ESCs are "
                  "confirmed 3D-capable (runbook step 3) and the mixer .lua is in APM/scripts (step 4).")
            if input("Type ESC 3D CONFIRMED to continue: ").strip().upper() != "ESC 3D CONFIRMED":
                sys.exit("cancelled; nothing was written")
        if input(f"\nType WRITE to write {len(changes)} parameter(s): ").strip().upper() != "WRITE":
            sys.exit("cancelled; nothing was written")
        failed = []
        for name, _, value, param_type in changes:
            ok = write(link, name, value, param_type)
            print(f"   {name:22s} {'OK' if ok else 'FAILED'}")
            if not ok:
                failed.append(name)
        if failed:
            print(f"\n{len(failed)} parameter(s) did not verify: {failed}. Run the same command again.")
            return
        print(f"\nAll {len(changes)} written and read back.")
        if input("Reboot the Cube now? [y/n] ").strip().lower() == "y":
            print("reboot " + ("accepted" if reboot(link) else "not acknowledged: power-cycle the Cube instead"))
            print("Wait ~20 s, then run this same command again"
                  + (f" (to write {', '.join(missing)})." if missing else " to confirm everything is set."))
        else:
            print("Reboot the Cube before flying (power-cycle), then run this same command again.")
    finally:
        link.close()


if __name__ == "__main__":
    main()
