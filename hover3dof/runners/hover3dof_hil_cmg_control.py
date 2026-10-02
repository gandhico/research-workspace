r"""Closed-loop control of the physical Quanser 3DOF Hover.

Combines the vendor's own validated LQR baseline (exact K matrix
reproduced from the Laboratory Guide / setup_lab_hover.m via MATLAB on
2026-08-27) with the ACC2027 online-PES adaptive CMG-PES residual, via the
canonical gra_control.hardware_bridges.SafeGateBridge (not reimplemented).

READ docs\\SAFETY_CHECKLIST.md BEFORE running this with --armed.

VERIFIED CHANNEL MAP (physical pulse test, 2026-08-27, this specific unit):
  Analog Output 0 -> Front, 1 -> Back, 2 -> Left, 3 -> Right
  Encoder 0 -> Pitch, 1 -> Roll, 2 -> Yaw

Defaults are maximally conservative: NOT armed (writes zero regardless of
what the controller computes), controller=classical (no CMG at all),
beta=0, duration capped at 30s per invocation, mission=hover (hold-level,
no step commands). Escalate explicitly and incrementally,
per the staged sequence in docs\\SAFETY_CHECKLIST.md: sensor-only (no
--armed) -> shadow (--controller set, still no --armed, watch the printed
residual/gate values) -> classical --armed (confirms the vendor baseline
alone balances on this rig) -> low-beta single controller --armed.

On ANY exit path, including an exception or Ctrl-C, all 4 channels are
forced to 0V before the program exits (try/finally). Every run writes
trace.csv / summary.json / manifest.json under results\hardware\, matching
the same provenance convention as the offline surrogate runner.
"""
from __future__ import annotations

import argparse
import array as arr
import csv
import time
from pathlib import Path

import numpy as np
from quanser.hardware import HIL, HILError

from gra_control.gate import CMGResidualAugmentor
from gra_control.hardware_bridges import SafeGateBridge
from gra_control.math3d import reference_euler
from gra_control.provenance import manifest, write_json

ACC_ROOT = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control")
HOVER_ROOT = Path(__file__).resolve().parents[1]

K_AMP = 3.0        # amplifier gain, user-confirmed 2026-08-27 (matches vendor setup_lab_hover.m)
V_MAX_AMP = 24.0   # motor-equivalent volts, vendor saturation (setup_lab_hover.m VMAX_AMP)
V_MAX_DAC = 10.0   # Q8-USB hardware analog-output ceiling (setup_lab_hover.m VMAX_DAC)
V_BIAS = 2.0       # motor-equivalent bias volts (setup_lab_hover.m V_bias)

# Encoder sensitivity, rad/count (config_hover.m -- note yaw's sign is vendor-negated).
K_EC_PITCH = 2*np.pi/(8*1024)
K_EC_ROLL = 2*np.pi/(8*1024)
K_EC_YAW = -2*np.pi/(8*1024)

# Bandlimited (high-pass) derivative for the velocity states, matching the vendor's
# own "Filter and Rate Limiter Settings" (setup_lab_hover.m: wcf = 2*pi*20 rad/s,
# zetaf = 0.8) and the Laboratory Guide's own note that the Simulink model uses
# "high-pass filters ... to obtain the velocity states" rather than a raw
# backward-difference of the encoder angle:
#   H(s) = wcf^2 * s / (s^2 + 2*zetaf*wcf*s + wcf^2)
# implemented as forward-Euler integration of the controllable-canonical-form
# state space. A raw finite difference of quantized encoder counts injects
# quantization noise straight into the LQR's rate-feedback terms (~30-40 gain) --
# this filter is what the vendor's own tuning was validated against.
WCF = 2*np.pi*20.0
ZETAF = 0.8


class RateFilter:
    def __init__(self, n: int):
        self.x1 = np.zeros(n)
        self.x2 = np.zeros(n)

    def step(self, u: np.ndarray, dt: float) -> np.ndarray:
        x1_dot = self.x2
        x2_dot = -WCF*WCF*self.x1-2*ZETAF*WCF*self.x2+u
        self.x1 = self.x1+dt*x1_dot
        self.x2 = self.x2+dt*x2_dot
        return WCF*WCF*self.x2

