"""Applications: reference tracking (done) and regulation-under-disturbance (P8).
Both share one closed-loop runner (`Application`); selectable by name."""
from __future__ import annotations

from aero2.applications.base import Application, ClosedLoopRecord
from aero2.applications.reference_tracking import (
    PitchSquareWaveTracking,
    SquareWaveTracking,
    YawSquareWaveTracking,
)
from aero2.applications.regulation import RegulationUnderDisturbance
from aero2.applications.large_yaw import (
    YawLargeSetpoint, YawComplexMission, PitchTrackYawSpin360, PitchYawSteps, PoseTour,
)

#: name -> Application class
APPLICATIONS = {
    "reference_tracking": SquareWaveTracking,
    "pitch_reference_tracking": PitchSquareWaveTracking,
    "yaw_reference_tracking": YawSquareWaveTracking,
    "regulation_disturbance": RegulationUnderDisturbance,
    "yaw_large_setpoint": YawLargeSetpoint,
    "yaw_complex_mission": YawComplexMission,
    "pitch_track_yaw_spin360": PitchTrackYawSpin360,
    "pitch_yaw_steps": PitchYawSteps,
    "pose_tour": PoseTour,
}


def make_application(name: str, **kwargs) -> Application:
    key = name.lower()
    if key not in APPLICATIONS:
        raise ValueError(f"unknown application: {name!r}; choose from {sorted(APPLICATIONS)}")
    return APPLICATIONS[key](**kwargs)


__all__ = [
    "Application",
    "ClosedLoopRecord",
    "SquareWaveTracking",
    "PitchSquareWaveTracking",
    "YawSquareWaveTracking",
    "RegulationUnderDisturbance",
    "YawLargeSetpoint",
    "APPLICATIONS",
    "make_application",
]
