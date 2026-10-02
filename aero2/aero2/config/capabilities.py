"""Capability/status metadata for Aero 2 runners, app, docs, and papers.

Keep implementation truth in code, but keep user-facing status language in one
place so the app does not imply that scaffolded or exploratory paths are
validated hardware-ready workflows.
"""
from __future__ import annotations


EXECUTION_MODES = {
    "offline": {
        "label": "Offline Simulation",
        "status": "implemented",
        "note": "Software-only plant execution through OfflineBackend.",
    },
    "virtual_twin": {
        "label": "Digital Twin",
        "status": "live_pitch_only_validated",
        "note": "PAL/QLabs backend implemented; the current QLabs asset is pitch-only in practice: pitch moves, but yaw encoder/rate stayed zero under open-loop yaw and direct motor pulses.",
    },
    "hardware": {
        "label": "Hardware Experiment",
        "status": "scaffolded",
        "note": "Direct HIL/PAL backend placeholder; not executable yet.",
    },
}


MODELS = {
    "helicopter_2dof": {
        "status": "primary",
        "note": "Primary coupled pitch-yaw Aero 2 model for controller comparison.",
    },
    "linear_2dof": {
        "status": "offline_supported",
        "note": "Linearized 2-DOF model for linear controller analysis.",
    },
    "pitch_only": {
        "status": "offline_supported",
        "note": "Pitch-axis model with yaw held inert.",
    },
    "yaw_only": {
        "status": "offline_supported",
        "note": "Yaw-axis model with pitch held inert and offline stiction approximation.",
    },
    "half_rotor": {
        "status": "not_validated",
        "note": "Exploratory half-rotor model; no hardware validation yet.",
    },
}


CONTROLLERS = {
    "pd": {
        "status": "baseline_validated_offline",
        "note": "Primary offline baseline and app smoke-test controller.",
    },
    "lqr": {
        "status": "offline_supported",
        "note": "Linear optimal controller using the linearized 2-DOF plant.",
    },
    "lqg": {
        "status": "offline_supported",
        "note": "LQR plus observer, validated in offline tests.",
    },
    "mpc": {
        "status": "offline_supported",
        "note": "Unconstrained finite-horizon first-move linear MPC.",
    },
    "backstepping": {
        "status": "offline_supported",
        "note": "Nonlinear inverse-dynamics/computed-torque controller.",
    },
    "smc": {
        "status": "offline_supported",
        "note": "Sliding-mode controller with boundary-layer saturation.",
    },
    "nmpc": {
        "status": "offline_supported",
        "note": "Lightweight grid-search NMPC; benchmarkable but not fastest.",
    },
    "hyperlif": {
        "status": "experimental_offline",
        "note": "PD plus Adaptive HyperLIF residual; no Aero 2 hardware result yet.",
    },
    "julia_policy": {
        "status": "julia_bridge_offline_validated",
        "note": "Bridge 1 controller: Python runner/backends with a Julia policy callable; offline smoke validated, live paths require explicit validation.",
    },
}


APPLICATIONS = {
    "reference_tracking": {
        "status": "implemented",
        "note": "Square-wave pitch/yaw reference tracking.",
    },
    "pitch_reference_tracking": {
        "status": "implemented",
        "note": "Pitch square-wave tracking with yaw reference held at zero.",
    },
    "yaw_reference_tracking": {
        "status": "implemented",
        "note": "Yaw square-wave tracking with pitch reference held at zero.",
    },
}


def mode_is_implemented(mode: str) -> bool:
    return EXECUTION_MODES[mode]["status"] in {
        "implemented",
        "external_required",
        "live_pitch_validated",
        "live_pitch_only_validated",
    }


def capability_notes(model: str, mode: str, controller: str, application: str) -> list[str]:
    """Return concise status lines for a selected experiment."""
    return [
        f"mode={mode}: {EXECUTION_MODES[mode]['status']} - {EXECUTION_MODES[mode]['note']}",
        f"model={model}: {MODELS[model]['status']} - {MODELS[model]['note']}",
        f"controller={controller}: {CONTROLLERS[controller]['status']} - {CONTROLLERS[controller]['note']}",
        f"application={application}: {APPLICATIONS[application]['status']} - {APPLICATIONS[application]['note']}",
    ]


__all__ = [
    "EXECUTION_MODES",
    "MODELS",
    "CONTROLLERS",
    "APPLICATIONS",
    "mode_is_implemented",
    "capability_notes",
]
