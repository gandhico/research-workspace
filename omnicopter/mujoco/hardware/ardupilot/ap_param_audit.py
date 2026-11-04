"""READ-ONLY audit of the Cube's ArduPilot configuration for the 6DoF omnicopter plan.

Downloads every parameter and the firmware version through the Pico W bridge,
saves them unchanged (Mission Planner .param format), and reports what still
has to change before 6DoF flight with OptiTrack.  It never sets a parameter,
arms, or spins a motor.

    python ap_param_audit.py                # waits for the Cube heartbeat on UDP 14550
    python ap_param_audit.py --pico-ip 192.168.1.50
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import time

from pymavlink import mavutil

from ap_link import connect, is_armed

HERE = Path(__file__).resolve().parent

FRAME_CLASS = {0: "Undefined", 1: "Quad", 2: "Hexa", 3: "Octa", 4: "OctaQuad", 5: "Y6", 6: "Heli",
               7: "Tri", 8: "SingleCopter", 9: "CoaxCopter", 10: "BiCopter", 11: "Heli_Dual",
               12: "DodecaHexa", 13: "HeliQuad", 14: "Deca", 15: "Scripting Matrix",
               16: "6DoF Scripting", 17: "Dynamic Scripting Matrix"}
PWM_TYPE = {0: "Normal PWM", 1: "OneShot", 2: "OneShot125", 3: "Brushed", 4: "DShot150",
            5: "DShot300", 6: "DShot600", 7: "DShot1200", 8: "PWMRange", 9: "PWMAngle"}
COPTER_MODES = {0: "Stabilize", 1: "Acro", 2: "AltHold", 3: "Auto", 4: "Guided", 5: "Loiter", 6: "RTL",
                7: "Circle", 9: "Land", 11: "Drift", 13: "Sport", 14: "Flip", 15: "AutoTune",
                16: "PosHold", 17: "Brake", 18: "Throw", 20: "Guided_NoGPS", 21: "SmartRTL",
                22: "FlowHold", 23: "Follow", 24: "ZigZag", 25: "SystemID", 27: "AutoRTL", 28: "Turtle"}
SRC_POS = {0: "None", 1: "Baro", 2: "RangeFinder", 3: "GPS", 4: "Beacon", 6: "ExternalNav"}
SRC_VEL = {0: "None", 3: "GPS", 4: "Beacon", 5: "OpticalFlow", 6: "ExternalNav", 7: "WheelEncoder"}
SRC_YAW = {0: "None", 1: "Compass", 2: "GPS", 3: "GPS+Compass fallback", 6: "ExternalNav", 8: "GSF"}
RC_OPTION = {31: "Motor Emergency Stop", 32: "Motor Interlock", 153: "Arm/Disarm", 154: "Arm/Disarm (AirMode)"}
GROUP_PREFIXES = ("MOT_", "SCR_", "SERVO_BLH", "SERVO_DSHOT", "AHRS_", "EK3_SRC", "VISO_", "ARMING_",
                  "FS_", "BATT_FS", "FENCE_", "LOG_", "INS_LOG", "INS_HNTCH", "SID_",
                  "ATC_RAT_", "ATC_ANG_", "ATC_ACCEL", "ATC_INPUT", "PSC_")


def name_of(message):
    raw = message.param_id
    return (raw.decode("utf-8", "ignore") if isinstance(raw, bytes) else str(raw)).rstrip("\x00")


def fetch_version(link, timeout_s=5.0):
    link.tx.mav.command_long_send(link.target_system, link.target_component,
                                  mavutil.mavlink.MAV_CMD_REQUEST_MESSAGE, 0,
                                  mavutil.mavlink.MAVLINK_MSG_ID_AUTOPILOT_VERSION, 0, 0, 0, 0, 0, 0)
    message = link.rx.recv_match(type="AUTOPILOT_VERSION", blocking=True, timeout=timeout_s)
    if message is None:
        return None
    v = message.flight_sw_version
    kind = {0: "dev", 64: "alpha", 128: "beta", 192: "rc", 255: "official"}.get(v & 0xFF, str(v & 0xFF))
    return {"version": f"{(v >> 24) & 0xFF}.{(v >> 16) & 0xFF}.{(v >> 8) & 0xFF}", "type": kind,
            "git_hash": bytes(message.flight_custom_version).hex()[:16], "board_version": message.board_version}


def fetch_rc(link, timeout_s=3.0):
    """Ask once for RC_CHANNELS: a connected receiver reports channels and non-zero PWM."""
    link.tx.mav.command_long_send(link.target_system, link.target_component,
                                  mavutil.mavlink.MAV_CMD_REQUEST_MESSAGE, 0,
                                  mavutil.mavlink.MAVLINK_MSG_ID_RC_CHANNELS, 0, 0, 0, 0, 0, 0)
    m = link.rx.recv_match(type="RC_CHANNELS", blocking=True, timeout=timeout_s)
    if m is None:
        return {"answered": False}
    pwm = [getattr(m, f"chan{i}_raw") for i in range(1, 9)]
    return {"answered": True, "chancount": m.chancount, "rssi": m.rssi, "ch1_8_pwm": pwm,
            "receiver_detected": bool(m.chancount) and any(900 <= v <= 2100 for v in pwm)}


def fetch_params(link, timeout_s=180.0, idle_s=2.0):
    params, seen, count = {}, set(), None
    link.tx.mav.param_request_list_send(link.target_system, link.target_component)
    start = last_rx = last_hb = time.time()
    while time.time() - start < timeout_s:
        if time.time() - last_hb > 1.0:
            link.send_heartbeat()
            last_hb = time.time()
        message = link.rx.recv_match(type="PARAM_VALUE", blocking=True, timeout=0.5)
        if message is not None:
            params[name_of(message)] = float(message.param_value)
            count = int(message.param_count)
            if 0 <= message.param_index < 65535:
                seen.add(int(message.param_index))
            last_rx = time.time()
            if count and len(seen) >= count:
                break
            continue
        if count and time.time() - last_rx > idle_s:          # re-request the gaps by index
            missing = [i for i in range(count) if i not in seen]
            print(f"  re-requesting {len(missing)} missing parameters ...", flush=True)
            for index in missing[:50]:
                link.tx.mav.param_request_read_send(link.target_system, link.target_component, b"", index)
            last_rx = time.time()
    return params, count


def fmt(value, table=None):
    if value is None:
        return "(absent)"
    shown = int(value) if float(value).is_integer() else value
    return f"{shown} = {table.get(int(value), '?')}" if table else str(shown)


def channels(mask):
    return [bit + 1 for bit in range(32) if int(mask) >> bit & 1]


def audit(p):
    """Return (key settings, findings) for the planned 6DoF + OptiTrack configuration."""
    g = p.get
    findings = []

    def need(ok, text):
        findings.append(("OK  " if ok else "TODO") + "  " + text)

    motors = {ch: int(g(f"SERVO{ch}_FUNCTION")) - 32 for ch in range(1, 17)
              if g(f"SERVO{ch}_FUNCTION") is not None and 33 <= g(f"SERVO{ch}_FUNCTION") <= 40}
    key = {
        "FRAME_CLASS": fmt(g("FRAME_CLASS"), FRAME_CLASS), "FRAME_TYPE": fmt(g("FRAME_TYPE")),
        "SCR_ENABLE": fmt(g("SCR_ENABLE")), "SCR_HEAP_SIZE": fmt(g("SCR_HEAP_SIZE")),
        "MOT_PWM_TYPE": fmt(g("MOT_PWM_TYPE"), PWM_TYPE),
        "MOT_PWM_MIN/MAX": f"{fmt(g('MOT_PWM_MIN'))} / {fmt(g('MOT_PWM_MAX'))}",
        "MOT_YAW_HEADROOM (6DoF reversal deadzone x1000)": fmt(g("MOT_YAW_HEADROOM")),
        "MOT_THST_EXPO / MOT_THST_HOVER": f"{fmt(g('MOT_THST_EXPO'))} / {fmt(g('MOT_THST_HOVER'))}",
        "Motor outputs (servo channel -> MotorN)": {f"SERVO{ch}": f"Motor{m}" for ch, m in sorted(motors.items())},
        "SERVO_BLH_3DMASK (3D/reversible DShot channels)": channels(g("SERVO_BLH_3DMASK") or 0),
        "SERVO_DSHOT_ESC (1 = BLHeli32/Kiss/AM32) / BRD_IO_DSHOT": f"{fmt(g('SERVO_DSHOT_ESC'))} / {fmt(g('BRD_IO_DSHOT'))}",
        "SERVO_BLH_RVMASK (reversed channels)": channels(g("SERVO_BLH_RVMASK") or 0),
        "SERVO_BLH_MASK / SERVO_BLH_OTYPE (forced output type)": f"{channels(g('SERVO_BLH_MASK') or 0)} / "
                                                                 f"{fmt(g('SERVO_BLH_OTYPE'), {**PWM_TYPE, 0: 'None'})}",
        "SERVO_BLH_BDMASK (bidirectional-telemetry channels)": channels(g("SERVO_BLH_BDMASK") or 0),
        "AHRS_ORIENTATION": fmt(g("AHRS_ORIENTATION")),
        "EK3_SRC1_POSXY / VELXY / POSZ / VELZ / YAW": " / ".join([
            fmt(g("EK3_SRC1_POSXY"), SRC_POS), fmt(g("EK3_SRC1_VELXY"), SRC_VEL), fmt(g("EK3_SRC1_POSZ"), SRC_POS),
            fmt(g("EK3_SRC1_VELZ"), SRC_VEL), fmt(g("EK3_SRC1_YAW"), SRC_YAW)]),
        "VISO_TYPE / VISO_DELAY_MS": f"{fmt(g('VISO_TYPE'))} / {fmt(g('VISO_DELAY_MS'))}",
        "Flight modes (FLTMODE1..6)": [fmt(g(f"FLTMODE{i}"), COPTER_MODES) for i in range(1, 7)],
        "RC switch options": {f"RC{i}_OPTION": fmt(g(f"RC{i}_OPTION"), RC_OPTION) for i in range(1, 17)
                              if g(f"RC{i}_OPTION") in RC_OPTION},
        "Telemetry ports (SERIALn protocol/baud)": {f"SERIAL{i}": f"{fmt(g(f'SERIAL{i}_PROTOCOL'))} / {fmt(g(f'SERIAL{i}_BAUD'))}"
                                                    for i in range(0, 8) if g(f"SERIAL{i}_PROTOCOL") in (1, 2)},
        "ARMING_SKIPCHK (4.7+, 0 = all checks) / ARMING_CHECK (<4.7)":
            f"{fmt(g('ARMING_SKIPCHK'))} / {fmt(g('ARMING_CHECK'))}",
        "GPS1_TYPE / COMPASS_USE,2,3": f"{fmt(g('GPS1_TYPE', g('GPS_TYPE')))} / "
                                       f"{fmt(g('COMPASS_USE'))},{fmt(g('COMPASS_USE2'))},{fmt(g('COMPASS_USE3'))}",
        "VISO_POS_M_NSE / VISO_YAW_M_NSE": f"{fmt(g('VISO_POS_M_NSE'))} / {fmt(g('VISO_YAW_M_NSE'))}",
        "BATT_MONITOR": fmt(g("BATT_MONITOR")), "FS_GCS_ENABLE": fmt(g("FS_GCS_ENABLE")),
        "FS_EKF_ACTION / FS_EKF_THRESH": f"{fmt(g('FS_EKF_ACTION'))} / {fmt(g('FS_EKF_THRESH'))}",
        "FENCE_ENABLE": fmt(g("FENCE_ENABLE")), "LOG_BITMASK": fmt(g("LOG_BITMASK")),
        "SystemID mode available (SID_AXIS present)": "SID_AXIS" in p,
    }

    need(g("FRAME_CLASS") == 16, f"FRAME_CLASS is {fmt(g('FRAME_CLASS'), FRAME_CLASS)}; the 6DoF mixer needs 16 (6DoF Scripting)")
    need(g("SCR_ENABLE") == 1, "SCR_ENABLE must be 1 so the generated Lua mixer runs")
    need(len(motors) == 8 and len(set(motors.values())) == 8,
         f"{len(motors)} servo outputs are assigned to Motor1..8 (need exactly 8, each once)")
    dshot = g("MOT_PWM_TYPE") is not None and 4 <= g("MOT_PWM_TYPE") <= 7
    if dshot:
        threed = set(channels(g("SERVO_BLH_3DMASK") or 0))
        need(set(motors) <= threed, "DShot: every motor channel should be in SERVO_BLH_3DMASK (3D/reversible)")
        # ArduPilot only sends DSHOT_3D_ON / DSHOT_REVERSE when the ESC type is a BLHeli type
        # (AP_HAL_ChibiOS/RCOutput_serial.cpp update_channel_masks, Copter-4.7.1).
        need(g("SERVO_DSHOT_ESC") in (1, 2, 3, 4),
             "SERVO_DSHOT_ESC = 1 (BLHeli32/Kiss/AM32) so ArduPilot switches the ESCs to 3D mode")
        if g("FRAME_CLASS") == 16:
            # The 6DoF frame never sets its motor outputs to DShot (AP_MotorsMatrix_6DoF_Scripting::init does
            # not call set_update_rate); force it with the BLHeli output-type override (AP_BLHeli::init).
            forced = set(channels(g("SERVO_BLH_MASK") or 0))
            need(set(motors) <= forced and g("SERVO_BLH_OTYPE") == g("MOT_PWM_TYPE"),
                 "6DoF frame: SERVO_BLH_MASK must cover the motor outputs and SERVO_BLH_OTYPE = MOT_PWM_TYPE "
                 "to force DShot (boot banner must read 'RCOut: DS300:1-8 ...')")
    else:
        findings.append("CHECK  PWM ESCs: reversibility (1500 us = stop) must be configured in the ESC firmware itself")
    need(g("EK3_SRC1_POSXY") == 6 and g("EK3_SRC1_POSZ") == 6 and g("EK3_SRC1_YAW") == 6
         and g("EK3_SRC1_VELXY") == 0 and g("EK3_SRC1_VELZ") == 0,
         "EKF3 source set 1 for OptiTrack: POSXY=6, POSZ=6, YAW=6, VELXY=0, VELZ=0 (ArduPilot OptiTrack wiki)")
    need((g("VISO_TYPE") or 0) >= 1, "VISO_TYPE must be 1 (MAVLink) to accept OptiTrack pose messages")
    need(all(g(k) in (None, 0) for k in ("COMPASS_USE", "COMPASS_USE2", "COMPASS_USE3")),
         "COMPASS_USE, COMPASS_USE2, COMPASS_USE3 = 0 indoors (yaw comes from OptiTrack)")
    need(g("GPS1_TYPE", g("GPS_TYPE")) in (None, 0), "GPS1_TYPE = 0 indoors (no GPS)")
    if "ARMING_SKIPCHK" in p:                              # ArduPilot 4.7+: bitmask of checks to SKIP
        need(g("ARMING_SKIPCHK") == 0, "ARMING_SKIPCHK should be 0 (no pre-arm checks skipped)")
    else:
        need(g("ARMING_CHECK") not in (None, 0), "ARMING_CHECK should not be 0 (all pre-arm checks disabled)")
    need((g("BATT_MONITOR") or 0) > 0, "BATT_MONITOR is 0: no voltage reading, no battery failsafe, "
                                         "no thrust voltage compensation")
    modes = {g(f"FLTMODE{i}") for i in range(1, 7)}
    need({0, 2, 9} <= modes or {0, 2, 5} <= modes,
         "Flight modes should include Stabilize (0), AltHold (2) and Loiter (5) or Land (9) on the mode switch")
    need("SID_AXIS" in p, "SystemID mode is needed for the in-flight frequency sweeps")
    need(any(g(f"RC{i}_OPTION") in (31, 32) for i in range(1, 17)),
         "An RC switch should be set to Motor Emergency Stop (31) or Motor Interlock (32)")

    groups = {prefix: {k: v for k, v in sorted(p.items()) if k.startswith(prefix)} for prefix in GROUP_PREFIXES}
    return key, findings, groups


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=14550)
    parser.add_argument("--pico-ip", help="Pico W IP if auto-detection fails")
    parser.add_argument("--timeout", type=float, default=180.0, help="Parameter download timeout [s]")
    parser.add_argument("--output", type=Path, default=HERE / "audits")
    args = parser.parse_args()

    print(f"Listening for the Cube on UDP {args.port} (read-only audit) ...", flush=True)
    link = connect(args.port, pico_ip=args.pico_ip)
    try:
        print(f"Connected: system {link.target_system}, component {link.target_component}, "
              f"Pico {link.pico[0]}:{link.pico[1]}, armed={is_armed(link.heartbeat)}", flush=True)
        version = fetch_version(link)
        print(f"Firmware: {version}", flush=True)
        rc = fetch_rc(link)
        print(f"RC receiver: {rc}", flush=True)
        print("Downloading parameters ...", flush=True)
        params, count = fetch_params(link, args.timeout)
    finally:
        link.close()
    if not params:
        raise SystemExit("No parameters received.")

    out = args.output / datetime.now().strftime("audit_%Y%m%d_%H%M%S")
    out.mkdir(parents=True, exist_ok=False)
    (out / "cube_params.param").write_text(
        "".join(f"{k},{v:.7g}\n" for k, v in sorted(params.items())), encoding="utf-8")
    key, findings, groups = audit(params)
    complete = count is not None and len(params) >= count
    findings.append(("OK  " if rc.get("receiver_detected") else "TODO") + "  RC receiver connected and bound "
                    "(a safety pilot with an E-stop switch is required for armed tests)")
    report = {"firmware": version, "rc": rc, "params_received": len(params), "params_expected": count,
              "complete": complete, "key_settings": key, "findings": findings, "groups": groups}
    (out / "audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(f"\nParameters: {len(params)} / {count} {'(complete)' if complete else '(INCOMPLETE - rerun)'}")
    print("\n== Key settings ==")
    for k, v in key.items():
        print(f"  {k}: {v}")
    print("\n== Readiness for 6DoF + OptiTrack ==")
    for line in findings:
        print("  " + line)
    print(f"\nSaved {out / 'cube_params.param'} and {out / 'audit.json'} (nothing was changed on the Cube).")


if __name__ == "__main__":
    main()
