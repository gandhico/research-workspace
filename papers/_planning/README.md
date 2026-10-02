# HyperLIF IEEE Paper Proposals Workspace

Created: 2026-07-19

Purpose: keep the clean proposal-level paper plans, readiness ledger, and progress notes for the HyperLIF / Adaptive HyperLIF publication portfolio. This folder is intentionally separate from experiment folders so it can be consulted later before continuing the research or preparing Overleaf projects.

## Recommended Portfolio

Current decision: keep **P1** and **P2** clean, and fuse the previous **P3/P4** control directions into one deeper robotics/control manuscript.

| Track | Recommended form | Working title | Current readiness |
|---|---:|---|---:|
| P1 | Journal | HyperLIF Learning: Sparse Temporal State in Continuous-Reset Spiking Networks | 94% |
| P2 | Journal | Nengo-Compatible Reference Implementation and NEF Capability Analysis of HyperLIF Neurons | 85% |
| P3 | Journal / IEEE RA-L style | Gate-State and Adaptive/Learned Residual Control with HyperLIF Neurons | 62% |

The old TNNLS paper should not be revived as a direct resubmission. It should be mined for theory, equations, and motivation, then split into P1 and P2. The gate-state residual control insight can be mentioned briefly in P1 and P2 as a translational implication/future-work bridge, but the full control story belongs in fused P3.

## Files

- `paper1_hyperlif_learning_ieee_proposal.tex`: IEEE journal proposal scaffold for the main learning/architecture paper.
- `paper2_nengo_reference_ieee_proposal.tex`: IEEE journal proposal scaffold for the Nengo/NEF reference paper.
- `paper3_fused_gate_state_adaptive_control_ieee_proposal.tex`: active IEEE journal or RA-L style scaffold for the fused fixed-gate/adaptive/learned quadrotor control paper.
- `paper3_gate_state_residual_control_ieee_proposal.tex`: earlier fixed-gate control scaffold, retained as source material.
- `paper4_adaptive_learned_gate_control_conference_proposal.tex`: earlier learned/adaptive gate scaffold, now folded into fused P3.
- `PROGRESS_REGISTER.md`: living readiness register, open experiments, and next actions.
- `P1_CLOSEOUT_CYCLE_2026_07_19.md`: first reviewer-driven closeout cycle for the P1 baseline and smoke gates.
- `P1_TRAIN_SMOKE_2026_07_19_registry.csv`: tiny PLIF/ALIF train-log smoke output; not a paper result.
- `P1_FF_NMNIST_TINY_PREFLIGHT_SUMMARY.md`: local five-neuron FF baseline preflight summary; claim-discipline artifact, not final paper evidence.
- `P1_FF_SHD_WIDE_SHORTLIST_SUMMARY.md`: harder audio-cache FF shortlist showing ALIF/HyperLIF/LIF/PLIF/Adaptive behavior.
- `P1_SHD_WIDE_ARCH_SHORTLIST_SUMMARY.md`: SHD-wide `rsnn`/`delay` architecture-cell shortlist with PLIF/ALIF baselines.
- `P1_JULIA_APEX_DATA_GATE_2026_07_19.md`: Julia ingestion and APEX `[F,N,T]` topology check for `shd_wide_T20.h5`.
- `P1_APEX_ENGINE_BRIDGE_AUDIT_2026_07_19.md`: location of the older APEX engine, SHD cache path, loader mismatch audit, generic HDF5 adapter scaffold, CUDA check, and APEX loader smoke.
- `P1_APEX_RANKING_SMOKE_2026_07_19.md`: bounded APEX train/eval smoke comparing vanilla LIF and HyperLIF/NSA on the real SHD-wide cache.
- `P1_APEX_MULTI_SEED_TUNING_2026_07_19.md`: multi-seed APEX tuning result showing tuned HyperLIF/NSA beats matched LIF after exposing gate-feedback parameters.
- `P1_FINAL_TABLE_SCOPE_2026_07_19.md`: frozen P1 figure/table/claim surface for the IEEEtran conversion.
- `P1_IEEE_CONVERSION_2026_07_19.md`: first compiled P1 IEEEtran package and build verification.
- `P2_NENGO_CAPABILITY_SEED_SMOKE_2026_07_19.md`: one-seed smoke of the new Nengo capability seed-sweep runner for T001/T002/T023/T033.
- `P2_NENGO_CAPABILITY_SEED_PREFLIGHT_2026_07_19.md`: completed three-seed Nengo/NEF capability preflight, 84/84 simulations with 0 failures.
- `P2_MANUSCRIPT_INTEGRATION_2026_07_19.md`: P2 active manuscript integration and PDF build verification after adding the three-seed preflight table.
- `best_by_neuron.csv`: best-readout table from the local five-neuron FF baseline preflight.
- `REVIEWER_ADVISOR_AUDIT.md`: TNNLS reviewer concerns mapped to current evidence and required fixes.
- `PAPER_PORTFOLIO_DECISION.md`: publication split, venue strategy, and ordering recommendation.
- `AI_AGENT_RESEARCH_WORKFLOW.md`: operating system for the AI-assisted research cycle: audit, decide, run, aggregate, write, verify, report.

## Immediate Order

1. Finish P1 first: add final paired/statistical tests, verify bibliography metadata, and copyedit the compiled IEEEtran package after advisor review.
2. Finish P2 second: polish the active IEEE manuscript after integrating the capability matrix, three-seed preflight, backend wall, PES rate-matching result, and clean limitation framing.
3. Develop fused P3 in parallel as the deep control paper. Its core is fixed gate-state residual control; its extension is Adaptive/learned gate control, but only where experiments prove the adaptive pathway is active.
4. Mention gate-state residual control in P1/P2 only in the discussion/future-work bridge, not as a main result.
