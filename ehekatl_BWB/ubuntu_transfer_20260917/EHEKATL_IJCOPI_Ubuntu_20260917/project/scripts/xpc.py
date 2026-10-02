import socket
import struct


def _b4(s):
    if isinstance(s, bytes):
        return s
    return str(s).encode('ascii')


def _b(s):
    if isinstance(s, bytes):
        return s
    return str(s).encode('utf-8')


class XPlaneConnect(object):
    '''XPlaneConnect (XPC) UDP client for Python 3.

    This keeps the same public API as the original NASA/user xpc.py used by the
    EHEKATL scripts, but fixes Python-3 bytes/str packing issues and the common
    single-string getDREFs case.
    '''

    def __init__(self, xpHost='localhost', xpPort=49009, port=0, timeout=1000):
        try:
            xpIP = socket.gethostbyname(xpHost)
        except Exception as exc:
            raise ValueError('Unable to resolve xpHost.') from exc
        if not (0 <= xpPort <= 65535):
            raise ValueError('The specified X-Plane port is not a valid port number.')
        if not (0 <= port <= 65535):
            raise ValueError('The specified local port is not a valid port number.')
        if timeout < 0:
            raise ValueError('timeout must be non-negative.')
        self.xpDst = (xpIP, xpPort)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socket.bind(('0.0.0.0', port))
        self.socket.settimeout(timeout / 1000.0)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def close(self):
        if getattr(self, 'socket', None) is not None:
            self.socket.close()
            self.socket = None

    def sendUDP(self, buffer):
        if not buffer:
            raise ValueError('sendUDP: buffer is empty.')
        self.socket.sendto(buffer, self.xpDst)

    def readUDP(self):
        return self.socket.recv(16384)

    def setCONN(self, port):
        if not (0 <= port <= 65535):
            raise ValueError('The specified port is not a valid port number.')
        buffer = struct.pack('<4sxH', b'CONN', int(port))
        self.sendUDP(buffer)
        timeout = self.socket.gettimeout()
        self.socket.close()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socket.bind(('0.0.0.0', port))
        self.socket.settimeout(timeout)
        self.socket.recv(1024)

    def pauseSim(self, pause):
        pause = int(pause)
        if pause < 0 or (pause > 2 and pause < 100) or (pause > 119 and pause < 200) or pause > 219:
            raise ValueError('Invalid argument for pause command.')
        self.sendUDP(struct.pack('<4sxB', b'SIMU', pause))

    def readDATA(self):
        buffer = self.readUDP()
        if len(buffer) < 6:
            return None
        rows = (len(buffer) - 5) // 36
        return [struct.unpack_from('9f', buffer, 5 + 36 * i) for i in range(rows)]

    def sendDATA(self, data):
        if len(data) > 134:
            raise ValueError('Too many rows in data.')
        buffer = struct.pack('<4sx', b'DATA')
        for row in data:
            if len(row) != 9:
                raise ValueError('Row does not contain exactly 9 values. <{}>'.format(row))
            buffer += struct.pack('<I8f', int(row[0]), *[float(v) for v in row[1:]])
        self.sendUDP(buffer)

    def getPOSI(self, ac=0):
        """Get aircraft position.

        Returns:
            [lat_deg, lon_deg, alt_m, pitch_deg, roll_deg, heading_deg, gear]
        Supports both old 34-byte POSI packets and newer 46-byte packets.
        """
        self.sendUDP(struct.pack('<4sxB', b'GETP', int(ac)))
        resultBuf = self.readUDP()

        if resultBuf[:4] != b'POSI':
            raise ValueError('Unexpected POSI header: {!r}'.format(resultBuf[:4]))

        if len(resultBuf) == 34:
            # Old format: aircraft byte + 7 floats
            result = struct.unpack('<4sxBfffffff', resultBuf)
            return result[2:]

        if len(resultBuf) == 46:
            # New format: aircraft byte, lat/lon/alt as doubles, attitude/gear as floats
            header, ac_num, lat, lon, alt, pitch, roll, heading, gear = struct.unpack(
                '<4sxBdddffff', resultBuf
            )
            return (lat, lon, alt, pitch, roll, heading, gear)

        raise ValueError('Unexpected POSI response length: {}'.format(len(resultBuf)))

    def sendPOSI(self, values, ac=0):
        if len(values) < 1 or len(values) > 7:
            raise ValueError('Must have between 1 and 7 items in values.')
        if ac < 0 or ac > 20:
            raise ValueError('Aircraft number must be between 0 and 20.')
        buffer = struct.pack('<4sxB', b'POSI', int(ac))
        for i in range(7):
            val = -998.0
            if i < len(values):
                val = float(values[i])
            buffer += struct.pack('<f', val)
        self.sendUDP(buffer)

    def getCTRL(self, ac=0):
        self.sendUDP(struct.pack('<4sxB', b'GETC', int(ac)))
        resultBuf = self.readUDP()
        if len(resultBuf) != 31:
            raise ValueError('Unexpected CTRL response length: {}'.format(len(resultBuf)))
        result = struct.unpack('<4sxffffbfBf', resultBuf)
        if result[0] != b'CTRL':
            raise ValueError('Unexpected CTRL header: {!r}'.format(result[0]))
        return result[1:7] + result[8:]

    def sendCTRL(self, values, ac=0):
        '''Send controls in XPC order:
        [latitudinal stick/aileron, longitudinal stick/elevator, rudder,
         throttle, gear, flaps, speedbrakes]
        Use -998 for fields you do not want to change.
        '''
        if len(values) < 1 or len(values) > 7:
            raise ValueError('Must have between 1 and 7 items in values.')
        if ac < 0 or ac > 20:
            raise ValueError('Aircraft number must be between 0 and 20.')
        buffer = struct.pack('<4sx', b'CTRL')
        for i in range(6):
            val = -998
            if i < len(values):
                val = values[i]
            if i == 4:  # gear is signed byte; -1 means do not change
                if abs(float(val) + 998.0) < 1e-4:
                    val = -1
                buffer += struct.pack('b', int(val))
            else:
                buffer += struct.pack('<f', float(val))
        buffer += struct.pack('B', int(ac))
        if len(values) == 7:
            buffer += struct.pack('<f', float(values[6]))
        self.sendUDP(buffer)

    def sendDREF(self, dref, values):
        self.sendDREFs([dref], [values])

    def sendDREFs(self, drefs, values):
        if isinstance(drefs, (str, bytes)):
            drefs = [drefs]
        if len(drefs) != len(values):
            raise ValueError('drefs and values must have the same number of elements.')
        buffer = struct.pack('<4sx', b'DREF')
        for dref, value in zip(drefs, values):
            dref_b = _b(dref)
            if len(dref_b) == 0 or len(dref_b) > 255:
                raise ValueError('dref must be a non-empty string less than 256 bytes.')
            if value is None:
                raise ValueError('value must be a scalar or sequence of floats.')
            if hasattr(value, '__len__') and not isinstance(value, (str, bytes)):
                vals = [float(v) for v in value]
                if len(vals) > 255:
                    raise ValueError('value must have less than 256 items.')
                fmt = '<B{}sB{}f'.format(len(dref_b), len(vals))
                buffer += struct.pack(fmt, len(dref_b), dref_b, len(vals), *vals)
            else:
                fmt = '<B{}sBf'.format(len(dref_b))
                buffer += struct.pack(fmt, len(dref_b), dref_b, 1, float(value))
        self.sendUDP(buffer)

    def getDREF(self, dref):
        return self.getDREFs([dref])[0]

    def getDREFs(self, drefs):
        if isinstance(drefs, (str, bytes)):
            drefs = [drefs]
        drefs_b = [_b(d) for d in drefs]
        buffer = struct.pack('<4sxB', b'GETD', len(drefs_b))
        for dref in drefs_b:
            fmt = '<B{}s'.format(len(dref))
            buffer += struct.pack(fmt, len(dref), dref)
        self.sendUDP(buffer)
        buffer = self.readUDP()
        resultCount = struct.unpack_from('B', buffer, 5)[0]
        offset = 6
        result = []
        for _ in range(resultCount):
            rowLen = struct.unpack_from('B', buffer, offset)[0]
            offset += 1
            fmt = '<{}f'.format(rowLen)
            row = struct.unpack_from(fmt, buffer, offset)
            result.append(row)
            offset += rowLen * 4
        return result

    def sendTEXT(self, msg, x=-1, y=-1):
        if y < -1:
            raise ValueError('y must be greater than or equal to -1.')
        if msg is None:
            msg = ''
        msg_b = _b(msg)
        msgLen = len(msg_b)
        buffer = struct.pack('<4sxiiB{}s'.format(msgLen), b'TEXT', int(x), int(y), msgLen, msg_b)
        self.sendUDP(buffer)

    def sendVIEW(self, view):
        if view < ViewType.Forwards or view > ViewType.FullscreenNoHud:
            raise ValueError('Unknown view command.')
        self.sendUDP(struct.pack('<4sxi', b'VIEW', int(view)))

    def sendWYPT(self, op, points):
        if op < 1 or op > 3:
            raise ValueError('Invalid operation specified.')
        if len(points) % 3 != 0:
            raise ValueError('Invalid points. Points should be divisible by 3.')
        if len(points) // 3 > 255:
            raise ValueError('Too many points. You can only send 255 points at a time.')
        if op == 3:
            buffer = struct.pack('<4sxBB', b'WYPT', 3, 0)
        else:
            buffer = struct.pack('<4sxBB{}f'.format(len(points)), b'WYPT', int(op), len(points), *[float(p) for p in points])
        self.sendUDP(buffer)

    def sendCOMM(self, comm):
        if comm is None:
            raise ValueError('comm must be non-empty.')
        comm_b = _b(comm)
        if len(comm_b) == 0 or len(comm_b) > 255:
            raise ValueError('comm must be a non-empty string less than 256 bytes.')
        fmt = '<B{}s'.format(len(comm_b))
        buffer = struct.pack('<4sx', b'COMM') + struct.pack(fmt, len(comm_b), comm_b)
        self.sendUDP(buffer)


class ViewType(object):
    Forwards = 73
    Down = 74
    Left = 75
    Right = 76
    Back = 77
    Tower = 78
    Runway = 79
    Chase = 80
    Follow = 81
    FollowWithPanel = 82
    Spot = 83
    FullscreenWithHud = 84
    FullscreenNoHud = 85
