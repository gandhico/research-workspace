"""Read-only probe of the 3 DOF Gyroscope's Q8-USB (board q8_usb, id 0).

No writes of any kind: no analog outputs (motor current commands), no digital outputs
(Quanser's model drives DO0-3 as active-low amplifier enables), no encoder resets, and no
channel configuration. It reads identity, encoders 0-7 (raw counts), and analog inputs 0-7.

Channel meaning from Quanser's q_3dgyro_lqr.mdl: enc0 = disc (4096 counts/rev), enc1-3 =
gimbals (4000 counts/rev, enc3 sign-flipped); which gimbal is which is confirmed by hand.
"""
import json
import sys
import time

import numpy as np
from quanser.hardware import HIL, HILError, IntegerProperty as IP, StringProperty as SP


def main(board_id="0", duration=2.0, rate_hz=50.0):
    card = HIL()
    try:
        card.open("q8_usb", board_id)
    except HILError as e:
        print(json.dumps({"connected": False, "error": e.get_error_message()}, indent=2))
        return 2
    rep = {"connected": True}
    try:
        props = {}
        for n in ("VENDOR_ID", "PRODUCT_ID", "FIRMWARE_MAJOR_VERSION", "FIRMWARE_MINOR_VERSION"):
            try:
                b = np.zeros(1, dtype=np.int32)
                card.get_integer_property(np.array([getattr(IP, n)], dtype=np.int32), 1, b)
                props[n] = int(b[0])
            except HILError as e:
                props[n] = f"n/a ({e.get_error_message()})"
        for n in ("MANUFACTURER", "PRODUCT_NAME", "MODEL_NAME", "SERIAL_NUMBER", "FIRMWARE_VERSION"):
            try:
                props[n] = card.get_string_property(getattr(SP, n), 128)
            except HILError as e:
                props[n] = f"n/a ({e.get_error_message()})"
        rep["properties"] = props

        enc_ch = np.arange(8, dtype=np.uint32)
        ai_ch = np.arange(8, dtype=np.uint32)
        enc = np.zeros(8, dtype=np.int32)
        ai = np.zeros(8)
        E, A, T = [], [], []
        t0 = time.perf_counter()
        for k in range(int(duration * rate_hz)):
            while time.perf_counter() < t0 + k / rate_hz:
                pass
            T.append(time.perf_counter() - t0)
            card.read_encoder(enc_ch, 8, enc)
            ai[:] = np.nan
            card.read_analog(ai_ch, 8, ai)
            E.append(enc.copy()); A.append(ai.copy())
        E, A = np.array(E), np.array(A)
        rep["encoders"] = {f"enc{i}": {"first": int(E[0, i]), "last": int(E[-1, i]),
                                       "span_counts": int(E[:, i].max() - E[:, i].min())} for i in range(8)}
        rep["disc_rpm_estimate"] = float((E[-1, 0] - E[0, 0]) / 4096 / (T[-1] - T[0]) * 60)
        rep["analog_in_V"] = {f"ai{i}": {"mean": round(float(np.nanmean(A[:, i])), 4),
                                         "std": round(float(np.nanstd(A[:, i])), 4)} for i in range(8)}
        rep["samples"] = len(T)
    finally:
        card.close()
    print(json.dumps(rep, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "0"))
