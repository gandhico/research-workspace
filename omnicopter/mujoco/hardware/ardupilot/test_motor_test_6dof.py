"""Safety test of motor_test_6dof.py against a fake Cube (no hardware, ~20 s).

    python test_motor_test_6dof.py

1. 6DoF frame (FRAME_CLASS 16, 3DMASK 255): every DO_MOTOR_TEST must be PWM type with values in
   {1500-delta, 1500+delta, 1500}; skipped motors get no pulse; stop (1500) and disarm are sent.
2. Normal octa (FRAME_CLASS 3): the tool must refuse and send NO motor command at all
   (1500 us on a normal DShot output is ~50 % thrust).
"""
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

from pymavlink.dialects.v20 import ardupilotmega as mavlink2

HERE = Path(__file__).resolve().parent
TOOL_PORT, CUBE_PORT = 14560, 14670


class FakeCube(threading.Thread):
    def __init__(self, params):
        super().__init__(daemon=True)
        self.params = params
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", CUBE_PORT))
        self.sock.settimeout(0.05)
        self.enc = mavlink2.MAVLink(None, srcSystem=1, srcComponent=1)
        self.parser = mavlink2.MAVLink(None)
        self.motor_tests, self.disarms = [], 0
        self.stop = threading.Event()

    def send(self, msg):
        self.sock.sendto(msg.pack(self.enc), ("127.0.0.1", TOOL_PORT))

    def run(self):
        next_hb = 0.0
        while not self.stop.is_set():
            if time.time() >= next_hb:
                next_hb = time.time() + 0.5
                self.send(self.enc.heartbeat_encode(mavlink2.MAV_TYPE_OCTOROTOR,
                                                    mavlink2.MAV_AUTOPILOT_ARDUPILOTMEGA, 0, 0, 3))
            try:
                data, _ = self.sock.recvfrom(65535)
            except (socket.timeout, OSError):
                continue
            for m in self.parser.parse_buffer(data) or []:
                kind = m.get_type()
                if kind == "PARAM_REQUEST_READ":
                    name = m.param_id.rstrip("\x00")
                    if name in self.params:
                        self.send(self.enc.param_value_encode(name.encode(), self.params[name], 9, 1000, 0))
                elif kind == "COMMAND_LONG" and m.command == 209:
                    self.motor_tests.append((int(m.param1), int(m.param2), round(m.param3), m.param4))
                    self.send(self.enc.command_ack_encode(209, mavlink2.MAV_RESULT_ACCEPTED))
                elif kind == "COMMAND_LONG" and m.command == mavlink2.MAV_CMD_COMPONENT_ARM_DISARM:
                    self.disarms += int(m.param1 == 0)


def run(params, answers):
    cube = FakeCube(params)
    cube.start()
    try:
        proc = subprocess.run([sys.executable, str(HERE / "motor_test_6dof.py"), "--motors", "1,2,3",
                               "--seconds", "0.3", "--delta", "40", "--pico-ip", "127.0.0.1",
                               "--port", str(TOOL_PORT), "--pico-port", str(CUBE_PORT)],
                              input=answers, text=True, capture_output=True, timeout=60, cwd=str(HERE))
        time.sleep(0.3)
        return proc, cube.motor_tests, cube.disarms
    finally:
        cube.stop.set()
        cube.join(1.0)
        cube.sock.close()


def main():
    before = set((HERE / "audits").glob("motor_test_*.csv"))
    try:
        cases()
    finally:
        for path in set((HERE / "audits").glob("motor_test_*.csv")) - before:
            path.unlink()                                    # results of the fake run are not data


def cases():
    ok = True
    # Case 1: 6DoF frame. Motor1 run, Motor2 skipped, Motor3 run.
    proc, tests, disarms = run({"FRAME_CLASS": 16, "SERVO_BLH_3DMASK": 255}, "YES\nr\n4\ny\ns\nr\n7\ny\n")
    pulses = [t for t in tests if t[3] > 0.2]
    stops = [t for t in tests if t[3] <= 0.2]
    case1 = (all(t[1] == 1 for t in tests)                                   # PWM type only
             and [(t[0], t[2]) for t in pulses] == [(1, 1540), (1, 1460), (3, 1540), (3, 1460)]
             and sorted(t[0] for t in stops) == list(range(1, 9)) and all(t[2] == 1500 for t in stops)
             and disarms >= 1)
    print("case 1 (6DoF): motor commands", tests, "disarms", disarms, "->", "PASS" if case1 else "FAIL")
    if not case1:
        print(proc.stdout[-1500:], proc.stderr[-1500:])
    ok &= case1
    # Case 2: normal octa. Must refuse and send nothing.
    proc, tests, disarms = run({"FRAME_CLASS": 3, "SERVO_BLH_3DMASK": 0}, "YES\n")
    case2 = tests == [] and "Refusing" in (proc.stdout + proc.stderr)
    print("case 2 (octa): motor commands", tests, "->", "PASS" if case2 else "FAIL")
    if not case2:
        print(proc.stdout[-1500:], proc.stderr[-1500:])
    ok &= case2
    print("PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
