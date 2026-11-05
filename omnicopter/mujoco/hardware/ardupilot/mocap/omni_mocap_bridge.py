"""OptiTrack (Motive) -> ArduPilot bridge for the Omnidrone (6DoF frame, EKF3 ExternalNav).

    python omni_mocap_bridge.py --server <MotivePC> --list         # rigid bodies, names, rates
    python omni_mocap_bridge.py --server <MotivePC> --calibrate    # define the room frame (2 hand moves)
    python omni_mocap_bridge.py --server <MotivePC> --check        # live pose in room / NED / twin frames
    python omni_mocap_bridge.py --server <MotivePC> --stream       # Cube link hub + pose to the EKF

Stream mode is the MAVLink hub for the Pico W link.  It binds UDP 14550 (where the Pico
sends Cube telemetry), relays every byte to Mission Planner on 127.0.0.1:14551
(Mission Planner: connect UDP, port 14551), relays Mission Planner's replies back to the
Pico, and injects VISION_POSITION_ESTIMATE at --rate Hz.  Close Mission Planner's
14550 connection first; only one program can own that port.

Frames (all right-handed):
  Motive world M (Y-up or Z-up), rigid body RB with pose A = R_M<-RB, p.
  Room = MuJoCo world: x = ArduPilot forward at calibration, y = left, z = up,
         origin = rigid-body pivot at the take-off spot.  Measured from motion, not assumed:
         C = [f; l; u] (Motive -> room), p_room = C (p - p0), R_room<-FLU = C A A0^T C^T.
  ArduPilot body FRD = mixer frame: forward = twin body +z, right = twin body -y,
         down = twin body +x (read from generated/omnidrone_6dof_mixer.json).
  NED = diag(1,-1,-1) room;  R_NED<-FRD = F R_room<-FLU F.
  Twin body attitude in MuJoCo world: R_room<-FLU @ FLU_FROM_MJ.  At calibration this is the
  XML hover quaternion (0.7071, 0, 0.7071, 0).

Safety behaviour: untracked frames, single-frame jumps (marker swaps) and stale data are
never sent; the EKF then times out and FS_EKF_ACTION applies.  After a gap the next good
frame increments reset_counter so the EKF treats it as a discontinuity.

NatNet client: natnet.py, copied unchanged from the tested QDrone2 ground station
(Desktop/GHYN/QDrone2_GroundStation_Python_2026-10-28/mocap, sha256 B37FFEEE280BE618...).
"""
from __future__ import annotations

import argparse
import collections
import csv
from datetime import datetime
import json
import math
from pathlib import Path
import select
import socket
import sys
import threading
import time

import numpy as np
from pymavlink.dialects.v20 import ardupilotmega as mavlink2

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import natnet  # noqa: E402

CAL_FILE = HERE / "omni_mocap_calib.json"
LOG_DIR = HERE / "logs"
MIXER_JSON = HERE.parent / "generated" / "omnidrone_6dof_mixer.json"
F = np.diag([1.0, -1.0, -1.0])                      # room <-> NED, FLU <-> FRD
BRIDGE_SYSTEM, BRIDGE_COMPONENT = 255, 197          # GCS system id, visual-odometry component
COPTER_MODES = {0: "Stabilize", 1: "Acro", 2: "AltHold", 3: "Auto", 4: "Guided", 5: "Loiter", 6: "RTL",
                9: "Land", 16: "PosHold", 17: "Brake", 25: "SystemID"}


def now():
    return time.perf_counter()                       # 0.1 us on Windows (time.monotonic is 15.6 ms)


# ---------------------------------------------------------------- frames
def flu_from_mj():
    """Rows: ArduPilot forward/left/up axes in MuJoCo body coordinates (from the mixer generator)."""
    frd = np.array([[0.0, 0.0, 1.0], [0.0, -1.0, 0.0], [1.0, 0.0, 0.0]])
    if MIXER_JSON.exists():
        frd = np.array(json.loads(MIXER_JSON.read_text(encoding="utf-8"))["ap_frd_axes_in_mujoco_body"])
    flu = F @ frd
    if not np.allclose(flu @ flu.T, np.eye(3), atol=1e-6) or not np.isclose(np.linalg.det(flu), 1.0):
        raise ValueError(f"{MIXER_JSON}: ArduPilot axes are not a rotation")
    return flu


