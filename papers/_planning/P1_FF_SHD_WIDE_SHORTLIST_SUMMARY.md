# P1 FF SHD-Wide Shortlist Summary

Date: 2026-07-19

Scope: `ff x selected readout per neuron x 5 seeds` on `shd_wide_T20`, 5 epochs, hidden 128, CPU.

This is a harder-dataset shortlist, not the final paper grid. It tests whether the PLIF/ALIF baseline story remains meaningful beyond the N-MNIST tiny preflight.

## Results

| config | accuracy | events/sample | stable |
|---|---:|---:|---:|
| `ff.alif.hybrid_vr_conductance` | 0.5570 +/- 0.0178 | 830.2 | 100% |
| `ff.hyperlif.hybrid_vr` | 0.5475 +/- 0.0203 | 1042.2 | 100% |
| `ff.adaptive.hybrid_vr_conductance` | 0.4785 +/- 0.0171 | 464.6 | 100% |
| `ff.lif.hybrid_vr` | 0.4238 +/- 0.0119 | 1208.7 | 100% |
| `ff.plif.hybrid_vr` | 0.4235 +/- 0.0106 | 1210.3 | 100% |

## Interpretation

- ALIF is the top short-run FF baseline on SHD-wide.
- HyperLIF is close to ALIF and strongly above LIF/PLIF.
- Adaptive HyperLIF is more event-efficient than ALIF/HyperLIF/LIF/PLIF, but is lower in accuracy in this FF shortlist.
- The result supports a nuanced P1 claim: HyperLIF is competitive with ALIF on a harder audio task and retains the gate-state mechanism, while PLIF does not close the gap over LIF in this configuration.

## Claim Status

Safe:

- The PLIF/ALIF baseline path is stable on a harder main local cache.
- ALIF must be treated as a serious adaptive baseline.
- HyperLIF beats LIF/PLIF in this SHD-wide FF shortlist.

Qualified:

- HyperLIF is competitive with ALIF, but ALIF slightly leads this specific shortlist.
- Adaptive HyperLIF is more event-efficient but needs tuning/readout/architecture work to recover accuracy.

Unsafe:

- HyperLIF universally beats ALIF.
- Adaptive HyperLIF is the best learning model on SHD-wide FF.
- This shortlist replaces the full architecture/full-dataset baseline table.

Source registry: `C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\results\p1_baseline_shortlist_ff_shd_wide_20260719\_registry.csv`
