import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
d = HERE / "results" / "supplementary_izhikevich" / "x2" / "hard45" / "nengo_izhikevich_pes"
tr = pd.read_csv(d / "trace.csv")
print(len(tr), "rows;", "t:", tr.t.min(), "-", tr.t.max())
for c in ("current_0", "voltage_0", "gate_0", "activity_0", "residual_x", "decoder_w_0"):
    v = tr[c].to_numpy()
    print(f"{c:12s} min {v.min():10.4f}  max {v.max():10.4f}  mean {v.mean():10.4f}")
sch = json.load(open(d / "neural_trace_schema.json"))
print("\nNPZ signals:", list(sch["signals"].keys()))
print("neuron_family_metadata:", json.load(open(d / "summary.json")).get("neuron_family_metadata"))
z = np.load(d / "neural_trace_full_rate.npz")
for k in ("voltage", "gate", "activity", "raw_output", "recovery"):
    if k in z:
        v = z[k]
        print(f"npz {k:10s} shape {v.shape} min {v.min():9.4f} max {v.max():9.4f} mean {v.mean():9.4f}")