FLU_FROM_MJ = flu_from_mj()


def quat_to_R(q):
    """(qx, qy, qz, qw) -> rotation matrix."""
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def R_to_wxyz(R):
    w = math.sqrt(max(0.0, 1 + R[0, 0] + R[1, 1] + R[2, 2])) / 2
    x = math.copysign(math.sqrt(max(0.0, 1 + R[0, 0] - R[1, 1] - R[2, 2])) / 2, R[2, 1] - R[1, 2])
    y = math.copysign(math.sqrt(max(0.0, 1 - R[0, 0] + R[1, 1] - R[2, 2])) / 2, R[0, 2] - R[2, 0])
    z = math.copysign(math.sqrt(max(0.0, 1 - R[0, 0] - R[1, 1] + R[2, 2])) / 2, R[1, 0] - R[0, 1])
    q = np.array([w, x, y, z])
    return q / np.linalg.norm(q)


def euler321(R):
    """roll, pitch, yaw [rad] of a body->world rotation (aerospace 3-2-1)."""
    return (math.atan2(R[2, 1], R[2, 2]), math.asin(max(-1.0, min(1.0, -R[2, 0]))), math.atan2(R[1, 0], R[0, 0]))


def rotation_angle(R):
    return math.acos(max(-1.0, min(1.0, (np.trace(R) - 1) / 2)))


def rotvec(R):
    angle = rotation_angle(R)
    axis = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])
    if angle < 1e-9:
        return 0.5 * axis
    return angle / (2 * math.sin(angle)) * axis


class Room:
    def __init__(self, cal, pivot_height=0.0):
        self.C = np.array(cal["C"])
        self.p0 = np.array(cal["p0"])
        self.A0T = quat_to_R(cal["q0"]).T
        self.id = int(cal["rb_id"])
        self.name = cal.get("name", "")
        self.pivot_height = pivot_height

    def pose(self, rb):
        """-> dict with room, NED/FRD and twin-frame pose of one NatNet rigid body sample."""
        p_room = self.C @ (np.asarray(rb.pos) - self.p0)
        R_room_flu = self.C @ quat_to_R(rb.quat) @ self.A0T @ self.C.T
        R_ned_frd = F @ R_room_flu @ F
        R_world_mj = R_room_flu @ FLU_FROM_MJ
        return {"p_room": p_room, "R_room_flu": R_room_flu, "p_ned": F @ p_room,
                "rpy_ned": euler321(R_ned_frd), "R_world_mj": R_world_mj,
                "p_twin": p_room + np.array([0.0, 0.0, self.pivot_height]), "q_twin": R_to_wxyz(R_world_mj)}


# ---------------------------------------------------------------- NatNet helpers
def make_client(a, on_body=None):
    ver = tuple(int(v) for v in a.natnet.split(".")) if a.natnet else None
    return natnet.NatNetClient(server=a.server, local_ip=a.local_ip, unicast=a.unicast, version=ver,
                               on_body=on_body, multicast=a.multicast).start()


def wait_frames(cl, seconds):
    t_end = now() + seconds
    while now() < t_end and cl.frames == 0:
        time.sleep(0.05)
    return cl.frames > 0


def resolve_id(cl, a, seconds=3.0):
    """Rigid-body id from its Motive name (preferred) or --id."""
    t_end = now() + seconds
    while now() < t_end and not cl.names:
        time.sleep(0.05)
    for rid, name in cl.names.items():
        if a.rb_name and name == a.rb_name:
            return rid
    if a.id is not None:
        return a.id
    raise SystemExit(f"rigid body '{a.rb_name}' not found; names seen {cl.names}, ids {sorted(cl.bodies())}. "
                     "Use --list, then --rb-name NAME or --id N.")


