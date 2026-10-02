"""Qube Servo 3 PENDULUM twin — energy swing-up + LQR balance (Python / PAL).

This is the Python reference for the equilibrium (upright balance) experiment on
the QLabs digital twin.  The Julia twin is `17_Julia_Quanser_Bridge/julia/
qube3_twin_swingup_balance.jl`; both must produce the same behaviour.

Conventions (VERIFIED by runners/twin_diagnostic.py on 2026-07-23)
------------------------------------------------------------------
* Virtual card = `0@tcpip://localhost:18923` (Qube3 + pendulum).
* Encoder zero is the RESTING (hanging) position, so
      alpha_upright = wrap(pendulumPosition - pi)     -> 0 rad == UPRIGHT
  The legacy `QuanserBalanceController` used wrap_to_pi(raw) with no shift,
  which regulates to HANGING on this twin.  Do not reuse it here.
* theta is taken with the raw PAL sign (no negation), matching the Julia bridge.
* rad = 2*pi*counts/2048 for both encoders.

Control
-------
Swing-up : Quanser energy law (sp6_pendulum_control / setup_swingup.m).
           Commands a PIVOT ACCELERATION, saturated at a_max, converted to volts.
Balance  : LQR  v = sign * K.x  with x = [theta, alpha, theta_dot, alpha_dot].

LED convention (visible in QLabs)
---------------------------------
  RED    : connected / idle / shutting down
  BLUE   : swing-up active
  GREEN  : balancing (upright equilibrium held)

Usage
-----
  python twin_swingup_balance.py [duration_s] [hz] [mu] [V_sw] [gains] [bal_sign]
    gains : "twin"   -> K = [-1.000, 26.72, -0.8269, 2.214]  (Quanser twin gain)
            "code"   -> K = [-1.2247, 24.9044, -0.6877, 3.1321] (repo code-truth)
"""
from __future__ import annotations
import sys, time, json, csv
from pathlib import Path

sys.path.insert(0, r"C:\Quanser\0_libraries\python")
import numpy as np
from pal.products.qube import QubeServo3

# ---------------- args ----------------
DUR      = float(sys.argv[1]) if len(sys.argv) > 1 else 20.0
HZ       = float(sys.argv[2]) if len(sys.argv) > 2 else 500.0
MU       = float(sys.argv[3]) if len(sys.argv) > 3 else 100.0
V_SW     = float(sys.argv[4]) if len(sys.argv) > 4 else 10.0
GAINSET  = sys.argv[5] if len(sys.argv) > 5 else "twin"
BAL_SIGN = float(sys.argv[6]) if len(sys.argv) > 6 else 1.0
KC       = 1.0          # arm-centring acceleration gain
DT       = 1.0 / HZ

# ------------- QUBE-Servo 3 rotary pendulum parameters (qube3_rotpen_param.m) -------------
Rm = 7.5;      kt = 0.0422
mr = 0.095;    r  = 0.085
mp = 0.024;    Lp = 0.129;   l = Lp / 2
g  = 9.81
Jp_cm   = mp * Lp**2 / 12          # inertia about CM (swing-up energy)
Er      = 2 * mp * g * l           # reference energy at the top  [J]
tau_max = kt * 10.0 / Rm           # motor torque at 10 V
a_max   = tau_max / (mr * r)       # max pivot acceleration [m/s^2]
ACC2V   = mr * r * Rm / kt         # pivot acceleration -> volts

GAINS = {
    "twin": np.array([-1.000, 26.72, -0.8269, 2.214]),
    "code": np.array([-1.2247, 24.9044, -0.6877, 3.1321]),
}
K = GAINS[GAINSET]
V_BAL         = 5.0
CAPTURE_RAD   = np.radians(20.0)
CAPTURE_RATE  = 6.0
CAPTURE_THETA = np.radians(110.0)
HOLD_RAD      = np.radians(35.0)   # latch: stay in balance until this is exceeded
CPR = 2048.0

LED_IDLE    = np.array([1.0, 0.0, 0.0])
LED_SWINGUP = np.array([0.0, 0.0, 1.0])
LED_BALANCE = np.array([0.0, 1.0, 0.0])

wrap = lambda x: (x + np.pi) % (2 * np.pi) - np.pi
def f(x):
    return float(np.asarray(x, dtype=float).reshape(-1)[0])

print("=" * 70)
print("QUBE3 PENDULUM TWIN — energy swing-up + LQR balance  (Python / PAL)")
print("=" * 70)
print(f"gains[{GAINSET}] K = {K.tolist()}   bal_sign = {BAL_SIGN:+.0f}   V_bal = {V_BAL} V")
print(f"mu = {MU}   V_sw = {V_SW} V   a_max = {a_max:.2f} m/s^2   Er = {Er:.4f} J   ACC2V = {ACC2V:.3f}")
print(f"capture: |alpha|<={np.degrees(CAPTURE_RAD):.0f}deg, |alpha_dot|<={CAPTURE_RATE} rad/s, "
      f"|theta|<={np.degrees(CAPTURE_THETA):.0f}deg;  hold until |alpha|>{np.degrees(HOLD_RAD):.0f}deg")

qube = QubeServo3(id=0, hardware=0, frequency=int(HZ), pendulum=1, readMode=1)
if not qube.card.is_valid():
    print("FAILED: card invalid — is the QLabs Qube pendulum scene running?")
    sys.exit(1)
print("connection OK (virtual card 18923); amplifier enabled by PAL constructor")

rows = []
n = int(DUR * HZ)
mode_prev = -1
catch_k = -1
streak = 0
best_streak = 0
t0 = time.perf_counter()
t_prev = t0
next_t = t0 + DT

