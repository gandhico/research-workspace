"""Interactive twin-plant GUI for quaternion PD versus Nengo CMG + PES.

This file is loaded by Nengo GUI.  It runs two synchronized MuJoCo plants:

1. the exact quaternion-PD baseline; and
2. the same baseline plus paired CMG activity, a learned 3 x 6 Nengo decoder,
   and Nengo's built-in online PES rule.

Environment variables set by ``launch_gui.py`` select the platform and mission.
The validated batch campaign remains the source of paper metrics; this GUI is a
transparent interactive digital-twin view and introduces one negligible 1 us
synapse on each plant command to break Nengo's algebraic feedback cycle.
"""
from __future__ import annotations

import os
import sys
import time
import warnings
import json
from pathlib import Path

import mujoco
import nengo
import numpy as np

try:
    import mujoco.viewer
except ImportError:  # Headless batch/smoke use does not require the viewer module.
    mujoco.viewer = None


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(HERE))

from gra_control.math3d import (  # noqa: E402
    euler_to_quat,
    quat_angle,
    quat_conj,
    quat_error,
    reference_euler,
    reference_quat,
)
from gra_control.platforms.drone import (  # noqa: E402
    SPECS,
    _free_joint,
    _mixer,
    torque_limits,
)
from nengo_cmg import CoupledMembraneGate  # noqa: E402


DT = 5e-4
PLATFORM = os.environ.get("GRA_GUI_PLATFORM", "x2")
MISSION = os.environ.get("GRA_GUI_MISSION", "hard45")
DURATION = float(os.environ.get("GRA_GUI_DURATION", "45"))
ACTUATOR_SCALE = float(
    os.environ.get("GRA_GUI_ACTUATOR_SCALE", "1.5" if PLATFORM == "cf2-rotor" else "1.0")
)
VIEWER_TARGET = os.environ.get("GRA_GUI_MUJOCO_VIEWER", "none").lower()
REALTIME = os.environ.get("GRA_GUI_REALTIME", "0") == "1"
VIEWER_FPS = float(os.environ.get("GRA_GUI_VIEWER_FPS", "30"))
SAVE_TELEMETRY = os.environ.get("GRA_GUI_SAVE_TELEMETRY", "1") == "1"
MAX_LOG_SECONDS = float(os.environ.get("GRA_GUI_MAX_LOG_SECONDS", str(DURATION)))
TELEMETRY_ROOT = Path(
    os.environ.get("GRA_GUI_TELEMETRY_ROOT", "")
    or (HERE / "results" / "gui_sessions")
)
if PLATFORM not in ("cf2-rotor", "x2"):
    raise ValueError("GRA_GUI_PLATFORM must be 'cf2-rotor' or 'x2'")
if MISSION not in ("hover", "roll", "full3", "hard45", "hardstep", "yaw360"):
    raise ValueError(f"Unsupported GRA_GUI_MISSION: {MISSION}")
if VIEWER_TARGET not in ("none", "neural", "baseline"):
    raise ValueError("GRA_GUI_MUJOCO_VIEWER must be none, neural, or baseline")
if not 1.0 <= VIEWER_FPS <= 120.0:
    raise ValueError("GRA_GUI_VIEWER_FPS must be between 1 and 120")
if MAX_LOG_SECONDS <= 0.0:
    raise ValueError("GRA_GUI_MAX_LOG_SECONDS must be positive")


