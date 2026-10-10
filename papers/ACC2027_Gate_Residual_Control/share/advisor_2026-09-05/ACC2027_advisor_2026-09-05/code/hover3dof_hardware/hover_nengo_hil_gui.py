r"""Live Nengo GUI for the Quanser 3DOF Hover PD/CMG-PES experiment.

The physical Q8 loop is isolated in a 200 Hz worker thread.  Its CMG/PES
controller is a genuine inner Nengo Simulator stepped ten times at dt=0.5 ms
per hardware sample.  The outer Nengo GUI samples immutable snapshots at 50 Hz;
dashboard rendering is therefore not inserted into the hardware deadline.

No physical output is possible unless launch_hover_nengo_gui.py sets all three
conditions: io=q8, armed=True, and confirm_hardware_review=True.
"""
from __future__ import annotations

import array as arr
import csv
import ctypes
import hashlib
import json
import os
import sys
import threading
import time
import traceback
from dataclasses import asdict, dataclass
from pathlib import Path

import nengo
import numpy as np

# Windows defaults to a ~15.6ms thread-scheduling timer quantum. Under GIL
# contention between this process's threads (the 200Hz hardware worker,
# nengo_gui's own web/event-loop server, the GUI-stepping thread), a thread
# that loses a scheduling round can be delayed by that entire quantum before
# it's rescheduled -- far more than the 5ms/200Hz hardware budget, even
# though every individual piece of per-step work (Q8 I/O, the Nengo CMG-PES
# step, the LIVE-state push) measured well under 1ms in isolation. Requesting
# 1ms timer resolution is the standard, well-documented Windows fix for this
# class of problem; measured to cut a reproduced worst-case LIVE.update()
# stall from 15.3ms to 5.8ms in isolated contention testing before this was
# added (see PROGRESS notes). Not a guarantee of zero misses, but the abort
# threshold is 20 *consecutive* misses, not any miss at all.

# --- portable paths (added for distribution) ---
import sys as _sys, pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from acc2027_paths import LAB_ROOT, ROOT, NENGO_NEF  # noqa: E402

if sys.platform == "win32":
    ctypes.windll.winmm.timeBeginPeriod(1)

HERE = Path(__file__).resolve().parent
HOVER_ROOT = LAB_ROOT / "hover3dof"
PD_ROOT = HOVER_ROOT / "pd_cmg_focused_final_round_2026-08-28"
ACC_ROOT = ROOT
NENGO_REFERENCE_ROOT = NENGO_NEF
sys.path.insert(0, str(PD_ROOT / "src"))
sys.path.insert(0, str(ACC_ROOT / "src"))
sys.path.insert(0, str(NENGO_REFERENCE_ROOT))

from nengo_cmg import NengoCMGPESAugmentor  # noqa: E402
from nengo_neuron_family import NengoNeuronFamilyAugmentor  # noqa: E402
from pd_baseline import (  # noqa: E402
    VendorPlant,
    allocate_stability_priority_torque,
    euler_rates_ypr_to_body_omega_ypr,
    limit_and_slew_motor_residual,
    mujoco_pd_parameters_ypr,
    mujoco_pes_target_ypr,
    mujoco_quaternion_pd_torque_ypr,
    realized_torque,
    torque_to_motor_differential,
)
from gra_control.math3d import (  # noqa: E402
    euler_to_quat,
    quat_angle,
    quat_error,
    reference_euler,
)


PLANT = VendorPlant()
HARDWARE_DT = 0.005
NEURAL_DT = 0.0005
NEURAL_SUBSTEPS = 10
GUI_DT = 0.02
K_AMP = 3.0
V_MAX_DAC = 10.0
K_EC_PITCH = 2.0 * np.pi / (8 * 1024)
K_EC_ROLL = 2.0 * np.pi / (8 * 1024)
K_EC_YAW = -2.0 * np.pi / (8 * 1024)
WCF = 2.0 * np.pi * 20.0
ZETAF = 0.8
CHANNELS = ("Vf", "Vb", "Vl", "Vr")
AXES = ("yaw", "pitch", "roll")
FAMILY_CONTROLLERS = tuple(
    f"nengo-{family}-{mode}"
    for family in ("cmg", "lif", "alif", "izhikevich", "lifrate")
    for mode in ("fixed", "pes")
)
SUPPORTED_CONTROLLERS = ("pd", "nengo-pes", "nengo-nef-pes", *FAMILY_CONTROLLERS)
HARDSTEP_TARGETS_RPY = np.array(
    [
        [0.75, -0.45, 0.55],
        [-0.65, 0.55, -0.70],
        [0.50, 0.50, 0.90],
        [-0.80, -0.35, 0.20],
    ]
)


def _env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, "1" if default else "0") == "1"


def _env_optional_float(name: str) -> float | None:
    value = os.environ.get(name, "").strip()
    return None if not value else float(value)


