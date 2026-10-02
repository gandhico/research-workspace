# P1 Closeout Cycle - 2026-07-19

Purpose: convert the TNNLS reviewer baseline criticism into an executable P1 closeout queue.

## Current Decision

Keep P1 focused on learning and architecture evidence. Mention gate-state residual control only as a short future-work bridge. Do not import MuJoCo results into P1.

The fastest reviewer-facing baseline fix is:

- PLIF: learnable membrane time constant / parametric LIF.
- ALIF/LSNN: adaptive-threshold LIF.

These complement the existing LIF, HyperLIF, and Adaptive HyperLIF roster. They are more appropriate for this manuscript than adding a large transformer or control architecture before the present evidence is statistically frozen.

## Code Paths Touched

Staged updates were prepared for these research files:

- `C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\src\adhyperlif_triage\neurons\snntorch_hyperlif.py`
- `C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\src\adhyperlif_triage\models\snntorch_net.py`
- `C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\hpc\train_hpc.py`
- `C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\hpc\grid.py`
- `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\src\arch\common.py`
- `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\src\arch\conv_resnet.py`
- `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\scripts\smoke.py`
- `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\docs\ROADMAP.md`

## Validation Gates

1. Syntax gate: `py_compile` on staged files. Status: passed.
2. Architecture smoke gate. Status: passed 150/150 checks on 2026-07-19.

```powershell
cd C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures
python scripts\smoke.py
```

Expected matrix after the baseline extension:

```text
5 architectures x 5 neurons x 6 readouts = 150 finite forward/backward checks
```

3. Grid sanity gate. Status: passed with local cache override.

```powershell
cd C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage
python hpc\grid.py --list
python hpc\grid.py --bundle-count
```

Local cache result on 2026-07-19. `hpc/grid.py` now falls back to this cache automatically
when cluster scratch is absent:

```text
HLL_CACHE=C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\data\tonic\_cache
55 bundles, 1650 configs
```

4. Train/log smoke gate. Status: passed for one-epoch FF membrane PLIF and ALIF on `nmnist_tiny_T20`, seed 0. See `P1_TRAIN_SMOKE_2026_07_19_registry.csv`.

5. Local evidence gate. Status: passed for FF N-MNIST tiny with five neurons, six readouts, and five seeds.

Rerun script:

```powershell
cd C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage
.\.venv\Scripts\python.exe scripts\run_p1_baseline_preflight.py
```

```text
best local preflight:
HyperLIF hybrid_vr = 0.8975 +/- 0.0062, 342.9 events/sample
ALIF hybrid_vr_conductance = 0.8967 +/- 0.0172, 323.3 events/sample
Adaptive HyperLIF hybrid_vr_conductance = 0.8767 +/- 0.0104, 224.5 events/sample
PLIF hybrid_vr = 0.8750 +/- 0.0095, 581.9 events/sample
LIF hybrid_vr = 0.8742 +/- 0.0110, 578.5 events/sample
```

6. Paper-grade evidence gate: run PLIF and ALIF/LSNN multi-seed configs on the same full/main caches and architecture cells used by the existing HyperLIF claims.

6b. SHD-wide FF shortlist. Status: passed on 2026-07-19.

```text
ALIF hybrid_vr_conductance = 0.5570 +/- 0.0178, 830.2 events/sample
HyperLIF hybrid_vr = 0.5475 +/- 0.0203, 1042.2 events/sample
Adaptive HyperLIF hybrid_vr_conductance = 0.4785 +/- 0.0171, 464.6 events/sample
LIF hybrid_vr = 0.4238 +/- 0.0119, 1208.7 events/sample
PLIF hybrid_vr = 0.4235 +/- 0.0106, 1210.3 events/sample
```

6c. SHD-wide architecture-cell shortlist. Status: passed on 2026-07-19 for `rsnn` and `delay`.

Rerun script:

```powershell
cd C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage
.\.venv\Scripts\python.exe scripts\run_p1_shd_wide_arch_shortlist.py
```

