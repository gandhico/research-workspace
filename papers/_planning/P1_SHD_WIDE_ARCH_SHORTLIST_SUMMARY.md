# P1 SHD-Wide Architecture Shortlist Summary

Date: 2026-07-19

Purpose: record the first architecture-cell PLIF/ALIF baseline extension for P1 after the TNNLS baseline critique.

## Source

Results root:

`C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\results\p1_baseline_arch_shortlist_shd_wide_20260719`

Registry:

`C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\results\p1_baseline_arch_shortlist_shd_wide_20260719\_registry.csv`

Aggregate:

`C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\results\p1_baseline_arch_shortlist_shd_wide_20260719\HPC_RESULTS.md`

Rerun script:

```powershell
cd C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage
.\.venv\Scripts\python.exe scripts\run_p1_shd_wide_arch_shortlist.py
```

Scope:

- Dataset: `shd_wide_T20`.
- Architectures: `rsnn`, `delay`.
- Neurons: `lif`, `plif`, `alif`, `hyperlif`, `adaptive`.
- Readouts: one selected readout per neuron from the FF shortlist.
- Seeds: 5.
- Epochs: 5.
- Total runs: 50.
- Stability: 50/50 stable, no NaN failures.

## Aggregate Table

| Config | Accuracy | Seeds | Events/sample | Stable |
|---|---:|---:|---:|---:|
| rsnn.hyperlif.hybrid_vr | 0.5695 +/- 0.0154 | 5 | 1035.0 | 100% |
| delay.alif.hybrid_vr_conductance | 0.5650 +/- 0.0187 | 5 | 840.6 | 100% |
| delay.hyperlif.hybrid_vr | 0.5593 +/- 0.0138 | 5 | 1033.2 | 100% |
| rsnn.alif.hybrid_vr_conductance | 0.5473 +/- 0.0160 | 5 | 818.8 | 100% |
| delay.lif.hybrid_vr | 0.4945 +/- 0.0193 | 5 | 1185.7 | 100% |
| delay.plif.hybrid_vr | 0.4940 +/- 0.0204 | 5 | 1191.1 | 100% |
| rsnn.adaptive.hybrid_vr_conductance | 0.4823 +/- 0.0142 | 5 | 471.0 | 100% |
| rsnn.lif.hybrid_vr | 0.4640 +/- 0.0081 | 5 | 1186.7 | 100% |
| rsnn.plif.hybrid_vr | 0.4637 +/- 0.0086 | 5 | 1189.3 | 100% |
| delay.adaptive.hybrid_vr_conductance | 0.4577 +/- 0.0203 | 5 | 474.4 | 100% |

## Interpretation

This shortlist changes the P1 story in a useful way:

- HyperLIF is the top RSNN cell on SHD-wide: `0.5695 +/- 0.0154`.
- ALIF is the top delay cell on SHD-wide: `0.5650 +/- 0.0187`.
- HyperLIF remains competitive in delay and strongly above LIF/PLIF.
- ALIF is a serious contemporary baseline and should be treated respectfully in the paper.
- PLIF tracks LIF closely in these cells, so PLIF is not currently the main challenger.
- Adaptive HyperLIF is lower accuracy in this shortlist but uses far fewer events/sample, so it remains an efficiency/operating-point result rather than a headline accuracy result.

## Claim Discipline

Safe wording:

- "On SHD-wide architecture shortlists, HyperLIF and ALIF form the strongest baseline pair, with HyperLIF leading the recurrent cell and ALIF slightly leading the delay cell."
- "HyperLIF and ALIF both substantially improve over LIF/PLIF in the selected temporal architecture cells."
- "Adaptive HyperLIF exposes a lower-event operating point, but does not lead accuracy in this shortlist."

Still unsafe:

- "HyperLIF outperforms every adaptive SNN baseline."
- "The HyperLIF advantage is architecture-independent."
- "Adaptive HyperLIF improves accuracy over HyperLIF in the main temporal benchmarks."

## Readiness Effect

P1 readiness moves from 88% to 89%.

Reason: the missing PLIF/ALIF architecture-cell evidence is no longer absent; it now exists as a clean SHD-wide shortlist with exact run provenance. Historical note: at this stage P1 could not move to 93% until Julia/APEX cross-framework reproduction was complete or the limitation was written cleanly. This was superseded on 2026-07-19 by `P1_APEX_MULTI_SEED_TUNING_2026_07_19.md`.
