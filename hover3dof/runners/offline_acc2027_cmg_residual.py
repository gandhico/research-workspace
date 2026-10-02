"""ACC2027 CMG residual controller against a 3DOF Hover offline surrogate.

Pure Python simulation. No hardware, no QUARC, no PAL. Imports the exact
canonical controller from the ACC2027 repository
(``gra_control.gate.CMGResidualAugmentor``, not reimplemented) and drives it
against a linear plant built from the vendor documentation's own equations
of motion (state vector, control vector, and the positive-voltage-only
control law of Eq. 2.5) -- see
``3DOF_Hover\\...\\Documentation\\3 DOF Hover - Laboratory Guide.pdf`` -- with
physical constants (K_f, K_t, L, inertias) taken from the vendor's own
identified values in
``3DOF_Hover\\...\\Technical Resources\\3 DOF Hover - User Manual.pdf``
Table 2.2 (2013 unit; not re-measured on this specific rig).

Still NOT hardware-validated: the vendor bias voltage / saturation limit
used below are its Laboratory Guide worked-example numbers, not measured on
this rig, and the amplifier gain (Table 2.2 assumes gain=3 per the User
Manual) is not accounted for -- this script's voltages are DAQ analog-output
volts, not motor volts. See docs\\SAFETY_CHECKLIST.md before doing anything
with real hardware.
"""

from __future__ import annotations

import argparse
import csv
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ACC_ROOT = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control")
HOVER_ROOT = Path(__file__).resolve().parents[1]

from gra_control.gate import CMGResidualAugmentor
from gra_control.provenance import manifest, write_json


@dataclass
class HoverPlant:
    """Vendor-identified constants (User Manual Table 2.2, 2013 unit) --
    see module docstring for what is and isn't verified for this rig."""
    K_f: float = 0.1188   # thrust-force constant, N/V (User Manual Table 2.2)
    K_t: float = 0.0036   # torque-thrust constant, N*m/V (User Manual Table 2.2)
    L: float = 0.197      # pivot-to-motor distance, m (User Manual Table 2.2)
    J_yaw: float = 0.110    # kg*m^2 (User Manual Table 2.2)
    J_pitch: float = 0.0552  # kg*m^2 (User Manual Table 2.2)
    J_roll: float = 0.0552   # kg*m^2 (User Manual Table 2.2)
    v_bias: float = 2.0    # V, Laboratory Guide worked example -- NOT measured on this rig
    v_max: float = 24.0    # V, Laboratory Guide worked example -- NOT measured on this rig


def mix_torques_to_voltages(tau: np.ndarray, plant: HoverPlant) -> np.ndarray:
    """Invert the vendor's Eqs. 2.1-2.3 to get [Vf, Vb, Vr, Vl] from
    [tau_pitch, tau_roll, tau_yaw], with a symmetric common-mode bias.
    Clipped to [0, v_max] per Eq. 2.5's positive-voltage-only law."""
    tau_pitch, tau_roll, tau_yaw = tau
    d_pitch = tau_pitch/(2.0*plant.K_f*plant.L)
    d_roll = tau_roll/(2.0*plant.K_f*plant.L)
    d_yaw = tau_yaw/(4.0*plant.K_t)
    v = plant.v_bias + np.array([
        d_pitch - d_yaw,   # front
        -d_pitch - d_yaw,  # back
        d_roll + d_yaw,    # right
        -d_roll + d_yaw,   # left
    ])
    return np.clip(v, 0.0, plant.v_max)


def voltages_to_torques(v: np.ndarray, plant: HoverPlant) -> np.ndarray:
    """Forward mixer (Eqs. 2.1-2.3): [Vf,Vb,Vr,Vl] -> [tau_pitch,tau_roll,tau_yaw]."""
    vf, vb, vr, vl = v
    tau_pitch = plant.K_f*plant.L*(vf - vb)
    tau_roll = plant.K_f*plant.L*(vr - vl)
    tau_yaw = plant.K_t*((vr + vl) - (vf + vb))
    return np.array([tau_pitch, tau_roll, tau_yaw])


