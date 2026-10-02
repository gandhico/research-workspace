"""Controlled single-satellite MuJoCo digital twin inside Basilisk 2.11.1.

The dynamics are propagated by Basilisk's native MJScene.  The controller is
the standard Basilisk message graph: inertial guidance -> attitude error ->
MRP feedback -> reaction-wheel allocation -> saturation -> MuJoCo actuators.
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from Basilisk.architecture import messaging
from Basilisk.fswAlgorithms import attTrackingError, inertial3D, mrpFeedback, rwMotorTorque
from Basilisk.simulation import NBodyGravity
from Basilisk.simulation import arrayMotorTorqueToSingleActuators
from Basilisk.simulation import mujoco
from Basilisk.simulation import pointMassGravityModel
from Basilisk.simulation import saturationSingleActuator
from Basilisk.simulation import scalarJointStatesToRWSpeed
from Basilisk.simulation import simpleNav
from Basilisk.utilities import SimulationBaseClass, macros, orbitalMotion, simIncludeGravBody

ROOT = Path(__file__).resolve().parent


def mjcf(bus_mass: float, inertia: tuple[float, float, float], rw_mass: float,
         rw_js: float, rw_jt: float) -> str:
    """Return a free bus with three orthogonal, torque-actuated reaction wheels."""
    ixx, iyy, izz = inertia
    return f"""
<mujoco model="controlledSatellite">
  <option><flag contact="disable"/></option>
  <worldbody>
    <body name="bus">
      <freejoint name="busFree"/>
      <inertial pos="0 0 0" mass="{bus_mass}" diaginertia="{ixx} {iyy} {izz}"/>
      <geom type="box" size="0.6 0.5 0.4" rgba="0.55 0.60 0.70 1"/>
      <body name="rw1"><joint name="rw1Spin" type="hinge" axis="1 0 0" limited="false"/>
        <inertial pos="0 0 0" mass="{rw_mass}" diaginertia="{rw_js} {rw_jt} {rw_jt}"/>
        <geom type="cylinder" size="0.08 0.03" euler="0 90 0" rgba="0.2 0.3 0.9 1"/></body>
      <body name="rw2"><joint name="rw2Spin" type="hinge" axis="0 1 0" limited="false"/>
        <inertial pos="0 0 0" mass="{rw_mass}" diaginertia="{rw_jt} {rw_js} {rw_jt}"/>
        <geom type="cylinder" size="0.08 0.03" euler="90 0 0" rgba="0.2 0.8 0.3 1"/></body>
      <body name="rw3" pos="0.5 0.5 0.5"><joint name="rw3Spin" type="hinge" axis="0 0 1" limited="false"/>
        <inertial pos="0 0 0" mass="{rw_mass}" diaginertia="{rw_jt} {rw_jt} {rw_js}"/>
        <geom type="cylinder" size="0.08 0.03" rgba="0.9 0.2 0.2 1"/></body>
    </body>
  </worldbody>
