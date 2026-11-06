"""Minimal OptiTrack NatNet client in pure Python (no SDK, no VRPN), for Motive 2.x / 3.x. Laptop side.

Reads rigid-body poses from Motive's NatNet stream (UDP; multicast 239.255.42.99:1511 by default, or unicast), the same data
Quanser's MissionServer gets through VRPN. Only what the QDrone needs is decoded: server info, frame number and rigid bodies
(id, position, quaternion, mean marker error, tracking-valid flag), plus rigid-body names from the model description.

Protocol (NatNet SDK 3.x / 4.x, all little-endian): every packet = uint16 message id + uint16 payload size + payload.
  0 NAT_CONNECT -> 1 NAT_SERVERINFO (app name[256], app version[4], NatNet version[4], clock Hz u64, data port u16,
  multicast u8, multicast address[4]);  4 NAT_REQUEST_MODELDEF -> 5 NAT_MODELDEF;  7 NAT_FRAMEOFDATA;  10 NAT_KEEPALIVE.
  Frame: frame number i32 | marker sets (count i32 [+ size i32 from 4.1]; name, n markers, xyz floats) | legacy other
  markers (count [+ size], xyz) | rigid bodies (count [+ size]; id i32, x y z f32, qx qy qz qw f32, [2.x: markers],
  mean error f32, params i16 with bit 0 = tracking valid) | ... (skeletons, labeled markers, ...: not needed).
The stream version is detected from the packets themselves (the 3.x and 4.1 layouts differ by the size fields), so a wrong
or missing server info does not break parsing.  2026-10-28, written for qdrone-67211; check against the real Motive with
qd2_mocap_bridge.py --list (it prints what it decoded and can dump raw packets with --dump).
"""
import select
import socket
import struct
import threading
import time

NAT_CONNECT, NAT_SERVERINFO, NAT_REQUEST_MODELDEF, NAT_MODELDEF, NAT_FRAMEOFDATA, NAT_KEEPALIVE = 0, 1, 4, 5, 7, 10
MULTICAST, DATA_PORT, CMD_PORT = "239.255.42.99", 1511, 1510
CANDIDATE_VERSIONS = ((4, 1), (3, 1), (2, 10))           # frame layouts tried when the version is unknown


class RigidBody:
    __slots__ = ("id", "pos", "quat", "err", "valid", "frame", "t_rx")

    def __init__(self, rid, pos, quat, err, valid, frame, t_rx):
        self.id, self.pos, self.quat, self.err, self.valid, self.frame, self.t_rx = rid, pos, quat, err, valid, frame, t_rx

    def __repr__(self):
        return "RigidBody(id=%d, pos=(%.4f, %.4f, %.4f), quat=(%.3f, %.3f, %.3f, %.3f), valid=%s, err=%.2f mm)" % (
            self.id, self.pos[0], self.pos[1], self.pos[2], *self.quat, self.valid, 1e3 * self.err)


def packet(msg_id, payload=b""):
    return struct.pack("<HH", msg_id, len(payload)) + payload


def _cstr(b, o):
    e = b.index(b"\0", o)
    return b[o:e].decode("utf-8", "replace"), e + 1


def parse_server_info(p):
    info = {"app": p[:256].split(b"\0")[0].decode("utf-8", "replace"), "app_version": tuple(p[256:260]),
            "natnet": tuple(p[260:264])}
    if len(p) >= 279:
        info["clock_hz"] = struct.unpack_from("<Q", p, 264)[0]
        info["data_port"] = struct.unpack_from("<H", p, 272)[0]
        info["multicast"] = bool(p[274])
        info["multicast_addr"] = socket.inet_ntoa(p[275:279])
    return info


