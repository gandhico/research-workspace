"""Headless test of gcs_core.GroundStation against fake Motive + a fake ArduPilot Cube in GUIDED (~25 s).

    python test_gcs_core.py

Fake Motive timeline (fake_motive.py): 0-6 s still at the spot, 6-14 s rises 0.30 m, 14-22 s moves 0.40 m
forward and back.  The room calibration is computed from the fake's known geometry, so no hand moves.

Checks: telemetry streams requested, EKF origin sent, GCS heartbeat >= 4 Hz, arming refused until the operator
confirms, arm in GUIDED, takeoff, nudge sends a position target, automatic LAND when the vehicle passes the
tether radius (0.25 m in this test), KILL force-disarms, twin-viewer packets published, logs written.
"""
import json
import math
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time

import numpy as np
from pymavlink.dialects.v20 import ardupilotmega as mavlink2

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "mocap"))
import fake_motive as fm  # noqa: E402
import gcs_core  # noqa: E402

GCS_PORT, CUBE_PORT, TWIN_PORT = 14652, 14662, 14602


class FakeCubeGuided(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", CUBE_PORT))
        self.sock.settimeout(0.02)
        self.enc = mavlink2.MAVLink(None, srcSystem=1, srcComponent=1)
        self.parser = mavlink2.MAVLink(None)
        self.mode, self.armed = 0, False
        self.vpe_t = 0.0
        self.streams, self.origin, self.targets, self.takeoff_alt = set(), None, [], None
        self.force_disarms, self.gcs_heartbeats = 0, 0
        self.sent, self.drop_every = 0, 10                # drop 10 % of the Cube's packets, like the real link
        self.stop = threading.Event()

    def send(self, msg, drop_every=0):
        buf = msg.pack(self.enc)
        self.enc.seq = (self.enc.seq + 1) % 256           # like a real autopilot: one sequence number per packet
        self.sent += 1
        if self.drop_every and self.sent % self.drop_every == 0:
            return                                        # simulated Wi-Fi loss
        self.sock.sendto(buf, ("127.0.0.1", GCS_PORT))

    def ack(self, command, ok=True):
        self.send(self.enc.command_ack_encode(command, mavlink2.MAV_RESULT_ACCEPTED if ok else mavlink2.MAV_RESULT_FAILED))

    def run(self):
        next_hb = next_slow = 0.0
        while not self.stop.is_set():
            now = time.time()
            if now >= next_hb:
                next_hb = now + 0.5
                base = mavlink2.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED | (mavlink2.MAV_MODE_FLAG_SAFETY_ARMED if self.armed else 0)
                self.send(self.enc.heartbeat_encode(mavlink2.MAV_TYPE_OCTOROTOR, mavlink2.MAV_AUTOPILOT_ARDUPILOTMEGA,
                                                    base, self.mode, mavlink2.MAV_STATE_ACTIVE))
            if now >= next_slow and self.streams:
                next_slow = now + 0.5
                self.send(self.enc.sys_status_encode(0, 0, 0, 0, 16400, 500, 90, 0, 0, 0, 0, 0, 0))
                self.send(self.enc.servo_output_raw_encode(0, 0, *([1500] * 8)))
            try:
                data, _ = self.sock.recvfrom(65535)
            except (socket.timeout, OSError):
                continue
            for m in self.parser.parse_buffer(data) or []:
                self.handle(m)

    def handle(self, m):
        kind = m.get_type()
        if kind == "HEARTBEAT" and m.type == mavlink2.MAV_TYPE_GCS:
            self.gcs_heartbeats += 1
        elif kind == "VISION_POSITION_ESTIMATE":
            self.vpe_t = time.time()                      # perfect EKF: echo the pose back
            self.send(self.enc.local_position_ned_encode(0, m.x, m.y, m.z, 0, 0, 0))
            self.send(self.enc.attitude_encode(0, m.roll, m.pitch, m.yaw, 0, 0, 0))
        elif kind == "SET_GPS_GLOBAL_ORIGIN":
            self.origin = (m.latitude, m.longitude, m.altitude)
        elif kind == "SET_POSITION_TARGET_LOCAL_NED":
            self.targets.append((m.x, m.y, m.z, m.yaw, m.type_mask, m.coordinate_frame))
        elif kind == "COMMAND_LONG":
            c = m.command
            if c == mavlink2.MAV_CMD_SET_MESSAGE_INTERVAL:
                self.streams.add(int(m.param1))
                self.ack(c)
            elif c == mavlink2.MAV_CMD_DO_SET_MODE:
                self.mode = int(m.param2)
                self.ack(c)
            elif c == mavlink2.MAV_CMD_COMPONENT_ARM_DISARM:
                if m.param1 == 1:
                    ok = self.mode == 4 and time.time() - self.vpe_t < 1.0
                    self.armed = self.armed or ok
                    self.ack(c, ok)
                elif int(m.param2) == gcs_core.FORCE_DISARM_MAGIC:
                    self.force_disarms += 1
                    self.armed = False
                    self.ack(c)
                else:
                    self.ack(c, False)                    # in flight: normal disarm refused
            elif c == mavlink2.MAV_CMD_NAV_TAKEOFF:
                ok = self.armed and self.mode == 4
                self.takeoff_alt = m.param7 if ok else None
                self.ack(c, ok)


def calibration_for_fake(path):
    """Room calibration that matches fake_motive.py exactly (Z-up, unicast)."""
    rb_rot = fm.rot_z(math.radians(70.0)) @ fm.rot_x(math.radians(4.0)) @ fm.rot_y(math.radians(-3.0))
    rm = fm.motive_frame("z")
    cal = {"rb_id": 1, "name": "QDrone2", "C": rm.T.tolist(), "p0": fm.P0_ROOM_IN_MOTIVE.tolist(),
           "q0": list(fm.R_to_quat(rm @ rb_rot)), "flu_from_mj": gcs_core.br.FLU_FROM_MJ.tolist()}
    Path(path).write_text(json.dumps(cal), encoding="utf-8")


def wait_until(predicate, timeout_s):
    end = time.time() + timeout_s
    while time.time() < end:
        if predicate():
            return True
        time.sleep(0.05)
    return False


def main():
    tmp = Path(tempfile.mkdtemp(prefix="gcs_test_"))
    cal = tmp / "cal.json"
    calibration_for_fake(cal)
    twin = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    twin.bind(("127.0.0.1", TWIN_PORT))
    twin.settimeout(0.05)
    twin_packets = []

    def twin_rx():
        while not stop_twin.is_set():
            try:
                twin_packets.append(gcs_core.TWIN_PACKET.unpack(twin.recvfrom(1024)[0]))
            except (socket.timeout, OSError):
                pass
    stop_twin = threading.Event()
    threading.Thread(target=twin_rx, daemon=True).start()

    cube = FakeCubeGuided()
    cube.start()
    fake = subprocess.Popen([sys.executable, "-I", str(HERE / "mocap" / "fake_motive.py"), "--natnet", "3.1",
                             "--up", "z", "--unicast", "--duration", "30"])
    t0 = time.time()
    limits = gcs_core.Limits(tether_radius_m=0.25, max_height_m=0.6)
    cfg = gcs_core.Config(server="127.0.0.1", unicast=True, rb_name="QDrone2", rb_id=1, cal=str(cal),
                          listen_port=GCS_PORT, pico_ip="127.0.0.1", pico_port=CUBE_PORT, log_dir=str(tmp),
                          twin_port=TWIN_PORT, limits=limits)
    gs = gcs_core.GroundStation(cfg).start()
    results = {}
    try:
        results["streams requested"] = wait_until(lambda: {30, 32, 1, 193, 36} <= cube.streams, 5)
        results["preflight all green except operator"] = wait_until(
            lambda: [label for ok, label, _ in gs.preflight() if not ok] == ["Operator: tether, area clear, kill ready"], 5)
        if not results["preflight all green except operator"]:
            print("   gates:", gs.preflight())
        results["arm refused before operator confirms"] = (not gs.arm()) and not cube.armed
        gs.operator_confirmed = True
        results["armed in GUIDED"] = gs.arm() and cube.armed and cube.mode == 4
        results["takeoff 0.2 m accepted"] = gs.takeoff(0.2) and abs((cube.takeoff_alt or 0) - 0.2) < 1e-6
        n_targets = len(cube.targets)
        results["nudge sends a position target"] = gs.nudge(dn=0.10) and wait_until(
            lambda: len(cube.targets) > n_targets and abs(cube.targets[-1][0] - (gs.home[0] + 0.10)) < 1e-3
            and cube.targets[-1][4] == gcs_core.POSITION_ONLY_MASK, 2)
        results["nudge clamped inside tether"] = gs.nudge(dn=5.0) and math.hypot(
            gs.target[0] - gs.home[0], gs.target[1] - gs.home[1]) <= limits.tether_radius_m - 0.15 + 1e-9
        results["origin sent"] = cube.origin == (0, 0, 0)
        # fake moves 0.40 m forward between 14 and 22 s: must trip the 0.25 m tether limit -> LAND
        results["auto LAND on tether breach"] = wait_until(lambda: cube.mode == 9, 25 - (time.time() - t0))
        results["auto action reason"] = gs.auto_action_done
        gs.kill("test")
        results["KILL force-disarms"] = wait_until(lambda: not cube.armed and cube.force_disarms >= 1, 2) and \
            wait_until(lambda: not gs.armed(), 2)
        elapsed = time.time() - t0
        results["GCS heartbeat >= 4 Hz"] = cube.gcs_heartbeats / elapsed >= 4.0
        loss = gs.status()["link_loss"]
        results["link loss measured ~10 %"] = 0.05 < loss < 0.15
        results["twin packets published"] = len(twin_packets) > 100
    finally:
        gs.close()
        cube.stop.set()
        stop_twin.set()
        fake.kill()
        fake.wait()
        twin.close()
    logs = {p.name: p.stat().st_size for p in tmp.glob("*.csv")}
    results["logs written"] = len(logs) == 2 and all(size > 1000 for size in logs.values())
    for event in gs.events:
        print(f"   [{event.level}] {event.text}")
    ok = all(v is True for k, v in results.items() if k != "auto action reason") and \
        "from the arming spot" in str(results["auto action reason"])
    for k, v in results.items():
        print(f"{k:42s} {v}")
    print("PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