class MuJoCoAttitudePlant:
    """Stateful rotor-interface MuJoCo plant: body torque -> measured state."""

    def __init__(self, platform: str, actuator_scale: float):
        self.spec = SPECS[platform]
        if self.spec.interface != "rotor4":
            raise ValueError("The GUI supports rotor-interface plants only")
        self.model = mujoco.MjModel.from_xml_path(str(self.spec.model))
        self.model.opt.timestep = DT
        self.data = mujoco.MjData(self.model)
        _, self.body_id, self.qa, self.va = _free_joint(self.model)
        self.inertia = self.model.body_inertia[self.body_id].copy()
        self.mass = float(np.sum(self.model.body_mass))
        self.gravity = abs(float(self.model.opt.gravity[2]))
        self.limits = torque_limits(platform, self.inertia, self.model, "model")
        self.act_ids, _, self.B_inv, self.ctrl_range = _mixer(self.model)
        self.ctrl_range[:, 1] *= actuator_scale
        self.model.actuator_ctrlrange[self.act_ids, 1] = self.ctrl_range[:, 1]
        self.data.qpos[self.qa : self.qa + 3] = [0.0, 0.0, 1.0]
        self.data.qpos[self.qa + 3 : self.qa + 7] = [1.0, 0.0, 0.0, 0.0]
        self.data.qvel[:] = 0.0
        self.data.ctrl[:] = 0.0
        mujoco.mj_forward(self.model, self.data)

    def __call__(self, t, tau):
        tau = np.clip(np.asarray(tau, dtype=float), -self.limits, self.limits)
        R = np.asarray(self.data.xmat[self.body_id], dtype=float).reshape(3, 3)
        z = float(self.data.qpos[self.qa + 2])
        vz = float(self.data.qvel[self.va + 2])
        tilt = max(float(R[2, 2]), 0.35)
        collective = self.mass * (self.gravity + 6.0 * (1.0 - z) - 4.0 * vz) / tilt
        collective = float(
            np.clip(collective, 0.0, 2.5 * self.mass * max(self.gravity, 1.0))
        )
        requested = self.B_inv @ np.r_[collective, tau]
        actuator = np.clip(requested, self.ctrl_range[:, 0], self.ctrl_range[:, 1])
        self.data.ctrl[:] = 0.0
        self.data.xfrc_applied[:] = 0.0
        self.data.ctrl[self.act_ids] = actuator
        mujoco.mj_step(self.model, self.data)

        q_meas = quat_conj(
            np.asarray(self.data.qpos[self.qa + 3 : self.qa + 7], dtype=float)
        )
        omega = np.asarray(self.data.qvel[self.va + 3 : self.va + 6], dtype=float)
        z = float(self.data.qpos[self.qa + 2])
        vz = float(self.data.qvel[self.va + 2])
        actuator_normalized = np.divide(
            actuator,
            self.ctrl_range[:, 1],
            out=np.zeros_like(actuator),
            where=self.ctrl_range[:, 1] > 1e-12,
        )
        saturated = float(
            np.any(np.isclose(actuator, self.ctrl_range[:, 0], atol=1e-7))
            or np.any(np.isclose(actuator, self.ctrl_range[:, 1], atol=1e-7))
        )
        return np.r_[q_meas, omega, z, vz, actuator_normalized, saturated]


baseline_plant_object = MuJoCoAttitudePlant(PLATFORM, ACTUATOR_SCALE)
neural_plant_object = MuJoCoAttitudePlant(PLATFORM, ACTUATOR_SCALE)
LIMITS = baseline_plant_object.limits.copy()
INERTIA = baseline_plant_object.inertia.copy()
WN = np.array([4.0, 4.0, 3.5])
KQ = 2.0 * INERTIA * WN * WN
KW = 2.0 * 0.95 * WN * INERTIA
N_UNITS = 6
DIRECT_LEARNING_RATE = 8e-4
NENGO_LEARNING_RATE = N_UNITS * DIRECT_LEARNING_RATE / DT
DECODER_LEAK = 1e-6
W0 = np.concatenate([np.eye(3), -np.eye(3)], axis=1)


def _reference(t):
    phase = t % max(DURATION, DT)
    return np.r_[reference_quat(phase, MISSION, DURATION), reference_euler(phase, MISSION, DURATION)]


def _quaternion_error(t, x):
    qe, eq = quat_error(x[:4], x[4:8])
    return np.r_[eq, quat_angle(qe)]


def _pd(t, x):
    return np.clip(-KQ * x[:3] - KW * x[3:6], -LIMITS, LIMITS)


def _target(t, x):
    return np.clip(-8.0 * x[:3], -1.0, 1.0)


