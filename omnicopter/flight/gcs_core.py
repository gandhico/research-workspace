"""Omnidrone ground-station core: OptiTrack -> EKF, Cube link, Guided commands and safety. No Mission Planner.

One process owns UDP 14550 (the Pico W link).  Used by omni_gcs.py (window) and tests/test_gcs_core.py (headless).

Flight without an RC link uses ArduPilot GUIDED mode only:
    set GUIDED -> arm -> MAV_CMD_NAV_TAKEOFF -> position targets (SET_POSITION_TARGET_LOCAL_NED) -> LAND.
KILL = MAV_CMD_COMPONENT_ARM_DISARM(0, 21196) force disarm, sent as a burst and repeated until the Cube
reports disarmed.  On the Cube, FS_GCS_ENABLE 5 lands if this program's heartbeat stops for FS_GCS_TIMEOUT.

Safety layers in this program (on top of ArduPilot's own pre-arm checks and failsafes):
  * arming gates (preflight()): OptiTrack tracked and streaming, EKF and Cube attitude agree with OptiTrack,
    link loss acceptable, no PreArm messages, operator confirmed tether/area/kill person;
  * while armed: LAND on tether-radius or height breach, on lost OptiTrack, or on tilt > land_tilt;
    KILL on tilt > kill_tilt (clearly out of control).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import csv
import math
from pathlib import Path
import socket
import struct
import sys
import threading
import time
from types import SimpleNamespace

import numpy as np
from pymavlink.dialects.v20 import ardupilotmega as mavlink2

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "mocap"))
import omni_mocap_bridge as br  # noqa: E402

GCS_SYSTEM, GCS_COMPONENT = 255, 190
MODES = {"STABILIZE": 0, "ALT_HOLD": 2, "GUIDED": 4, "LOITER": 5, "LAND": 9, "BRAKE": 17}
MODE_NAMES = {**{v: k for k, v in br.COPTER_MODES.items()}, **{v: k for k, v in MODES.items()}}
FORCE_DISARM_MAGIC = 21196
POSITION_ONLY_MASK = 2552            # SET_POSITION_TARGET: use x, y, z and yaw; ignore vel/acc/yaw-rate
# ATTITUDE, LOCAL_POSITION_NED, SYS_STATUS, EKF_STATUS, SERVO_OUTPUT_RAW, GPS_GLOBAL_ORIGIN, HOME_POSITION.
# ArduPilot only sends the last two once the EKF origin / home exist, so their arrival confirms them.
STREAMS_HZ = {30: 10, 32: 10, 1: 2, 193: 2, 36: 5, 49: 0.5, 242: 0.5}
TWIN_PORT = 14600
TWIN_PACKET = struct.Struct("<4sd3d4d8H")   # b"OMNT", t, twin xyz, twin quat wxyz, servo1..8 us
TWIN_MAGIC = b"OMNT"


@dataclass
class Limits:
    tether_radius_m: float = 0.5      # horizontal distance from the arming spot -> LAND
    max_height_m: float = 0.6         # height above the arming spot -> LAND
    max_takeoff_m: float = 0.4        # largest takeoff / target height the app will command
    land_tilt_deg: float = 30.0       # tilt from level (ATC_ANGLE_MAX is 20) -> LAND
    kill_tilt_deg: float = 60.0       # tilt from level -> KILL (out of control)
    mocap_timeout_s: float = 0.5      # no accepted OptiTrack frame while airborne -> LAND
    gate_ekf_mocap_m: float = 0.05    # arming gate
    gate_att_diff_deg: float = 5.0    # arming gate
    gate_link_loss: float = 0.25      # arming gate (fraction of Cube packets lost)
    gate_min_rate_hz: float = 20.0    # arming gate (poses sent per second)
    gate_home_radius_m: float = 0.3   # arming gate: start near the calibration spot


@dataclass
class Event:
    wall: float
    text: str
    level: str = "info"               # info | warn | action


@dataclass
class Config:
    server: str = "127.0.0.1"
    cal: str = str(br.CAL_FILE)
    local_ip: str | None = None
    unicast: bool = False
    natnet: str | None = None
    rb_name: str = "Aries_Omnidrone"
    rb_id: int | None = None
    rate: float = 30.0
    listen_port: int = 14550
    pico_ip: str | None = None
    pico_port: int = 14550
    relay: bool = False
    gcs_port: int = 14551
    # EKF origin: any valid NON-ZERO location. Copter-4.7.1 GCS_MAVLINK::set_ekf_origin silently denies
    # 0,0,0 (Location::is_zero). Default: approximate NMSU campus, Las Cruces; only a reference point.
    origin: str = "32.2828,-106.7473,1200"
    log_dir: str = str(HERE / "data" / "logs")
    twin_port: int = TWIN_PORT
    limits: Limits = field(default_factory=Limits)


def tilt_deg(roll, pitch):
    """Angle between body down and world down for an FRD roll/pitch."""
    return math.degrees(math.acos(max(-1.0, min(1.0, math.cos(roll) * math.cos(pitch)))))


class GroundStation:
    def __init__(self, cfg: Config):
        self.cfg, self.lim = cfg, cfg.limits
        br.check_origin(cfg.origin)
        a = SimpleNamespace(server=cfg.server, local_ip=cfg.local_ip, unicast=cfg.unicast,
                            multicast=br.natnet.MULTICAST, natnet=cfg.natnet, rb_name=cfg.rb_name, id=cfg.rb_id,
                            cal=cfg.cal, pivot_height=0.0, listen_port=cfg.listen_port, pico_ip=cfg.pico_ip,
                            pico_port=cfg.pico_port, gcs_port=cfg.gcs_port, no_relay=not cfg.relay)
        self.a = a
        self.room = br.load_room(a)
        if self.room is None:
            raise SystemExit(f"No OptiTrack room calibration at {cfg.cal}: run "
                             "python mocap\\omni_mocap_bridge.py --server <MOTIVE_PC_IP> --calibrate first.")
        self.hub = br.Hub(a, print_status=False)
        log_dir = Path(cfg.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.mocap_log = (log_dir / f"mocap_{stamp}.csv").open("w", newline="", encoding="utf-8")
        mocap_writer = csv.writer(self.mocap_log)
        mocap_writer.writerow(br.MOCAP_LOG_COLUMNS)
        self.telemetry_log = (log_dir / f"telemetry_{stamp}.csv").open("w", newline="", encoding="utf-8")
        self.tlm = csv.writer(self.telemetry_log)
        self.tlm.writerow(["time_s", "hb_age_s", "armed", "mode", "ekf_n", "ekf_e", "ekf_d", "roll", "pitch", "yaw",
                           "mocap_n", "mocap_e", "mocap_d", "mocap_roll", "mocap_pitch", "mocap_yaw",
                           *[f"servo{i}_us" for i in range(1, 9)], "batt_v", "link_loss",
                           "target_n", "target_e", "target_d", "event"])
        self.log_paths = (Path(self.mocap_log.name), Path(self.telemetry_log.name))
        self.streamer = br.PoseStreamer(self.room, self.hub, cfg.rate, mocap_writer)
        self.client = None
        self.enc = mavlink2.MAVLink(None, srcSystem=GCS_SYSTEM, srcComponent=GCS_COMPONENT)
        self.enc_lock = threading.Lock()
        self.events = []
        self.events_lock = threading.Lock()
        self.operator_confirmed = False
        self.home = None              # NED of the arming spot
        self.target = None            # [n, e, d, yaw] current Guided position target
        self.airborne = False
        self.takeoff_height, self.takeoff_started, self.takeoff_done = None, None, False
        self.takeoff_warned = False
        self.killing_until = 0.0
        self.auto_action_done = None  # reason of the last automatic LAND/KILL (one per flight)
        self._stop = threading.Event()
        self._thread = None
        self._rates = {"t": br.now(), "in": 0, "sent": 0, "rate_in": 0.0, "rate_out": 0.0}
        self._loss = (0.0, 0)
        self._last_hb_seen = None
        self._origin_sends = 0
        self._twin_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # ------------------------------------------------------------------ lifecycle
    def start(self):
        self.client = br.make_client(self.a, on_body=self.streamer.on_body)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self.event(f"Started. Logs: {self.log_paths[0].name}, {self.log_paths[1].name}")
        return self

    def close(self):
        self._stop.set()
        if self._thread:
            self._thread.join(2.0)
        if self.client:
            self.client.close()
        self.hub.close()
        self._twin_sock.close()
        self.mocap_log.close()
        self.telemetry_log.close()

    def event(self, text, level="info"):
        with self.events_lock:
            self.events.append(Event(time.time(), text, level))
        self._event_for_log = text

    # ------------------------------------------------------------------ MAVLink out
    def _send(self, msg):
        with self.enc_lock:
            buf = msg.pack(self.enc)
            self.enc.seq = (self.enc.seq + 1) % 256       # pack() alone does not advance the sequence
        return self.hub.send_to_vehicle(buf)

    def _command(self, command, params, wait_s=1.2, attempts=3):
        """COMMAND_LONG with retries over the lossy link. Returns the MAV_RESULT or None."""
        target = self.hub.target_system or 1
        p = (list(params) + [0] * 7)[:7]
        for attempt in range(attempts):
            sent_at = br.now()
            self._send(self.enc.command_long_encode(target, 1, command, attempt, *p))
            end = sent_at + wait_s
            while br.now() < end:
                ack = self.hub.acks.get(command)
                if ack and ack[0] >= sent_at:
                    return ack[1]
                time.sleep(0.01)
        return None

    def _heartbeat(self):
        self._send(self.enc.heartbeat_encode(mavlink2.MAV_TYPE_GCS, mavlink2.MAV_AUTOPILOT_INVALID,
                                             0, 0, mavlink2.MAV_STATE_ACTIVE))

    def _request_streams(self):
        target = self.hub.target_system or 1
        for msg_id, hz in STREAMS_HZ.items():
            self._send(self.enc.command_long_encode(target, 1, mavlink2.MAV_CMD_SET_MESSAGE_INTERVAL, 0,
                                                    msg_id, int(1e6 / hz), 0, 0, 0, 0, 0))

    def _send_origin(self):
        lat, lon, alt = (float(v) for v in self.cfg.origin.split(","))
        target = self.hub.target_system or 1
        self._send(self.enc.set_gps_global_origin_encode(target, int(lat * 1e7), int(lon * 1e7), int(alt * 1000),
                                                         int(br.now() * 1e6)))

    def _send_target(self):
        if self.target is None:
            return
        n, e, d, yaw = self.target
        target = self.hub.target_system or 1
        self._send(self.enc.set_position_target_local_ned_encode(
            int(br.now() * 1000) & 0xFFFFFFFF, target, 1, mavlink2.MAV_FRAME_LOCAL_NED, POSITION_ONLY_MASK,
            n, e, d, 0, 0, 0, 0, 0, 0, yaw, 0))

    # ------------------------------------------------------------------ state
    def armed(self):
        hb = self.hub.vehicle_hb
        return bool(hb and hb[1])

    def mode(self):
        hb = self.hub.vehicle_hb
        return MODE_NAMES.get(hb[2], str(hb[2])) if hb else "?"

    def mocap(self):
        """(age_s, ned, rpy, p_twin, q_twin) of the last accepted pose, or None."""
        st = self.streamer.st
        if st["last_pose"] is None or self.streamer.latest is None:
            return None
        t, ned, rpy = st["last_pose"]
        latest = self.streamer.latest[1]
        return br.now() - t, np.asarray(ned), rpy, latest["p_twin"], latest["q_twin"]

    def status(self):
        t = br.now()
        hub, st, lim = self.hub, self.streamer.st, self.lim
        hb = hub.vehicle_hb
        m = self.mocap()
        s = {"hb_age": (t - hb[0]) if hb else None, "armed": self.armed(), "mode": self.mode(),
             "link_loss": self._loss[0], "link_packets": self._loss[1],
             "rate_in": self._rates["rate_in"], "rate_out": self._rates["rate_out"],
             "tracked": m is not None and m[0] < 0.3, "pico": hub.pico,
             "mocap_ned": None if m is None else m[1], "mocap_rpy": None if m is None else m[2],
             "ekf_ned": None, "ekf_mocap_m": None, "cube_rpy": None, "att_diff_deg": None,
             "battery": None if hub.battery is None or hub.battery[1] <= 0 else hub.battery[1:],
             "servo": None if hub.servo is None or t - hub.servo[0] > 2 else hub.servo[1],
             "home": self.home, "target": self.target, "airborne": self.airborne,
             "jumps": st["jumps"], "auto_action": self.auto_action_done,
             "origin_set": hub.origin_msg is not None and t - hub.origin_msg[0] < 6.0,
             "home_set": hub.home_msg is not None and t - hub.home_msg[0] < 6.0}
        if hub.local and t - hub.local[0] < 1.0:
            s["ekf_ned"] = np.array(hub.local[1:])
            if m is not None:
                s["ekf_mocap_m"] = float(np.linalg.norm(s["ekf_ned"] - m[1]))
        if hub.attitude and t - hub.attitude[0] < 1.0:
            s["cube_rpy"] = hub.attitude[1:]
            if m is not None:
                s["att_diff_deg"] = [math.degrees(math.remainder(hub.attitude[1 + k] - m[2][k], 2 * math.pi))
                                     for k in range(3)]
        return s

    def preflight(self):
        """Arming gates: list of (ok, label, detail)."""
        s, lim = self.status(), self.lim
        recent_prearm = [e for e in list(self.hub.messages)[-30:]
                         if e[2].startswith("PreArm") and time.time() - e[0] < 3.0]
        near_home = s["mocap_ned"] is not None and math.hypot(*s["mocap_ned"][:2]) < lim.gate_home_radius_m
        gates = [
            (s["hb_age"] is not None and s["hb_age"] < 1.5, "Cube link",
             "no heartbeat" if s["hb_age"] is None else f"heartbeat {s['hb_age']:.1f} s ago"),
            (not s["armed"], "Disarmed", s["mode"]),
            (s["tracked"] and s["rate_out"] >= lim.gate_min_rate_hz, "OptiTrack to EKF",
             f"{s['rate_out']:.0f} Hz sent" + ("" if s["tracked"] else ", NOT TRACKED")),
            (s["ekf_mocap_m"] is not None and s["ekf_mocap_m"] < lim.gate_ekf_mocap_m, "EKF = OptiTrack",
             "no EKF position" if s["ekf_mocap_m"] is None else f"{100 * s['ekf_mocap_m']:.1f} cm"),
            (s["att_diff_deg"] is not None and max(abs(v) for v in s["att_diff_deg"]) < lim.gate_att_diff_deg,
             "Cube attitude = OptiTrack", "no attitude" if s["att_diff_deg"] is None else
             "r/p/y " + "/".join(f"{v:+.1f}" for v in s["att_diff_deg"]) + " deg"),
            (s["link_packets"] > 20 and s["link_loss"] < lim.gate_link_loss, "Link quality",
             f"{100 * s['link_loss']:.0f} % lost of {s['link_packets']}"),
            (not recent_prearm, "Cube pre-arm checks", recent_prearm[-1][2] if recent_prearm else "no PreArm messages"),
            # Guided takeoff converts "height above home" to "above EKF origin": without an origin the
            # Cube refuses TAKEOFF with FAILED (ModeGuided::do_user_takeoff_start_m, Copter-4.7.1).
            (s["origin_set"], "EKF origin set on the Cube",
             "confirmed by the Cube" if s["origin_set"] else "not confirmed yet (the app keeps sending it)"),
            (near_home, "At the take-off spot", "no pose" if s["mocap_ned"] is None else
             f"{100 * math.hypot(*s['mocap_ned'][:2]):.0f} cm from the calibration spot"),
            (self.operator_confirmed, "Operator: tether, area clear, kill ready", "tick the box"),
        ]
        return gates

    # ------------------------------------------------------------------ commands
    def set_mode(self, name):
        result = self._command(mavlink2.MAV_CMD_DO_SET_MODE, [mavlink2.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, MODES[name]])
        ok = result == mavlink2.MAV_RESULT_ACCEPTED
        self.event(f"Mode {name}: {'accepted' if ok else self._result_name(result)}", "info" if ok else "warn")
        return ok

    def arm(self):
        failed = [label for ok, label, _ in self.preflight() if not ok]
        if failed:
            self.event("ARM refused by the app: " + ", ".join(failed), "warn")
            return False
        if self.mode() != "GUIDED":
            if not self.set_mode("GUIDED") or not self._wait_state(mode="GUIDED"):
                self.event("GUIDED not confirmed by the Cube heartbeat", "warn")
                return False
        result = self._command(mavlink2.MAV_CMD_COMPONENT_ARM_DISARM, [1])
        ok = result == mavlink2.MAV_RESULT_ACCEPTED and self._wait_state(armed=True)
        if ok:
            m = self.mocap()
            self.home = m[1].copy()
            self.target = [*self.home, m[2][2]]
            self.airborne = False
            self.takeoff_height, self.takeoff_started, self.takeoff_done = None, None, False
            self.takeoff_warned = False
            self.auto_action_done = None
        self.event("ARMED (GUIDED)" if ok else f"Arm rejected: {self._result_name(result)} (see Cube messages)",
                   "action" if ok else "warn")
        return ok

    def takeoff(self, height_m):
        height_m = float(height_m)
        if not (0.05 <= height_m <= self.lim.max_takeoff_m):
            self.event(f"Takeoff height must be 0.05..{self.lim.max_takeoff_m} m", "warn")
            return False
        if not self.armed() or self.mode() != "GUIDED" or self.home is None:
            self.event("Takeoff needs ARMED in GUIDED", "warn")
            return False
        sent_at = br.now()
        result = self._command(mavlink2.MAV_CMD_NAV_TAKEOFF, [0, 0, 0, 0, 0, 0, height_m])
        ok = result == mavlink2.MAV_RESULT_ACCEPTED
        reply_lost = False
        if not ok and self._motors_spooling_since(sent_at):
            # 2026-11-04 on the vehicle: the ACCEPTED reply was lost, the retry got FAILED because the takeoff was
            # already running, and the app believed it was still on the ground (safety limits inactive).
            ok = reply_lost = True
        if ok:
            self.target = [self.home[0], self.home[1], self.home[2] - height_m, self.target[3]]
            self.airborne = True                  # safety limits active from now on
            # No position target until the takeoff has climbed: any SET_POSITION_TARGET switches Guided from
            # its TakeOff sub-mode to Pos, which keeps a landed vehicle at ground idle (motors stopped) and
            # lets DISARM_DELAY disarm it (found on the vehicle 2026-11-04, Copter-4.7.1 ModeGuided).
            self.takeoff_height = height_m
            self.takeoff_started = br.now()
            self.takeoff_done = False
            self.event(f"Takeoff to {height_m:.2f} m: accepted"
                       + (" (reply lost on the link, but the motors are spooling up)" if reply_lost else "")
                       + " (nudges enabled once it reaches the height)", "action")
        else:
            s = self.status()
            hints = []
            if not s["origin_set"]:
                hints.append("EKF origin not confirmed")
            if not s["home_set"]:
                hints.append("home not set on the Cube")
            self.event(f"Takeoff to {height_m:.2f} m: {self._result_name(result)} (the Cube refused"
                       + (": " + ", ".join(hints) if hints else "; it must be landed, armed in GUIDED") + ")", "warn")
        return ok

    def _motors_spooling_since(self, since, wait_s=1.5, threshold_us=40):
        """True if SERVO_OUTPUT_RAW shows any motor leaving 1500 us (6DoF idle) after `since` (waits up to wait_s)."""
        end = br.now() + wait_s
        while True:
            servo = self.hub.servo
            if servo and servo[0] > since and any(abs(us - 1500) > threshold_us for us in servo[1]):
                return True
            if br.now() >= end:
                return False
            time.sleep(0.05)

    def nudge(self, dn=0.0, de=0.0, dup=0.0, dyaw_deg=0.0):
        """Move the Guided position target, clamped inside the tether limits."""
        if not (self.armed() and self.mode() == "GUIDED" and self.airborne and self.target and self.home is not None):
            self.event("Nudge needs an airborne GUIDED flight", "warn")
            return False
        if not self.takeoff_done:
            m = self.mocap()
            height = None if m is None else self.home[2] - m[1][2]
            self.event("Nudge ignored: the takeoff has not reached its height yet"
                       + ("" if height is None else f" ({height:.2f} of {self.takeoff_height:.2f} m)"), "warn")
            return False
        n, e, d, yaw = self.target
        n, e, d = n + dn, e + de, d - dup
        r = math.hypot(n - self.home[0], e - self.home[1])
        r_max = max(0.0, self.lim.tether_radius_m - 0.15)
        if r > r_max:
            n = self.home[0] + (n - self.home[0]) * r_max / r
            e = self.home[1] + (e - self.home[1]) * r_max / r
        height = min(max(self.home[2] - d, 0.1), self.lim.max_takeoff_m)
        self.target = [n, e, self.home[2] - height, math.remainder(yaw + math.radians(dyaw_deg), 2 * math.pi)]
        self._send_target()
        self.event("Target N {:+.2f} E {:+.2f} up {:.2f} m, yaw {:+.0f} deg".format(
            n - self.home[0], e - self.home[1], height, math.degrees(self.target[3])))
        return True

    def land(self, reason="operator"):
        ok = self.set_mode("LAND")
        self.event(f"LAND ({reason})", "action")
        return ok

    def disarm(self):
        result = self._command(mavlink2.MAV_CMD_COMPONENT_ARM_DISARM, [0])
        ok = result == mavlink2.MAV_RESULT_ACCEPTED
        self.event("Disarmed" if ok else f"Disarm rejected: {self._result_name(result)} (still flying? use LAND)",
                   "action" if ok else "warn")
        return ok

    def kill(self, reason="operator"):
        """Force disarm: motors stop immediately. Burst now; the run loop repeats every 0.1 s for up to 3 s
        until the Cube reports disarmed (the Wi-Fi link can drop single packets)."""
        self.killing_until = br.now() + 3.0
        self._force_disarm_burst()
        self.event(f"KILL ({reason}): force disarm sent", "action")

    def _force_disarm_burst(self, count=5):
        target = self.hub.target_system or 1
        for _ in range(count):
            self._send(self.enc.command_long_encode(target, 1, mavlink2.MAV_CMD_COMPONENT_ARM_DISARM, 0,
                                                    0, FORCE_DISARM_MAGIC, 0, 0, 0, 0, 0))

    def _wait_state(self, armed=None, mode=None, timeout_s=2.5):
        """Wait for the Cube's heartbeat (1 Hz on the real vehicle) to confirm a state change."""
        end = br.now() + timeout_s
        while br.now() < end:
            if (armed is None or self.armed() == armed) and (mode is None or self.mode() == mode):
                return True
            time.sleep(0.02)
        return False

    @staticmethod
    def _result_name(result):
        if result is None:
            return "no reply"
        entry = mavlink2.enums["MAV_RESULT"].get(result)
        return entry.name.replace("MAV_RESULT_", "") if entry else str(result)

    # ------------------------------------------------------------------ background loop
    def _auto_land(self, reason):
        """Automatic LAND from the safety monitor. Runs in its own thread: set_mode waits for the Cube's ACK,
        and the background loop that reads those ACKs must never block (2026-11-04 test finding)."""
        self.auto_action_done = reason
        threading.Thread(target=self.land, args=(reason,), daemon=True).start()

    def _watch_takeoff(self, t):
        """Enable position targets once OptiTrack shows the takeoff height (within 3 cm)."""
        if not self.airborne or self.takeoff_done or self.takeoff_height is None or self.home is None:
            return
        m = self.mocap()
        if m is not None and self.home[2] - m[1][2] >= self.takeoff_height - 0.03:
            self.takeoff_done = True
            self.event(f"Takeoff complete at {self.home[2] - m[1][2]:.2f} m: holding, nudges enabled", "action")
        elif not self.takeoff_warned and t - self.takeoff_started > 15.0:
            self.takeoff_warned = True
            height = None if m is None else self.home[2] - m[1][2]
            self.event("Takeoff has not reached its height after 15 s"
                       + ("" if height is None else f" (at {height:.2f} m)") + ": LAND (L) or KILL (SPACE)", "warn")

    def _safety(self, t):
        if not self.armed():
            if self.airborne and self.auto_action_done is None:
                self.event("Disarmed")
            self.airborne = False
            return
        if self.auto_action_done is not None or self.home is None:
            return
        s, lim = self.status(), self.lim
        rpy = s["cube_rpy"] or s["mocap_rpy"]
        if rpy is not None:
            tilt = tilt_deg(rpy[0], rpy[1])
            if tilt > lim.kill_tilt_deg:
                self.auto_action_done = f"tilt {tilt:.0f} deg"
                self.kill(self.auto_action_done)
                return
            if tilt > lim.land_tilt_deg and self.airborne:
                self._auto_land(f"tilt {tilt:.0f} deg")
                return
        if not self.airborne:
            return
        m = self.mocap()
        if m is None or m[0] > lim.mocap_timeout_s:
            self._auto_land("OptiTrack lost")
            return
        r = math.hypot(m[1][0] - self.home[0], m[1][1] - self.home[1])
        height = self.home[2] - m[1][2]
        if r > lim.tether_radius_m:
            self._auto_land(f"{r:.2f} m from the arming spot")
        elif height > lim.max_height_m:
            self._auto_land(f"{height:.2f} m high")

    def _run(self):
        next_hb = next_streams = next_safety = next_log = next_twin = next_rate = next_target = next_kill = 0.0
        next_origin = 0.0
        self._origin_confirmed = self._home_confirmed = False
        self._event_for_log = ""
        while not self._stop.is_set():
            self.hub.pump(0.01)
            t = br.now()
            hb = self.hub.vehicle_hb
            if hb and (self._last_hb_seen is None or hb[0] - self._last_hb_seen > 5.0):
                self.event("Cube connected" if self._last_hb_seen is None else "Cube heartbeat back (rebooted?)")
                next_streams, self._origin_sends = 0.0, 0
                # a rebooted Cube has lost its EKF origin and home: forget the old confirmations
                self.hub.origin_msg = self.hub.home_msg = None
                self._origin_confirmed = self._home_confirmed = False
            self._last_hb_seen = hb[0] if hb else self._last_hb_seen
            if t >= next_hb:
                next_hb = t + 0.2
                self._heartbeat()
            if hb and t >= next_streams:
                next_streams = t + (10.0 if self.hub.attitude and t - self.hub.attitude[0] < 2 else 2.0)
                self._request_streams()
            # EKF origin: send until the Cube confirms it with GPS_GLOBAL_ORIGIN. A single burst at start-up can
            # arrive while the EKF is still initialising (2026-11-04: TAKEOFF then FAILED).
            if hb and self.streamer.st["sent"] > 10 and self.hub.origin_msg is None and t >= next_origin:
                next_origin = t + 2.0
                self._send_origin()
                self._origin_sends += 1
                if self._origin_sends == 1:
                    self.event(f"EKF origin sent ({self.cfg.origin}), waiting for the Cube to confirm")
            if self.hub.origin_msg is not None and not self._origin_confirmed:
                self._origin_confirmed = True
                self.event("EKF origin confirmed by the Cube")
            if self.hub.home_msg is not None and not self._home_confirmed:
                self._home_confirmed = True
                self.event("Home set on the Cube")
            if t < self.killing_until and self.armed() and t >= next_kill:
                next_kill = t + 0.1
                self._force_disarm_burst()
            self._watch_takeoff(t)
            if t >= next_target:
                next_target = t + 1.0
                if self.airborne and self.takeoff_done and self.armed() and self.mode() == "GUIDED":
                    self._send_target()                   # refresh: covers a lost packet (never during takeoff)
            if t >= next_safety:
                next_safety = t + 0.05
                self._safety(t)
            if t >= next_rate:
                next_rate = t + 1.0
                st = self.streamer.st
                self._rates.update(rate_in=st["in"] - self._rates["in"], rate_out=st["sent"] - self._rates["sent"],
                                   **{"in": st["in"], "sent": st["sent"]})
                if t - self._rates["t"] > 3.0:
                    self._loss = self.hub.link_loss(reset=True)
                    self._rates["t"] = t
            if t >= next_twin:
                next_twin = t + 1 / 30
                self._publish_twin(t)
            if t >= next_log:
                next_log = t + 0.1
                self._log(t)

    def _publish_twin(self, t):
        latest = self.streamer.latest
        if latest is None:
            return
        p, q = latest[1]["p_twin"], latest[1]["q_twin"]
        servo = (self.hub.servo[1] if self.hub.servo else [1500] * 8)
        try:
            self._twin_sock.sendto(TWIN_PACKET.pack(TWIN_MAGIC, t, *p, *q, *[int(v) for v in servo]),
                                   ("127.0.0.1", self.cfg.twin_port))
        except OSError:
            pass

    def _log(self, t):
        s = self.status()
        hb = self.hub.vehicle_hb

        def fmt(v, n=3):
            return "" if v is None else [f"{x:.{n}f}" for x in v]
        row = [f"{t:.3f}", "" if s["hb_age"] is None else f"{s['hb_age']:.2f}", int(s["armed"]),
               hb[2] if hb else ""]
        row += fmt(s["ekf_ned"]) or ["", "", ""]
        row += fmt(s["cube_rpy"], 4) or ["", "", ""]
        row += fmt(s["mocap_ned"]) or ["", "", ""]
        row += fmt(s["mocap_rpy"], 4) or ["", "", ""]
        row += list(s["servo"]) if s["servo"] else [""] * 8
        row += ["" if s["battery"] is None else f"{s['battery'][0]:.2f}", f"{s['link_loss']:.3f}"]
        row += fmt(self.target[:3]) if self.target else ["", "", ""]
        row.append(self._event_for_log)
        self._event_for_log = ""
        self.tlm.writerow(row)
        if int(t * 10) % 10 == 0:
            self.mocap_log.flush()
            self.telemetry_log.flush()