try:
    qube.write_led(LED_IDLE)
    for k in range(n):
        qube.read_outputs()
        t = time.perf_counter()
        dt_meas = t - t_prev
        t_prev = t

        theta      = f(qube.motorPosition)
        alpha      = wrap(f(qube.pendulumPosition) - np.pi)   # 0 == UPRIGHT
        theta_dot  = f(qube.motorSpeed)
        alpha_dot  = f(qube.pendulumSpeed)

        latched = (mode_prev == 1)
        capture = (abs(alpha) <= CAPTURE_RAD and abs(alpha_dot) <= CAPTURE_RATE
                   and abs(theta) <= CAPTURE_THETA)
        if capture or (latched and abs(alpha) <= HOLD_RAD):
            mode = 1
            if catch_k < 0:
                catch_k = k
            streak += 1
            best_streak = max(best_streak, streak)
            v = float(np.clip(BAL_SIGN * (K[0]*theta + K[1]*alpha
                                          + K[2]*theta_dot + K[3]*alpha_dot),
                              -V_BAL, V_BAL))
            E = u_pump = u_center = u = np.nan
        else:
            mode = 0
            streak = 0
            E = 0.5 * Jp_cm * alpha_dot**2 + mp * g * l * (1 + np.cos(alpha))
            u_pump = MU * (E - Er) * np.sign(alpha_dot * np.cos(alpha))
            u_center = -KC * theta
            u = float(np.clip(u_pump + u_center, -a_max, a_max))
            v = float(np.clip(ACC2V * u, -V_SW, V_SW))

        qube.write_voltage(v)
        if mode != mode_prev:
            qube.write_led(LED_BALANCE if mode == 1 else LED_SWINGUP)
            mode_prev = mode

        rows.append(dict(
            t=t - t0, dt=dt_meas, mode=mode, voltage=v,
            theta=theta, alpha=alpha, theta_dot=theta_dot, alpha_dot=alpha_dot,
            alpha_deg=np.degrees(alpha), theta_deg=np.degrees(theta),
            energy=E, u_accel=u,
            motor_counts=f(qube.motorEncoderCounts),
            pend_counts=f(qube.pendulumEncoderCounts),
            current=f(qube.motorCurrent),
            amp_fault=f(qube.amplifierFault),
            stall_det=f(qube.motorStallDetected),
            stall_err=f(qube.motorStallError),
        ))
        rem = next_t - time.perf_counter()
        if rem > 0:
            time.sleep(rem)
        next_t += DT
finally:
    qube.write_voltage(0.0)
    qube.write_led(LED_IDLE)
    qube.terminate()
    print("shutdown: 0 V, LED RED, amplifier disabled, card closed.")

# ---------------- metrics ----------------
A = lambda key: np.array([r[key] for r in rows], dtype=float)
alpha = A("alpha"); mode = A("mode"); dts = A("dt")[1:]
realized = 1.0 / dts.mean()
tail_n = int(min(2.0, DUR / 4) * HZ)
a_tail = alpha[-tail_n:]
bal_frac = float((mode[-tail_n:] == 1).mean())
amp_faults = int(A("amp_fault").sum())
stalls = int(A("stall_det").sum())

print(f"\nsamples {len(rows)}   realized {realized:.1f} Hz")
print(f"first capture : {catch_k/HZ:.2f} s" if catch_k >= 0 else "first capture : NEVER")
print(f"longest hold  : {best_streak/HZ:.2f} s ({best_streak} samples)")
print(f"closest to top: {np.degrees(np.abs(alpha).min()):.2f} deg")
print(f"final {min(2.0,DUR/4):.1f}s -> balance fraction {bal_frac:.3f}, "
      f"alpha RMS {np.sqrt((a_tail**2).mean()):.4f} rad "
      f"({np.degrees(np.sqrt((a_tail**2).mean())):.2f} deg), "
      f"|alpha|max {np.degrees(np.abs(a_tail).max()):.2f} deg")
print(f"amplifier faults {amp_faults}   stalls {stalls}")

out = Path(__file__).resolve().parent.parent / "results" / "twin"
out.mkdir(parents=True, exist_ok=True)
stamp = time.strftime("%Y%m%d_%H%M%S")
tag = f"python_{GAINSET}_sign{int(BAL_SIGN):+d}_{stamp}"
with open(out / f"twin_swingup_{tag}.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
summary = dict(
    impl="python_pal", gains=GAINSET, K=K.tolist(), bal_sign=BAL_SIGN,
    duration_s=DUR, hz=HZ, realized_hz=realized, mu=MU, v_sw=V_SW, v_bal=V_BAL,
    first_capture_s=(catch_k / HZ if catch_k >= 0 else None),
    longest_hold_s=best_streak / HZ, balance_fraction_tail=bal_frac,
    alpha_rms_tail_rad=float(np.sqrt((a_tail**2).mean())),
    alpha_max_tail_deg=float(np.degrees(np.abs(a_tail).max())),
    closest_to_top_deg=float(np.degrees(np.abs(alpha).min())),
    amp_faults=amp_faults, stalls=stalls,
    params=dict(Rm=Rm, kt=kt, mr=mr, r=r, mp=mp, Lp=Lp, l=l, g=g,
                Jp_cm=Jp_cm, Er=Er, a_max=a_max, ACC2V=ACC2V, CPR=CPR),
)
(out / f"twin_swingup_{tag}.json").write_text(json.dumps(summary, indent=2))
print(f"saved: {out / f'twin_swingup_{tag}.csv'}")
