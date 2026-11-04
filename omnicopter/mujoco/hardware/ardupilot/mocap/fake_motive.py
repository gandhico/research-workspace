"""Fake Motive NatNet server for testing natnet.py / qd2_mocap_bridge.py without the lab (laptop, localhost).

    python fake_motive.py --natnet 4.1 --up y            # multicast 239.255.42.99:1511, command port 1510 on 127.0.0.1
    python fake_motive.py --natnet 3.1 --up z --unicast

Packets are built from the NatNet SDK layouts (see natnet.py). The fake drone's room frame is rotated 30 deg (azimuth) in
Motive's horizontal plane and its rigid body's own axes are rotated arbitrarily, so the bridge calibration must recover
everything from the motion. Motion (seconds after start): 0-6 still | 6-14 lift 0.30 m (peak at 10) | 14-22 forward 0.40 m
(peak at 18) | 22-26 still | 26+ circle r = 0.3 m at z = 0.5 m with yaw = 20 deg sin(0.5 t). truth(t) gives the room-frame
pose for tests.
"""
import argparse
import math
import socket
import struct
import time

import numpy as np

AZ = math.radians(30.0)                       # room x in Motive's horizontal plane
RB_ROT = None                                 # rigid body axes w.r.t. the drone body (set in main)
P0_ROOM_IN_MOTIVE = np.array([0.7, -0.4, 0.0])


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def R_to_quat(R):
    """-> (qx, qy, qz, qw)."""
    w = math.sqrt(max(0.0, 1 + R[0, 0] + R[1, 1] + R[2, 2])) / 2
    x = math.copysign(math.sqrt(max(0.0, 1 + R[0, 0] - R[1, 1] - R[2, 2])) / 2, R[2, 1] - R[1, 2])
    y = math.copysign(math.sqrt(max(0.0, 1 - R[0, 0] + R[1, 1] - R[2, 2])) / 2, R[0, 2] - R[2, 0])
    z = math.copysign(math.sqrt(max(0.0, 1 - R[0, 0] - R[1, 1] + R[2, 2])) / 2, R[1, 0] - R[0, 1])
    return x, y, z, w


def bump(t, t0, t1):
    if t <= t0 or t >= t1:
        return 0.0
    return 0.5 * (1 - math.cos(2 * math.pi * (t - t0) / (t1 - t0)))


def truth(t):
    """room-frame (x, y, z) and yaw (rad) of the fake drone at time t (s since start)."""
    x = 0.40 * bump(t, 14.0, 22.0)
    z = 0.30 * bump(t, 6.0, 14.0)
    y, yaw = 0.0, 0.0
    if t >= 26.0:
        s = t - 26.0
        r = 0.3 * min(1.0, s / 3.0)
        x, y, z = r * math.sin(0.6 * s), r * (1 - math.cos(0.6 * s)), 0.5 * min(1.0, s / 3.0)
        yaw = math.radians(20.0) * math.sin(0.5 * s)
    return np.array([x, y, z]), yaw


def motive_frame(up):
    """Rotation room -> Motive world. Motive is right-handed; Y-up: (X, Y, Z) with Y up; Z-up: Z up."""
    R_room_to_zup = rot_z(AZ)                 # azimuth of room x in a z-up version of Motive's frame
    if up == "z":
        return R_room_to_zup
    # z-up world (x', y', z') -> Motive Y-up (X, Y, Z): X = x', Y = z', Z = -y'
    M = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], dtype=float)
    return M @ R_room_to_zup


def build_frame(fr, t, pos, quat, ver, valid=True):
    sized = tuple(ver) >= (4, 1)
    S = lambda n: struct.pack("<i", n) if sized else b""
    markers = [pos + np.array([0.05 * i, 0.02 * i, 0.01 * (i % 2)]) for i in range(5)]
    sec = b""
    for name in ("QDrone2", "all"):
        sec += name.encode() + b"\0" + struct.pack("<i", len(markers)) + b"".join(struct.pack("<3f", *m) for m in markers)
    b = struct.pack("<i", fr) + struct.pack("<i", 2) + S(len(sec)) + sec
    b += struct.pack("<i", 0) + S(0)                                     # legacy other markers
    rb = struct.pack("<i7f", 1, *pos, *quat) + struct.pack("<f", 0.0004) + struct.pack("<h", 1 if valid else 0)
    b += struct.pack("<i", 1) + S(len(rb)) + rb
    for _ in range(4):                                                   # skeletons, labeled markers, force plates, devices
        b += struct.pack("<i", 0) + S(0)
    b += struct.pack("<IIdQQQhi", 0, 0, t, 0, 0, 0, 0, 0)
    return struct.pack("<HH", 7, len(b)) + b


