"""Qube3 pendulum twin — HyperLIF gate residual with LEARNED decode + LED error gauge.

Ports the MuJoCo learned-gate architecture (Paper 5) onto the QLabs Qube twin.
Uses the SAME neuron implementations as the MuJoCo campaign by importing
`neuron_dynamics.make_direct_neuron` from neuromorphic-robotics-control, so
LIF / HyperLIF / Adaptive HyperLIF / Izhikevich are bit-identical code paths.

Architecture (Qube adaptation of the MuJoCo LearnedGate)
--------------------------------------------------------
    baseline   v_lqr = sign * K.x,  x = [theta, alpha, theta_dot, alpha_dot]
    encode     3 signals -> 6 pair-coded currents:
                 [alpha+, alpha-, alpha_dot+, alpha_dot-, v_norm+, v_norm-]
    neuron     6 gate units, activity_mode='gate', scale='control'
    decode     signed = clip(W @ activity, -1, 1),  W is 1x6
               W_init = [0,0,0,0,+1,-1]  -> fixed_gate reproduces the classic
               pair decode on the baseline command
    blend      v = (1-b)*v_lqr + b*(signed*V_bal)          [MuJoCo convention]
    learn      PES delta rule on W (online_pes / eprop_anneal)
                 target = clip(-k_err*alpha - k_rate*alpha_dot, -1, 1)
                 e_dec  = target - signed
                 W     += lr(t) * e_dec * act_used - leak*W ; clip

The residual is active ONLY while balancing; swing-up always uses the classical
energy law. The research question is whether the gate improves the EQUILIBRIUM.

LED error gauge (channels 11000/11001/11002, full RGB floats)
-------------------------------------------------------------
    swing-up : BLUE
    balance  : GREEN -> RED continuously, in proportion to |alpha|/CAPTURE_RAD
    shutdown : RED

Usage
-----
  python twin_hyperlif_residual.py [method] [neuron] [duration] [blend] [lr] [k_rate]
    method : baseline | fixed_gate | online_pes | eprop_anneal
    neuron : lif | hyperlif | adaptive_hyperlif | izhikevich
"""
from __future__ import annotations
import sys, time, json, csv
from pathlib import Path

sys.path.insert(0, r"C:\Quanser\0_libraries\python")
sys.path.insert(0, r"C:\02_Research\00_Code_Ecosystem\neuromorphic-robotics-control\experiments\controller_benchmarks")
import numpy as np
from pal.products.qube import QubeServo3
from neuron_dynamics import make_direct_neuron

METHOD = sys.argv[1] if len(sys.argv) > 1 else "online_pes"
NEURON = sys.argv[2] if len(sys.argv) > 2 else "hyperlif"
DUR    = float(sys.argv[3]) if len(sys.argv) > 3 else 25.0
BLEND  = float(sys.argv[4]) if len(sys.argv) > 4 else 0.25
LR     = float(sys.argv[5]) if len(sys.argv) > 5 else 8e-4
K_RATE = float(sys.argv[6]) if len(sys.argv) > 6 else 0.3

HZ = 500.0; DT = 1.0 / HZ
MU = 100.0; V_SW = 10.0; KC = 1.0
K = np.array([-1.000, 26.72, -0.8269, 2.214])
V_BAL = 5.0
CAPTURE_RAD = np.radians(20.0); CAPTURE_RATE = 6.0
CAPTURE_THETA = np.radians(110.0); HOLD_RAD = np.radians(35.0)
CPR = 2048.0
GATE_GAIN = 1e5
CURRENT_BIAS, CURRENT_GAIN = 0.75, 1.25
K_ERR = 8.0; LEAK = 1e-3; W_CLIP = 6.0
ALPHA_NORM, RATE_NORM = CAPTURE_RAD, 6.0

# Qube3 rotary pendulum parameters
Rm=7.5; kt=0.0422; mr=0.095; r=0.085; mp=0.024; Lp=0.129; l=Lp/2; g=9.81
Jp_cm = mp*Lp**2/12; Er = 2*mp*g*l
a_max = (kt*10.0/Rm)/(mr*r); ACC2V = mr*r*Rm/kt

wrap = lambda x: (x + np.pi) % (2*np.pi) - np.pi
def f(x): return float(np.asarray(x, dtype=float).reshape(-1)[0])

LED_IDLE = np.array([1.0, 0.0, 0.0]); LED_SWINGUP = np.array([0.0, 0.0, 1.0])
def led_gauge(alpha):
    """GREEN at alpha=0 -> RED at |alpha|>=CAPTURE_RAD (continuous RGB)."""
    e = float(np.clip(abs(alpha) / CAPTURE_RAD, 0.0, 1.0))
    return np.array([e, 1.0 - e, 0.0])