@dataclass(frozen=True)
class RunConfig:
    io_mode: str = os.environ.get("HOVER_NENGO_IO", "emulated")
    armed: bool = _env_bool("HOVER_NENGO_ARMED")
    confirm_hardware_review: bool = _env_bool("HOVER_NENGO_CONFIRMED")
    controller: str = os.environ.get("HOVER_NENGO_CONTROLLER", "pd")
    mission: str = os.environ.get("HOVER_NENGO_MISSION", "hover")
    duration: float = float(os.environ.get("HOVER_NENGO_DURATION", "5"))
    stop_after: float | None = _env_optional_float("HOVER_NENGO_STOP_AFTER")
    reference_scale: float = float(os.environ.get("HOVER_NENGO_REFERENCE_SCALE", "1"))
    hardstep_transition_s: float = float(os.environ.get("HOVER_NENGO_HARDSTEP_TRANSITION", "0"))
    beta: float = float(os.environ.get("HOVER_NENGO_BETA", "0.5"))
    motor_residual_cap_volts: float = float(os.environ.get("HOVER_NENGO_MOTOR_CAP", "0.3"))
    learning_rate: float = float(os.environ.get("HOVER_NENGO_LEARNING_RATE", "0.0008"))
    k_error: float = float(os.environ.get("HOVER_NENGO_K_ERROR", "8"))
    k_rate: float = float(os.environ.get("HOVER_NENGO_K_RATE", "0"))
    residual_slew_v_per_s: float = float(os.environ.get("HOVER_NENGO_RESIDUAL_SLEW", "4"))
    allocation_policy: str = os.environ.get("HOVER_NENGO_ALLOCATION", "fixed-bias")
    motor_floor_volts: float = float(os.environ.get("HOVER_NENGO_MOTOR_FLOOR", "2"))
    max_abs_pitch_deg: float = float(os.environ.get("HOVER_NENGO_MAX_PITCH", "55"))
    max_abs_roll_deg: float = float(os.environ.get("HOVER_NENGO_MAX_ROLL", "55"))
    expected_raw_home_yaw_deg: float | None = _env_optional_float("HOVER_NENGO_EXPECTED_HOME_YAW")
    raw_home_yaw_tolerance_deg: float = float(os.environ.get("HOVER_NENGO_HOME_TOLERANCE", "5"))
    max_encoder_step_deg: float = float(os.environ.get("HOVER_NENGO_MAX_ENCODER_STEP_DEG", "5"))
    max_consecutive_deadline_misses: int = int(os.environ.get("HOVER_NENGO_MAX_MISSES", "20"))
    gui_heartbeat_timeout_s: float = float(os.environ.get("HOVER_NENGO_HEARTBEAT_TIMEOUT", "0.5"))
    disturbance: str = os.environ.get("HOVER_NENGO_DISTURBANCE", "none")
    disturbance_scale: float = float(os.environ.get("HOVER_NENGO_DISTURBANCE_SCALE", "1"))
    emulation_realtime: bool = _env_bool("HOVER_NENGO_EMULATION_REALTIME", True)
    output_root: str = os.environ.get("HOVER_NENGO_OUTPUT_ROOT", str(HERE / "results" / "hardware"))

    @property
    def run_duration(self) -> float:
        return self.duration if self.stop_after is None else self.stop_after

    def validate(self) -> None:
        if self.io_mode not in ("emulated", "q8"):
            raise ValueError("io_mode must be emulated or q8")
        if self.controller not in SUPPORTED_CONTROLLERS:
            raise ValueError(f"unsupported controller: {self.controller}")
        if self.mission not in ("hover", "roll", "full3", "hard45", "hardstep", "yaw360"):
            raise ValueError(f"unsupported mission: {self.mission}")
        duration_limit = 60.0 if self.mission == "yaw360" else 30.0
        if not 0.0 < self.duration <= duration_limit:
            raise ValueError(f"duration must be in (0,{duration_limit:g}]")
        if self.stop_after is not None and not 0.0 < self.stop_after <= self.duration:
            raise ValueError("stop_after must be in (0,duration]")
        if self.armed and self.io_mode != "q8":
            raise ValueError("armed output is valid only with io_mode=q8")
        if self.armed and not self.confirm_hardware_review:
            raise ValueError("armed output requires confirm_hardware_review")
        if self.armed and self.controller not in ("pd", "nengo-pes"):
            raise ValueError(
                "only the qualified pd and nengo-pes controllers may drive Q8 outputs; "
                "neuron-family benchmarks are emulation/shadow only"
            )
        if not 0.0 <= self.beta <= 1.0:
            raise ValueError("beta must be in [0,1]")
        if self.motor_residual_cap_volts <= 0.0:
            raise ValueError("motor residual cap must be positive")
        if not 0.0 < self.reference_scale <= 1.0:
            raise ValueError("reference_scale must be in (0,1]")
        if not 0.0 <= self.hardstep_transition_s < 2.0:
            raise ValueError("hardstep transition must be in [0,2)")
        if self.mission != "hardstep" and self.hardstep_transition_s != 0.0:
            raise ValueError("hardstep transition is valid only for hardstep")
        if self.allocation_policy not in ("fixed-bias", "stability-priority"):
            raise ValueError("invalid allocation policy")
        if self.disturbance not in ("none", "hard-pulses"):
            raise ValueError("disturbance must be none or hard-pulses")
        if self.disturbance != "none" and self.io_mode != "emulated":
            raise ValueError("software torque disturbances are valid only in emulated mode")
        if self.disturbance_scale < 0.0:
            raise ValueError("disturbance_scale must be nonnegative")
        if not PLANT.minimum_voltage <= self.motor_floor_volts < PLANT.maximum_voltage:
            raise ValueError("motor floor must be inside [0,24)")
        if self.max_encoder_step_deg <= 0.0:
            raise ValueError("max_encoder_step_deg must be positive")


CFG = RunConfig()
CFG.validate()
_, _, CMG_TORQUE_LIMITS = mujoco_pd_parameters_ypr(PLANT)


