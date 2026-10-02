"""VirtualTwinBackend — Quanser QLabs/PAL virtual Aero 2.

This backend uses the installed PAL wrapper ``pal.products.aero2.Aero2`` with
``hardware=0``. PAL then opens the virtual Aero 2 at
``<id>@tcpip://localhost:18950``. QLabs must already be running and the virtual
Aero 2 must be available.

The controller still sees the clean backend-agnostic contract:
``u = [u_pitch, u_yaw]``. This backend maps that virtual command to motor
voltages before calling ``Aero2.write_voltage``.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Callable, Optional

import numpy as np

from aero2.execution.backend import Measurement
from aero2.config import params


DEFAULT_QUANSER_PYTHON = Path(os.environ.get("QUANSER_PYTHON", r"C:\Quanser\0_libraries\python"))
DEFAULT_QUANSER_SITE_PACKAGES = Path(
    os.environ.get(
        "QUANSER_SITE_PACKAGES",
        r"C:\02_Research\01_Robotics_Quanser\.quanser_env\Lib\site-packages",
    )
)
LED_IDLE_RED = np.array([1.0, 0.0, 0.0], dtype=np.float64)
LED_ACTIVE_GREEN = np.array([0.0, 1.0, 0.0], dtype=np.float64)


def ensure_quanser_python(path: Path | str | None = DEFAULT_QUANSER_PYTHON) -> None:
    candidates: list[Path] = []
    if path is not None:
        candidates.append(Path(path))
    if DEFAULT_QUANSER_SITE_PACKAGES.exists() and DEFAULT_QUANSER_SITE_PACKAGES not in candidates:
        candidates.append(DEFAULT_QUANSER_SITE_PACKAGES)

    for p in candidates:
        if not p.exists():
            raise FileNotFoundError(f"Quanser Python path not found: {p}")
        s = str(p)
        if s not in sys.path:
            sys.path.insert(0, s)


def map_virtual_to_motor(u: np.ndarray, output_mode: str, voltage_limit: float) -> np.ndarray:
    """Map virtual [pitch, yaw] command to PAL motor voltages.

    ``mixed`` matches the old ``RuntimeAdapter.mix_collective_differential``:
    motor0 = pitch - yaw, motor1 = pitch + yaw.
    """
    u = np.asarray(u, dtype=float).reshape(2)
    u_pitch, u_yaw = float(u[0]), float(u[1])
    if output_mode == "direct":
        motors = np.array([u_pitch, u_yaw], dtype=float)
    elif output_mode == "mixed":
        motors = np.array([u_pitch - u_yaw, u_pitch + u_yaw], dtype=float)
    elif output_mode == "mixed-reversed":
        motors = np.array([u_pitch + u_yaw, u_pitch - u_yaw], dtype=float)
    else:
        raise ValueError(f"unknown output_mode={output_mode!r}")
    return np.clip(motors, -abs(float(voltage_limit)), abs(float(voltage_limit)))


class VirtualTwinBackend:
    """QLabs virtual Aero 2 backend behind the shared ``Backend`` contract."""

    name = "virtual_twin"

    def __init__(
        self,
        aero_id: str | int = "0",
        frequency: float = 200.0,
        read_mode: int = 1,
        output_mode: str = "mixed",
        voltage_limit: float = 15.0,
        hardware: int = 0,
        quanser_python: Path | str | None = DEFAULT_QUANSER_PYTHON,
        aero_factory: Optional[Callable[..., object]] = None,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        self.aero_id = aero_id
        self.frequency = float(frequency)
        self.read_mode = int(read_mode)
        self.output_mode = output_mode
        self.voltage_limit = min(abs(float(voltage_limit)), 15.0)
        self.hardware = int(hardware)
        self.clock = clock
        self._t0 = 0.0
        self._last_t: float | None = None
        self._last_dt = 1.0 / self.frequency
        self._last_virtual_u = np.zeros(2)
        self._last_motor_v = np.zeros(2)
        self._led_state = "unknown"
        self._led_error: str | None = None

        if aero_factory is None:
            ensure_quanser_python(quanser_python)
            try:
                from pal.products.aero2 import Aero2
            except Exception as exc:  # pragma: no cover - depends on local PAL install
                raise RuntimeError("VirtualTwinBackend requires pal.products.aero2.Aero2.") from exc
            aero_factory = Aero2

        self.aero = aero_factory(
            id=self.aero_id,
            hardware=self.hardware,
            readMode=self.read_mode,
            frequency=int(round(self.frequency)),
        )
        self._set_led("idle")

    def reset(self, x0: np.ndarray) -> Measurement:
        # PAL/QLabs does not expose a general state reset through this wrapper.
        # We command zero, show idle-red, and return the current measured state.
        del x0
        self._t0 = self.clock()
        self._last_t = self._t0
        self._last_dt = 1.0 / self.frequency
        self._last_virtual_u = np.zeros(2)
        self._last_motor_v = np.zeros(2)
        self.aero.write_voltage(0.0, 0.0)
        self._set_led("idle")
        return self.read()

    def apply(self, u: np.ndarray) -> None:
        self._last_virtual_u = np.asarray(u, dtype=float).reshape(2).copy()
        self._last_motor_v = map_virtual_to_motor(self._last_virtual_u, self.output_mode, self.voltage_limit)
        self._set_led("active")
        self.aero.write_voltage(float(self._last_motor_v[0]), float(self._last_motor_v[1]))

    def read(self) -> Measurement:
        self.aero.read_analog_encoder_other_channels()
        now = self.clock()
        if self._last_t is not None:
            self._last_dt = max(1e-9, now - self._last_t)
        self._last_t = now

        gyro = self._vector_attr("gyroscope", 3)
        accel = self._vector_attr("accelerometer", 3)
        currents = self._vector_attr("motorCurrent", 2)
        motor_position = self._vector_attr("motorPosition", 2)
        motor_speed = self._vector_attr("motorSpeed", 2)
        encoder_counts = self._vector_attr("readEncoderBuffer", 4)
        other_channels = self._vector_attr("readOtherBufer", 10)

        return Measurement(
            t=float(now - self._t0),
            theta=float(getattr(self.aero, "pitchAngle", 0.0)),
            psi=float(getattr(self.aero, "yawAngle", 0.0)),
            theta_dot=float(getattr(self.aero, "pitchRate", 0.0)),
            psi_dot=float(getattr(self.aero, "yawRate", 0.0)),
            gyro=gyro,
            accel=accel,
            currents=currents,
            raw={
                "backend": self.name,
                "aero_id": str(self.aero_id),
                "read_mode": self.read_mode,
                "output_mode": self.output_mode,
                "virtual_command": self._last_virtual_u.copy(),
                "motor_voltage": self._last_motor_v.copy(),
                "voltage_limit": self.voltage_limit,
                "pal_hardware_flag": 0,
                "motor_position": motor_position,
                "motor_speed": motor_speed,
                "encoder_counts": encoder_counts,
                "other_channels": other_channels,
                "led_state": self._led_state,
            },
        )

    def dt_actual(self) -> float:
        return self._last_dt

    def close(self) -> None:
        try:
            self._set_led("idle")
            self.aero.write_voltage(0.0, 0.0)
        finally:
            terminate = getattr(self.aero, "terminate", None)
            if callable(terminate):
                terminate()

    def _set_led(self, state: str) -> None:
        color = LED_ACTIVE_GREEN if state == "active" else LED_IDLE_RED
        write_led = getattr(self.aero, "write_led", None)
        if not callable(write_led):
            self._led_state = "unsupported"
            return
        try:
            write_led(color.copy())
            self._led_state = state
            self._led_error = None
        except Exception as exc:  # pragma: no cover - defensive PAL path
            self._led_state = f"{state}_failed"
            self._led_error = str(exc)

    def _vector_attr(self, name: str, size: int) -> np.ndarray:
        value = getattr(self.aero, name, np.zeros(size))
        arr = np.asarray(value, dtype=float).reshape(-1)
        if arr.size < size:
            out = np.zeros(size)
            out[: arr.size] = arr
            return out
        return arr[:size].copy()


__all__ = [
    "DEFAULT_QUANSER_PYTHON",
    "DEFAULT_QUANSER_SITE_PACKAGES",
    "LED_ACTIVE_GREEN",
    "LED_IDLE_RED",
    "VirtualTwinBackend",
    "ensure_quanser_python",
    "map_virtual_to_motor",
]