def _currents(t, tau0):
    normalized = np.divide(
        tau0, LIMITS, out=np.zeros_like(tau0), where=LIMITS > 1e-12
    )
    return np.r_[
        0.75 + 1.25 * np.maximum(normalized, 0.0),
        0.75 + 1.25 * np.maximum(-normalized, 0.0),
    ]


def _pes_error(t, x):
    enable = np.clip(x[6], 0.0, 1.0)
    return enable * (x[:3] - x[3:6])


def _residual_command(t, x):
    tau0 = np.clip(x[:3], -LIMITS, LIMITS)
    decoded = np.clip(x[3:6], -1.0, 1.0)
    beta = np.clip(x[6], 0.0, 0.75)
    requested_residual = beta * decoded * LIMITS
    command = np.clip(tau0 + requested_residual, -LIMITS, LIMITS)
    return np.r_[command, command - tau0]


def _quat_to_euler(t, q):
    w, x, y, z = q / max(float(np.linalg.norm(q)), 1e-12)
    roll = np.arctan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
    pitch = np.arcsin(np.clip(2 * (w * y - z * x), -1.0, 1.0))
    yaw = np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
    return [roll, pitch, yaw]


class LiveSignals:
    voltage = np.zeros(6)
    gate = np.zeros(6)
    activity = np.zeros(6)
    weights = W0.copy()


LIVE = LiveSignals()


class InteractiveRuntime:
    """Optional wall-clock governor and passive MuJoCo visualization state."""

    viewer = None
    viewer_plant = None
    wall_origin = 0.0
    sim_origin = 0.0
    next_viewer_sync = 0.0
    telemetry = {}
    telemetry_saved = False


RUNTIME = InteractiveRuntime()