def no_data_help(cl, a):
    print(f"no NatNet frames from {a.server} (packets {cl.packets}, unparsable {cl.bad}, local {cl.local_ip}, "
          f"{'unicast' if a.unicast else 'multicast ' + a.multicast}).")
    if cl.last_error:
        print("  last error:", cl.last_error)
    print("  Motive > Data Streaming: Broadcast Frame Data ON, Local Interface = Motive PC network IP (not loopback),\n"
          "  Rigid Bodies ON. Use --unicast for Unicast transmission. Allow Python through the firewall (UDP 1510/1511).")


def record(cl, rid, seconds, label):
    out, last = [], None
    t_end = now() + seconds
    while now() < t_end:
        rb = cl.latest(rid)
        if rb is not None and rb.frame != last and rb.valid:
            last = rb.frame
            out.append((np.array(rb.pos), rb.quat))
        time.sleep(0.002)
    print(f"   {label}: {len(out)} tracked frames in {seconds:.0f} s", flush=True)
    return out


# ---------------------------------------------------------------- modes
def do_list(a):
    cl = make_client(a)
    try:
        if not wait_frames(cl, 5.0):
            no_data_help(cl, a)
            return 2
        start = {k: v.frame for k, v in cl.bodies().items()}
        time.sleep(a.seconds)
        info = cl.info or {}
        print(f"Motive {info.get('app', '?')} | NatNet {'.'.join(map(str, info.get('natnet', ()))) or '?'} | "
              f"layout {'%d.%d' % cl.version if cl.version else '?'} | frames {cl.frames}, unparsable {cl.bad}")
        for k, rb in sorted(cl.bodies().items()):
            rate = (rb.frame - start.get(k, rb.frame)) / a.seconds
            mark = "  <== Omnidrone" if cl.names.get(k) == a.rb_name else ""
            print(f"  id {k} '{cl.names.get(k, '?')}': ~{rate:.0f} Hz, tracked {rb.valid}, "
                  f"pos ({rb.pos[0]:.3f}, {rb.pos[1]:.3f}, {rb.pos[2]:.3f}) m, error {1e3 * rb.err:.2f} mm{mark}")
        return 0
    finally:
        cl.close()