def server_info(ver, multicast, group):
    p = b"Motive (fake)".ljust(256, b"\0") + bytes([3, 1, 0, 0]) + bytes([ver[0], ver[1], 0, 0])
    p += struct.pack("<QHB", 10_000_000, 1511, 1 if multicast else 0) + socket.inet_aton(group)
    return struct.pack("<HH", 1, len(p)) + p


def modeldef(ver):
    sized = tuple(ver) >= (4, 1)
    ms = b"QDrone2\0" + struct.pack("<i", 5) + b"".join(b"Marker%d\0" % i for i in range(5))
    rb = b"QDrone2\0" + struct.pack("<ii3f", 1, -1, 0, 0, 0) + struct.pack("<i", 5)
    rb += b"".join(struct.pack("<3f", 0.05 * i, 0.02 * i, 0.0) for i in range(5)) + struct.pack("<5i", *range(5))
    if ver[0] >= 4:
        rb += b"".join(b"Marker%d\0" % i for i in range(5))
    body = struct.pack("<i", 2)
    for typ, d in ((0, ms), (1, rb)):
        body += struct.pack("<i", typ) + (struct.pack("<i", len(d)) if sized else b"") + d
    return struct.pack("<HH", 5, len(body)) + body


def main():
    global RB_ROT
    ap = argparse.ArgumentParser()
    ap.add_argument("--natnet", default="4.1")
    ap.add_argument("--up", choices=("y", "z"), default="y")
    ap.add_argument("--unicast", action="store_true")
    ap.add_argument("--rate", type=float, default=120.0)
    ap.add_argument("--group", default="239.255.42.99")
    ap.add_argument("--duration", type=float, default=120.0)
    ap.add_argument("--iface", default="127.0.0.1", help="interface for multicast (Windows: the LAN IP, not loopback)")
    ap.add_argument("--lose", default=None, help="t0,t1: rigid body not tracked in this window (s)")
    a = ap.parse_args()
    ver = tuple(int(v) for v in a.natnet.split("."))
    RB_ROT = rot_z(math.radians(70.0)) @ rot_x(math.radians(4.0)) @ rot_y(math.radians(-3.0))
    Rm = motive_frame(a.up)
    lose = tuple(float(v) for v in a.lose.split(",")) if a.lose else None
    cmd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    cmd.bind(("127.0.0.1", 1510))
    cmd.setblocking(False)
    data = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(a.iface))
    data.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
    clients = set()
    t0 = time.monotonic()
    fr, next_t = 0, t0
    print("fake Motive: NatNet %s, up %s, %s, %.0f Hz" % (a.natnet, a.up, "unicast" if a.unicast else "multicast", a.rate),
          flush=True)
    while time.monotonic() - t0 < a.duration:
        try:
            while True:
                msg, src = cmd.recvfrom(4096)
                mid = struct.unpack_from("<H", msg)[0]
                if mid == 0:
                    clients.add(src)
                    cmd.sendto(server_info(ver, not a.unicast, a.group), src)
                elif mid == 4:
                    cmd.sendto(modeldef(ver), src)
        except (BlockingIOError, ConnectionResetError, OSError):
            pass
        now = time.monotonic()
        if now >= next_t:
            next_t += 1.0 / a.rate
            t = now - t0
            p_room, yaw = truth(t)
            pos = P0_ROOM_IN_MOTIVE + Rm @ p_room
            A = Rm @ rot_z(yaw) @ RB_ROT                     # rigid body -> Motive
            valid = not (lose and lose[0] <= t < lose[1])
            pk = build_frame(fr, t, pos, R_to_quat(A), ver, valid)
            fr += 1
            if a.unicast:
                for c in list(clients):
                    cmd.sendto(pk, c)
            else:
                data.sendto(pk, (a.group, 1511))
        time.sleep(0.0005)


if __name__ == "__main__":
    main()
