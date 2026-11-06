"""MAVLink link to the Cube through the Pico W UDP bridge (same scheme as motor_test_1.py).

The Pico forwards Cube telemetry to this PC on UDP 14550.  We listen there,
learn the Pico's address from the first packets, and open a separate
``udpout`` connection back to it for commands/requests.
"""
from __future__ import annotations

from dataclasses import dataclass
import time

from pymavlink import mavutil

GCS_SYSTEM, GCS_COMPONENT = 255, 190


@dataclass
class Link:
    rx: object
    tx: object
    target_system: int
    target_component: int
    pico: tuple
    heartbeat: object

    def send_heartbeat(self):
        self.tx.mav.heartbeat_send(mavutil.mavlink.MAV_TYPE_GCS, mavutil.mavlink.MAV_AUTOPILOT_INVALID,
                                   0, 0, mavutil.mavlink.MAV_STATE_ACTIVE)

    def close(self):
        self.tx.close()
        self.rx.close()


def connect(port: int = 14550, timeout_s: float = 15.0, pico_ip: str | None = None,
            pico_port: int | None = None) -> Link:
    """Commands go to (Pico IP, pico_port or port), as in the tested motor_test_1.py."""
    try:
        rx = mavutil.mavlink_connection(f"udpin:0.0.0.0:{port}", source_system=GCS_SYSTEM,
                                        source_component=GCS_COMPONENT)
    except OSError as error:                       # WinError 10013 / 10048: the port is taken
        raise SystemExit(
            f"UDP port {port} is already in use by another program ({error.strerror}).\n"
            "Usually Mission Planner connected over UDP/Wi-Fi, or the OptiTrack bridge.\n"
            "  -> Mission Planner: click DISCONNECT (or close it), or connect it by USB (COM port, 115200).\n"
            "  -> Bridge: stop it with Ctrl+C.\n"
            "Then run this command again.") from None
    deadline = time.time() + timeout_s
    while True:
        remaining = deadline - time.time()
        heartbeat = rx.wait_heartbeat(timeout=remaining) if remaining > 0 else None
        if heartbeat is None:
            rx.close()
            raise TimeoutError(f"No Cube heartbeat on UDP {port} within {timeout_s:.0f} s "
                               "(is the Pico W powered and on this Wi-Fi network?)")
        # Ignore other GCS heartbeats (e.g. Mission Planner) if any reach this port.
        if heartbeat.type != mavutil.mavlink.MAV_TYPE_GCS:
            break
    if pico_ip is None:
        clients = list(getattr(rx, "clients", None) or [])
        if not clients:
            rx.close()
            raise RuntimeError("Could not determine the Pico W address; pass --pico-ip")
        pico_ip = clients[0][0]
    pico = (pico_ip, pico_port or port)
    tx = mavutil.mavlink_connection(f"udpout:{pico[0]}:{pico[1]}", source_system=GCS_SYSTEM,
                                    source_component=GCS_COMPONENT)
    link = Link(rx, tx, heartbeat.get_srcSystem(), heartbeat.get_srcComponent(), pico, heartbeat)
    link.send_heartbeat()
    return link


def is_armed(heartbeat) -> bool:
    return bool(heartbeat.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