def do_calibrate(a):
    cl = make_client(a)
    try:
        if not wait_frames(cl, 5.0):
            no_data_help(cl, a)
            return 2
        rid = resolve_id(cl, a)
        prompt = (lambda s: print("\n" + s + " (auto)", flush=True)) if a.auto else (lambda s: input("\n" + s + " Press Enter..."))
        prompt("1/3: Omnidrone on the floor at the take-off spot, in its HOVER ATTITUDE (twin body +x towards the floor),\n"
               "     ArduPilot-forward side (twin body +z) pointing where room +x should be. Hands off for 2 s.")
        still = record(cl, rid, 2.0, "still")
        if len(still) < 20:
            print("too few tracked frames: is the rigid body visible?")
            return 3
        P = np.array([s[0] for s in still])
        spread = float(np.ptp(P, 0).max())
        if spread > 0.003:
            print(f"it moved during the still phase ({1e3 * spread:.1f} mm): repeat")
            return 3
        p0, q0 = P.mean(0), still[-1][1]
        prompt("2/3 (8 s): lift it STRAIGHT UP ~30 cm without rotating it, hold 1 s, put it back on the same spot.")
        lift = record(cl, rid, 8.0, "lift")
        D = np.array([s[0] for s in lift]) - p0 if lift else np.zeros((0, 3))
        if len(D) < 50 or np.linalg.norm(D, axis=1).max() < 0.15:
            print("lift not seen (needs ~30 cm with the rigid body tracked)")
            return 3
        dmax = D[np.argmax(np.linalg.norm(D, axis=1))]
        u_hand = dmax / np.linalg.norm(dmax)
        axis = int(np.argmax(np.abs(u_hand)))
        u = np.zeros(3)
        u[axis] = math.copysign(1.0, u_hand[axis])
        lift_tilt = math.degrees(math.acos(min(1.0, abs(u_hand[axis]))))
        if lift_tilt > 10.0:
            print(f"the lift was {lift_tilt:.0f} deg away from every Motive axis: repeat straight up "
                  "(or re-level Motive's ground plane)")
            return 3
        prompt("3/3 (8 s): slide it ~40 cm towards its ArduPilot-forward side (twin body +z), level, then back.")
        fwd = record(cl, rid, 8.0, "forward")
        D = np.array([s[0] for s in fwd]) - p0 if fwd else np.zeros((0, 3))
        H = D - np.outer(D @ u, u) if len(D) else D
        if len(H) < 50 or np.linalg.norm(H, axis=1).max() < 0.20:
            print("forward move not seen (needs ~40 cm)")
            return 3
        hmax = H[np.argmax(np.linalg.norm(H, axis=1))]
        f = hmax / np.linalg.norm(hmax)
        C = np.vstack([f, np.cross(u, f), u])
        cal = {"rb_id": rid, "name": cl.names.get(rid, ""), "C": C.tolist(), "p0": p0.tolist(), "q0": list(q0),
               "motive_up": ("+" if u[axis] > 0 else "-") + "XYZ"[axis], "hand_lift_tilt_deg": lift_tilt,
               "lift_m": float(np.linalg.norm(dmax)), "forward_m": float(np.linalg.norm(hmax)),
               "still_spread_mm": 1e3 * spread, "natnet": "%d.%d" % cl.version if cl.version else None,
               "motive": (cl.info or {}).get("app"), "date": datetime.now().isoformat(timespec="seconds"),
               "frames": "room x = ArduPilot forward (twin body +z) at calibration, y left, z up (Motive up axis); "
                         "origin = rigid-body pivot at the take-off spot",
               "flu_from_mj": FLU_FROM_MJ.tolist()}
        Path(a.cal).write_text(json.dumps(cal, indent=1), encoding="utf-8")
        print(f"\nroom frame saved to {a.cal}\n  rigid body {rid} '{cal['name']}', Motive up {cal['motive_up']} "
              f"(hand lift {lift_tilt:.1f} deg off), lift {cal['lift_m']:.2f} m, forward {cal['forward_m']:.2f} m")
        print("  next: --check, move it by hand: forward -> N+, right -> E+, up -> D-, turn right -> yaw+")
        return 0
    finally:
        cl.close()


