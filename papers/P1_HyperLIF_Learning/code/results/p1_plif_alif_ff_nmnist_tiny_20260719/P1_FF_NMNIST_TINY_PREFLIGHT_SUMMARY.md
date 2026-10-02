# P1 FF N-MNIST Tiny Preflight Summary

Date: 2026-07-19

Scope: `ff x {lif, plif, alif, hyperlif, adaptive} x 6 readouts x 5 seeds` on `nmnist_tiny_T20`, 5 epochs, hidden 64, CPU.

This is a local preflight and claim-discipline table. It is not a final paper table.

## Best Readout Per Neuron

| neuron | best readout | accuracy | macro F1 | events/sample | stable | seeds |
|---|---|---:|---:|---:|---:|---:|
| hyperlif | hybrid_vr | 0.8975 ± 0.0062 | 0.8946 | 342.9 | 100% | 5 |
| alif | hybrid_vr_conductance | 0.8967 ± 0.0172 | 0.8935 | 323.3 | 100% | 5 |
| adaptive | hybrid_vr_conductance | 0.8767 ± 0.0104 | 0.8743 | 224.5 | 100% | 5 |
| plif | hybrid_vr | 0.8750 ± 0.0095 | 0.8704 | 581.9 | 100% | 5 |
| lif | hybrid_vr | 0.8742 ± 0.0110 | 0.8694 | 578.5 | 100% | 5 |

## Interpretation

- HyperLIF is the top local preflight model by mean accuracy: 0.8975 with `hybrid_vr`.
- ALIF is statistically close in this tiny setting: 0.8967 ± 0.0172. Treat ALIF as a serious baseline, not a weak control.
- HyperLIF uses fewer events than the best LIF/PLIF configs: 342.9 vs LIF 578.5 and PLIF 581.9.
- Adaptive HyperLIF is more spike-efficient than HyperLIF here (224.5 events/sample) but lower in accuracy (0.8767).
- LIF/PLIF gate-only and hybrid_gr readouts collapse to chance because those models expose no gate or conductance state; keep this as a structural-blindness control, not as a fairness error.

## Claim Status

Safe: the expanded baseline harness is stable; HyperLIF remains competitive with ALIF/PLIF/LIF on this local preflight; HyperLIF improves spike efficiency against LIF/PLIF at similar or better accuracy.

Pending: full-data multi-seed rankings, architecture transfer, Julia/APEX reproduction, and paired statistical tests.

Unsafe: HyperLIF universally beats ALIF, or Adaptive HyperLIF is best on this setting.

Source registry: `C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\results\p1_plif_alif_ff_nmnist_tiny_20260719\_registry.csv`
