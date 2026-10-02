"""Large-yaw setpoint application — exercises 360 deg-capable yaw positioning.

Holds pitch at 0 and steps the yaw setpoint through large angles that cross the
+/-180 deg boundary and go beyond a half-turn, so a wrap-aware controller (`qpd`)
can be compared against a naive-error controller (`pd`). Evaluate yaw with a
SHORTEST-PATH metric, not `psi_ref - psi` (which is unfair once angles wrap).
"""
from __future__ import annotations

import numpy as np

from aero2.applications.base import Application
from aero2.control.base import Reference

#: (t_start_s, yaw_setpoint_deg). Held until the next entry.
YAW_STEPS_DEG = [(0.0, 0.0), (3.0, 170.0), (9.0, -170.0), (15.0, 270.0), (21.0, 0.0)]


class YawLargeSetpoint(Application):
    name = "yaw_large_setpoint"

    def __init__(self, duration_s: float = 27.0, nominal_hz: float = 200.0,
                 steps_deg=None) -> None:
        super().__init__(duration_s, nominal_hz)
        self.steps = [(float(t), np.deg2rad(float(a)))
                      for t, a in (steps_deg if steps_deg is not None else YAW_STEPS_DEG)]

    def _psi_set(self, t: float) -> float:
        psi = self.steps[0][1]
        for ts, a in self.steps:
            if t >= ts:
                psi = a
        return psi

    def reference(self, t: float) -> Reference:
        return Reference(theta=0.0, psi=self._psi_set(t))


#: Control-rich, both-directions "random-looking" yaw schedule (deg), pitch held 0.
#: Large slews + many +/-180 deg wrap crossings + direction reversals.
YAW_COMPLEX_DEG = [
    (0.0, 0), (2.5, 200), (5.0, -150), (7.5, 300), (10.0, -90),
    (12.5, 170), (15.0, -270), (17.5, 45), (20.0, -200), (22.5, 0),
]


class YawComplexMission(Application):
    """Pitch held at 0; yaw follows a control-rich both-directions schedule that
    repeatedly crosses +/-180 deg (exercises shortest-path / quaternion yaw)."""

    name = "yaw_complex_mission"

    def __init__(self, duration_s: float = 25.0, nominal_hz: float = 200.0,
                 steps_deg=None) -> None:
        super().__init__(duration_s, nominal_hz)
        self.steps = [(float(t), np.deg2rad(float(a)))
                      for t, a in (steps_deg if steps_deg is not None else YAW_COMPLEX_DEG)]

    def _psi(self, t: float) -> float:
        psi = self.steps[0][1]
        for ts, a in self.steps:
            if t >= ts:
                psi = a
        return psi

    def reference(self, t: float) -> Reference:
        return Reference(theta=0.0, psi=self._psi(t))


#: Bidirectional 360-deg finale: pitch tracks a considerable +/- angle while yaw
#: sweeps a full turn each way (continuous ramp), crossing +/-180 deg repeatedly.
PITCH_AMP_DEG = 25.0     # considerable pitch tracking amplitude
YAW_SPIN_DPS = 90.0      # yaw sweep rate [deg/s] -> ~4 s per revolution


class PitchTrackYawSpin360(Application):
    """Pitch tracks a slow +/-25 deg triangle; yaw sweeps +360 then -360 (continuous)."""

    name = "pitch_track_yaw_spin360"

    def __init__(self, duration_s: float = 24.0, nominal_hz: float = 200.0,
                 pitch_amp_deg: float = PITCH_AMP_DEG, yaw_dps: float = YAW_SPIN_DPS) -> None:
        super().__init__(duration_s, nominal_hz)
        self.pa = np.deg2rad(float(pitch_amp_deg))
        self.yr = np.deg2rad(float(yaw_dps))

    def reference(self, t: float) -> Reference:
        # pitch: slow triangle wave, period 12 s (considerable, smooth, trackable)
        frac = (t / 12.0) % 1.0
        tri = 4.0 * abs(frac - 0.5) - 1.0            # in [-1, 1]
        theta = self.pa * tri
        # yaw: +full turn for first half, -full turn for second half (continuous ramp)
        half = self.duration_s / 2.0
        if t < half:
            psi = self.yr * t                         # spin + (CCW)
        else:
            psi = self.yr * half - self.yr * (t - half)   # spin - (CW) back through 0
        return Reference(theta=theta, psi=psi)


#: Figure-8 mission: pitch STEPS (+/-20 deg) + yaw large-angle STEP staircase (to 270 deg).
PITCH_STEP_DEG = [(0, 0), (3, 20), (8, -20), (13, 20), (18, 0)]
YAW_STAIR_DEG = [(0, 0), (3, 90), (8, 180), (13, 270), (18, 90), (22, 0)]


class PitchYawSteps(Application):
    """Pitch step reference (+/-20 deg) with a large-angle yaw step staircase (to 270 deg)."""

    name = "pitch_yaw_steps"

    def __init__(self, duration_s: float = 24.0, nominal_hz: float = 200.0,
                 pitch_steps=None, yaw_steps=None) -> None:
        super().__init__(duration_s, nominal_hz)
        self.ps = [(float(t), np.deg2rad(float(a))) for t, a in (pitch_steps or PITCH_STEP_DEG)]
        self.ys = [(float(t), np.deg2rad(float(a))) for t, a in (yaw_steps or YAW_STAIR_DEG)]

    @staticmethod
    def _val(t, steps):
        v = steps[0][1]
        for ts, a in steps:
            if t >= ts:
                v = a
        return v

    def reference(self, t: float) -> Reference:
        return Reference(theta=self._val(t, self.ps), psi=self._val(t, self.ys))


#: Photo pose-tour: HOLD distinct (pitch, yaw) poses ~4 s each for clean stills.
#: (t_start_s, pitch_deg, yaw_deg) — spans the 6 twin-render poses.
POSE_TOUR_DEG = [
    (0.0, 0, 0), (4.0, 40, 0), (12.0, 25, 90), (20.0, 0, 180),
    (28.0, 0, 270), (36.0, 15, 45), (44.0, 0, 135), (52.0, 0, 0),
]


class PoseTour(Application):
    """Holds a sequence of (pitch, yaw) poses ~8 s each for clean photo capture."""

    name = "pose_tour"

    def __init__(self, duration_s: float = 60.0, nominal_hz: float = 200.0, poses=None) -> None:
        super().__init__(duration_s, nominal_hz)
        self.poses = [(float(t), np.deg2rad(float(p)), np.deg2rad(float(y)))
                      for t, p, y in (poses if poses is not None else POSE_TOUR_DEG)]

    def reference(self, t: float) -> Reference:
        th, ps = self.poses[0][1], self.poses[0][2]
        for ts, p, y in self.poses:
            if t >= ts:
                th, ps = p, y
        return Reference(theta=th, psi=ps)


__all__ = ["YawLargeSetpoint", "YAW_STEPS_DEG", "YawComplexMission", "YAW_COMPLEX_DEG",
           "PitchTrackYawSpin360", "PitchYawSteps", "PITCH_STEP_DEG", "YAW_STAIR_DEG",
           "PoseTour", "POSE_TOUR_DEG"]