model = nengo.Network(
    label=f"PD vs Nengo CMG-PES | {PLATFORM} | {MISSION} | dt={DT:g}s",
    seed=1,
)
with model:
    reference = nengo.Node(_reference, size_out=7, label="mission reference [q, roll,pitch,yaw]")

    with nengo.Network(label="Quaternion-PD baseline twin") as baseline_branch:
        baseline_plant = nengo.Node(
            baseline_plant_object,
            size_in=3,
            size_out=14,
            label=f"MuJoCo {PLATFORM} baseline",
        )
        baseline_error = nengo.Node(
            _quaternion_error, size_in=8, size_out=4, label="baseline shortest-path q error"
        )
        baseline_pd = nengo.Node(_pd, size_in=6, size_out=3, label="baseline quaternion PD torque")
        nengo.Connection(reference[:4], baseline_error[:4], synapse=None)
        nengo.Connection(baseline_plant[:4], baseline_error[4:8], synapse=None)
        nengo.Connection(baseline_error[:3], baseline_pd[:3], synapse=None)
        nengo.Connection(baseline_plant[4:7], baseline_pd[3:6], synapse=None)
        nengo.Connection(baseline_pd, baseline_plant, synapse=nengo.Lowpass(1e-6))

    with nengo.Network(label="PD + paired CMG + online PES twin") as neural_branch:
        neural_plant = nengo.Node(
            neural_plant_object,
            size_in=3,
            size_out=14,
            label=f"MuJoCo {PLATFORM} neural",
        )
        neural_error = nengo.Node(
            _quaternion_error, size_in=8, size_out=4, label="neural shortest-path q error"
        )
        neural_pd = nengo.Node(_pd, size_in=6, size_out=3, label="same quaternion PD torque")
        pes_target = nengo.Node(_target, size_in=6, size_out=3, label="signed PES target")
        paired_currents = nengo.Node(
            _currents, size_in=3, size_out=6, label="paired currents [+x,+y,+z,-x,-y,-z]"
        )
        nengo.Connection(reference[:4], neural_error[:4], synapse=None)
        nengo.Connection(neural_plant[:4], neural_error[4:8], synapse=None)
        nengo.Connection(neural_error[:3], neural_pd[:3], synapse=None)
        nengo.Connection(neural_plant[4:7], neural_pd[3:6], synapse=None)
        nengo.Connection(neural_error[:3], pes_target[:3], synapse=None)
        nengo.Connection(neural_plant[4:7], pes_target[3:6], synapse=None)
        nengo.Connection(neural_pd, paired_currents, synapse=None)

        cmg_population = nengo.Ensemble(
            N_UNITS,
            1,
            neuron_type=CoupledMembraneGate(adaptive=True),
            gain=np.ones(N_UNITS),
            bias=np.zeros(N_UNITS),
            encoders=np.ones((N_UNITS, 1)),
            label="six coupled membrane-gate units",
        )
        nengo.Connection(paired_currents, cmg_population.neurons, synapse=None)

        decoded_residual = nengo.Node(
            size_in=3, label="learned normalized residual y = W a"
        )
        decoded_clipped = nengo.Node(
            lambda t, x: np.clip(x, -1.0, 1.0),
            size_in=3,
            size_out=3,
            label="clipped decoder used by PES and residual",
        )
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="This learning rate is very high.*")
            adaptive_decoder = nengo.Connection(
                cmg_population.neurons,
                decoded_residual,
                transform=W0,
                synapse=None,
                learning_rule_type=nengo.PES(
                    learning_rate=NENGO_LEARNING_RATE, pre_synapse=None
                ),
            )
        nengo.Connection(decoded_residual, decoded_clipped, synapse=None)
        learning_enable = nengo.Node([1.0], label="PES learning enable [0,1]")
        pes_error = nengo.Node(
            _pes_error, size_in=7, size_out=3, label="PES error = enable(y-y*)"
        )
        nengo.Connection(decoded_clipped, pes_error[:3], synapse=None)
        nengo.Connection(pes_target, pes_error[3:6], synapse=None)
        nengo.Connection(learning_enable, pes_error[6], synapse=None)
        nengo.Connection(pes_error, adaptive_decoder.learning_rule, synapse=None)

        beta_control = nengo.Node([0.5], label="residual authority beta [0,0.75]")
        augmented_torque = nengo.Node(
            _residual_command,
            size_in=7,
            size_out=6,
            label="bounded tau=tau0+delta_tau [tau, residual]",
        )
        nengo.Connection(neural_pd, augmented_torque[:3], synapse=None)
        nengo.Connection(decoded_clipped, augmented_torque[3:6], synapse=None)
        nengo.Connection(beta_control, augmented_torque[6], synapse=None)
        nengo.Connection(augmented_torque[:3], neural_plant, synapse=nengo.Lowpass(1e-6))

    # ------------------------ dashboard signals ------------------------
    baseline_attitude = nengo.Node(_quat_to_euler, size_in=4, size_out=3, label="PD attitude")
    neural_attitude = nengo.Node(_quat_to_euler, size_in=4, size_out=3, label="CMG-PES attitude")
    nengo.Connection(baseline_plant[:4], baseline_attitude, synapse=None)
    nengo.Connection(neural_plant[:4], neural_attitude, synapse=None)

    attitude_tracking = nengo.Node(
        size_in=9,
        label="attitude [PD rpy, CMG-PES rpy, reference rpy]",
    )
    nengo.Connection(baseline_attitude, attitude_tracking[:3], synapse=None)
    nengo.Connection(neural_attitude, attitude_tracking[3:6], synapse=None)
    nengo.Connection(reference[4:7], attitude_tracking[6:9], synapse=None)

    error_comparison = nengo.Node(
        size_in=2, label="quaternion-angle error [PD, CMG-PES]"
    )
    nengo.Connection(baseline_error[3], error_comparison[0], synapse=None)
    nengo.Connection(neural_error[3], error_comparison[1], synapse=None)

    normalized_torque = nengo.Node(
        lambda t, x: np.r_[x[:3] / LIMITS, x[3:6] / LIMITS, x[6:9] / LIMITS],
        size_in=9,
        size_out=9,
        label="normalized torque [tau0, residual, command]",
    )
    nengo.Connection(neural_pd, normalized_torque[:3], synapse=None)
    nengo.Connection(augmented_torque[3:6], normalized_torque[3:6], synapse=None)
    nengo.Connection(augmented_torque[:3], normalized_torque[6:9], synapse=None)

    actuator_comparison = nengo.Node(
        size_in=8, label="normalized rotors [PD 1..4, CMG-PES 1..4]"
    )
    nengo.Connection(baseline_plant[9:13], actuator_comparison[:4], synapse=None)
    nengo.Connection(neural_plant[9:13], actuator_comparison[4:8], synapse=None)

    # These Nodes read the actual simulator signals installed by on_start.
    cmg_voltage_monitor = nengo.Node(
        lambda t: LIVE.voltage, size_out=6, label="CMG membrane voltage v"
    )
    cmg_gate_monitor = nengo.Node(lambda t: LIVE.gate, size_out=6, label="CMG gate r")
    cmg_activity_monitor = nengo.Node(
        lambda t: LIVE.activity, size_out=6, label="CMG decoder activity a"
    )
    decoder_norm_monitor = nengo.Node(
        lambda t: np.linalg.norm(LIVE.weights.reshape(3, 6), axis=1),
        size_out=3,
        label="online decoder row norms",
    )

    # Headless smoke-test probes. Nengo GUI adds its own visualization probes.
    p_errors = nengo.Probe(error_comparison, synapse=None)
    p_attitude = nengo.Probe(attitude_tracking, synapse=None)
    p_residual = nengo.Probe(augmented_torque[3:6], synapse=None)
    p_activity = nengo.Probe(cmg_population.neurons, synapse=None)