def load_room(a):
    try:
        cal = json.loads(Path(a.cal).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print(f"no room calibration ({a.cal}): run --calibrate first")
        return None
    if not np.allclose(np.array(cal.get("flu_from_mj", FLU_FROM_MJ)), FLU_FROM_MJ):
        print("calibration was made with a different mixer frame: recalibrate")
        return None
    return Room(cal, a.pivot_height)


def do_check(a):
    room = load_room(a)
    if room is None:
        return 2
    cl = make_client(a)
    try:
        if not wait_frames(cl, 5.0):
            no_data_help(cl, a)
            return 2
        print("NED (m) and ArduPilot roll/pitch/yaw (deg); twin quaternion wxyz. Ctrl+C to stop.")
        while True:
            rb = cl.latest(room.id)
            if rb is None:
                print(f"   rigid body {room.id} not seen")
            else:
                s = room.pose(rb)
                r, p, y = (math.degrees(v) for v in s["rpy_ned"])
                print(f"   N {s['p_ned'][0]:+6.3f} E {s['p_ned'][1]:+6.3f} D {s['p_ned'][2]:+6.3f} | "
                      f"roll {r:+6.1f} pitch {p:+6.1f} yaw {y:+7.1f} | twin q {np.round(s['q_twin'], 3)} | "
                      f"{'tracked' if rb.valid else 'NOT TRACKED'}", flush=True)
            time.sleep(0.25)
    except KeyboardInterrupt:
        return 0
    finally:
        cl.close()


class Hub:
    """UDP hub: Pico <-> Mission Planner relay plus pose injection and vehicle monitoring."""

    def __init__(self, a, print_status=True):
        self.a = a
        self.print_status = print_status
        try:
            self.vehicle = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.vehicle.bind(("0.0.0.0", a.listen_port))
        except OSError as error:
            raise SystemExit(f"UDP port {a.listen_port} is already in use ({error.strerror}). Disconnect Mission "
                             "Planner from UDP / stop the other tool, then start again.") from None
        self.gcs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.gcs.bind(("127.0.0.1", 0))
        self.gcs_dest = ("127.0.0.1", a.gcs_port)
        self.pico = (a.pico_ip, a.pico_port) if a.pico_ip else None
        self.parser = mavlink2.MAVLink(None)
        self.parser.robust_parsing = True
        self.encoder = mavlink2.MAVLink(None, srcSystem=BRIDGE_SYSTEM, srcComponent=BRIDGE_COMPONENT)
        self.lock = threading.Lock()
        self.target_system = None
        self.vehicle_hb = None             # (t, armed, custom_mode)
        self.ekf_flags = None
        self.local = None                  # (t, x, y, z) from LOCAL_POSITION_NED
        self.attitude = None               # (t, roll, pitch, yaw)
        self.battery = None                # (t, volts, amps, percent) from SYS_STATUS
        self.servo = None                  # (t, [servo1..8 us]) from SERVO_OUTPUT_RAW
        self.acks = {}                     # command id -> (t, MAV_RESULT)
        self.messages = collections.deque(maxlen=200)   # (wall time, severity, text) from STATUSTEXT
        self.seq_last, self.seq_received, self.seq_lost = None, 0, 0   # link quality, autopilot stream
        self.relayed_up = self.relayed_down = 0

    def send_to_vehicle(self, buf):
        if self.pico is None:
            return False
        try:
            self.vehicle.sendto(buf, self.pico)
            return True
        except OSError:
            return False

    def encode(self, message):
        with self.lock:
            buf = message.pack(self.encoder)
            # pack() does not advance the MAVLink sequence number (only MAVLink.send() does)
            self.encoder.seq = (self.encoder.seq + 1) % 256
            return buf

    def pump(self, timeout):
        ready, _, _ = select.select([self.vehicle, self.gcs], [], [], timeout)
        for sock in ready:
            try:
                data, addr = sock.recvfrom(65535)
            except OSError:            # Windows: ICMP port-unreachable when Mission Planner is not listening
                continue
            if sock is self.vehicle:
                if self.pico is None:
                    self.pico = (addr[0], self.a.pico_port)
                    print(f"Pico W at {addr[0]} (sending to port {self.a.pico_port})", flush=True)
                if not self.a.no_relay:
                    try:
                        self.gcs.sendto(data, self.gcs_dest)
                        self.relayed_up += 1
                    except OSError:
                        pass
                self.monitor(data)
            elif self.send_to_vehicle(data):
                self.relayed_down += 1

    def monitor(self, data):
        try:
            messages = self.parser.parse_buffer(data) or []
        except Exception:              # robust parsing: never let a bad byte stop the hub
            return
        t = now()
        for m in messages:
            kind = m.get_type()
            if kind == "BAD_DATA":
                continue
            if m.get_srcComponent() == 1 and (self.target_system is None or m.get_srcSystem() == self.target_system):
                seq = m.get_seq()                             # autopilot packets: count gaps = lost packets
                if self.seq_last is not None:
                    self.seq_lost += (seq - self.seq_last - 1) % 256
                self.seq_last = seq
                self.seq_received += 1
            if kind == "HEARTBEAT" and m.type != mavlink2.MAV_TYPE_GCS and m.get_srcComponent() == 1:
                self.target_system = m.get_srcSystem()
                self.vehicle_hb = (t, bool(m.base_mode & mavlink2.MAV_MODE_FLAG_SAFETY_ARMED), m.custom_mode)
            elif kind == "EKF_STATUS_REPORT":
                self.ekf_flags = m.flags
            elif kind == "LOCAL_POSITION_NED":
                self.local = (t, m.x, m.y, m.z)
            elif kind == "ATTITUDE":
                self.attitude = (t, m.roll, m.pitch, m.yaw)
            elif kind == "SYS_STATUS":
                self.battery = (t, m.voltage_battery / 1000.0, m.current_battery / 100.0, m.battery_remaining)
            elif kind == "SERVO_OUTPUT_RAW":
                self.servo = (t, [getattr(m, f"servo{i}_raw") for i in range(1, 9)])
            elif kind == "COMMAND_ACK":
                self.acks[m.command] = (t, m.result)
            elif kind == "STATUSTEXT":
                self.messages.append((time.time(), m.severity, m.text))
                if self.print_status:
                    print(f"   CUBE: {m.text}", flush=True)

    def link_loss(self, reset=False):
        """Fraction of autopilot packets lost since the last reset (from MAVLink sequence gaps)."""
        total = self.seq_received + self.seq_lost
        loss = self.seq_lost / total if total else 0.0
        if reset:
            self.seq_received = self.seq_lost = 0
        return loss, total

    def close(self):
        self.vehicle.close()
        self.gcs.close()


MOCAP_LOG_COLUMNS = ["time_s", "frame", "valid", "accepted", "sent", "reset_counter",
                     "x_m", "y_m", "z_m", "q_w", "q_x", "q_y", "q_z", "wx_rad_s", "wy_rad_s", "wz_rad_s",
                     "n_m", "e_m", "d_m", "roll_rad", "pitch_rad", "yaw_rad", "marker_error_mm"]


class PoseStreamer:
    """OptiTrack frame -> validated pose -> VISION_POSITION_ESTIMATE at a fixed rate; logs every frame.

    Untracked frames, single-frame jumps (marker swaps) and frames before the first Cube packet are
    never sent.  After a tracking gap longer than gap_s the reset_counter increments.  Shared by the
    CLI bridge (--stream) and the ground-station app.
    """

    def __init__(self, room, hub, rate, writer, max_jump_m=0.10, max_jump_deg=20.0, gap_s=0.5):
        self.room, self.hub, self.writer = room, hub, writer
        self.period = 1.0 / rate
        self.max_jump_m, self.max_jump_deg, self.gap_s = max_jump_m, max_jump_deg, gap_s
        self.st = {"in": 0, "sent": 0, "untracked": 0, "jumps": 0, "reset": 0, "last_ok": None,
                   "next_send": 0.0, "last_pose": None, "last_valid_t": None, "send_fail": 0, "no_pico": 0}
        self.latest = None        # (t, pose dict, accepted) of the newest frame, for displays

    def on_body(self, rb):
        st, hub = self.st, self.hub
        if rb.id != self.room.id:
            return
        t = now()
        st["in"] += 1
        s = self.room.pose(rb)
        accepted = bool(rb.valid)
        if not rb.valid:
            st["untracked"] += 1
        omega = np.full(3, np.nan)
        last = st["last_ok"]
        if accepted and last is not None:
            dt = max(t - last[0], 1e-4)
            if t - last[0] > self.gap_s:
                st["reset"] = (st["reset"] + 1) % 256        # tracking regained after a gap
            elif (np.linalg.norm(s["p_room"] - last[1]) > self.max_jump_m + 4.0 * dt
                  or math.degrees(rotation_angle(last[2].T @ s["R_world_mj"])) > self.max_jump_deg + 400.0 * dt):
                accepted = False
                st["jumps"] += 1
            if accepted:
                omega = rotvec(last[2].T @ s["R_world_mj"]) / dt        # twin-body rate (derived)
        sent = False
        if accepted:
            st["last_ok"] = (t, s["p_room"], s["R_world_mj"])
            st["last_valid_t"] = t
            # Fixed send schedule: frames arrive in OS-timer bursts, so "time since last send"
            # would round the period up to whole bursts and undershoot the requested rate.
            if t >= st["next_send"]:
                st["next_send"] = t + self.period if t - st["next_send"] > self.period else st["next_send"] + self.period
                n, e, d = s["p_ned"]
                r, p, y = s["rpy_ned"]
                msg = hub.encoder.vision_position_estimate_encode(int(t * 1e6), n, e, d, r, p, y,
                                                                  reset_counter=st["reset"])
                st["last_pose"] = (t, s["p_ned"], s["rpy_ned"])
                if hub.pico is None:
                    st["no_pico"] += 1                         # no Cube telemetry seen yet
                elif hub.send_to_vehicle(hub.encode(msg)):
                    sent = True
                    st["sent"] += 1
                else:
                    st["send_fail"] += 1
        self.latest = (t, s, accepted)
        self.writer.writerow([f"{t:.6f}", rb.frame, int(rb.valid), int(accepted), int(sent), st["reset"],
                              *(f"{v:.5f}" for v in s["p_twin"]), *(f"{v:.6f}" for v in s["q_twin"]),
                              *(f"{v:.4f}" for v in omega), *(f"{v:.5f}" for v in s["p_ned"]),
                              *(f"{v:.6f}" for v in s["rpy_ned"]), f"{1e3 * rb.err:.3f}"])


def do_stream(a):
    room = load_room(a)
    if room is None:
        return 2
    hub = Hub(a)
    log_dir = Path(a.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = log_dir / f"mocap_{stamp}.csv"
    fh = log_path.open("w", newline="", encoding="utf-8")
    writer = csv.writer(fh)
    writer.writerow(MOCAP_LOG_COLUMNS)
    vlog = (log_dir / f"vehicle_{stamp}.csv").open("w", newline="", encoding="utf-8")
    vwriter = csv.writer(vlog)
    vwriter.writerow(["time_s", "ekf_n_m", "ekf_e_m", "ekf_d_m", "roll_rad", "pitch_rad", "yaw_rad",
                      "armed", "mode", "ekf_flags"])
    streamer = PoseStreamer(room, hub, a.rate, writer, a.max_jump_m, a.max_jump_deg, a.gap_s)
    st = streamer.st
    cl = make_client(a, on_body=streamer.on_body)
    print(f"Hub on UDP {a.listen_port}; Mission Planner: connect UDP port {a.gcs_port}. "
          f"Pose of rigid body {room.id} '{room.name}' at {a.rate:.0f} Hz. Ctrl+C to stop.\nLogs: {log_path}", flush=True)
    origin_sent, t_status, counts, last_local_t = 0, now() + 1.0, (0, 0), None
    try:
        if not wait_frames(cl, 5.0):
            no_data_help(cl, a)
        while True:
            hub.pump(0.05)
            t = now()
            if a.origin and hub.target_system is not None and origin_sent < 3 and st["sent"] > 0:
                lat, lon, alt = (float(v) for v in a.origin.split(","))
                msg = hub.encoder.set_gps_global_origin_encode(hub.target_system, int(lat * 1e7), int(lon * 1e7),
                                                               int(alt * 1000), int(t * 1e6))
                if hub.send_to_vehicle(hub.encode(msg)):
                    origin_sent += 1
                    print(f"   EKF origin sent ({origin_sent}/3): {a.origin}", flush=True)
            if hub.local is not None and hub.attitude is not None and hub.local[0] != last_local_t:
                last_local_t = hub.local[0]
                vwriter.writerow([f"{hub.local[0]:.6f}", *hub.local[1:], *hub.attitude[1:],
                                  int(hub.vehicle_hb[1]) if hub.vehicle_hb else "",
                                  hub.vehicle_hb[2] if hub.vehicle_hb else "", hub.ekf_flags])
            if t >= t_status:
                rate_in = (st["in"] - counts[0])
                rate_out = (st["sent"] - counts[1])
                counts = (st["in"], st["sent"])
                t_status = t + 1.0
                parts = [f"mocap {rate_in:3d} Hz in / {rate_out:2d} Hz sent"]
                if st["last_valid_t"] is None or t - st["last_valid_t"] > 0.3:
                    parts.append("NOT TRACKED - nothing sent")
                if hub.pico is None:
                    parts.append("waiting for the Pico W (no Cube telemetry yet)")
                if st["last_pose"]:
                    _, pn, rpy = st["last_pose"]
                    parts.append(f"NED {pn[0]:+.3f} {pn[1]:+.3f} {pn[2]:+.3f} yaw {math.degrees(rpy[2]):+6.1f}")
                if hub.vehicle_hb and t - hub.vehicle_hb[0] < 3:
                    mode = COPTER_MODES.get(hub.vehicle_hb[2], str(hub.vehicle_hb[2]))
                    parts.append(f"Cube {'ARMED' if hub.vehicle_hb[1] else 'disarmed'} {mode}")
                else:
                    parts.append("NO CUBE HEARTBEAT")
                if hub.local and st["last_pose"] and t - hub.local[0] < 1.0:
                    diff = np.linalg.norm(np.array(hub.local[1:]) - st["last_pose"][1])
                    parts.append(f"EKF-mocap {100 * diff:4.1f} cm")
                if hub.attitude and st["last_pose"] and t - hub.attitude[0] < 1.0:
                    # Cube attitude (IMU roll/pitch, EKF yaw) minus OptiTrack: roll/pitch disagreement
                    # beyond a few degrees means AHRS_ORIENTATION or the calibration pose is wrong.
                    d = [math.degrees(math.remainder(hub.attitude[1 + k] - st["last_pose"][2][k], 2 * math.pi))
                         for k in range(3)]
                    parts.append(f"Cube-mocap roll {d[0]:+5.1f} pitch {d[1]:+5.1f} yaw {d[2]:+5.1f} deg")
                if st["jumps"] or st["send_fail"]:
                    parts.append(f"jumps rejected {st['jumps']}, send failures {st['send_fail']}")
                print("   " + " | ".join(parts), flush=True)
                fh.flush()
                vlog.flush()
    except KeyboardInterrupt:
        return 0
    finally:
        cl.close()
        hub.close()
        fh.close()
        vlog.close()
        print(f"logs: {log_path}", flush=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--server", required=True, help="Motive PC IP address")
    ap.add_argument("--local-ip", default=None, help="this PC's IP on the Motive network (default: auto)")
    ap.add_argument("--unicast", action="store_true", help="Motive Transmission Type = Unicast")
    ap.add_argument("--multicast", default=natnet.MULTICAST)
    ap.add_argument("--natnet", default=None, help="force the stream layout, e.g. 4.1 (default: detect)")
    ap.add_argument("--rb-name", default="Aries_Omnidrone", help="Motive rigid-body name (preferred over --id)")
    ap.add_argument("--id", type=int, default=None, help="rigid-body Streaming ID if the name is not streamed")
    ap.add_argument("--cal", default=str(CAL_FILE))
    ap.add_argument("--pivot-height", type=float, default=0.0,
                    help="height of the rigid-body pivot above the floor at calibration [m], for twin logs only")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--list", action="store_true")
    mode.add_argument("--calibrate", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--stream", action="store_true")
    ap.add_argument("--seconds", type=float, default=3.0, help="--list duration")
    ap.add_argument("--auto", action="store_true", help="--calibrate without Enter prompts (tests)")
    ap.add_argument("--rate", type=float, default=30.0, help="VISION_POSITION_ESTIMATE rate [Hz]")
    ap.add_argument("--listen-port", type=int, default=14550, help="UDP port the Pico sends telemetry to")
    ap.add_argument("--pico-ip", default=None, help="Pico W IP (default: learned from its first packet)")
    ap.add_argument("--pico-port", type=int, default=14550, help="UDP port the Pico listens on")
    ap.add_argument("--gcs-port", type=int, default=14551, help="Mission Planner UDP port on this PC")
    ap.add_argument("--no-relay", action="store_true", help="do not forward telemetry to Mission Planner")
    ap.add_argument("--origin", default=None, help="LAT,LON,ALT_M: send SET_GPS_GLOBAL_ORIGIN (no GPS indoors)")
    ap.add_argument("--max-jump-m", type=float, default=0.10, help="reject single-frame position jumps above this")
    ap.add_argument("--max-jump-deg", type=float, default=20.0, help="reject single-frame rotation jumps above this")
    ap.add_argument("--gap-s", type=float, default=0.5, help="tracking gap that increments reset_counter")
    ap.add_argument("--log-dir", default=str(LOG_DIR))
    a = ap.parse_args(argv)
    if a.list:
        return do_list(a)
    if a.calibrate:
        return do_calibrate(a)
    if a.check:
        return do_check(a)
    return do_stream(a)


if __name__ == "__main__":
    sys.exit(main())
