# Task board

Claim one task before editing. Status values: `open`, `active`, `review`, `done`, `blocked`.

| ID | Status | Owner/branch | Task | Acceptance check |
|---|---|---|---|---|
| P4-001 | done | initial construction | Core viability/heterogeneity/homeostasis/CBF module | Julia package tests pass |
| P4-002 | done | initial construction | Constant-current atlas and high-reactivity calibration | CSVs generated; naive block documented |
| P4-003 | done | initial construction | Exact-cache SHD heterogeneous runner | timestamped smoke JSON/checkpoint |
| P4-004 | open | — | ODE/discrete/GPU parity and release/block suite | tolerance table + passing tests |
| P4-005 | review | claude-opus-5 / 2026-09-10 | Matched homogeneous HyperLIF baseline in P4 harness | done: `--model=homogeneous|ensemble|heterogeneous`, equal hidden state, effective counts within 63; triple running |
| P4-006 | open | — | Julia LIF/PLIF/ALIF controls | unit tests + SHD smoke |
| P4-007 | open | — | Three-seed SHD discovery matrix | aggregate table with failures and CIs |
| P4-008 | blocked | — | Exact N-MNIST/DVS/SSC replication | original cache binaries and verified hashes recovered |
| P4-009 | open | — | Conditional subthreshold-feature ablation | paired held-out predictions and test |
| P4-010 | open | — | Gain-drift homeostasis experiment | rate restoration/diversity/accuracy curves |
| P4-011 | open | — | Bounded residual interface to P3 simulator | deterministic scenario smoke |
| P4-012 | open | — | Production QP safety filter | feasibility, robustness, and deadline tests |
| P4-013 | open | — | Formal novelty database review | reproducible Scopus/WoS/GS query log |
| P4-014 | done | claude-opus-5 / 2026-09-10 | Reachable SHD event-rate envelope; re-derive target bands from data not synthetic current | `reachable_rate_envelope.csv`, `shared_gain_sweep.csv`, `shd_shared_gain_regimes` + tests |
| P4-015 | review | claude-opus-5 / 2026-09-10 | Fix vacuous homeostasis pairing | done: `homeostasis_effective` flag + warning, `--homeostasis-interval` for in-epoch action; a non-vacuous paired run still needs running |
| P4-016 | open | — | Event-carrying readout so the event-communication clause is testable | `:hybrid_zr` or surrogate/`:spike_count` run at matched accuracy |
| P4-017 | open | — | Re-run regime separation after training, not only at initialization | per-population rate trace stays ordered through training |
| P4-018 | open | — | Initialize the P4 Git repository (Stage 0 exit criterion, still unmet) | repo with first commit; per-task branches possible |