print("=" * 72)
print(f"QUBE3 TWIN — gate residual :: method={METHOD} neuron={NEURON} blend={BLEND}")
print("=" * 72)

learn = METHOD in ("online_pes", "eprop_anneal")
elig = anneal = (METHOD == "eprop_anneal")
use_residual = METHOD != "baseline"

neuron = make_direct_neuron(NEURON, n=6, activity_mode="gate", scale="control") if use_residual else None
W = np.array([0.0, 0.0, 0.0, 0.0, 1.0, -1.0])
e_trace = np.zeros(6)

qube = QubeServo3(id=0, hardware=0, frequency=int(HZ), pendulum=1, readMode=1)
if not qube.card.is_valid():
    print("FAILED: card invalid — is the QLabs Qube pendulum scene running?"); sys.exit(1)
print(f"connected 18923 | learn={learn} elig={elig} anneal={anneal} | W0={W.tolist()}")


def settle_and_reference(q, timeout=25.0, tol_rate=0.05, hold_s=1.0):
    """Wait for the pendulum to hang at rest, then return its raw angle.

    CRITICAL: the PAL constructor zeroes the encoders at whatever pose the
    pendulum happens to be in, so `raw` always reads 0 at startup. If a previous
    run left the pendulum upright, the naive `alpha = wrap(raw - pi)` convention
    is inverted. Referencing to the settled (hanging) raw angle makes the run
    correct from ANY starting pose.
    """
    t_start = time.perf_counter(); stable_since = None
    while time.perf_counter() - t_start < timeout:
        q.read_outputs(); q.write_voltage(0.0)
        if abs(f(q.pendulumSpeed)) < tol_rate:
            if stable_since is None:
                stable_since = time.perf_counter()
            elif time.perf_counter() - stable_since >= hold_s:
                return f(q.pendulumPosition), True
        else:
            stable_since = None
        time.sleep(DT)
    return f(q.pendulumPosition), False


qube.write_led(np.array([1.0, 1.0, 0.0]))  # YELLOW = settling
REST_RAW, settled = settle_and_reference(qube)
print(f"settle: rest_raw = {REST_RAW:+.4f} rad ({np.degrees(REST_RAW):+.2f} deg), "
      f"settled={settled} -> alpha = wrap(raw - rest_raw - pi)")

rows = []; n = int(DUR*HZ)
mode_prev = -1; catch_k = -1; streak = 0; best_streak = 0
act_sum = 0.0; res_sum = 0.0; res_steps = 0
t0 = time.perf_counter(); t_prev = t0; next_t = t0 + DT
try:
    qube.write_led(LED_IDLE)
    for k in range(n):
        qube.read_outputs()
        t = time.perf_counter(); dt_meas = t - t_prev; t_prev = t
        tt = t - t0
        theta = f(qube.motorPosition)
        alpha = wrap(f(qube.pendulumPosition) - REST_RAW - np.pi)
        theta_dot = f(qube.motorSpeed); alpha_dot = f(qube.pendulumSpeed)

        latched = (mode_prev == 1)
        capture = (abs(alpha) <= CAPTURE_RAD and abs(alpha_dot) <= CAPTURE_RATE
                   and abs(theta) <= CAPTURE_THETA)
        gate_mean = signed = residual_v = np.nan

        if capture or (latched and abs(alpha) <= HOLD_RAD):
            mode = 1
            if catch_k < 0: catch_k = k
            streak += 1; best_streak = max(best_streak, streak)
            v_lqr = float(np.clip(K[0]*theta + K[1]*alpha + K[2]*theta_dot + K[3]*alpha_dot,
                                  -V_BAL, V_BAL))
            if use_residual:
                a_n  = float(np.clip(alpha / ALPHA_NORM, -1, 1))
                ad_n = float(np.clip(alpha_dot / RATE_NORM, -1, 1))
                v_n  = float(np.clip(v_lqr / V_BAL, -1, 1))
                cur = np.array([
                    CURRENT_BIAS + CURRENT_GAIN*max(a_n, 0.0),
                    CURRENT_BIAS + CURRENT_GAIN*max(-a_n, 0.0),
                    CURRENT_BIAS + CURRENT_GAIN*max(ad_n, 0.0),
                    CURRENT_BIAS + CURRENT_GAIN*max(-ad_n, 0.0),
                    CURRENT_BIAS + CURRENT_GAIN*max(v_n, 0.0),
                    CURRENT_BIAS + CURRENT_GAIN*max(-v_n, 0.0)])
                res = neuron.step(cur, DT)
                act = np.clip(np.asarray(res.activity, dtype=float) * GATE_GAIN, 0.0, 1.0)
                signed = float(np.clip(W @ act, -1.0, 1.0))
                v_neu = signed * V_BAL
                v = float(np.clip((1.0 - BLEND)*v_lqr + BLEND*v_neu, -V_BAL, V_BAL))
                residual_v = BLEND*(v_neu - v_lqr)
                if learn:
                    target = float(np.clip(-K_ERR*a_n - K_RATE*ad_n, -1.0, 1.0))
                    e_dec = target - signed
                    if elig:
                        frac = np.clip(tt/DUR, 0, 1); decay = 0.98 - 0.48*frac
                        e_trace = decay*e_trace + (1.0-decay)*act
                        act_used = e_trace
                    else:
                        act_used = act
                    lr_now = LR*(1.0 - 0.8*np.clip(tt/DUR, 0, 1)) if anneal else LR
                    W = np.clip(W + lr_now*e_dec*act_used - LEAK*W, -W_CLIP, W_CLIP)
                gate_mean = float(act.mean())
                act_sum += gate_mean; res_sum += abs(residual_v); res_steps += 1
            else:
                v = v_lqr
            led = led_gauge(alpha)
        else:
            mode = 0; streak = 0
            E = 0.5*Jp_cm*alpha_dot**2 + mp*g*l*(1 + np.cos(alpha))
            u = float(np.clip(MU*(E-Er)*np.sign(alpha_dot*np.cos(alpha)) - KC*theta, -a_max, a_max))
            v = float(np.clip(ACC2V*u, -V_SW, V_SW))
            led = LED_SWINGUP
            if use_residual and neuron is not None and hasattr(neuron, "reset"):
                pass  # keep neuron state warm across brief excursions

        qube.write_voltage(v)
        if mode != mode_prev or mode == 1:
            qube.write_led(led)
            mode_prev = mode

        rows.append(dict(t=tt, dt=dt_meas, mode=mode, voltage=v,
                         theta=theta, alpha=alpha, alpha_deg=np.degrees(alpha),
                         theta_dot=theta_dot, alpha_dot=alpha_dot,
                         gate_mean=gate_mean, signed=signed, residual_v=residual_v,
                         current=f(qube.motorCurrent), amp_fault=f(qube.amplifierFault),
                         stall=f(qube.motorStallDetected)))
        rem = next_t - time.perf_counter()
        if rem > 0: time.sleep(rem)
        next_t += DT