</mujoco>
"""


def run(duration: float = 600.0, dt: float = 0.1, output: Path | None = None) -> dict:
    if duration <= 0 or dt <= 0:
        raise ValueError("duration and dt must be positive")
    output = output or ROOT / "results" / datetime.now().strftime("single_satellite_%Y%m%d_%H%M%S")
    output.mkdir(parents=True, exist_ok=True)

    bus_mass = 750.0
    bus_inertia = (900.0, 800.0, 600.0)
    rw_mass, rw_u_max = 9.0, 0.2
    rw_omega_max = 6000.0 * macros.RPM
    rw_js = 50.0 / rw_omega_max
    rw_jt = 0.5 * rw_js
    n_rw = 3

    sim = SimulationBaseClass.SimBaseClass()
    process = sim.CreateNewProcess("simulationProcess")
    process.addTask(sim.CreateNewTask("simulationTask", macros.sec2nano(dt)))

    scene = mujoco.MJScene(mjcf(bus_mass, bus_inertia, rw_mass, rw_js, rw_jt))
    scene.ModelTag = "mujocoScene"
    sim.AddModelToTask("simulationTask", scene)
    bus = scene.getBody("bus")
    wheel_bodies = [scene.getBody(f"rw{i}") for i in range(1, n_rw + 1)]
    wheel_joints = [wheel_bodies[i].getScalarJoint(f"rw{i + 1}Spin") for i in range(n_rw)]
    wheel_actuators = [scene.addJointSingleActuator(f"rw{i + 1}Act", wheel_joints[i]) for i in range(n_rw)]

    gravity = NBodyGravity.NBodyGravity()
    scene.AddModelToDynamicsTask(gravity)
    grav_factory = simIncludeGravBody.gravBodyFactory()
    earth = grav_factory.createEarth()
    earth.isCentralBody = True
    earth_model = pointMassGravityModel.PointMassGravityModel()
    earth_model.muBody = earth.mu
    gravity.addGravitySource("earth", earth_model, isCentralBody=True)
    gravity.addGravityTarget("bus", bus)
    for i, body in enumerate(wheel_bodies, start=1):
        gravity.addGravityTarget(f"rw{i}", body)

    nav = simpleNav.SimpleNav()
    nav.scStateInMsg.subscribeTo(bus.getCenterOfMass().stateOutMsg)
    sim.AddModelToTask("simulationTask", nav)
    guidance = inertial3D.inertial3D()
    guidance.sigma_R0N = [0.0, 0.0, 0.0]
    sim.AddModelToTask("simulationTask", guidance)
    error = attTrackingError.attTrackingError()
    error.attNavInMsg.subscribeTo(nav.attOutMsg)
    error.attRefInMsg.subscribeTo(guidance.attRefOutMsg)
    sim.AddModelToTask("simulationTask", error)

    rw_cfg = messaging.RWArrayConfigMsgPayload()
    rw_cfg.numRW = n_rw
    rw_cfg.GsMatrix_B = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
    rw_cfg.JsList = [rw_js] * n_rw
    rw_cfg.uMax = [rw_u_max] * n_rw
    rw_cfg_msg = messaging.RWArrayConfigMsg().write(rw_cfg)

    speeds = scalarJointStatesToRWSpeed.ScalarJointStatesToRWSpeed()
    speeds.setNumJoints(n_rw)
    for i in range(n_rw):
        speeds.jointStateInMsgs[i].subscribeTo(wheel_joints[i].stateDotOutMsg)
    sim.AddModelToTask("simulationTask", speeds)

    control = mrpFeedback.mrpFeedback()
    control.K, control.Ki, control.P, control.integralLimit = 3.5, -1.0, 30.0, 0.0
    control.guidInMsg.subscribeTo(error.attGuidOutMsg)
    control.rwParamsInMsg.subscribeTo(rw_cfg_msg)
    control.rwSpeedsInMsg.subscribeTo(speeds.rwSpeedOutMsg)
    inertia_flat = [bus_inertia[0], 0.0, 0.0, 0.0, bus_inertia[1], 0.0, 0.0, 0.0, bus_inertia[2]]
    control.vehConfigInMsg.subscribeTo(
        messaging.VehicleConfigMsg().write(messaging.VehicleConfigMsgPayload(ISCPntB_B=inertia_flat))
    )
    sim.AddModelToTask("simulationTask", control)

    allocation = rwMotorTorque.rwMotorTorque()
    allocation.rwParamsInMsg.subscribeTo(rw_cfg_msg)
    allocation.vehControlInMsg.subscribeTo(control.cmdTorqueOutMsg)
    allocation.controlAxes_B = [1, 0, 0, 0, 1, 0, 0, 0, 1]
    sim.AddModelToTask("simulationTask", allocation)
    split = arrayMotorTorqueToSingleActuators.ArrayMotorTorqueToSingleActuators()
    split.setNumActuators(n_rw)
    split.torqueInMsg.subscribeTo(allocation.rwMotorTorqueOutMsg)
    sim.AddModelToTask("simulationTask", split)
    limiters = []
    for i in range(n_rw):
        limiter = saturationSingleActuator.SaturationSingleActuator()
        limiter.setMinInput(-rw_u_max)
        limiter.setMaxInput(rw_u_max)
        limiter.actuatorInMsg.subscribeTo(split.actuatorOutMsgs[i])
        sim.AddModelToTask("simulationTask", limiter)
        wheel_actuators[i].actuatorInMsg.subscribeTo(limiter.actuatorOutMsg)
        limiters.append(limiter)

    attitude_log = error.attGuidOutMsg.recorder(macros.sec2nano(max(dt, 0.5)))
    torque_logs = [act.actuatorInMsg.recorder(macros.sec2nano(max(dt, 0.5))) for act in wheel_actuators]
    speed_logs = [joint.stateDotOutMsg.recorder(macros.sec2nano(max(dt, 0.5))) for joint in wheel_joints]
    sim.AddModelToTask("simulationTask", attitude_log)
    for logger in torque_logs + speed_logs:
        sim.AddModelToTask("simulationTask", logger)

    sim.InitializeSimulation()
    elements = orbitalMotion.ClassicElements()
    elements.a, elements.e, elements.i = 10_000_000.0, 0.01, 33.3 * macros.D2R
    elements.Omega, elements.omega, elements.f = 48.2 * macros.D2R, 347.8 * macros.D2R, 85.3 * macros.D2R
    position, velocity = orbitalMotion.elem2rv(earth.mu, elements)
    bus.setPosition(position)
    bus.setVelocity(velocity)
    bus.setAttitude([0.1, 0.2, -0.3])
    bus.setAttitudeRate([0.001, -0.01, 0.03])
    for joint, rpm in zip(wheel_joints, (100.0, 200.0, 300.0)):
        joint.setVelocity(rpm * macros.RPM)

    sim.ConfigureStopTime(macros.sec2nano(duration))
    sim.ExecuteSimulation()

    time_s = attitude_log.times() * macros.NANO2SEC
    sigma = np.asarray(attitude_log.sigma_BR)
    omega = np.asarray(attitude_log.omega_BR_B)
    torque = np.column_stack([np.asarray(log.input) for log in torque_logs])
    wheel_speed = np.column_stack([np.asarray(log.state) for log in speed_logs])
    initial_error, final_error = float(np.linalg.norm(sigma[0])), float(np.linalg.norm(sigma[-1]))
    summary = {
        "basilisk_version": "2.11.1",
        "dynamics": "Basilisk MJScene (MuJoCo)",
        "controller": "inertial3D + attTrackingError + mrpFeedback + rwMotorTorque",
        "duration_s": duration,
        "dt_s": dt,
        "initial_mrp_error_norm": initial_error,
        "final_mrp_error_norm": final_error,
        "final_rate_error_norm_rad_s": float(np.linalg.norm(omega[-1])),
        "max_abs_wheel_torque_nm": float(np.max(np.abs(torque))),
        "max_abs_wheel_speed_rpm": float(np.max(np.abs(wheel_speed / macros.RPM))),
        "converged": bool(final_error < 0.05 * initial_error and np.linalg.norm(omega[-1]) < 1e-3),
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    with (output / "trace.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["time_s", "sigma_1", "sigma_2", "sigma_3", "omega_1", "omega_2", "omega_3",
                         "rw_torque_1", "rw_torque_2", "rw_torque_3", "rw_speed_1", "rw_speed_2", "rw_speed_3"])
        writer.writerows(np.column_stack([time_s, sigma, omega, torque, wheel_speed]))

    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    axes[0].plot(time_s, sigma)
    axes[0].set_ylabel("MRP attitude error")
    axes[0].legend(["sigma1", "sigma2", "sigma3"], ncol=3)
    axes[1].plot(time_s, omega)
    axes[1].set_ylabel("rate error [rad/s]")
    axes[1].set_xlabel("time [s]")
    fig.tight_layout()
    fig.savefig(output / "attitude_convergence.png", dpi=180)
    plt.close(fig)

    if not np.all(np.isfinite(np.column_stack([sigma, omega, torque, wheel_speed]))):
        raise RuntimeError("non-finite state in simulation")
    if not summary["converged"]:
        raise RuntimeError(f"controller did not meet convergence gate: {summary}")
    return {"output": str(output), **summary}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=float, default=600.0)
    parser.add_argument("--dt", type=float, default=0.1)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.duration, args.dt, args.output), indent=2))


if __name__ == "__main__":
    main()
