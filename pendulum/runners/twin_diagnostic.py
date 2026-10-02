"""Qube Servo 3 PENDULUM twin — safe diagnostic (NO motor voltage).

Purpose
-------
1. Confirm the QLabs connection (virtual card = port 18923 for Qube3 + pendulum).
2. Exercise and verify the LEDs so they are visibly registered in QLabs.
3. Log EVERY parameter the PAL API exposes, with units.
4. Determine the resting pendulum convention: is encoder zero HANGING or UPRIGHT?
   This decides whether alpha must be shifted by pi before balance control.

Safety: writes 0 V for the whole run. The amplifier is enabled by the PAL
constructor; terminate() zeroes voltage, sets the LED red and disables it.

Usage:  python twin_diagnostic.py [seconds]
"""
from __future__ import annotations
import sys, time, json
from pathlib import Path

sys.path.insert(0, r"C:\Quanser\0_libraries\python")
import numpy as np
from pal.products.qube import QubeServo3

DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 6.0
HZ = 500.0
DT = 1.0 / HZ
CPR = 2048.0  # counts/rev after quadrature -> rad = 2*pi*counts/2048

def f(x):
    return float(np.asarray(x, dtype=float).reshape(-1)[0])

print("=" * 68)
print("QUBE SERVO 3 PENDULUM — TWIN DIAGNOSTIC (no voltage commanded)")
print("=" * 68)
print(f"target: virtual card, tcpip://localhost:18923  (version=3, pendulum=1)")

qube = QubeServo3(id=0, hardware=0, frequency=int(HZ), pendulum=1, readMode=1)
if not qube.card.is_valid():
    print("FAILED: card invalid — is the QLabs Qube pendulum scene running?")
    sys.exit(1)
print("connection: OK  (card valid)")
print(f"board options: {qube._boardSpecificOptions}")
print(f"read channels -> analog {qube.READ_ANALOG_CHANNELS.tolist()}, "
      f"encoder {qube.READ_ENCODER_CHANNELS.tolist()}, "
      f"digital {qube.READ_DIGITAL_CHANNELS.tolist()}, "
      f"other {qube.READ_OTHER_CHANNELS.tolist()}")
print(f"write channels -> analog {qube.WRITE_ANALOG_CHANNELS.tolist()}, "
      f"digital {qube.WRITE_DIGITAL_CHANNELS.tolist()}, "
      f"other(LED) {qube.WRITE_OTHER_CHANNELS.tolist()}")

results = {"card_valid": True, "board_options": qube._boardSpecificOptions}