finally:
    qube.write_voltage(0.0); qube.write_led(LED_IDLE); qube.terminate()
    print("shutdown: 0 V, LED RED, amplifier disabled, card closed.")

A = lambda key: np.array([r[key] for r in rows], dtype=float)
alpha = A("alpha"); mode = A("mode")
realized = 1.0/np.diff(A("t")).mean()
tail_n = int(min(4.0, DUR/4)*HZ); a_tail = alpha[-tail_n:]
bal_frac = float((mode[-tail_n:] == 1).mean())
rms_deg = float(np.degrees(np.sqrt((a_tail**2).mean())))
summary = dict(method=METHOD, neuron=NEURON, blend=BLEND, lr=LR, k_rate=K_RATE,
               duration_s=DUR, realized_hz=realized,
               first_capture_s=(catch_k/HZ if catch_k >= 0 else None),
               longest_hold_s=best_streak/HZ, balance_fraction_tail=bal_frac,
               alpha_rms_tail_deg=rms_deg,
               alpha_max_tail_deg=float(np.degrees(np.abs(a_tail).max())),
               gate_activity_mean=(act_sum/res_steps if res_steps else None),
               residual_abs_mean_V=(res_sum/res_steps if res_steps else None),
               W_final=W.tolist() if use_residual else None,
               amp_faults=int(A("amp_fault").sum()), stalls=int(A("stall").sum()))
print(f"\ncapture {summary['first_capture_s']}s | hold {summary['longest_hold_s']:.2f}s | "
      f"bal_frac {bal_frac:.3f} | alpha RMS {rms_deg:.3f} deg | rate {realized:.1f} Hz")
if use_residual and res_steps:
    print(f"gate act {summary['gate_activity_mean']:.4f} | |residual| {summary['residual_abs_mean_V']:.4f} V | "
          f"W_final {np.round(W,3).tolist()}")
elif use_residual:
    print("residual never engaged (no balance samples)")

out = Path(__file__).resolve().parent.parent / "results" / "twin_residual"
out.mkdir(parents=True, exist_ok=True)
stamp = time.strftime("%Y%m%d_%H%M%S")
tag = f"{METHOD}_{NEURON}_b{BLEND}_{stamp}"
with open(out / f"{tag}.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
(out / f"{tag}.json").write_text(json.dumps(summary, indent=2))
print(f"saved: {out / (tag + '.csv')}")