# Exact vendor LQR gain (Q=diag([500,350,350,0,20,20]), R=0.01*I4), reproduced via
# MATLAB lqr(A,B,Q,R) on this machine 2026-08-27 -- matches the Laboratory Guide's
# Sec. 2.2.2 K matrix to displayed precision.
#
# Row order here is [Vf, Vb, Vl, Vr] -- i.e. matched to this unit's VERIFIED
# physical Analog Output order (AO0=Front, AO1=Back, AO2=Left, AO3=Right, see
# docs\SAFETY_CHECKLIST.md), NOT the Lab Guide's own [Vf,Vb,Vr,Vl] convention.
# The Lab Guide's K rows 3 and 4 (Vr, Vl) are swapped below for exactly this
# reason -- writing the Guide's row order straight to AO[2],AO[3] silently
# inverted the sign of roll correction (confirmed on hardware 2026-08-27: roll
# ran away monotonically to -60+ deg instead of holding near zero). Columns =
# state x = [yaw, pitch, roll, yaw_dot, pitch_dot, roll_dot].
K_LQR = np.array([
    [-111.8034,  132.2876,    0.0,     -41.4128,   36.2268,    0.0],       # Vf
    [-111.8034, -132.2876,    0.0,     -41.4128,  -36.2268,    0.0],       # Vb
    [ 111.8034,    0.0,    -132.2876,   41.4128,    0.0,     -36.2268],    # Vl (AO2)
    [ 111.8034,    0.0,     132.2876,   41.4128,    0.0,      36.2268],    # Vr (AO3)
])

MODES = {
    "fixed-residual": ("residual", False),
    "adaptive-residual": ("residual", True),
    "online-pes-adaptive": ("online_pes", True),
}