def _controller(name: str, limits: np.ndarray, beta: float, learning_rate: float):
    if name == "classical":
        return None
    if name == "fixed-residual":
        return CMGResidualAugmentor(3, limits, "residual", False, beta)
    if name == "adaptive-residual":
        return CMGResidualAugmentor(3, limits, "residual", True, beta)
    if name in {"online-pes", "online-pes-adaptive"}:
        return CMGResidualAugmentor(3, limits, "online_pes", True, beta, learning_rate=learning_rate)
    if name == "online-pes-fixed":
        return CMGResidualAugmentor(3, limits, "online_pes", False, beta, learning_rate=learning_rate)
    raise ValueError(f"Unknown controller: {name}")


def reference_deg(t: float, mission: str) -> np.ndarray:
    """[yaw, pitch, roll] reference in degrees, matching the vendor demo's
    step amplitudes/frequencies (Laboratory Guide Sec. 3.1.2, step 5)."""
    if mission == "vendor-demo":
        return np.array([
            5.0*np.sign(np.sin(2*np.pi*0.04*t)),
            4.0*np.sign(np.sin(2*np.pi*0.10*t)),
            4.0*np.sign(np.sin(2*np.pi*0.08*t)),
        ])
    if mission == "hover":
        return np.zeros(3)
    raise ValueError(f"Unknown mission: {mission}")