def parse_frame(p, ver):
    """-> (frame number, [(id, (x, y, z), (qx, qy, qz, qw), mean error m, valid)]). Raises on a malformed payload."""
    major, minor = ver[0], ver[1]
    sized = (major, minor) >= (4, 1)
    o = 0
    frame, nsets = struct.unpack_from("<ii", p, o)
    o += 8 + (4 if sized else 0)
    if not 0 <= nsets < 1000:
        raise ValueError("marker-set count %d" % nsets)
    for _ in range(nsets):
        name, o = _cstr(p, o)
        if not name or not all(31 < ord(c) < 127 for c in name):
            raise ValueError("marker-set name %r" % name[:20])
        nm = struct.unpack_from("<i", p, o)[0]
        if not 0 <= nm < 100000:
            raise ValueError("marker count %d" % nm)
        o += 4 + 12 * nm
    nother = struct.unpack_from("<i", p, o)[0]
    if not 0 <= nother < 100000:
        raise ValueError("other-marker count %d" % nother)
    o += 4 + (4 if sized else 0) + 12 * nother
    nrb = struct.unpack_from("<i", p, o)[0]
    if not 0 <= nrb < 1000:
        raise ValueError("rigid-body count %d" % nrb)
    o += 4 + (4 if sized else 0)
    out = []
    for _ in range(nrb):
        rid, x, y, z, qx, qy, qz, qw = struct.unpack_from("<i7f", p, o)
        o += 32
        if 0 < major < 3:                                  # NatNet 2.x: marker data inside each rigid body
            nm = struct.unpack_from("<i", p, o)[0]
            o += 4 + 12 * nm + (8 * nm if major >= 2 else 0)
        err, valid = 0.0, True
        if major >= 2 or major == 0:
            err = struct.unpack_from("<f", p, o)[0]
            o += 4
        if (major, minor) >= (2, 6) or major == 0:
            valid = bool(struct.unpack_from("<h", p, o)[0] & 1)
            o += 2
        out.append((rid, (x, y, z), (qx, qy, qz, qw), err, valid))
    if o > len(p):
        raise ValueError("frame shorter than its rigid bodies")
    return frame, out


def plausible(bodies):
    """Rejects a frame decoded with the wrong layout (2026-10-28: a 3.1 frame read as 4.1 gave id 1045220557 with a
    unit-norm quaternion by chance, so ids and names are checked too)."""
    if len({b[0] for b in bodies}) != len(bodies):
        return False
    for rid, pos, q, err, valid in bodies:
        if not 0 <= rid < 65536:
            return False
        n = sum(c * c for c in q) ** 0.5
        if not (abs(n - 1.0) < 0.05 or (not valid and n < 1e-6)):
            return False
        if any(abs(c) > 100.0 for c in pos) or not 0.0 <= err < 1.0:
            return False
    return True


def parse_modeldef(p, ver):
    """Best effort: {rigid body id: name}. Stops quietly at anything it cannot skip."""
    major, minor = ver[0], ver[1]
    sized = (major, minor) >= (4, 1)
    names, o = {}, 0
    n = struct.unpack_from("<i", p, o)[0]
    o += 4
    for _ in range(n):
        typ = struct.unpack_from("<i", p, o)[0]
        o += 4
        size, start = None, o
        if sized:
            size = struct.unpack_from("<i", p, o)[0]
            o += 4
            start = o
        if typ == 0:                                       # marker set
            _, o = _cstr(p, o)
            nm = struct.unpack_from("<i", p, o)[0]
            o += 4
            for _ in range(nm):
                _, o = _cstr(p, o)
        elif typ == 1:                                     # rigid body
            name = ""
            if major >= 2 or major == 0:
                name, o = _cstr(p, o)
            rid = struct.unpack_from("<i", p, o)[0]
            names[rid] = name
            o += 8 + 12
            if major >= 3 or major == 0:
                nm = struct.unpack_from("<i", p, o)[0]
                o += 4 + 16 * nm
                if major >= 4 or major == 0:
                    for _ in range(nm):
                        _, o = _cstr(p, o)
        elif size is None:
            break
        if size is not None:
            o = start + size
    return names


