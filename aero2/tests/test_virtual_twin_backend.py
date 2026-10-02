"""Virtual-twin backend tests.

These tests validate the PAL/QLabs adapter without opening QLabs by injecting a
small fake Aero2 object. Live QLabs connection checks remain manual/lab tests.
"""
from __future__ import annotations

import numpy as np
import pytest

from aero2.execution.backend import Backend
from aero2.execution.virtual_twin import LED_ACTIVE_GREEN, LED_IDLE_RED, VirtualTwinBackend, map_virtual_to_motor


def test_map_virtual_to_motor_modes_and_clipping():
    assert np.allclose(map_virtual_to_motor([2.0, 0.5], "mixed", 15.0), [1.5, 2.5])
    assert np.allclose(map_virtual_to_motor([2.0, 0.5], "mixed-reversed", 15.0), [2.5, 1.5])
    assert np.allclose(map_virtual_to_motor([2.0, 0.5], "direct", 15.0), [2.0, 0.5])
    assert np.allclose(map_virtual_to_motor([20.0, 0.0], "direct", 15.0), [15.0, 0.0])
    with pytest.raises(ValueError):
        map_virtual_to_motor([0.0, 0.0], "unknown", 15.0)


class FakeClock:
    def __init__(self) -> None:
        self.t = 10.0

    def __call__(self) -> float:
        self.t += 0.005
        return self.t


class FakeAero2:
    instances = []

    def __init__(self, id, hardware, readMode, frequency) -> None:
        self.id = id
        self.hardware = hardware
        self.readMode = readMode
        self.frequency = frequency
        self.writes = []
        self.leds = []
        self.terminated = False
        self.pitchAngle = 0.1
        self.yawAngle = -0.2
        self.pitchRate = 0.3
        self.yawRate = -0.4
        self.gyroscope = np.array([0.01, 0.02, 0.03])
        self.accelerometer = np.array([1.0, 2.0, 3.0])
        self.motorCurrent = np.array([0.4, 0.5])
        FakeAero2.instances.append(self)

    def read_analog_encoder_other_channels(self) -> None:
        self.pitchAngle += 0.001
        self.yawAngle -= 0.001

    def write_voltage(self, v0, v1) -> None:
        self.writes.append((float(v0), float(v1)))

    def write_led(self, color) -> None:
        self.leds.append(np.asarray(color, dtype=float).copy())

    def terminate(self) -> None:
        self.terminated = True


def test_virtual_twin_backend_uses_pal_virtual_flag_and_safe_shutdown():
    FakeAero2.instances.clear()
    backend = VirtualTwinBackend(
        aero_id="7",
        frequency=200,
        read_mode=1,
        output_mode="mixed",
        voltage_limit=18.0,  # PAL path must cap this to 15 V
        aero_factory=FakeAero2,
        clock=FakeClock(),
    )

    assert isinstance(backend, Backend)
    fake = FakeAero2.instances[-1]
    assert fake.id == "7"
    assert fake.hardware == 0
    assert fake.readMode == 1
    assert fake.frequency == 200
    assert backend.voltage_limit == 15.0
    assert np.allclose(fake.leds[-1], LED_IDLE_RED)

    meas0 = backend.reset(np.zeros(4))
    assert meas0.raw["pal_hardware_flag"] == 0
    assert meas0.raw["led_state"] == "idle"
    assert fake.writes[-1] == (0.0, 0.0)
    assert np.allclose(fake.leds[-1], LED_IDLE_RED)

    backend.apply(np.array([2.0, 0.5]))
    assert fake.writes[-1] == (1.5, 2.5)
    assert np.allclose(fake.leds[-1], LED_ACTIVE_GREEN)
    meas = backend.read()

    assert meas.theta == pytest.approx(fake.pitchAngle)
    assert meas.psi == pytest.approx(fake.yawAngle)
    assert np.allclose(meas.raw["virtual_command"], [2.0, 0.5])
    assert np.allclose(meas.raw["motor_voltage"], [1.5, 2.5])
    assert meas.raw["led_state"] == "active"
    assert backend.dt_actual() == pytest.approx(0.005)

    backend.close()
    assert fake.writes[-1] == (0.0, 0.0)
    assert np.allclose(fake.leds[-1], LED_IDLE_RED)
    assert fake.terminated is True
