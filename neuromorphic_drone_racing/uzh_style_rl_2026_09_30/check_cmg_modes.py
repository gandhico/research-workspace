"""Parity of the batched CMG cells with cmg_cells.py in all four modes, plus each mode's event activity under the
policy's current range (the operating condition that decides whether a spiking readout carries signal)."""
import json
import sys
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "rl_cmg_2026_09_30"))
from vec_race import CMGBatch  # noqa: E402
from cmg_cells import CMGPopulation, policy_preset  # noqa: E402

torch.set_num_threads(1)
rng = np.random.default_rng(3)
cur = rng.uniform(0.05, 2.2, size=(2400, 32))                    # 1.2 s of random currents in the encoder's range
out = {}
for mode in CMGBatch.MODES:
    ref = CMGPopulation(32, mode, policy_preset(mode))
    bat = CMGBatch(1, 32, mode, torch.float64)
    worst = 0.0
    for j in cur:
        f = ref.step(j, 0.0005)
        bat.step(torch.as_tensor(j)[None], 0.0005)
        worst = max(worst, float(np.abs(f - bat.features()[0].numpy()).max()),
                    float(np.abs(ref.v - bat.v[0].numpy()).max()))
    rate = bat.events[0].numpy() / (len(cur) * 0.0005)
    out[mode] = dict(max_abs_diff=worst, mean_event_rate_hz=float(rate.mean()),
                     fraction_units_spiking=float((rate > 0).mean()), mean_feature=float(bat.features().mean()))
print(json.dumps(out, indent=1))
(HERE / "results" / "cmg_modes_check.json").write_text(json.dumps(out, indent=1))
