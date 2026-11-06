"""Live MuJoCo view of the real Omnidrone: the canonical twin model posed by OptiTrack (sent by omni_gcs.py).

    python twin_view.py              # started by the "Twin view" button; listens on UDP 127.0.0.1:14600

The twin is drawn at the measured pose only (kinematics, no physics step), so you can see the real attitude
in the same frames as the simulation: BOTTOM face down at the hover attitude, rotor sites with their +Z axes.
The window title shows the motor outputs (us; 1500 = stopped).
"""
from __future__ import annotations

import argparse
from pathlib import Path
import socket
import struct
import time

import mujoco
import mujoco.viewer

ROOT = Path(__file__).resolve().parents[1]          # omnicopter
XML = ROOT / "twin" / "omnidrone.xml"
TWIN_PACKET = struct.Struct("<4sd3d4d8H")            # same layout as gcs_core.TWIN_PACKET
TWIN_MAGIC = b"OMNT"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--port", type=int, default=14600)
    p.add_argument("--pivot-height", type=float, default=0.204,
                   help="height of the rigid-body pivot (cube centre) above the floor when resting [m]")
    p.add_argument("--duration", type=float, default=None, help=argparse.SUPPRESS)       # smoke tests
    a = p.parse_args()
    model = mujoco.MjModel.from_xml_path(str(XML))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", a.port))
    sock.setblocking(False)
    received, latest, start = 0, None, time.time()
    with mujoco.viewer.launch_passive(model, data) as viewer:
        with viewer.lock():
            viewer.opt.frame = mujoco.mjtFrame.mjFRAME_SITE
            viewer.cam.lookat[:] = [0, 0, a.pivot_height]
            viewer.cam.distance, viewer.cam.azimuth, viewer.cam.elevation = 1.6, 135, -20
        while viewer.is_running() and (a.duration is None or time.time() - start < a.duration):
            while True:
                try:
                    packet = sock.recv(1024)
                except (BlockingIOError, OSError):
                    break
                if len(packet) == TWIN_PACKET.size and packet[:4] == TWIN_MAGIC:
                    latest = TWIN_PACKET.unpack(packet)
                    received += 1
            if latest is not None:
                _, _, x, y, z, qw, qx, qy, qz, *servo = latest
                with viewer.lock():
                    data.qpos[:3] = [x, y, z + a.pivot_height]
                    data.qpos[3:7] = [qw, qx, qy, qz]
                    data.qvel[:] = 0
                    mujoco.mj_forward(model, data)
            viewer.sync()
            time.sleep(1 / 60)
    sock.close()
    print(f"twin view closed ({received} poses received)")


if __name__ == "__main__":
    main()