def on_start(sim):
    """Bind live state monitors and append the canonical post-PES regularizer."""
    LIVE.voltage = sim.signals[sim.model.sig[cmg_population.neurons]["voltage"]]
    LIVE.gate = sim.signals[sim.model.sig[cmg_population.neurons]["gate"]]
    LIVE.activity = sim.signals[sim.model.sig[cmg_population.neurons]["out"]]
    LIVE.weights = sim.signals[sim.model.sig[adaptive_decoder]["weights"]]

    weights_before = np.empty_like(LIVE.weights)

    def node_output(node):
        return sim.signals[sim.model.sig[node]["out"]]

    signal = {
        "reference": node_output(reference),
        "baseline_plant": node_output(baseline_plant),
        "neural_plant": node_output(neural_plant),
        "baseline_error": node_output(baseline_error),
        "neural_error": node_output(neural_error),
        "baseline_tau": node_output(baseline_pd),
        "neural_tau0": node_output(neural_pd),
        "target": node_output(pes_target),
        "current": node_output(paired_currents),
        "decoded_raw": node_output(decoded_residual),
        "decoded_clipped": node_output(decoded_clipped),
        "pes_error": node_output(pes_error),
        "augmented_torque": node_output(augmented_torque),
        "attitude_tracking": node_output(attitude_tracking),
        "error_comparison": node_output(error_comparison),
        "normalized_torque": node_output(normalized_torque),
        "actuator_comparison": node_output(actuator_comparison),
        "beta": node_output(beta_control),
        "learning_enable": node_output(learning_enable),
    }
    names = (
        "t", "reference_quat", "reference_euler", "baseline_plant_output",
        "neural_plant_output", "baseline_quaternion_error", "neural_quaternion_error",
        "baseline_tau", "neural_tau0", "target", "current", "voltage", "gate",
        "activity", "effective_threshold", "gate_argument", "gate_target",
        "conductance_gain", "conductance", "membrane_lambda", "membrane_drive",
        "decoded_raw", "decoded_clipped", "pes_error", "weights", "weight_delta",
        "command_torque", "residual_torque", "attitude_tracking", "error_comparison",
        "normalized_torque", "actuator_comparison", "beta", "learning_enable",
    )
    RUNTIME.telemetry = {name: [] for name in names}
    RUNTIME.telemetry_saved = False

    def capture_decoder_before_step():
        weights_before[:] = LIVE.weights

    def regularize_decoder():
        LIVE.weights[:] -= DECODER_LEAK * weights_before
        np.clip(LIVE.weights, -6.0, 6.0, out=LIVE.weights)

    def capture_telemetry():
        if not SAVE_TELEMETRY:
            return
        if float(sim.time) > MAX_LOG_SECONDS + 0.5 * DT:
            _save_telemetry()
            return
        neuron = cmg_population.neuron_type
        voltage = np.asarray(LIVE.voltage, dtype=float).copy()
        gate = np.asarray(LIVE.gate, dtype=float).copy()
        current = np.asarray(signal["current"], dtype=float).copy()
        effective_threshold = neuron.v_threshold - neuron.gamma * gate
        gate_argument = np.clip(
            neuron.alpha * (voltage - effective_threshold), -60.0, 60.0
        )
        gate_target = 1.0 / (1.0 + np.exp(-gate_argument))
        conductance_gain = np.full_like(current, neuron.base_gain)
        if neuron.adaptive:
            conductance_gain += neuron.gain_scaling * np.abs(current)
        conductance = conductance_gain * gate * gate
        membrane_lambda = 1.0 / neuron.tau + conductance
        membrane_drive = (
            neuron.v_rest / neuron.tau
            + current / neuron.tau
            + conductance * neuron.v_reset
        )
        values = {
            "t": float(sim.time),
            "reference_quat": signal["reference"][:4].copy(),
            "reference_euler": signal["reference"][4:7].copy(),
            "baseline_plant_output": signal["baseline_plant"].copy(),
            "neural_plant_output": signal["neural_plant"].copy(),
            "baseline_quaternion_error": signal["baseline_error"].copy(),
            "neural_quaternion_error": signal["neural_error"].copy(),
            "baseline_tau": signal["baseline_tau"].copy(),
            "neural_tau0": signal["neural_tau0"].copy(),
            "target": signal["target"].copy(),
            "current": current,
            "voltage": voltage,
            "gate": gate,
            "activity": np.asarray(LIVE.activity, dtype=float).copy(),
            "effective_threshold": effective_threshold,
            "gate_argument": gate_argument,
            "gate_target": gate_target,
            "conductance_gain": conductance_gain,
            "conductance": conductance,
            "membrane_lambda": membrane_lambda,
            "membrane_drive": membrane_drive,
            "decoded_raw": signal["decoded_raw"].copy(),
            "decoded_clipped": signal["decoded_clipped"].copy(),
            "pes_error": signal["pes_error"].copy(),
            "weights": LIVE.weights.copy(),
            "weight_delta": LIVE.weights.copy() - weights_before,
            "command_torque": signal["augmented_torque"][:3].copy(),
            "residual_torque": signal["augmented_torque"][3:6].copy(),
            "attitude_tracking": signal["attitude_tracking"].copy(),
            "error_comparison": signal["error_comparison"].copy(),
            "normalized_torque": signal["normalized_torque"].copy(),
            "actuator_comparison": signal["actuator_comparison"].copy(),
            "beta": signal["beta"].copy(),
            "learning_enable": signal["learning_enable"].copy(),
        }
        for name, value in values.items():
            RUNTIME.telemetry[name].append(value)

    sim._steps.insert(0, capture_decoder_before_step)
    sim._steps.append(regularize_decoder)
    sim._steps.append(capture_telemetry)

    RUNTIME.wall_origin = time.perf_counter()
    RUNTIME.sim_origin = float(sim.time)
    RUNTIME.next_viewer_sync = float(sim.time)
    if VIEWER_TARGET != "none":
        if mujoco.viewer is None:
            raise RuntimeError("MuJoCo viewer support is unavailable in this environment")
        RUNTIME.viewer_plant = (
            neural_plant_object if VIEWER_TARGET == "neural" else baseline_plant_object
        )
        RUNTIME.viewer = mujoco.viewer.launch_passive(
            RUNTIME.viewer_plant.model,
            RUNTIME.viewer_plant.data,
            show_left_ui=True,
            show_right_ui=True,
        )
        with RUNTIME.viewer.lock():
            body_position = RUNTIME.viewer_plant.data.xpos[
                RUNTIME.viewer_plant.body_id
            ]
            RUNTIME.viewer.cam.lookat[:] = body_position
            RUNTIME.viewer.cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
            RUNTIME.viewer.cam.trackbodyid = RUNTIME.viewer_plant.body_id
            RUNTIME.viewer.cam.distance = max(
                2.5 * float(RUNTIME.viewer_plant.model.stat.extent), 0.5
            )
            RUNTIME.viewer.cam.azimuth = 135.0
            RUNTIME.viewer.cam.elevation = -25.0
        RUNTIME.viewer.sync()
    print(
        f"GUI ready: platform={PLATFORM}, mission={MISSION}, duration={DURATION}s, "
        f"dt={sim.dt}s, actuator_scale={ACTUATOR_SCALE}, "
        f"direct_eta={DIRECT_LEARNING_RATE}, Nengo_eta={NENGO_LEARNING_RATE}, "
        f"viewer={VIEWER_TARGET}@{VIEWER_FPS:g}Hz, realtime={REALTIME}."
    )


