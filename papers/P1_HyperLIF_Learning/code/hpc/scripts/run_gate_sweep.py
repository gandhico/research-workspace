"""Gate-gain x neuron sweep for the gate-state residual (answers the team's open question +
adds the novel origin variant).

For each gate_gain, compare {HyperLIF, Adaptive, Adaptive+origin}:
  - low_act  : mean |residual| in the LOW-demand regime (|tau_norm| < 0.20)  -> want small (dormant)
  - high_act : mean |residual| in the HIGH-demand regime                     -> want large (assists)
  - select   : high_act / low_act                                            -> demand-triggered selectivity
  - diff_HL  : RMS difference of this neuron's residual vs HyperLIF           -> does adaptation/origin matter HERE?

Hypothesis: at high gate_gain the gate is binary -> diff_HL ~ 0 (Adaptive == HyperLIF, as the team
found). At low (graded) gate_gain the gate VALUE matters -> Adaptive/origin diverge, and the origin
(deeper AHP) should sharpen selectivity (lower low_act / higher select).

    python scripts/run_gate_sweep.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from adhyperlif_triage.control.gate_residual import (  # noqa: E402
    demand_profile, residual_from_conductance, residual_from_gates, run_gates,
)
from adhyperlif_triage.neurons import HyperLIFConfig  # noqa: E402

DT = 5e-4  # control dt (0.5 ms), matching the embodied-control loop


def ccfg(model, **kw):
    base = dict(tau=0.05, tau_r=0.005, alpha=50.0, gamma=2.0, v_thresh=1.0, v_rest=0.0, v_reset=0.0,
                reset_gain=120.0, base_gain=120.0, gain_scaling=80.0, amplitude=1.0)
    base.update(kw)
    return HyperLIFConfig(model=model, **base)


NEURONS = [
    ("HyperLIF", ccfg("hyperlif")),
    ("Adaptive", ccfg("adaptive_hyperlif")),
    ("Adaptive+origin", ccfg("adaptive_hyperlif", delta_reset=0.5, min_voltage=-2.0)),
]
GATE_GAINS = [1, 3, 10, 30, 100, 1000, 100000]
THR = 0.20


def _metrics(d, low, high, d_ref):
    la = float(np.mean(np.abs(d[low])))
    ha = float(np.mean(np.abs(d[high])))
    return la, ha, ha / max(la, 1e-9), float(np.sqrt(np.mean((d - d_ref) ** 2)))


def main():
    tau = demand_profile(DT)
    low = np.abs(tau) < THR
    high = ~low
    gates = {name: run_gates(tau, cfg, DT) for name, cfg in NEURONS}  # (r_pos, r_neg, g_pos, g_neg)

    print(f"demand profile: {len(tau)} steps @ dt={DT}s; low-demand frac={low.mean():.2f}; "
          f"gate fires above |tau_norm|={THR}\n")
    hdr = f"{'neuron':16s} {'low_act':>9s} {'high_act':>9s} {'select':>8s} {'diff_HL':>9s}"

    print("=== GATE-state residual (reads r) — the team's mechanism ===")
    for gg in GATE_GAINS:
        rp, rn, _, _ = gates["HyperLIF"]
        d_hl = residual_from_gates(rp, rn, gg)
        print(f"gate_gain={gg}")
        print("  " + hdr)
        for name, _ in NEURONS:
            rp, rn, _, _ = gates[name]
            la, ha, sel, diff = _metrics(residual_from_gates(rp, rn, gg), low, high, d_hl)
            print(f"  {name:16s} {la:9.4f} {ha:9.4f} {sel:8.1f} {diff:9.4f}")

    print("\n=== CONDUCTANCE residual (reads G_eff=(G_base+beta|I|)r^2) — beta+demand appear directly ===")
    _, _, gp, gn = gates["HyperLIF"]
    dc_hl = residual_from_conductance(gp, gn, gate_gain=1)
    print("  " + hdr)
    for name, _ in NEURONS:
        _, _, gp, gn = gates[name]
        la, ha, sel, diff = _metrics(residual_from_conductance(gp, gn, gate_gain=1), low, high, dc_hl)
        print(f"  {name:16s} {la:9.4f} {ha:9.4f} {sel:8.1f} {diff:9.4f}")


if __name__ == "__main__":
    main()
