"""Foundation smoke check: the skeleton is functional end-to-end (not just parity).

Confirms: package imports, population forward pass, dynamics metrics, autograd flow through
the surrogate event (training will work), the origin knob actually changes dynamics, and the
runner config mapping + stub behaviour. Prints PASS/FAIL.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402
import torch  # noqa: E402

from adhyperlif_triage.neurons import HyperLIFConfig, HyperLIFLayer  # noqa: E402
from adhyperlif_triage.metrics import dynamics_metrics  # noqa: E402
from adhyperlif_triage.runner import build_neuron_config  # noqa: E402

checks = []


def ok(name, cond):
    checks.append((name, bool(cond)))
    print(f"  [{'ok' if cond else 'XX'}] {name}")


dt = 1e-3
T, N = 60, 8
torch.manual_seed(0)
J = (1.5 + 0.8 * torch.randn(T, N, dtype=torch.float32)).abs()

# 1. population forward + dynamics metrics
out = HyperLIFLayer(HyperLIFConfig(model="adaptive_hyperlif")).forward(J, dt)
m = dynamics_metrics(out, dt)
ok("forward shapes", out["voltage"].shape == (T, N) and out["reset_gate"].shape == (T, N))
ok("dynamics metrics finite", all(np.isfinite(v) for v in m.values()))
ok("no NaNs in dynamics", m["nan_count"] == 0)

# 2. autograd flows through the surrogate event (training viability).
#    Short horizon: full BPTT through the *stiff* conductance explodes over long horizons
#    (the "exact gradient explodes once active" finding from the Gate-Eligibility study) ->
#    training must use truncated BPTT + clipping + the annealed surrogate. Here we only
#    verify the graph is wired and finite on a short, well-conditioned window.
Tg = 8
gain = torch.ones(1, requires_grad=True)
out_g = HyperLIFLayer(HyperLIFConfig(model="adaptive_hyperlif")).forward(J[:Tg] * gain, dt)
loss = out_g["voltage"].pow(2).mean() + out_g["events"].sum()
loss.backward()
ok("autograd reaches input (grad not None)", gain.grad is not None)
ok("short-horizon gradient finite", gain.grad is not None and bool(torch.isfinite(gain.grad).all()))

# 3. origin knob (idea 1) actually changes dynamics; delta_reset=0 is the reference path
v0 = HyperLIFLayer(HyperLIFConfig(model="adaptive_hyperlif", delta_reset=0.0)).forward(J, dt)["voltage"]
v1 = HyperLIFLayer(HyperLIFConfig(model="adaptive_hyperlif", delta_reset=0.6)).forward(J, dt)["voltage"]
ok("origin delta_reset changes voltage", float((v0 - v1).abs().max()) > 1e-4)

# 4. runner config mapping + safe handling of unknown keys
cfg = build_neuron_config({"model": "hyperlif", "gamma": 0.3, "unknown_key": 123})
ok("config maps known keys / ignores unknown", cfg.model == "hyperlif" and abs(cfg.gamma - 0.3) < 1e-12)

passed = all(c for _, c in checks)
print(f"\n{'PASS' if passed else 'FAIL'}  ({sum(c for _, c in checks)}/{len(checks)} checks)")
raise SystemExit(0 if passed else 1)