try:
    # ---------- 1. LED check (visible in QLabs) ----------
    print("\n--- LED CHECK — watch the Qube base in QLabs ---")
    led_seq = [("RED", [1, 0, 0]), ("GREEN", [0, 1, 0]), ("BLUE", [0, 0, 1]),
               ("YELLOW", [1, 1, 0]), ("WHITE", [1, 1, 1]), ("OFF", [0, 0, 0])]
    for name, rgb in led_seq:
        qube.write_led(np.array(rgb, dtype=np.float64))
        print(f"  LED -> {name:7s} rgb={rgb}")
        time.sleep(0.6)
    qube.write_led(np.array([0, 1, 0], dtype=np.float64))
    print("  LED -> GREEN (idle/ready)")
    results["led_sequence_ok"] = True

    # ---------- 2. Read every parameter at rest ----------
    print("\n--- RESTING STATE (0 V commanded) ---")
    qube.write_voltage(0.0)
    time.sleep(0.5)
    samples = []
    n = int(DUR * HZ)
    t0 = time.perf_counter()
    next_t = t0 + DT
    for k in range(n):
        qube.read_outputs()
        qube.write_voltage(0.0)  # explicit: stay at zero
        samples.append(dict(
            t=time.perf_counter() - t0,
            motor_counts=f(qube.motorEncoderCounts),
            pend_counts=f(qube.pendulumEncoderCounts),
            theta_rad=f(qube.motorPosition),
            alpha_raw_rad=f(qube.pendulumPosition),
            motor_speed=f(qube.motorSpeed),
            pend_speed=f(qube.pendulumSpeed),
            current=f(qube.motorCurrent),
            amp_fault=f(qube.amplifierFault),
            stall_det=f(qube.motorStallDetected),
            stall_err=f(qube.motorStallError),
        ))
        rem = next_t - time.perf_counter()
        if rem > 0:
            time.sleep(rem)
        next_t += DT

    last = samples[-1]
    arr = lambda k: np.array([s[k] for s in samples])
    dts = np.diff(arr("t"))
    realized = 1.0 / dts.mean()

    print(f"  samples: {len(samples)}   realized rate: {realized:.1f} Hz (target {HZ:.0f})")
    print(f"  motor  encoder counts : {last['motor_counts']:.0f}   theta = {last['theta_rad']:+.4f} rad "
          f"({np.degrees(last['theta_rad']):+.2f} deg)")
    print(f"  pend   encoder counts : {last['pend_counts']:.0f}   alpha_raw = {last['alpha_raw_rad']:+.4f} rad "
          f"({np.degrees(last['alpha_raw_rad']):+.2f} deg)")
    print(f"  motor speed (tach)    : {last['motor_speed']:+.4f} rad/s")
    print(f"  pend  speed (tach)    : {last['pend_speed']:+.4f} rad/s")
    print(f"  motor current         : {last['current']:+.4f} A")
    print(f"  amplifier fault       : {last['amp_fault']:.0f}")
    print(f"  motor stall detected  : {last['stall_det']:.0f}")
    print(f"  motor stall error     : {last['stall_err']:.0f}")
    print(f"  encoder scaling       : rad = 2*pi*counts/{CPR:.0f}  ({2*np.pi/CPR:.6e} rad/count)")

    # ---------- 3. Convention determination ----------
    a_raw = last["alpha_raw_rad"]
    a_wrapped = (a_raw + np.pi) % (2 * np.pi) - np.pi
    a_shift = (a_raw + 2 * np.pi) % (2 * np.pi) - np.pi  # alternative
    print("\n--- PENDULUM CONVENTION ---")
    print(f"  raw alpha at rest        : {a_raw:+.4f} rad ({np.degrees(a_raw):+.2f} deg)")
    print(f"  wrap_to_pi(raw)          : {a_wrapped:+.4f} rad ({np.degrees(a_wrapped):+.2f} deg)")
    print(f"  wrap(raw - pi)           : {(a_raw-np.pi+np.pi)%(2*np.pi)-np.pi:+.4f} rad")
    if abs(a_wrapped) < np.radians(15):
        verdict = ("ENCODER ZERO = RESTING (HANGING) position.  "
                   "alpha_upright = wrap(raw - pi).  The Julia convention is correct; "
                   "the Python balance law needs the -pi shift.")
    elif abs(abs(a_wrapped) - np.pi) < np.radians(15):
        verdict = ("ENCODER ZERO = UPRIGHT.  alpha_upright = wrap_to_pi(raw) directly. "
                   "The Python convention is correct as written.")
    else:
        verdict = (f"UNRESOLVED — pendulum is resting at {np.degrees(a_wrapped):+.1f} deg. "
                   "It may still be moving, or the scene zeroed mid-swing.")
    print(f"  VERDICT: {verdict}")
    results.update(dict(
        realized_hz=realized, alpha_raw_rest=a_raw, alpha_wrapped_rest=a_wrapped,
        verdict=verdict, motor_counts=last["motor_counts"], pend_counts=last["pend_counts"],
        amp_fault=last["amp_fault"], stall=last["stall_det"],
        rad_per_count=2 * np.pi / CPR,
    ))

    out = Path(__file__).resolve().parent.parent / "results" / "twin"
    out.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    (out / f"twin_diagnostic_{stamp}.json").write_text(json.dumps(results, indent=2))
    print(f"\nsaved: {out / f'twin_diagnostic_{stamp}.json'}")

finally:
    qube.terminate()
    print("shutdown: 0 V written, LED set RED, amplifier disabled, card closed.")
