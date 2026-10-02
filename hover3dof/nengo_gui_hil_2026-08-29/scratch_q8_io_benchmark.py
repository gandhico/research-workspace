"""Isolated timing benchmark of the raw Q8 read/write round-trip, no GUI/Nengo/
threading involved -- writes zero volts only (identical to what _open_q8()
already does at startup), reads encoders. Safe: no motor engagement.
"""
import array as arr
import time

import numpy as np
from quanser.hardware import HIL

K_EC_PITCH = 2 * np.pi / (8192 * 4)
K_EC_ROLL = 2 * np.pi / (8192 * 4)
K_EC_YAW = 2 * np.pi / (8192 * 4)

card = HIL()
card.open("q8_usb", "0")
ao_channels = arr.array("i", [0, 1, 2, 3])
encoder_channels = arr.array("i", [0, 1, 2])
counts = arr.array("i", [0, 0, 0])
zero = arr.array("d", [0.0] * 4)

card.write_analog(ao_channels, 4, zero)

n = 500
read_times = []
write_times = []
for _ in range(n):
    t0 = time.perf_counter()
    card.read_encoder(encoder_channels, 3, counts)
    t1 = time.perf_counter()
    card.write_analog(ao_channels, 4, zero)
    t2 = time.perf_counter()
    read_times.append(t1 - t0)
    write_times.append(t2 - t1)

card.write_analog(ao_channels, 4, zero)
card.close()

read_times = np.array(read_times)
write_times = np.array(write_times)
total = read_times + write_times
print(f"n={n}")
print(f"read : mean={read_times.mean()*1000:.3f}ms  median={np.median(read_times)*1000:.3f}ms  p95={np.percentile(read_times,95)*1000:.3f}ms  max={read_times.max()*1000:.3f}ms")
print(f"write: mean={write_times.mean()*1000:.3f}ms  median={np.median(write_times)*1000:.3f}ms  p95={np.percentile(write_times,95)*1000:.3f}ms  max={write_times.max()*1000:.3f}ms")
print(f"total: mean={total.mean()*1000:.3f}ms  median={np.median(total)*1000:.3f}ms  p95={np.percentile(total,95)*1000:.3f}ms  max={total.max()*1000:.3f}ms")
print(f"fraction of read+write pairs alone exceeding 5ms budget: {(total > 0.005).mean()*100:.1f}%")