```text
rsnn.hyperlif.hybrid_vr = 0.5695 +/- 0.0154, 1035.0 events/sample
delay.alif.hybrid_vr_conductance = 0.5650 +/- 0.0187, 840.6 events/sample
delay.hyperlif.hybrid_vr = 0.5593 +/- 0.0138, 1033.2 events/sample
rsnn.alif.hybrid_vr_conductance = 0.5473 +/- 0.0160, 818.8 events/sample
delay.lif.hybrid_vr = 0.4945 +/- 0.0193, 1185.7 events/sample
delay.plif.hybrid_vr = 0.4940 +/- 0.0204, 1191.1 events/sample
rsnn.adaptive.hybrid_vr_conductance = 0.4823 +/- 0.0142, 471.0 events/sample
rsnn.lif.hybrid_vr = 0.4640 +/- 0.0081, 1186.7 events/sample
rsnn.plif.hybrid_vr = 0.4637 +/- 0.0086, 1189.3 events/sample
delay.adaptive.hybrid_vr_conductance = 0.4577 +/- 0.0203, 474.4 events/sample
```

7. Julia/APEX data-contract gate. Status: passed on 2026-07-19 for `shd_wide_T20.h5`.

```text
Julia ingestion:
X_train (700, 20, 2000), X_test (700, 20, 800), classes = 20
sum(X_train) = 1.551635e7

APEX topology:
X_train [F,N,T] = (700, 2000, 20), X_test = (700, 800, 20)
```

This validates the data bridge and APEX layout, not the APEX ranking result.

8. Manuscript gate: no P1 claim may say HyperLIF beats PLIF/ALIF universally. Safe wording is that HyperLIF leads the SHD-wide recurrent shortlist, ALIF slightly leads the SHD-wide delay shortlist, and both are materially stronger than LIF/PLIF under the selected readouts.

## Claim Ledger

Safe now:

- P1 has a stronger baseline harness in progress.
- PLIF and ALIF/LSNN are the correct next baselines for reviewer response.
- P1 has clean PLIF/ALIF FF evidence and SHD-wide architecture-cell shortlist evidence.
- The Julia/APEX data bridge is validated for `shd_wide_T20.h5`.
- P1 is currently 89 percent ready.

Pending:

- HyperLIF vs PLIF/ALIF accuracy ranking over the final full paper grid.
- HyperLIF vs PLIF/ALIF sparse-efficiency Pareto ranking.
- Whether ALIF adaptation-state readouts narrow or widen the HyperLIF gate-readout advantage.
- Whether convres remains a limitation/negative result after baseline expansion.
- APEX GPU cross-framework ranking reproduction on byte-identical caches.

Unsafe until evidence appears:

- "HyperLIF outperforms all adaptive SNN baselines."
- "The advantage is architecture-independent."
- "The Julia/APEX result reproduces PyTorch."

## Readiness Rule

Current P1 readiness is 89 percent.

Raise only after evidence gates:

- 86 percent: expanded smoke gate passes. Status: reached on 2026-07-19.
- 87 percent: fair local five-neuron FF preflight table exists. Status: reached on 2026-07-19.
- 88 percent: SHD-wide FF shortlist exists. Status: reached on 2026-07-19.
- 89 percent: PLIF/ALIF SHD-wide architecture-cell shortlist exists. Status: reached on 2026-07-19.
- 93 percent: Julia/APEX reproduces the headline ranking or the limitation is cleanly explained.
- 96 percent: final statistics, figures, and tables are regenerated from CSV/log sources.
- 98 percent: IEEEtran Overleaf package compiles with all figures and tables.
- 100 percent: advisor-facing claim audit is complete and no TNNLS-unsafe language remains.

## Next Agent Action

Run APEX GPU ranking validation next. If the APEX run is blocked, launch the remaining full-grid baseline scope needed for final paper tables, then regenerate figure/table artifacts.
