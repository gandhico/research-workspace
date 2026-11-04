"""Loopback test: fake Motive -> omni_mocap_bridge.py -> fake Pico/Cube, with a fake Mission Planner.

    python test_omni_bridge.py          # ~2 x 55 s; writes test_omni_bridge_result.json

Checks per configuration (NatNet 3.1 / Z-up / unicast and NatNet 4.1 / Y-up / multicast):
  calibration rotation vs the fake's true room frame; NED position and yaw (sign!) vs truth from the
  bridge log (Motive frame numbers give the fake's exact time); twin quaternion = XML hover attitude
  when the fake is still; VISION_POSITION_ESTIMATE content equals the logged sent rows; nothing sent
  while untracked and reset_counter increments after the gap; relay Pico -> MP and MP -> Pico;
  SET_GPS_GLOBAL_ORIGIN delivered.
"""
import csv
import json
import math
import os
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
import fake_motive as fm  # noqa: E402
import omni_mocap_bridge as br  # noqa: E402

BRIDGE_PORT, PICO_PORT, MP_PORT = 14650, 14660, 14651
HOVER_Q = np.array([math.sqrt(0.5), 0.0, math.sqrt(0.5), 0.0])


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 9))
        return s.getsockname()[0]
    finally:
        s.close()


class FakePico(threading.Thread):
    """Cube behind the Pico: heartbeats to the bridge, records what it receives, echoes a perfect EKF."""

    def __init__(self):
        super().__init__(daemon=True)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", PICO_PORT))
        self.sock.settimeout(0.05)
        self.enc = mavlink2.MAVLink(None, srcSystem=1, srcComponent=1)
        self.parser = mavlink2.MAVLink(None)
        self.vpe, self.origin, self.param_requests = [], [], 0
        self.stop = threading.Event()

    def send(self, msg):
        self.sock.sendto(msg.pack(self.enc), ("127.0.0.1", BRIDGE_PORT))

    def run(self):
        next_hb = 0.0
        while not self.stop.is_set():
            t = time.perf_counter()
            if t >= next_hb:
                next_hb = t + 0.5
                self.send(self.enc.heartbeat_encode(mavlink2.MAV_TYPE_OCTOROTOR, mavlink2.MAV_AUTOPILOT_ARDUPILOTMEGA,
                                                    0, 0, mavlink2.MAV_STATE_STANDBY))
            try:
                data, _ = self.sock.recvfrom(65535)
            except (socket.timeout, OSError):
                continue
            for m in self.parser.parse_buffer(data) or []:
                kind = m.get_type()
                if kind == "VISION_POSITION_ESTIMATE":
                    self.vpe.append((time.perf_counter(), m.usec, m.x, m.y, m.z, m.roll, m.pitch, m.yaw, m.reset_counter))
                    self.send(self.enc.local_position_ned_encode(0, m.x, m.y, m.z, 0, 0, 0))
                    self.send(self.enc.attitude_encode(0, m.roll, m.pitch, m.yaw, 0, 0, 0))
                elif kind == "SET_GPS_GLOBAL_ORIGIN":
                    self.origin.append((m.latitude, m.longitude, m.altitude))
                elif kind == "PARAM_REQUEST_LIST":
                    self.param_requests += 1