def run(
    controller_name: str,
    mission: str,
    duration: float,
    dt: float,
    beta: float,
    learning_rate: float,
    k_error: float,
    k_rate: float,
    seed: int,
    output: Path,
) -> dict:
    plant = HoverPlant()
    wn = np.array([3.0, 3.0, 3.0])  # [yaw, pitch, roll] natural frequency, rad/s
    inertia = np.array([plant.J_yaw, plant.J_pitch, plant.J_roll])
    kq = inertia*wn*wn
    kw = 2.0*0.9*wn*inertia
    torque_limits = np.array([
        4.0*plant.K_t*(plant.v_max - plant.v_bias),
        2.0*plant.K_f*plant.L*(plant.v_max - plant.v_bias),
        2.0*plant.K_f*plant.L*(plant.v_max - plant.v_bias),
    ])
    augmentor = _controller(controller_name, torque_limits, beta, learning_rate)

    x = np.zeros(6)  # [yaw, pitch, roll, yaw_dot, pitch_dot, roll_dot], rad, rad/s
    rows: list[dict] = []
    n_steps = int(round(duration/dt))

    for k in range(n_steps):
        t = k*dt
        ref = np.deg2rad(reference_deg(t, mission))
        angle = x[0:3]
        rate = x[3:6]
        err = ref - angle
        # order [yaw, pitch, roll] -> reorder to [pitch, roll, yaw] for the
        # mixer, which follows the vendor's Eq. 2.1 (pitch), 2.2 (roll), 2.3 (yaw)
        tau0_ypr = np.clip(kq*err - kw*rate, -np.roll(torque_limits, 1), np.roll(torque_limits, 1))
        tau0 = np.array([tau0_ypr[1], tau0_ypr[2], tau0_ypr[0]])  # [pitch, roll, yaw]

        if augmentor is None:
            tau, residual, gate_mean = tau0, np.zeros(3), 0.0
        else:
            target = np.clip(k_error*np.array([err[1], err[2], err[0]]) - k_rate*np.array([rate[1], rate[2], rate[0]]), -1.0, 1.0)
            is_online = controller_name in {"online-pes", "online-pes-fixed", "online-pes-adaptive"}
            out = augmentor.step(tau0, dt, target if is_online else None)
            tau, residual = out.command, out.residual
            gate_mean = float(np.mean(out.gate))

        v = mix_torques_to_voltages(tau, plant)
        tau_applied = voltages_to_torques(v, plant)  # what the clipped voltages actually produce
        tau_yaw, tau_pitch, tau_roll = tau_applied[2], tau_applied[0], tau_applied[1]

        angle_ddot = np.array([tau_yaw, tau_pitch, tau_roll])/inertia
        x[3:6] += dt*angle_ddot
        x[0:3] += dt*x[3:6]

        rows.append({
            "t": t,
            "yaw_err_deg": np.rad2deg(err[0]), "pitch_err_deg": np.rad2deg(err[1]),
            "roll_err_deg": np.rad2deg(err[2]),
            "Vf": v[0], "Vb": v[1], "Vr": v[2], "Vl": v[3],
            "residual_norm": float(np.linalg.norm(residual)), "gate_mean": gate_mean,
        })

    output.mkdir(parents=True, exist_ok=True)
    csv_path = output/"trace.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)

    err_deg = np.array([[r["yaw_err_deg"], r["pitch_err_deg"], r["roll_err_deg"]] for r in rows])
    err_mag = np.linalg.norm(err_deg, axis=1)
    summary = {
        "platform": "hover3dof_offline_surrogate",
        "fidelity": "PLACEHOLDER physical constants (Kf/Kt/L/inertia not vendor-identified); "
                    "structure (state/control vectors, Eq. 2.5 positive-voltage-only law) "
                    "matches the vendor Laboratory Guide. NOT hardware-validated.",
        "controller": controller_name, "mission": mission, "duration": duration, "dt": dt,
        "beta": beta, "learning_rate": learning_rate, "k_error": k_error, "k_rate": k_rate,
        "seed": seed, "torque_limits_Nm_pitch_roll_yaw": torque_limits.tolist(),
        "angle_err_mean_deg": float(np.mean(err_mag)), "angle_err_max_deg": float(np.max(err_mag)),
        "min_voltage_seen": float(min(min(r["Vf"], r["Vb"], r["Vr"], r["Vl"]) for r in rows)),
        "max_voltage_seen": float(max(max(r["Vf"], r["Vb"], r["Vr"], r["Vl"]) for r in rows)),
        "trace": str(csv_path),
    }
    args = {
        "controller": controller_name, "mission": mission, "duration": duration, "dt": dt,
        "beta": beta, "learning_rate": learning_rate, "k_error": k_error, "k_rate": k_rate,
        "seed": seed,
    }
    prov = manifest(ACC_ROOT, "hover3dof_offline_surrogate", controller_name,
                     Path(__file__), args)
    write_json(output/"summary.json", summary)
    write_json(output/"manifest.json", prov)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--controller", default="online-pes-adaptive",
                         choices=["classical", "fixed-residual", "adaptive-residual",
                                  "online-pes", "online-pes-fixed", "online-pes-adaptive"])
    parser.add_argument("--mission", default="vendor-demo", choices=["vendor-demo", "hover"])
    parser.add_argument("--duration", type=float, default=20.0)
    parser.add_argument("--dt", type=float, default=1e-3)
    parser.add_argument("--beta", type=float, default=0.5)
    parser.add_argument("--learning-rate", type=float, default=8e-4)
    parser.add_argument("--k-error", type=float, default=8.0)
    parser.add_argument("--k-rate", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output = HOVER_ROOT/"results"/"offline"/f"{args.controller}_{args.mission}_{timestamp}"

    summary = run(
        controller_name=args.controller, mission=args.mission, duration=args.duration,
        dt=args.dt, beta=args.beta, learning_rate=args.learning_rate,
        k_error=args.k_error, k_rate=args.k_rate, seed=args.seed, output=output,
    )
    print(f"angle_err_mean_deg={summary['angle_err_mean_deg']:.4f}  "
          f"angle_err_max_deg={summary['angle_err_max_deg']:.4f}")
    print(f"voltage range seen: [{summary['min_voltage_seen']:.3f}, {summary['max_voltage_seen']:.3f}] V")
    print(f"trace: {summary['trace']}")


if __name__ == "__main__":
    main()