def _save_telemetry():
    if RUNTIME.telemetry_saved or not SAVE_TELEMETRY or not RUNTIME.telemetry.get("t"):
        return
    RUNTIME.telemetry_saved = True
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output = TELEMETRY_ROOT / f"{PLATFORM}_{MISSION}_{timestamp}"
    output.mkdir(parents=True, exist_ok=True)
    arrays = {name: np.asarray(values) for name, values in RUNTIME.telemetry.items()}
    archive = output / "neural_trace_full_rate.npz"
    np.savez_compressed(archive, **arrays)
    schema = {
        "schema": 1,
        "source": "interactive synchronized MuJoCo/Nengo GUI",
        "sample_rate_hz": 1.0 / DT,
        "sample_period_s": DT,
        "axis_order": ["x/roll", "y/pitch", "z/yaw"],
        "unit_order": ["+x", "+y", "+z", "-x", "-y", "-z"],
        "weight_shape_per_sample": [3, 6],
        "plant_output_layout": ["q_w", "q_x", "q_y", "q_z", "omega_x", "omega_y", "omega_z", "z", "vz", "rotor_1_norm", "rotor_2_norm", "rotor_3_norm", "rotor_4_norm", "saturated"],
        "signals": {name: {"shape": list(value.shape), "dtype": str(value.dtype)} for name, value in arrays.items()},
        "semantics": {
            "decoded_raw": "unbounded W @ activity",
            "decoded_clipped": "clip(W @ activity,-1,1), used by PES and residual",
            "weight_delta": "all 18 decoder changes during this 0.5-ms Nengo step",
            "gate_target": "sigmoid(alpha*(voltage-effective_threshold))",
            "pes_error": "learning_enable*(decoded_clipped-target)",
        },
    }
    (output / "neural_trace_schema.json").write_text(
        json.dumps(schema, indent=2) + "\n", encoding="utf-8"
    )
    summary = {
        "platform": PLATFORM,
        "mission": MISSION,
        "duration_reference_s": DURATION,
        "logged_samples": len(arrays["t"]),
        "logged_duration_s": float(arrays["t"][-1] - arrays["t"][0]) if len(arrays["t"]) > 1 else 0.0,
        "dt_s": DT,
        "actuator_scale": ACTUATOR_SCALE,
        "viewer_target": VIEWER_TARGET,
        "archive": str(archive),
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Saved full-rate GUI telemetry: {archive} ({len(arrays['t'])} samples)")


def on_step(sim):
    """Pace the graph and refresh visualization without changing plant physics."""
    if REALTIME:
        target_wall = RUNTIME.wall_origin + (float(sim.time) - RUNTIME.sim_origin)
        remaining = target_wall - time.perf_counter()
        if remaining > 0.0:
            time.sleep(remaining)

    viewer = RUNTIME.viewer
    if viewer is None or float(sim.time) + 1e-12 < RUNTIME.next_viewer_sync:
        return
    if viewer.is_running():
        viewer.sync()
        RUNTIME.next_viewer_sync = float(sim.time) + 1.0 / VIEWER_FPS
    else:
        viewer.close()
        RUNTIME.viewer = None
        RUNTIME.viewer_plant = None


def on_close(sim):
    """Release the optional native viewer when Nengo rebuilds or exits."""
    del sim
    _save_telemetry()
    if RUNTIME.viewer is not None:
        RUNTIME.viewer.close()
        RUNTIME.viewer = None
        RUNTIME.viewer_plant = None