class FakeMissionPlanner(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", MP_PORT))
        self.sock.settimeout(0.05)
        self.parser = mavlink2.MAVLink(None)
        self.enc = mavlink2.MAVLink(None, srcSystem=255, srcComponent=190)
        self.heartbeats, self.requested = 0, False
        self.stop = threading.Event()

    def run(self):
        while not self.stop.is_set():
            try:
                data, addr = self.sock.recvfrom(65535)
            except (socket.timeout, OSError):
                continue
            for m in self.parser.parse_buffer(data) or []:
                if m.get_type() == "HEARTBEAT":
                    self.heartbeats += 1
                    if not self.requested:
                        self.sock.sendto(self.enc.param_request_list_encode(1, 1).pack(self.enc), addr)
                        self.requested = True


def run_config(natnet_ver, up, unicast):
    print(f"\n=== NatNet {natnet_ver}, up {up}, {'unicast' if unicast else 'multicast'}", flush=True)
    lan = lan_ip()
    fake = subprocess.Popen([sys.executable, "-I", str(HERE / "fake_motive.py"), "--natnet", natnet_ver, "--up", up,
                             "--duration", "56", "--lose", "40,41", "--iface", lan] + (["--unicast"] if unicast else []))
    t_start = time.perf_counter()
    # Name first, id as fallback: on one PC the multicast fake's command-port replies (names) do not return.
    common = (["--server", "127.0.0.1", "--rb-name", "QDrone2", "--id", "1"]
              + (["--unicast"] if unicast else ["--local-ip", lan]))
    tmp = Path(tempfile.mkdtemp(prefix="omni_bridge_test_"))
    cal = tmp / "calib.json"
    res = {}
    pico, mp = FakePico(), FakeMissionPlanner()
    try:
        time.sleep(0.6)
        assert br.main(common + ["--list", "--seconds", "0.4"]) == 0, "list failed"
        assert br.main(common + ["--calibrate", "--auto", "--cal", str(cal)]) == 0, "calibration failed"
        c = json.loads(cal.read_text())
        C = np.array(c["C"])
        res["calibration rotation error deg"] = round(math.degrees(br.rotation_angle(C @ fm.motive_frame(up))), 3)
        res["motive_up"] = c["motive_up"]
        pico.start()
        mp.start()
        bridge = subprocess.Popen([sys.executable, "-I", str(HERE / "omni_mocap_bridge.py")] + common
                                  + ["--stream", "--cal", str(cal), "--rate", "30", "--listen-port", str(BRIDGE_PORT),
                                     "--pico-port", str(PICO_PORT), "--gcs-port", str(MP_PORT),
                                     "--origin", "1.5,-2.25,100", "--log-dir", str(tmp)],
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        while time.perf_counter() - t_start < 54.0:
            time.sleep(0.2)
        bridge.terminate()
        out, _ = bridge.communicate(timeout=10)
        status = [line.strip() for line in out.splitlines() if "mocap" in line and "Hz in" in line]
        res["status lines (last 4)"] = status[-4:] if status else [out[-300:]]
        res["status during gap"] = [s for s in status if "NOT TRACKED" in s][:2]
        rows = list(csv.DictReader(next(tmp.glob("mocap_*.csv")).open()))
        frame = np.array([int(r["frame"]) for r in rows])
        tf = frame / 120.0                                     # fake runs on a fixed 120 Hz schedule
        acc = np.array([r["accepted"] == "1" for r in rows])
        ned = np.array([[float(r["n_m"]), float(r["e_m"]), float(r["d_m"])] for r in rows])
        yaw = np.array([float(r["yaw_rad"]) for r in rows])
        roll_pitch = np.array([[float(r["roll_rad"]), float(r["pitch_rad"])] for r in rows])
        qt = np.array([[float(r[k]) for k in ("q_w", "q_x", "q_y", "q_z")] for r in rows])
        circ = acc & (tf > 29.5) & (tf < 39.5)
        truth = np.array([fm.truth(t)[0] for t in tf[circ]])
        truth_yaw = np.array([fm.truth(t)[1] for t in tf[circ]])
        ned_truth = truth * np.array([1.0, -1.0, -1.0])
        res["NED pos err max cm"] = round(100 * float(np.abs(ned[circ] - ned_truth).max()), 3)
        res["NED yaw err max deg (yaw_NED = -yaw_room)"] = round(math.degrees(float(np.abs(
            np.angle(np.exp(1j * (yaw[circ] + truth_yaw)))).max())), 3)
        res["roll/pitch max deg"] = round(math.degrees(float(np.abs(roll_pitch[circ]).max())), 3)
        still = acc & (tf > 22.5) & (tf < 25.5)
        dq = np.minimum(np.linalg.norm(qt[still] - HOVER_Q, axis=1), np.linalg.norm(qt[still] + HOVER_Q, axis=1))
        res["twin quaternion vs XML hover (still) max"] = round(float(dq.max()), 5) if still.any() else None
        valid = np.array([r["valid"] == "1" for r in rows])
        sent = np.array([r["sent"] == "1" for r in rows])
        res["untracked frames (fake gap 40-41 s)"] = int((~valid).sum())
        res["sent while untracked"] = int((sent & ~valid).sum())
        sent_rows = [r for r in rows if r["sent"] == "1"]
        vpe = pico.vpe
        n = min(len(sent_rows), len(vpe))
        k0 = len(sent_rows) - n                                # the first sends may precede the fake Pico
        mismatch = max(abs(float(sent_rows[k0 + i][key]) - vpe[i][j]) for i in range(n)
                       for key, j in (("n_m", 2), ("e_m", 3), ("d_m", 4), ("yaw_rad", 7)))
        res["VPE received"] = len(vpe)
        res["VPE vs log max abs diff"] = round(float(mismatch), 6)
        span = vpe[-1][0] - vpe[0][0] if len(vpe) > 1 else 1
        res["VPE rate Hz"] = round(len(vpe) / span, 1)
        resets = [v[8] for v in vpe]
        res["reset_counter before/after gap"] = [resets[0], resets[-1]]
        res["relay Pico->MP heartbeats"] = mp.heartbeats
        res["relay MP->Pico PARAM_REQUEST_LIST"] = pico.param_requests
        res["origin received"] = pico.origin[:1]
        print(json.dumps(res, indent=1), flush=True)
        return res
    finally:
        for helper in (pico, mp):
            helper.stop.set()
            if helper.is_alive():
                helper.join(1.0)
            helper.sock.close()
        fake.kill()
        fake.wait()


def passed(r):
    return (r["calibration rotation error deg"] < 0.5 and r["NED pos err max cm"] < 1.0
            and r["NED yaw err max deg (yaw_NED = -yaw_room)"] < 0.5 and r["roll/pitch max deg"] < 0.5
            and r["twin quaternion vs XML hover (still) max"] is not None
            and r["twin quaternion vs XML hover (still) max"] < 1e-3
            and r["untracked frames (fake gap 40-41 s)"] > 60 and r["sent while untracked"] == 0
            and r["VPE vs log max abs diff"] < 1e-4 and 28.5 <= r["VPE rate Hz"] <= 30.5
            and r["reset_counter before/after gap"] == [0, 1]
            and r["relay Pico->MP heartbeats"] > 10 and r["relay MP->Pico PARAM_REQUEST_LIST"] >= 1
            and r["origin received"] == [(15000000, -22500000, 100000)])


if __name__ == "__main__":
    results = {"3.1 Z-up unicast": run_config("3.1", "z", True),
               "4.1 Y-up multicast": run_config("4.1", "y", False)}
    ok = all(passed(r) for r in results.values())
    results["PASS"] = ok
    (HERE / "test_omni_bridge_result.json").write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8")
    print("\nPASS" if ok else "\nFAIL")
    sys.exit(0 if ok else 1)
