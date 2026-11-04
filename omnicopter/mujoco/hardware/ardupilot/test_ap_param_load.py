"""Test ap_param_load.py against a fake Cube holding the real 2026-11-04 parameters (~30 s).

    python test_ap_param_load.py

Pass 1 writes stage 1 (VISO_* missing until VISO_TYPE=1 + reboot), the fake reboots and creates
VISO_*, pass 2 writes them, pass 3 finds everything set, and stage 2 without the ESC
confirmation writes nothing.
"""
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

from pymavlink.dialects.v20 import ardupilotmega as mavlink2

HERE = Path(__file__).resolve().parent
TOOL_PORT, CUBE_PORT = 14562, 14672
REAL = HERE / "audits" / "audit_20261104_140935" / "cube_params.param"


class FakeCube(threading.Thread):
    def __init__(self, params):
        super().__init__(daemon=True)
        self.params = params
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", CUBE_PORT))
        self.sock.settimeout(0.05)
        self.enc = mavlink2.MAVLink(None, srcSystem=1, srcComponent=1)
        self.parser = mavlink2.MAVLink(None)
        self.reboots, self.sets = 0, []
        self.stop = threading.Event()

    def send(self, msg):
        self.sock.sendto(msg.pack(self.enc), ("127.0.0.1", TOOL_PORT))

    def value(self, name):
        self.send(self.enc.param_value_encode(name.encode(), self.params[name], 9, len(self.params), 0))

    def run(self):
        next_hb = 0.0
        while not self.stop.is_set():
            if time.time() >= next_hb:
                next_hb = time.time() + 0.5
                self.send(self.enc.heartbeat_encode(14, 3, 0, 0, 3))
            try:
                data, _ = self.sock.recvfrom(65535)
            except (socket.timeout, OSError):
                continue
            for m in self.parser.parse_buffer(data) or []:
                kind = m.get_type()
                if kind == "PARAM_REQUEST_READ" and m.param_id in self.params:
                    self.value(m.param_id)
                elif kind == "PARAM_SET" and m.param_id in self.params:
                    self.params[m.param_id] = m.param_value
                    self.sets.append(m.param_id)
                    self.value(m.param_id)
                elif kind == "COMMAND_LONG" and m.command == mavlink2.MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN:
                    self.reboots += 1
                    if self.params.get("VISO_TYPE") == 1:              # VISO_* exist after reboot
                        self.params.setdefault("VISO_POS_M_NSE", 0.2)
                        self.params.setdefault("VISO_YAW_M_NSE", 0.2)
                    self.send(self.enc.command_ack_encode(m.command, mavlink2.MAV_RESULT_ACCEPTED))


def run(params, param_file, answers):
    cube = FakeCube(params)
    cube.start()
    try:
        proc = subprocess.run([sys.executable, str(HERE / "ap_param_load.py"), str(param_file),
                               "--port", str(TOOL_PORT), "--pico-ip", "127.0.0.1", "--pico-port", str(CUBE_PORT)],
                              input=answers, text=True, capture_output=True, timeout=120, cwd=str(HERE))
        time.sleep(0.2)
        return proc.stdout + proc.stderr, cube
    finally:
        cube.stop.set()
        cube.join(1.0)
        cube.sock.close()


def main():
    params = {l.split(",")[0]: float(l.split(",")[1]) for l in REAL.read_text().splitlines() if "," in l}
    stage1 = HERE / "config" / "stage1_optitrack_ekf.param"
    stage2 = HERE / "config" / "stage2_6dof_frame.param"
    results = []

    out, cube = run(params, stage1, "WRITE\ny\n")
    # 14 lines: AHRS_EKF_TYPE 3 and EK3_ENABLE 1 are already set on this Cube; VISO_* do not exist yet.
    ok = ("All 10 written and read back" in out and cube.reboots == 1 and len(cube.sets) == 10
          and "VISO_POS_M_NSE" in out and "not on the Cube yet" in out
          and params["VISO_TYPE"] == 1 and params["EK3_SRC1_POSXY"] == 6 and params["COMPASS_USE"] == 0)
    results.append(("pass 1: 10 written, VISO_* missing, reboot", ok, out))

    out, cube = run(params, stage1, "WRITE\ny\n")
    ok = ("All 2 written and read back" in out and abs(params["VISO_POS_M_NSE"] - 0.1) < 1e-6
          and "not on the Cube yet" not in out)
    results.append(("pass 2: VISO_* written", ok, out))

    out, cube = run(params, stage1, "")
    ok = "Everything in this file is already set" in out and cube.sets == []
    results.append(("pass 3: nothing left to write", ok, out))

    out, cube = run(params, stage2, "no\n")
    ok = "cancelled; nothing was written" in out and cube.sets == [] and params["FRAME_CLASS"] == 3
    results.append(("stage 2 without ESC confirmation: nothing written", ok, out))

    for name, ok, out in results:
        print(f"{name:55s} {'PASS' if ok else 'FAIL'}")
        if not ok:
            print(out[-1500:])
    passed = all(ok for _, ok, _ in results)
    print("PASS" if passed else "FAIL")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