class NatNetClient:
    """Background receiver. latest(id) -> RigidBody or None; bodies() -> {id: RigidBody}; on_body(rb) callback per frame."""

    def __init__(self, server="127.0.0.1", local_ip=None, multicast=MULTICAST, data_port=DATA_PORT, cmd_port=CMD_PORT,
                 unicast=False, version=None, on_body=None, dump=None):
        self.server, self.multicast, self.data_port, self.cmd_port = server, multicast, data_port, cmd_port
        self.unicast, self.forced = unicast, tuple(version) if version else None
        self.local_ip = local_ip or self._route_ip(server)
        self.on_body, self.dump = on_body, dump
        self.info, self.names, self.version = None, {}, self.forced
        self._bodies, self._lock = {}, threading.Lock()
        self.frames, self.bad, self.packets = 0, 0, 0
        self.last_error = None
        self._stop = threading.Event()
        self._thread = None

    @staticmethod
    def _route_ip(server):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect((server, 9))                         # no packet is sent; picks the interface towards the server
            return s.getsockname()[0]
        except OSError:
            return "0.0.0.0"
        finally:
            s.close()

    def start(self):
        self.cmd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.cmd.bind((self.local_ip if self.local_ip != "0.0.0.0" else "", 0))
        self.data = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.data.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.data.bind(("", self.data_port))
        if not self.unicast:
            self.data.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                                 socket.inet_aton(self.multicast) + socket.inet_aton(self.local_ip))
        for s in (self.cmd, self.data):
            s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1 << 20)
        self.connect()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def connect(self):
        ping = bytearray(270)
        ping[0:4] = b"Ping"
        ping[265:269] = bytes([4, 1, 0, 0])                # client version, as the NatNet 4 SDK sample sends
        self._send(packet(NAT_CONNECT, bytes(ping)))

    def request_modeldef(self):
        self._send(packet(NAT_REQUEST_MODELDEF))

    def _send(self, data):
        try:
            self.cmd.sendto(data, (self.server, self.cmd_port))
        except OSError as e:
            self.last_error = "send to %s:%d failed: %s" % (self.server, self.cmd_port, e)

    def _run(self):
        next_ka = time.monotonic() + 1.0
        while not self._stop.is_set():
            try:
                ready, _, _ = select.select([self.cmd, self.data], [], [], 0.2)
            except OSError:
                break
            for s in ready:
                try:
                    data, src = s.recvfrom(65536)
                except OSError:
                    continue
                self._handle(data, time.monotonic())
            now = time.monotonic()
            if now > next_ka:
                next_ka = now + 1.0
                if self.unicast:
                    self._send(packet(NAT_KEEPALIVE))
                if self.info is None:
                    self.connect()                        # keep asking until Motive answers (it may start later)
                if not self.names:
                    self.request_modeldef()               # rigid-body names (repeated until one parses)

    def _handle(self, data, t_rx):
        if len(data) < 4:
            return
        self.packets += 1
        msg, size = struct.unpack_from("<HH", data, 0)
        p = data[4:4 + size] if size else data[4:]
        if self.dump is not None and len(self.dump) < 20:
            self.dump.append(data)
        if msg == NAT_SERVERINFO:
            self.info = parse_server_info(p)
            if self.forced is None and self.version is None and self.info["natnet"][0] > 0:
                self.version = self.info["natnet"][:2]
            self.request_modeldef()
        elif msg == NAT_MODELDEF:
            for ver in ([self.version] if self.version else []) + list(CANDIDATE_VERSIONS):
                try:
                    names = parse_modeldef(p, ver)
                    if names:
                        self.names = names
                        break
                except (struct.error, ValueError, IndexError):
                    continue
        elif msg == NAT_FRAMEOFDATA:
            self._frame(p, t_rx)

    def _frame(self, p, t_rx):
        order = [self.version] if self.version else []
        if self.forced is None:
            order += [v for v in CANDIDATE_VERSIONS if v != self.version]
        for ver in order:
            try:
                frame, bodies = parse_frame(p, ver)
            except (struct.error, ValueError, IndexError) as e:
                self.last_error = "frame parse (NatNet %d.%d): %s" % (ver[0], ver[1], e)
                continue
            if not plausible(bodies):
                self.last_error = "frame parse (NatNet %d.%d): implausible rigid body" % ver
                continue
            if bodies and self.forced is None:
                self.version = ver                         # this layout works on the real stream: keep it
            self.frames += 1
            for rid, pos, q, err, valid in bodies:
                rb = RigidBody(rid, pos, q, err, valid, frame, t_rx)
                with self._lock:
                    self._bodies[rid] = rb
                if self.on_body is not None:
                    self.on_body(rb)
            return
        self.bad += 1

    def latest(self, rid):
        with self._lock:
            return self._bodies.get(rid)

    def bodies(self):
        with self._lock:
            return dict(self._bodies)

    def close(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(1.0)
        for s in (getattr(self, "cmd", None), getattr(self, "data", None)):
            if s is not None:
                try:
                    s.close()
                except OSError:
                    pass