def read_angles(card: HIL, enc_channels: arr.array, counts: arr.array) -> np.ndarray:
    card.read_encoder(enc_channels, 3, counts)
    pitch = counts[0]*K_EC_PITCH
    roll = counts[1]*K_EC_ROLL
    yaw = counts[2]*K_EC_YAW
    return np.array([yaw, pitch, roll])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--armed", action="store_true",
                         help="Write nonzero voltage. Omit for a zero-output sensor-only/shadow dry run.")
    parser.add_argument("--controller", default="classical",
                         choices=["classical", *MODES.keys()])
    parser.add_argument("--beta", type=float, default=0.0)
    parser.add_argument("--learning-rate", type=float, default=5e-4)
    parser.add_argument("--k-error", type=float, default=8.0,
                         help="Learning-target position-error gain, matching the MuJoCo "
                              "drone controllers' k_error (gra_control.platforms.drone).")
    parser.add_argument("--k-rate", type=float, default=0.0,
                         help="Learning-target rate gain, matching the MuJoCo drone "
                              "controllers' k_rate.")
    parser.add_argument("--max-residual-volts", type=float, default=0.5,
                         help="Per-motor CMG residual bound, motor-equivalent volts.")
    parser.add_argument("--duration", type=float, default=5.0)
    parser.add_argument("--rate-hz", type=float, default=200.0)
    parser.add_argument("--mission", default="hover",
                         choices=["hover", "roll", "full3", "hard45", "hardstep", "yaw360"],
                         help="Reference trajectory, from the exact gra_control.math3d.reference_euler "
                              "used by the MuJoCo X2/CF2 runs -- same code, for direct cross-platform "
                              "comparability. reference_euler returns [roll,pitch,yaw]; remapped below "
                              "to this script's [yaw,pitch,roll] state order.")
    args = parser.parse_args()

    if args.duration > 30.0:
        raise SystemExit("Refusing to run more than 30s in one invocation. "
                          "Validate shorter runs first, then re-run with a longer explicit --duration.")

    bridge = None
    if args.controller != "classical":
        mode, adaptive = MODES[args.controller]
        limits = np.full(4, args.max_residual_volts)
        bridge = SafeGateBridge(limits, mode=mode, adaptive_conductance=adaptive,
                                 beta=args.beta, slew_per_second=np.full(4, 4.0))
        if mode == "online_pes":
            bridge.augmentor = CMGResidualAugmentor(
                4, limits, "online_pes", True, args.beta, learning_rate=args.learning_rate,
            )

    card = HIL()
    card.open("q8_usb", "0")
    ao_channels = arr.array("i", [0, 1, 2, 3])
    zero = arr.array("d", [0.0]*4)
    enc_channels = arr.array("i", [0, 1, 2])
    counts = arr.array("i", [0, 0, 0])

    # Incremental encoders have no absolute zero -- they count from wherever they
    # happened to be when this process's HIL handle started (which may carry over
    # state from earlier runs/tests). Tare against the current reading, which is
    # assumed to be the physically level pose you already balanced per
    # docs\SAFETY_CHECKLIST.md Sec 3.2. All control below is relative to this.
    angle_home = read_angles(card, enc_channels, counts)
    print(f"Tared at startup: home angles (raw) = {np.rad2deg(angle_home)} deg")

    dt = 1.0/args.rate_hz
    n_steps = int(args.duration*args.rate_hz)
    rate_filter = RateFilter(3)
    rows: list[dict] = []

    print(f"armed={args.armed} controller={args.controller} beta={args.beta} "
          f"max_residual_volts={args.max_residual_volts} duration={args.duration}s "
          f"rate={args.rate_hz}Hz mission={args.mission}")
    print("Ctrl-C at any time forces all 4 channels to 0V and exits.")

    try:
        card.write_analog(ao_channels, 4, zero)
        for k in range(n_steps):
            t0 = time.perf_counter()

            angles = read_angles(card, enc_channels, counts)-angle_home  # [yaw, pitch, roll], relative to tare
            rates = rate_filter.step(angles, dt)

            ref_rpy = reference_euler(k*dt, args.mission, args.duration)  # [roll, pitch, yaw]
            setpoint = np.array([ref_rpy[2], ref_rpy[1], ref_rpy[0]])     # -> [yaw, pitch, roll]

            x = np.concatenate([angles, rates])
            # Reference rate is always zero, matching the vendor's own Eq. 2.5 x_d
            # convention (setup_lab_hover.m) -- the rate-feedback term acts as pure
            # damping against any state rate, not as a moving-target rate tracker.
            err = np.concatenate([setpoint, np.zeros(3)])-x
            u_baseline = K_LQR @ err+V_BIAS  # [Vf, Vb, Vl, Vr], motor-equivalent volts (AO0-AO3 order)
            u_baseline = np.clip(u_baseline, 0.0, V_MAX_AMP)

            if bridge is None:
                command = u_baseline if args.armed else np.zeros(4)
                residual_norm, gate_mean = 0.0, 0.0
                neuron_v = neuron_r = None
            else:
                # CMGResidualAugmentor.step(baseline, dt, learning_target) uses TWO
                # DISTINCT signals, matching gra_control.platforms.drone.py's actual
                # MuJoCo controller (drone.py:191-199, the source of the paper's proven
                # results):
                #   - `baseline` drives the gate's own firing current (gate.py:
                #     current = f(baseline/limits)) -- in drone.py this is `tau0`, the
                #     FULL K_LQR/PD-weighted baseline command (kq, kw gains).
                #   - `learning_target` only steers the online-PES decoder weights -- in
                #     drone.py this is a SEPARATELY, independently-weighted view of the
                #     same state error (k_error, k_rate gains, distinct from kq/kw).
                # An earlier version of this script fed the IDENTICAL signal into both
                # roles -- gate excitation and its own supervision target were the same
                # variable, giving the decoder zero room to diverge from a saturated copy
                # of that one proxy (confirmed on hardware: gate reached ~0.96 engagement,
                # residual ~1V average, real authority genuinely used -- yet tracking error
                # vs. classical was within +/-0.5%, no benefit despite real engagement).
                # Fix: `gate_drive` goes back to the K_LQR-weighted view of u_baseline
                # (matching drone.py's tau0 role) rescaled into +/-max_residual_volts so it
                # still only excites the gate within the reviewed safety bound; the K_LQR
                # bound never expands -- only `out.residual` (bounded to +/-beta*max_residual_volts)
                # gets added to the untouched full-authority u_baseline afterward.
                # `learning_target` keeps the independently-weighted k_error/k_rate signal.
                gate_drive = np.clip((u_baseline-V_BIAS)/(V_MAX_AMP-V_BIAS), -1.0, 1.0)*args.max_residual_volts
                yaw_t, pitch_t, roll_t = args.k_error*err[0:3]+args.k_rate*err[3:6]
                target = np.clip(np.array([
                    pitch_t-yaw_t, -pitch_t-yaw_t, -roll_t+yaw_t, roll_t+yaw_t,
                ]), -1.0, 1.0)
                out = bridge.step(gate_drive, target, dt, armed=True)
                residual_norm, gate_mean = float(np.linalg.norm(out.residual)), out.gate_mean
                residual_to_apply = out.residual if args.armed else np.zeros(4)
                command = u_baseline+residual_to_apply
                # CoupledMembraneGateBank internal state, post-step -- same fields the
                # MuJoCo rerun_with_euler_logging.py script logs. 8 units here (2*4
                # channels: Vf,Vb,Vl,Vr each split into a positive/negative branch),
                # vs. 6 for the drones (2*3 torque axes).
                neuron_v = bridge.augmentor.units.v.copy()
                neuron_r = bridge.augmentor.units.r.copy()

            command = np.clip(command, 0.0, V_MAX_AMP)
            dac = np.clip(command/K_AMP, 0.0, V_MAX_DAC)
            card.write_analog(ao_channels, 4, arr.array("d", dac.tolist()))

            row = {
                "t": k*dt,
                "yaw_deg": np.rad2deg(angles[0]), "pitch_deg": np.rad2deg(angles[1]), "roll_deg": np.rad2deg(angles[2]),
                "yaw_ref_deg": np.rad2deg(setpoint[0]), "pitch_ref_deg": np.rad2deg(setpoint[1]), "roll_ref_deg": np.rad2deg(setpoint[2]),
                "yaw_rate_dps": np.rad2deg(rates[0]), "pitch_rate_dps": np.rad2deg(rates[1]), "roll_rate_dps": np.rad2deg(rates[2]),
                "Vf": command[0], "Vb": command[1], "Vl": command[2], "Vr": command[3],
                "residual_norm": residual_norm, "gate_mean": gate_mean,
            }
            if neuron_v is not None:
                for i, (vv, rr) in enumerate(zip(neuron_v, neuron_r)):
                    row[f"neuron_v_{i}"] = vv
                    row[f"neuron_r_{i}"] = rr
            rows.append(row)

            if k % int(args.rate_hz) == 0:
                print(f"t={k*dt:5.2f}s yaw={np.rad2deg(angles[0]):6.2f} pitch={np.rad2deg(angles[1]):6.2f} "
                      f"roll={np.rad2deg(angles[2]):6.2f}deg  cmd_V={np.round(command, 2)}  "
                      f"residual_norm={residual_norm:.3f} gate={gate_mean:.3f}")

            elapsed = time.perf_counter()-t0
            if elapsed < dt:
                time.sleep(dt-elapsed)
    finally:
        card.write_analog(ao_channels, 4, zero)
        card.close()
        print("All 4 channels forced to 0V. Closed.")

        if rows:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            armed_tag = "armed" if args.armed else "dryrun"
            output = HOVER_ROOT/"results"/"hardware"/f"{args.controller}_{armed_tag}_{timestamp}"
            output.mkdir(parents=True, exist_ok=True)

            csv_path = output/"trace.csv"
            with csv_path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                writer.writeheader(); writer.writerows(rows)

            actual = np.array([[r["yaw_deg"], r["pitch_deg"], r["roll_deg"]] for r in rows])
            ref = np.array([[r["yaw_ref_deg"], r["pitch_ref_deg"], r["roll_ref_deg"]] for r in rows])
            err_mag = np.linalg.norm(actual-ref, axis=1)
            summary = {
                "platform": "hover3dof_hardware", "hardware": True,
                "controller": args.controller, "armed": args.armed, "beta": args.beta,
                "learning_rate": args.learning_rate, "max_residual_volts": args.max_residual_volts,
                "k_error": args.k_error, "k_rate": args.k_rate,
                "duration": args.duration, "rate_hz": args.rate_hz, "mission": args.mission,
                "angle_err_mean_deg": float(np.mean(err_mag)), "angle_err_max_deg": float(np.max(err_mag)),
                "n_steps_logged": len(rows), "trace": str(csv_path),
            }
            args_dict = {
                "controller": args.controller, "armed": args.armed, "beta": args.beta,
                "learning_rate": args.learning_rate, "max_residual_volts": args.max_residual_volts,
                "k_error": args.k_error, "k_rate": args.k_rate,
                "duration": args.duration, "rate_hz": args.rate_hz, "mission": args.mission,
            }
            try:
                prov = manifest(ACC_ROOT, "hover3dof_hardware", args.controller, Path(__file__), args_dict)
                write_json(output/"manifest.json", prov)
            except Exception as ex:
                print(f"(manifest write skipped: {ex})")
            write_json(output/"summary.json", summary)
            print(f"angle_err_mean_deg={summary['angle_err_mean_deg']:.3f}  "
                  f"angle_err_max_deg={summary['angle_err_max_deg']:.3f}")
            print(f"results: {output}")


if __name__ == "__main__":
    try:
        main()
    except HILError as ex:
        print(f"HIL error: {ex.get_error_message()}")
        raise
