"""`Backend` interface — where the plant actually runs (brief §5).

Three implementations share this one contract so that swapping
`offline -> virtual_twin -> hardware` is a single config field, never an
`if` branch inside a controller:

    OfflineBackend     integrates a chosen Model (ground truth + injectable
                       noise / quantization / disturbance).
    VirtualTwinBackend QLabs connection.
    HardwareBackend    real-time HIL/PAL (Direct HIL DirectHilAero2IO.read).

`dt_actual()` returns the *measured* loop period and is the linchpin of the
timing rule (config.timing): controllers must update on this, not the nominal.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol, runtime_checkable

import numpy as np


@dataclass
class Measurement:
    """One sampled snapshot from any backend.

    Angles/rates are the canonical interface; raw IMU/current channels are
    optional and may be ``None`` on backends that do not expose them.
    """
    t: float                                  # timestamp [s]
    theta: float                              # pitch angle [rad]
    psi: float                                # yaw angle [rad]
    theta_dot: Optional[float] = None         # pitch rate [rad/s] (gyro-y corrected)
    psi_dot: Optional[float] = None           # yaw rate [rad/s] (gyro-z corrected)
    gyro: Optional[np.ndarray] = None         # raw [wx, wy, wz] [rad/s]
    accel: Optional[np.ndarray] = None        # raw [ax, ay, az] [m/s^2]
    currents: Optional[np.ndarray] = None     # motor currents [A]
    raw: dict = field(default_factory=dict)   # backend-specific extras

    def state(self) -> np.ndarray:
        """Best-effort state vector [theta, theta_dot, psi, psi_dot].

        Missing rates default to 0.0; a real StateEstimator should be used to
        fill them properly (see aero2/io/state_estimation.py).
        """
        return np.array([
            self.theta,
            0.0 if self.theta_dot is None else self.theta_dot,
            self.psi,
            0.0 if self.psi_dot is None else self.psi_dot,
        ], dtype=float)


@runtime_checkable
class Backend(Protocol):
    """Plant execution contract (offline / virtual-twin / hardware)."""

    def reset(self, x0: np.ndarray) -> Measurement:
        """Reset the plant to initial state x0; return the first measurement."""
        ...

    def apply(self, u: np.ndarray) -> None:
        """Send the virtual command u = [u_p, u_y] (or mapped motor voltages)."""
        ...

    def read(self) -> Measurement:
        """Read the latest measurement (angles, rates, currents, imu, timestamp)."""
        ...

    def dt_actual(self) -> float:
        """Measured loop period [s] of the last cycle (critical; brief §9)."""
        ...

    def close(self) -> None:
        """Release hardware / simulation resources."""
        ...


__all__ = ["Measurement", "Backend"]