def experiment_reference_euler(t: float) -> np.ndarray:
    if CFG.mission != "hardstep" or CFG.hardstep_transition_s <= 0.0:
        return CFG.reference_scale * reference_euler(t, CFG.mission, CFG.duration)
    if t < 1.0:
        return np.zeros(3)
    phase_number = int((t - 1.0) // 2.0)
    phase = phase_number % len(HARDSTEP_TARGETS_RPY)
    current = HARDSTEP_TARGETS_RPY[phase]
    previous = (
        np.zeros(3)
        if phase_number == 0
        else HARDSTEP_TARGETS_RPY[(phase - 1) % len(HARDSTEP_TARGETS_RPY)]
    )
    phase_start = 1.0 + 2.0 * phase_number
    fraction = np.clip((t - phase_start) / CFG.hardstep_transition_s, 0.0, 1.0)
    smooth = fraction * fraction * (3.0 - 2.0 * fraction)
    return CFG.reference_scale * ((1.0 - smooth) * previous + smooth * current)


def experiment_disturbance_torque(t: float) -> np.ndarray:
    """Deterministic hard pulse train in yaw/pitch/roll torque coordinates."""
    if CFG.disturbance == "none":
        return np.zeros(3)
    events = (
        (4.0, 0.25, np.array([0.80, 0.00, 0.00])),
        (9.0, 0.25, np.array([0.00, 0.80, 0.00])),
        (14.0, 0.25, np.array([0.00, 0.00, 0.80])),
        (19.0, 0.35, np.array([-0.60, 0.55, -0.55])),
    )
    normalized = np.zeros(3)
    for start, width, vector in events:
        if start <= t < start + width:
            normalized += vector
    return CFG.disturbance_scale * CMG_TORQUE_LIMITS * normalized


class RateFilter:
    def __init__(self) -> None:
        self.x1 = np.zeros(3)
        self.x2 = np.zeros(3)

    def step(self, angle: np.ndarray) -> np.ndarray:
        x1_dot = self.x2
        x2_dot = -WCF * WCF * self.x1 - 2.0 * ZETAF * WCF * self.x2 + angle
        self.x1 += HARDWARE_DT * x1_dot
        self.x2 += HARDWARE_DT * x2_dot
        return WCF * WCF * self.x2


def build_augmentor(controller: str):
    """Build the requested 2-kHz Nengo residual without changing the plant path."""
    if controller == "pd":
        return None
    if controller in ("nengo-pes", "nengo-nef-pes"):
        return NengoCMGPESAugmentor(
            channels=3,
            limits=CMG_TORQUE_LIMITS,
            dt=NEURAL_DT,
            beta=CFG.beta,
            learning_rate=CFG.learning_rate,
            adaptive_conductance=True,
        )
    _, family, mode = controller.split("-", 2)
    calibration = json.loads(
        (NENGO_REFERENCE_ROOT / "feature_calibration.json").read_text(encoding="utf-8")
    )
    item = calibration["families"][family]
    return NengoNeuronFamilyAugmentor(
        family=family,
        limits=CMG_TORQUE_LIMITS,
        dt=NEURAL_DT,
        beta=CFG.beta,
        mode=mode,
        learning_rate=CFG.learning_rate,
        feature_tau=calibration["feature_tau_s"],
        feature_scale=item["feature_scale"],
        native_current_scale=item.get("native_current_scale", 1.0),
        seed=1,
    )


def normalized_neural_diagnostics(augmentor, diagnostics: dict) -> dict:
    """Map every neuron family into a lossless common telemetry schema."""
    z6 = np.zeros(6)
    states = diagnostics.get("states", {})
    voltage = diagnostics.get("voltage", states.get("voltage", z6))
    gate = diagnostics.get("gate")
    if gate is None:
        gate = states.get(
            "adaptation",
            states.get("recovery", states.get("refractory_time", z6)),
        )
    is_cmg = getattr(augmentor, "family", "cmg") == "cmg"
    payload = {
        "current": diagnostics["current"],
        "voltage": voltage,
        "gate": gate,
        "activity": diagnostics["activity"],
        "raw_output": diagnostics.get("raw_output", diagnostics["activity"]),
        "native_voltage": states.get("voltage", voltage),
        "native_refractory_time": states.get("refractory_time", z6),
        "native_adaptation": states.get("adaptation", z6),
        "native_recovery": states.get("recovery", z6),
        "effective_threshold": diagnostics.get("effective_threshold", z6),
        "gate_argument": diagnostics.get("gate_argument", z6),
        "gate_target": diagnostics.get("gate_target", z6),
        "conductance_gain": diagnostics.get("conductance_gain", z6),
        "conductance": diagnostics.get("conductance", z6),
        "membrane_lambda": diagnostics.get("membrane_lambda", z6),
        "membrane_drive": diagnostics.get("membrane_drive", z6),
        "decoded_raw": diagnostics["decoded_raw"],
        "decoded_clipped": diagnostics["decoded_clipped"],
        "pes_error": diagnostics["pes_error"],
        "weights": diagnostics["weights"],
        "is_cmg": is_cmg,
    }
    return {name: np.asarray(value, dtype=float).copy() if name != "is_cmg" else value for name, value in payload.items()}


class LiveSnapshot:
    """Thread-safe numerical state exposed to the read-only GUI Nodes."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.data = {
            "tracking": np.zeros(6),             # measured ypr, reference ypr [deg]
            "error": np.zeros(4),                # ypr error [deg], q error [rad]
            "rates": np.zeros(3),                # ypr rates [deg/s]
            "torque": np.zeros(9),               # PD, requested residual, realized residual
            "motors": np.zeros(12),              # baseline, computed, written [V]
            "currents": np.zeros(6),
            "voltage": np.zeros(6),
            "gate": np.zeros(6),
            "activity": np.zeros(6),
            "decoder_norms": np.linalg.norm(np.c_[np.eye(3), -np.eye(3)], axis=1),
            "decoder": np.zeros(6),              # raw decoder, clipped decoder
            "weight_update_norms": np.zeros(3),
            "gate_target": np.zeros(6),
            "conductance": np.zeros(6),
            "pes": np.zeros(6),                  # target, PES error
            "allocator": np.zeros(3),            # yaw scale, pitch/roll scale, common mode
            "disturbance": np.zeros(3),          # injected emulated yaw/pitch/roll torque
            "status": np.zeros(8),               # progress, armed, q8, running, complete, abort, miss, heartbeat age
        }
        self.text_status = "created"

    def get(self, name: str) -> np.ndarray:
        with self.lock:
            return self.data[name].copy()

    def update(self, **values) -> None:
        with self.lock:
            for name, value in values.items():
                if name == "text_status":
                    self.text_status = str(value)
                else:
                    self.data[name][...] = np.asarray(value, dtype=float)


LIVE = LiveSnapshot()


class HoverWorker:
    """Dedicated 200 Hz controller/Q8 thread; GUI rendering never runs here."""

    def __init__(self) -> None:
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.heartbeat_wall = time.perf_counter()
        self.card = None
        self.ao_channels = arr.array("i", [0, 1, 2, 3])
        self.encoder_channels = arr.array("i", [0, 1, 2])
        self.counts = arr.array("i", [0, 0, 0])
        self.zero = arr.array("d", [0.0] * 4)
        self.io_lock = threading.Lock()
        self.output_dir: Path | None = None
        self.abort_reason = ""
        self.started_once = False
        self._emulated_angles = np.zeros(3)
        self._emulated_rates = np.zeros(3)

    def heartbeat(self) -> None:
        self.heartbeat_wall = time.perf_counter()

    def start(self) -> None:
        if self.thread is not None and self.thread.is_alive():
            return
        if self.started_once:
            print("Hardware worker restart suppressed: this GUI process is single-run by design.")
            return
        self.started_once = True
        self.stop_event.clear()
        self.heartbeat()
        self.thread = threading.Thread(target=self._run_guarded, name="hover-q8-200hz", daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=2.0)
        if self.thread is not None and self.thread.is_alive() and self.card is not None:
            try:
                with self.io_lock:
                    self.card.write_analog(self.ao_channels, 4, self.zero)
            except Exception:
                pass

    def _open_q8(self) -> np.ndarray:
        from quanser.hardware import HIL

        self.card = HIL()
        self.card.open("q8_usb", "0")
        with self.io_lock:
            self.card.write_analog(self.ao_channels, 4, self.zero)
        return self._read_q8_angles()

    def _read_q8_angles(self) -> np.ndarray:
        with self.io_lock:
            self.card.read_encoder(self.encoder_channels, 3, self.counts)
        return np.array(
            [
                self.counts[2] * K_EC_YAW,
                self.counts[0] * K_EC_PITCH,
                self.counts[1] * K_EC_ROLL,
            ]
        )

    def _write_q8(self, motor_volts: np.ndarray) -> None:
        dac = np.clip(np.asarray(motor_volts) / K_AMP, 0.0, V_MAX_DAC)
        with self.io_lock:
            self.card.write_analog(self.ao_channels, 4, arr.array("d", dac.tolist()))

    def _step_emulated(self, motor_volts: np.ndarray, disturbance_tau: np.ndarray) -> None:
        torque = realized_torque(motor_volts, PLANT) + disturbance_tau
        damping = np.array([0.035, 0.055, 0.055])
        acceleration = (torque - damping * self._emulated_rates) / PLANT.inertia
        self._emulated_rates += HARDWARE_DT * acceleration
        self._emulated_angles += HARDWARE_DT * self._emulated_rates

    @staticmethod
    def _dependency_hash(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest().upper()

    def _run_guarded(self) -> None:
        try:
            self._run()
        except Exception as exc:
            if not self.abort_reason:
                self.abort_reason = f"{type(exc).__name__}: {exc}"
            LIVE.update(text_status=f"ABORT: {self.abort_reason}")
            print(f"ABORT: {self.abort_reason}\n{traceback.format_exc()}")

    def _run(self) -> None:
        rows: list[dict] = []
        neural_log: dict[str, list] = {
            name: []
            for name in (
                "t",
                "hardware_step",
                "substep",
                "baseline_tau_ypr",
                "target_ypr",
                "current",
                "voltage",
                "gate",
                "activity",
                "raw_output",
                "native_voltage",
                "native_refractory_time",
                "native_adaptation",
                "native_recovery",
                "effective_threshold",
                "gate_argument",
                "gate_target",
                "conductance_gain",
                "conductance",
                "membrane_lambda",
                "membrane_drive",
                "decoded_raw",
                "decoded_clipped",
                "pes_error",
                "weights",
                "weight_delta",
                "residual_torque_ypr",
                "disturbance_torque_ypr",
            )
        }
        completed = False
        augmentor = None
        raw_home = np.zeros(3)
        previous_motor_residual = np.zeros(4)
        rate_filter = RateFilter()
        previous_raw_angles: np.ndarray | None = None
        consecutive_misses = 0
        n_steps = int(round(CFG.run_duration / HARDWARE_DT))

        # Build the Nengo decoder before opening Q8, so initialization latency
        # can never occur while nonzero physical output is possible.
        augmentor = build_augmentor(CFG.controller)

        try:
            if CFG.io_mode == "q8":
                raw_home = self._open_q8()
                raw_home_deg = np.rad2deg(raw_home)
                if CFG.expected_raw_home_yaw_deg is not None:
                    mismatch = raw_home_deg[0] - CFG.expected_raw_home_yaw_deg
                    if abs(mismatch) > CFG.raw_home_yaw_tolerance_deg:
                        raise RuntimeError(
                            f"raw yaw home {raw_home_deg[0]:.3f} deg differs from expected "
                            f"{CFG.expected_raw_home_yaw_deg:.3f} deg by {mismatch:+.3f} deg"
                        )
            else:
                raw_home_deg = np.zeros(3)

            print(f"Tared at startup: raw home={raw_home_deg} deg; io={CFG.io_mode}")
            print(
                f"controller={CFG.controller} armed={CFG.armed} mission={CFG.mission} "
                f"run={CFG.run_duration:g}s reference={CFG.duration:g}s; "
                f"hardware=200Hz neural=2000Hz; beta={CFG.beta:g} cap={CFG.motor_residual_cap_volts:g}V"
            )
            LIVE.update(text_status="running")
            session_start = time.perf_counter()

            for k in range(n_steps):
                loop_start = time.perf_counter()
                if self.stop_event.is_set():
                    self.abort_reason = "GUI/server stop requested"
                    break
                heartbeat_age = loop_start - self.heartbeat_wall
                if CFG.armed and heartbeat_age > CFG.gui_heartbeat_timeout_s:
                    self.abort_reason = (
                        f"GUI heartbeat lost for {heartbeat_age:.3f}s "
                        f"> {CFG.gui_heartbeat_timeout_s:.3f}s"
                    )
                    raise RuntimeError(self.abort_reason)

                t = k * HARDWARE_DT
                if CFG.io_mode == "q8":
                    raw_angles = self._read_q8_angles()
                    if previous_raw_angles is not None:
                        encoder_step_deg = np.abs(np.rad2deg(raw_angles - previous_raw_angles))
                        if np.any(encoder_step_deg > CFG.max_encoder_step_deg):
                            axes = ", ".join(
                                f"{AXES[i]}={encoder_step_deg[i]:.3f} deg"
                                for i in np.flatnonzero(encoder_step_deg > CFG.max_encoder_step_deg)
                            )
                            self.abort_reason = (
                                f"implausible encoder step ({axes}) exceeds "
                                f"{CFG.max_encoder_step_deg:.3f} deg/sample"
                            )
                            raise RuntimeError(self.abort_reason)
                    previous_raw_angles = raw_angles.copy()
                    angles = raw_angles - raw_home
                else:
                    angles = self._emulated_angles.copy()
                rates = rate_filter.step(angles)
                pitch_deg = float(np.rad2deg(angles[1]))
                roll_deg = float(np.rad2deg(angles[2]))
                if abs(pitch_deg) > CFG.max_abs_pitch_deg:
                    self.abort_reason = f"pitch safety limit exceeded: {pitch_deg:.3f} deg"
                    raise RuntimeError(self.abort_reason)
                if abs(roll_deg) > CFG.max_abs_roll_deg:
                    self.abort_reason = f"roll safety limit exceeded: {roll_deg:.3f} deg"
                    raise RuntimeError(self.abort_reason)

                ref_rpy = experiment_reference_euler(t)
                setpoint = np.array([ref_rpy[2], ref_rpy[1], ref_rpy[0]])
                error_ypr = setpoint - angles
                error_ypr[0] = np.arctan2(np.sin(error_ypr[0]), np.cos(error_ypr[0]))
                q_ref = euler_to_quat(*ref_rpy)
                q_meas = euler_to_quat(angles[2], angles[1], angles[0])
                qe, eq_xyz = quat_error(q_ref, q_meas)
                eq_ypr = eq_xyz[[2, 1, 0]]
                body_omega_ypr = euler_rates_ypr_to_body_omega_ypr(angles, rates)
                tau0 = mujoco_quaternion_pd_torque_ypr(eq_ypr, body_omega_ypr, PLANT)
                baseline_raw = PLANT.bias_voltage + torque_to_motor_differential(tau0, PLANT)
                baseline_clipped = np.clip(baseline_raw, PLANT.minimum_voltage, PLANT.maximum_voltage)

                requested_delta_tau = np.zeros(3)
                requested_delta_v = np.zeros(4)
                applied_delta_v = np.zeros(4)
                target = np.zeros(3)
                neuron_v = np.zeros(6)
                neuron_r = np.zeros(6)
                activity = np.zeros(6)
                currents = np.zeros(6)
                weights = np.c_[np.eye(3), -np.eye(3)]
                decoded_raw = np.zeros(3)
                decoded_clipped = np.zeros(3)
                weight_update = np.zeros((3, 6))
                pes_error = np.zeros(3)
                gate_target = np.zeros(6)
                effective_threshold = np.ones(6)
                gate_argument = np.zeros(6)
                conductance_gain = np.zeros(6)
                conductance = np.zeros(6)
                membrane_lambda = np.zeros(6)
                membrane_drive = np.zeros(6)

                if augmentor is not None:
                    target = mujoco_pes_target_ypr(
                        eq_ypr, body_omega_ypr, CFG.k_error, CFG.k_rate
                    )
                    out = None
                    weights_hardware_start = augmentor.W
                    for substep in range(NEURAL_SUBSTEPS):
                        weights_before = augmentor.W
                        out = augmentor.step(tau0, target)
                        diagnostics = normalized_neural_diagnostics(
                            augmentor, augmentor.diagnostics()
                        )
                        neural_log["t"].append(t + (substep + 1) * NEURAL_DT)
                        neural_log["hardware_step"].append(k)
                        neural_log["substep"].append(substep)
                        neural_log["baseline_tau_ypr"].append(tau0.copy())
                        neural_log["target_ypr"].append(target.copy())
                        for name in (
                            "current",
                            "voltage",
                            "gate",
                            "activity",
                            "raw_output",
                            "native_voltage",
                            "native_refractory_time",
                            "native_adaptation",
                            "native_recovery",
                            "effective_threshold",
                            "gate_argument",
                            "gate_target",
                            "conductance_gain",
                            "conductance",
                            "membrane_lambda",
                            "membrane_drive",
                            "decoded_raw",
                            "decoded_clipped",
                            "pes_error",
                            "weights",
                        ):
                            neural_log[name].append(diagnostics[name].copy())
                        neural_log["weight_delta"].append(
                            diagnostics["weights"] - weights_before
                        )
                        neural_log["residual_torque_ypr"].append(out.residual.copy())
                        neural_log["disturbance_torque_ypr"].append(
                            experiment_disturbance_torque(t).copy()
                        )
                    requested_delta_tau = out.residual.copy()
                    requested_delta_v = torque_to_motor_differential(requested_delta_tau, PLANT)
                    applied_delta_v = limit_and_slew_motor_residual(
                        requested_delta_v,
                        previous_motor_residual,
                        CFG.motor_residual_cap_volts,
                        CFG.residual_slew_v_per_s,
                        HARDWARE_DT,
                    )
                    previous_motor_residual = applied_delta_v.copy()
                    neuron_v = diagnostics["voltage"]
                    neuron_r = diagnostics["gate"]
                    activity = diagnostics["activity"]
                    weights = diagnostics["weights"]
                    weight_update = weights - weights_hardware_start
                    pes_error = diagnostics["pes_error"]
                    currents = diagnostics["current"]
                    decoded_raw = diagnostics["decoded_raw"]
                    decoded_clipped = diagnostics["decoded_clipped"]
                    gate_target = diagnostics["gate_target"]
                    effective_threshold = diagnostics["effective_threshold"]
                    gate_argument = diagnostics["gate_argument"]
                    conductance_gain = diagnostics["conductance_gain"]
                    conductance = diagnostics["conductance"]
                    membrane_lambda = diagnostics["membrane_lambda"]
                    membrane_drive = diagnostics["membrane_drive"]

                requested_total_tau = tau0 + realized_torque(applied_delta_v, PLANT)
                disturbance_tau = experiment_disturbance_torque(t)
                command_preclip = baseline_raw + applied_delta_v
                if CFG.allocation_policy == "stability-priority":
                    base_alloc = allocate_stability_priority_torque(
                        tau0, PLANT, CFG.motor_floor_volts
                    )
                    total_alloc = allocate_stability_priority_torque(
                        requested_total_tau, PLANT, CFG.motor_floor_volts
                    )
                    baseline_clipped = base_alloc.voltage_fblr
                    command_computed = total_alloc.voltage_fblr
                    realized_baseline_tau = base_alloc.realized_torque_ypr
                    realized_command_tau = total_alloc.realized_torque_ypr
                    allocator = np.array(
                        [total_alloc.yaw_scale, total_alloc.pitch_roll_scale, total_alloc.common_mode_voltage]
                    )
                else:
                    command_computed = np.clip(
                        command_preclip, PLANT.minimum_voltage, PLANT.maximum_voltage
                    )
                    realized_baseline_tau = realized_torque(baseline_clipped, PLANT)
                    realized_command_tau = realized_torque(command_computed, PLANT)
                    # Fixed-bias has no priority scaling operation; expose unity
                    # rather than NaN because Nengo Nodes require finite output.
                    allocator = np.array([1.0, 1.0, PLANT.bias_voltage])
                realized_delta_tau = realized_command_tau - realized_baseline_tau

                if CFG.io_mode == "q8":
                    command_written = command_computed if CFG.armed else np.zeros(4)
                    self._write_q8(command_written)
                else:
                    command_written = command_computed.copy()
                    self._step_emulated(command_written, disturbance_tau)

                compute_elapsed = time.perf_counter() - loop_start
                deadline_miss = compute_elapsed > HARDWARE_DT
                consecutive_misses = consecutive_misses + 1 if deadline_miss else 0
                if (
                    consecutive_misses >= CFG.max_consecutive_deadline_misses
                    and (CFG.io_mode == "q8" or CFG.emulation_realtime)
                ):
                    self.abort_reason = f"{consecutive_misses} consecutive 200-Hz deadline misses"
                    raise RuntimeError(self.abort_reason)

                progress = min((k + 1) / max(n_steps, 1), 1.0)
                LIVE.update(
                    tracking=np.r_[np.rad2deg(angles), np.rad2deg(setpoint)],
                    error=np.r_[np.rad2deg(error_ypr), quat_angle(qe)],
                    rates=np.rad2deg(rates),
                    torque=np.r_[tau0, requested_delta_tau, realized_delta_tau],
                    motors=np.r_[baseline_clipped, command_computed, command_written],
                    currents=currents,
                    voltage=neuron_v,
                    gate=neuron_r,
                    activity=activity,
                    decoder_norms=np.linalg.norm(weights, axis=1),
                    decoder=np.r_[decoded_raw, decoded_clipped],
                    weight_update_norms=np.linalg.norm(weight_update, axis=1),
                    gate_target=gate_target,
                    conductance=conductance,
                    pes=np.r_[target, pes_error],
                    allocator=allocator,
                    disturbance=disturbance_tau,
                    status=np.array(
                        [progress, CFG.armed, CFG.io_mode == "q8", 1, 0, 0, deadline_miss, heartbeat_age]
                    ),
                )

                row = {
                    "t": t,
                    "wall_t": loop_start - session_start,
                    "yaw_deg": np.rad2deg(angles[0]),
                    "pitch_deg": pitch_deg,
                    "roll_deg": roll_deg,
                    "yaw_ref_deg": np.rad2deg(setpoint[0]),
                    "pitch_ref_deg": np.rad2deg(setpoint[1]),
                    "roll_ref_deg": np.rad2deg(setpoint[2]),
                    "yaw_error_wrapped_deg": np.rad2deg(error_ypr[0]),
                    "pitch_error_deg": np.rad2deg(error_ypr[1]),
                    "roll_error_deg": np.rad2deg(error_ypr[2]),
                    "qerr_rad": quat_angle(qe),
                    "loop_elapsed_s": compute_elapsed,
                    "deadline_miss": int(deadline_miss),
                    "allocator_yaw_scale": allocator[0],
                    "allocator_pitch_roll_scale": allocator[1],
                    "allocator_common_mode_V": allocator[2],
                    "disturbance_yaw_Nm": disturbance_tau[0],
                    "disturbance_pitch_Nm": disturbance_tau[1],
                    "disturbance_roll_Nm": disturbance_tau[2],
                }
                for i, axis in enumerate(AXES):
                    row[f"tau0_{axis}"] = tau0[i]
                    row[f"requested_delta_tau_{axis}"] = requested_delta_tau[i]
                    row[f"realized_delta_tau_{axis}"] = realized_delta_tau[i]
                    row[f"learning_target_{axis}"] = target[i]
                    row[f"pes_error_{axis}"] = pes_error[i]
                for i, channel in enumerate(CHANNELS):
                    row[f"{channel}_baseline"] = baseline_clipped[i]
                    row[f"{channel}_computed"] = command_computed[i]
                    row[f"{channel}_written"] = command_written[i]
                    row[f"{channel}_delta_requested"] = requested_delta_v[i]
                    row[f"{channel}_delta_applied"] = applied_delta_v[i]
                for i in range(6):
                    row[f"neuron_v_{i}"] = neuron_v[i]
                    row[f"neuron_r_{i}"] = neuron_r[i]
                    row[f"neuron_activity_{i}"] = activity[i]
                    row[f"neuron_current_{i}"] = currents[i]
                    row[f"neuron_gate_target_{i}"] = gate_target[i]
                    row[f"neuron_effective_threshold_{i}"] = effective_threshold[i]
                    row[f"neuron_gate_argument_{i}"] = gate_argument[i]
                    row[f"neuron_conductance_gain_{i}"] = conductance_gain[i]
                    row[f"neuron_conductance_{i}"] = conductance[i]
                    row[f"neuron_membrane_lambda_{i}"] = membrane_lambda[i]
                    row[f"neuron_membrane_drive_{i}"] = membrane_drive[i]
                for i, weight in enumerate(weights.ravel()):
                    row[f"decoder_w_{i}"] = weight
                    row[f"decoder_dw_hardware_{i}"] = weight_update.ravel()[i]
                for i, axis in enumerate(AXES):
                    row[f"decoder_raw_{axis}"] = decoded_raw[i]
                    row[f"decoder_clipped_{axis}"] = decoded_clipped[i]
                    row[f"decoder_update_norm_{axis}"] = np.linalg.norm(weight_update[i])
                    row[f"quaternion_error_vector_{axis}"] = eq_ypr[i]
                    row[f"body_omega_{axis}_rad_s"] = body_omega_ypr[i]
                for i, name in enumerate(("w", "x", "y", "z")):
                    row[f"q_ref_{name}"] = q_ref[i]
                    row[f"q_meas_{name}"] = q_meas[i]
                    row[f"q_error_{name}"] = qe[i]
                row["raw_encoder_count_pitch"] = self.counts[0] if CFG.io_mode == "q8" else 0
                row["raw_encoder_count_roll"] = self.counts[1] if CFG.io_mode == "q8" else 0
                row["raw_encoder_count_yaw"] = self.counts[2] if CFG.io_mode == "q8" else 0
                for i, channel in enumerate(CHANNELS):
                    row[f"{channel}_dac_written"] = (
                        np.clip(command_written[i] / K_AMP, 0.0, V_MAX_DAC)
                        if CFG.io_mode == "q8"
                        else 0.0
                    )
                rows.append(row)

                if k % 200 == 0:
                    print(
                        f"t={t:5.2f}s ypr={np.round(np.rad2deg(angles),2)} "
                        f"V={np.round(command_computed,2)} residual={np.round(applied_delta_v,3)} "
                        f"gate={np.mean(neuron_r):.3f}"
                    )
                remaining = session_start + (k + 1) * HARDWARE_DT - time.perf_counter()
                if remaining > 0.0 and (CFG.io_mode == "q8" or CFG.emulation_realtime):
                    time.sleep(remaining)

            completed = not self.abort_reason and not self.stop_event.is_set() and len(rows) == n_steps
        finally:
            if self.card is not None:
                try:
                    self._write_q8(np.zeros(4))
                finally:
                    self.card.close()
                    self.card = None
                print("All four Q8 analog outputs forced to zero. Card closed.")
            if augmentor is not None:
                augmentor.close()
            self._save(rows, raw_home, completed, neural_log)
            LIVE.update(
                status=np.array(
                    [
                        len(rows) / max(n_steps, 1),
                        CFG.armed,
                        CFG.io_mode == "q8",
                        0,
                        completed,
                        bool(self.abort_reason),
                        0,
                        time.perf_counter() - self.heartbeat_wall,
                    ]
                ),
                text_status="complete" if completed else f"stopped: {self.abort_reason}",
            )

    def _save(
        self,
        rows: list[dict],
        raw_home: np.ndarray,
        completed: bool,
        neural_log: dict[str, list],
    ) -> None:
        if not rows:
            return
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        mode = "armed" if CFG.armed else ("q8-dryrun" if CFG.io_mode == "q8" else "emulated")
        disturbance_label = CFG.disturbance.replace("-", "")
        self.output_dir = Path(CFG.output_root) / (
            f"{CFG.controller}_{CFG.mission}_{disturbance_label}_{mode}_{timestamp}"
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)
        trace_path = self.output_dir / "trace.csv"
        with trace_path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        neural_path = None
        neural_schema_path = None
        if neural_log["t"]:
            neural_path = self.output_dir / "neural_trace_2khz.npz"
            np.savez_compressed(
                neural_path,
                **{name: np.asarray(values) for name, values in neural_log.items()},
            )
            neural_schema_path = self.output_dir / "neural_trace_schema.json"
            neural_schema = {
                "format": "NumPy compressed archive",
                "sample_rate_hz": 1.0 / NEURAL_DT,
                "axis_order": ["yaw", "pitch", "roll"],
                "unit_order": ["+yaw", "+pitch", "+roll", "-yaw", "-pitch", "-roll"],
                "weight_shape": [3, 6],
                "controller": CFG.controller,
                "neuron_family": (
                    "cmg"
                    if CFG.controller in ("nengo-pes", "nengo-nef-pes")
                    else (CFG.controller.split("-", 2)[1] if CFG.controller.startswith("nengo-") else None)
                ),
                "decoder_mode": (
                    "pes"
                    if CFG.controller in ("nengo-pes", "nengo-nef-pes")
                    else (CFG.controller.split("-", 2)[2] if CFG.controller.startswith("nengo-") else None)
                ),
                "signals": {
                    name: {
                        "shape": list(np.asarray(values).shape),
                        "dtype": str(np.asarray(values).dtype),
                    }
                    for name, values in neural_log.items()
                },
                "semantics": {
                    "decoded_raw": "unbounded W@a",
                    "decoded_clipped": "clip(W@a,-1,1), used by PES and residual",
                    "weight_delta": "per-0.5-ms Nengo step change after PES and leak",
                    "activity": "CMG gate-derived activity, filtered spikes, or filtered rate according to neuron_family",
                    "raw_output": "native Nengo neuron output before feature normalization/filtering",
                    "native_voltage/refractory_time/adaptation/recovery": "family-native states; absent states are zero-filled and declared by neuron_family",
                    "gate": "CMG gate for CMG; auxiliary native state in the 200-Hz compatibility trace for conventional families",
                    "gate_target": "CMG sigmoid(alpha*(v-effective_threshold)); zero for non-CMG families",
                    "conductance": "CMG conductance_gain*r^2; zero for non-CMG families",
                },
            }
            neural_schema_path.write_text(
                json.dumps(neural_schema, indent=2) + "\n", encoding="utf-8"
            )
        errors = np.array(
            [[row["yaw_error_wrapped_deg"], row["pitch_error_deg"], row["roll_error_deg"]] for row in rows]
        )
        qerror = np.array([row["qerr_rad"] for row in rows])
        summary = {
            "schema": 1,
            "platform": "quanser_3dof_hover_nengo_gui_hil",
            "hardware": CFG.io_mode == "q8",
            "config": asdict(CFG),
            "hardware_rate_hz": 1.0 / HARDWARE_DT,
            "neural_rate_hz": 1.0 / NEURAL_DT,
            "gui_rate_hz": 1.0 / GUI_DT,
            "raw_home_ypr_deg": np.rad2deg(raw_home).tolist(),
            "run_completed": completed,
            "abort_reason": self.abort_reason,
            "n_steps_logged": len(rows),
            "angle_err_mean_deg": float(np.mean(np.linalg.norm(errors, axis=1))),
            "angle_err_max_deg": float(np.max(np.linalg.norm(errors, axis=1))),
            "axis_error_mae_deg": dict(zip(AXES, np.mean(np.abs(errors), axis=0).tolist())),
            "qerr_mean_rad": float(np.mean(qerror)),
            "qerr_max_rad": float(np.max(qerror)),
            "deadline_miss_fraction": float(np.mean([row["deadline_miss"] for row in rows])),
            "neuron_family_metadata": {
                "controller": CFG.controller,
                "family": (
                    "cmg"
                    if CFG.controller in ("nengo-pes", "nengo-nef-pes")
                    else (CFG.controller.split("-", 2)[1] if CFG.controller.startswith("nengo-") else None)
                ),
                "decoder_mode": (
                    "pes"
                    if CFG.controller in ("nengo-pes", "nengo-nef-pes")
                    else (CFG.controller.split("-", 2)[2] if CFG.controller.startswith("nengo-") else None)
                ),
                "hardware_qualified": CFG.controller in ("pd", "nengo-pes"),
            },
            "trace": str(trace_path),
            "neural_trace_2khz": None if neural_path is None else str(neural_path),
            "neural_trace_schema": None if neural_schema_path is None else str(neural_schema_path),
            "neuron_columns": {
                "membrane": "neuron_v_0..5",
                "gate_or_auxiliary_state": "neuron_r_0..5",
                "activity": "neuron_activity_0..5",
                "current": "neuron_current_0..5",
                "decoder": "decoder_w_0..17",
                "derived_dynamics": "neuron_gate_target/effective_threshold/gate_argument/conductance_gain/conductance/membrane_lambda/membrane_drive_0..5",
                "decoder_diagnostics": "decoder_raw/clipped/update_norm and decoder_dw_hardware",
            },
        }
        manifest = {
            "runner": str(Path(__file__).resolve()),
            "dependencies": {
                "pd_baseline.py": {
                    "path": str(PD_ROOT / "src" / "pd_baseline.py"),
                    "sha256": self._dependency_hash(PD_ROOT / "src" / "pd_baseline.py"),
                },
                "nengo_cmg.py": {
                    "path": str(NENGO_REFERENCE_ROOT / "nengo_cmg.py"),
                    "sha256": self._dependency_hash(NENGO_REFERENCE_ROOT / "nengo_cmg.py"),
                },
                "nengo_neuron_family.py": {
                    "path": str(NENGO_REFERENCE_ROOT / "nengo_neuron_family.py"),
                    "sha256": self._dependency_hash(NENGO_REFERENCE_ROOT / "nengo_neuron_family.py"),
                },
                "feature_calibration.json": {
                    "path": str(NENGO_REFERENCE_ROOT / "feature_calibration.json"),
                    "sha256": self._dependency_hash(NENGO_REFERENCE_ROOT / "feature_calibration.json"),
                },
            },
        }
        (self.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        (self.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(
            f"angle_err_mean_deg={summary['angle_err_mean_deg']:.3f} "
            f"angle_err_max_deg={summary['angle_err_max_deg']:.3f} results={self.output_dir}"
        )


WORKER = HoverWorker()

if CFG.controller == "pd":
    GUI_FAMILY = "no neural residual"
elif CFG.controller in ("nengo-pes", "nengo-nef-pes"):
    GUI_FAMILY = "CMG / PES"
else:
    _, _family, _mode = CFG.controller.split("-", 2)
    GUI_FAMILY = f"{_family} / {_mode}"


model = nengo.Network(
    label=(
        f"3DOF Hover | {CFG.controller} | {CFG.io_mode} | {CFG.mission} | "
        f"hardware 200 Hz / neural 2 kHz"
    ),
    seed=1,
)
with model:
    with nengo.Network(label="Dedicated 200 Hz Hover/Q8 worker") as hardware_worker:
        tracking = nengo.Node(lambda t: LIVE.get("tracking"), size_out=6, label="measured/ref ypr [deg]")
        error = nengo.Node(lambda t: LIVE.get("error"), size_out=4, label="ypr errors [deg], q-error [rad]")
        rates = nengo.Node(lambda t: LIVE.get("rates"), size_out=3, label="estimated rates [deg/s]")
        torque = nengo.Node(lambda t: LIVE.get("torque"), size_out=9, label="PD/requested/realized torque [Nm]")
        motors = nengo.Node(lambda t: LIVE.get("motors"), size_out=12, label="baseline/computed/written motors [V]")
        allocator = nengo.Node(lambda t: LIVE.get("allocator"), size_out=3, label="allocator scales/common mode")
        disturbance = nengo.Node(lambda t: LIVE.get("disturbance"), size_out=3, label="injected emulated disturbance torque")
        status = nengo.Node(lambda t: LIVE.get("status"), size_out=8, label="safety and run status")

    with nengo.Network(label=f"Inner Nengo residual population: {GUI_FAMILY}") as neural_worker:
        currents = nengo.Node(lambda t: LIVE.get("currents"), size_out=6, label="paired currents [+y,+p,+r,-y,-p,-r]")
        membrane = nengo.Node(lambda t: LIVE.get("voltage"), size_out=6, label="membrane / native voltage")
        gate = nengo.Node(lambda t: LIVE.get("gate"), size_out=6, label="CMG gate or family auxiliary state")
        activity = nengo.Node(lambda t: LIVE.get("activity"), size_out=6, label="normalized decoder activity a")
        decoder_norms = nengo.Node(lambda t: LIVE.get("decoder_norms"), size_out=3, label="decoder row norms")
        decoder = nengo.Node(lambda t: LIVE.get("decoder"), size_out=6, label="decoder raw/clipped")
        weight_update_norms = nengo.Node(lambda t: LIVE.get("weight_update_norms"), size_out=3, label="PES decoder update norms")
        gate_target = nengo.Node(lambda t: LIVE.get("gate_target"), size_out=6, label="CMG gate target r_inf (zero for other families)")
        conductance = nengo.Node(lambda t: LIVE.get("conductance"), size_out=6, label="CMG conductance (zero for other families)")
        pes = nengo.Node(lambda t: LIVE.get("pes"), size_out=6, label="PES target/error")


_gui_wall_origin = 0.0
_gui_sim_origin = 0.0


def on_start(sim) -> None:
    global _gui_wall_origin, _gui_sim_origin
    _gui_wall_origin = time.perf_counter()
    _gui_sim_origin = float(sim.time)
    WORKER.start()
    print(
        "GUI monitor ready. Hardware worker begins only after the model builds; "
        "closing/pausing the GUI heartbeat aborts an armed run."
    )


def on_step(sim) -> None:
    WORKER.heartbeat()
    target = _gui_wall_origin + (float(sim.time) - _gui_sim_origin)
    remaining = target - time.perf_counter()
    if remaining > 0.0:
        time.sleep(remaining)


def on_close(sim) -> None:
    del sim
    WORKER.stop()
