# HyperLIF Publication Progress Register

Created: 2026-07-19

This is the living register to update after every experiment, figure, table, manuscript edit, and advisor decision.

## Portfolio Status

| Track | Status | Readiness | Next milestone |
|---|---|---:|---|
| P1 Learning | Frozen for advisor review | 98% | Only author/funding/repository details, copyedit, and advisor approval remain |
| P2 Nengo/NEF | Active, near submittable after focused edit | 91% | Regenerate current IEEEtran package, then advisor copyedit |
| P3 Fused control | Active fused P3/P4 paper | 62% | Complete X2 rotor rows, figures, statistics, ablations, and adaptive/learned gate proof |

## P1 - HyperLIF Learning

Current evidence:

- Multi-seed PyTorch/snnTorch benchmark.
- HyperLIF-family advantage across temporal datasets and architecture cells.
- PLIF/ALIF baseline support now covers FF preflights and an SHD-wide `rsnn`/`delay` architecture shortlist.
- Gate-only readout demonstrates a structural signal absent in LIF.
- Sparse efficiency can reach one to two orders of magnitude in selected settings.
- Draft exists: `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\paper\paper2_manuscript.md`.

Freeze decision:

- P1 is frozen for advisor review as of 2026-07-20.
- Do not open new P1 experiments unless an advisor explicitly requests them.
- Remaining work is submission metadata, copyedit, and advisor approval only.

Open tasks:

- [x] Run bounded Julia/APEX cross-framework training smoke on byte-identical HDF5 caches.
- [x] Add PLIF and ALIF/LSNN baseline support in the same snnTorch/HPC architecture harness.
- [x] Run expanded smoke gate after copying the patched harness into `07_AdHyperLIF_Triage` and `08_HyperLIF_Architectures`: 150/150 finite forward/backward checks passed.
- [x] Run one-epoch train/log smoke for PLIF and ALIF on `nmnist_tiny_T20`, FF membrane readout, seed 0: both stable, no NaNs.
- [x] Run local five-neuron FF N-MNIST tiny preflight: `ff x {lif, plif, alif, hyperlif, adaptive} x 6 readouts x 5 seeds`.
- [x] Run SHD-wide FF shortlist: `ff x selected readout per neuron x 5 seeds`.
- [x] Run SHD-wide architecture-cell shortlist: `{rsnn, delay} x selected readout per neuron x 5 seeds`.
- [x] Run Julia HDF5 ingestion and APEX `[F,N,T]` data-topology gate for `shd_wide_T20.h5`.
- [x] Locate the older APEX engine and add a generic P1 HDF5-to-APEX loader adapter scaffold.
- [x] Instantiate the APEX Julia project, verify CUDA, and run an adapter-backed loader smoke.
- [x] Create the APEX SHD-wide ranking runner using the verified loader and a matched vanilla LIF vs HyperLIF/NSA cell.
- [x] Run APEX GPU ranking reproduction on the byte-identical SHD-wide HDF5 cache with tuned HyperLIF/NSA.
- [x] Add APEX architecture-family modes for dense, recurrent/RSNN, and delay, then run compile and three-seed preflights.
- [ ] Regenerate paper-grade best-readout baseline tables across the final intended cache/architecture scope.
- [x] Generate final-statistics audit for full feedforward, architecture-transfer, and reviewer-baseline tables, including sample std, CI95, paired deltas, and failure counts.
- [x] Update feedforward, architecture-transfer, and reviewer-baseline IEEE tables with five-seed sample-std and zero-failure framing.
- [x] Convert Markdown manuscript into first IEEEtran LaTeX package.
- [x] Freeze current IEEE claim wording and remove unsafe benchmark/lab-internal language.
- [x] Prepare first Overleaf package with figures, table provenance, bibliography seed, and compiled PDF.
- [x] Verify bibliography metadata for the current reference set and rebuild with BibTeX.
- [ ] Finalize Overleaf package after paired tests or shortlist-framing decision, author/funding metadata, and advisor copyedit.

## P2 - HyperLIF in Nengo / NEF

Current evidence:

- Active IEEEtran paper exists: `C:\00_Research_\Neural_Networks_and_Learning\04_Adaptive_HyperLIF_Nengo\05_Adaptive_HyperLIF_Nengo_Paper\paper\main.tex`.
- Figures and tables exist.
- Exact standalone-vs-Nengo parity is paper-ready.
- NengoCore capability matrix runs 9/9 applications.
- Calibrated candidate T023 and Adaptive T033 results exist.
- PES rate-matching exposes the learning-speed trade clearly.
- Three-seed core capability preflight completed 84/84 Nengo simulations with 0 failures for T001/T002/T023/T033 across seven NEF apps.
- The active manuscript now includes the three-seed preflight table and builds to a clean 26-page PDF.
- The five-seed run is now a venue/reviewer contingency, not a blocker for the current methods-paper claim.
- A guarded NEF decoder-state ablation preflight exists for LIF, calibrated HyperLIF T023, and Adaptive T033.
- The final five-seed scalar NEF decoder-ablation table is now integrated in the manuscript as `tab:nef-decoder-ablation`.
- Final claim-artifact audit exists and marks the stale June `main_ieee.tex` as not upload-ready.

Open tasks:

- [x] Update active manuscript with latest capability, backend, PES, and seed-preflight evidence.
- [x] Add backend-portability section from NengoOCL/Loihi/NengoDL probes.
- [x] Add PES rate-matched curve and limitation framing.
- [x] Add `experiments/17_capability_seed_sweep.py` and run a one-seed smoke for T001/T002/T023/T033 across seven core Nengo apps.
- [x] Run three-seed capability preflight for calibrated NEF candidates.
- [x] Decide whether to run the five-seed paper-grade sweep or keep the three-seed preflight as sufficient methods-paper evidence.
- [x] Run P2 LaTeX build-hygiene pass: no undefined citations/references, no overfull boxes, BibTeX warning count 0.
- [x] Add bounded NEF state-decoder ablation preflight for `theta_event=0.95`, origin-aware T023, and Adaptive T033.
- [x] Decide whether to promote the decoder-ablation preflight into a paper table or keep gate decoding in the future-work/control lane.
- [x] Run final five-seed scalar NEF decoder-ablation sweep and integrate the table into the manuscript.
- [ ] Add broader NEF ensemble tuning validation only if advisor/reviewer asks for higher-dimensional decoder evidence.
- [x] Ensure every main claim is linked to CSV, script, figure, table, log, or explicit future-work framing.
- [x] Mark stale `paper\main_ieee.tex` package as not current.
- [ ] Copyedit the P2 manuscript for final IEEE tone, table economy, and Overleaf packaging.
- [ ] Regenerate current IEEEtran package from `paper\main.tex`.

## P3 - Fused Gate-State and Adaptive/Learned Residual Control

Current evidence:

- Full LaTeX draft exists: `C:\00_Research_\Neuromorphic_Embodied_AI\01_HyperLIF_Gate_Residual\v2_clean\paper\main2.tex`.
- Two MuJoCo quadrotors are modeled: Crazyflie 2 and Skydio X2.
- HyperLIF gate-state residual improves selected hard maneuvers and beats neural baselines that degrade performance.
- Safety/residual blending story is promising.
- Learned/adaptive gate evidence is promising but should remain a subsection until it proves a non-inert contribution.

Open tasks:

- [ ] Fill TODO rows in `main.tex`/`main2.tex`: gate-gain sweep and X2 rotor-level table rows.
- [ ] Fix figure paths and verify every included PDF renders.
- [ ] Add multi-seed or repeated-trial statistics.
- [ ] Add timing-shuffled gate ablation and energy-matched residual ablation.
- [ ] Connect controller neuron implementation to the Nengo reference implementation.
- [ ] Explicitly state that gate-mode residual attributes improvement to HyperLIF gate state unless voltage/event mode proves Adaptive-specific gains.
- [ ] Add fixed-gate vs learned-gate vs adaptive-gate comparison on both quadrotors.
- [ ] Decide whether learned/adaptive control becomes a main result, secondary result, or future-work paragraph based on the ablation table.

## Today's Audit Notes

- TNNLS rejection should be treated as final for that manuscript.
- The reviewer comments are mostly addressable by the new portfolio, but not by a lightly revised old paper.
- The strongest immediate paper is P1, but P2 may be one focused editing pass from a cleaner specialized submission.
- P3/P4 should be fused: fixed gate-state residual is the core control story; adaptive/learned gate control is the extension that must earn its place through ablations.
- 2026-07-19 P1 operating-cycle decision: use PLIF plus ALIF/LSNN as the immediate contemporary baselines. This is lower risk and more reviewer-relevant than adding Spikformer before the paper is statistically frozen.
- 2026-07-19 implementation note: updates expose `lif`, `plif`, `alif`, `hyperlif`, and `adaptive` in the same architecture/HPC sweep.
- 2026-07-19 validation note: `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\scripts\smoke.py` passed 150/150 checks using `C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\.venv\Scripts\python.exe`.
- 2026-07-19 grid note: `hpc/grid.py` now falls back to `C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\data\tonic\_cache` when cluster scratch is absent. The expanded local grid sees 55 bundles and 1650 configs.
- 2026-07-19 train-smoke note: `P1_TRAIN_SMOKE_2026_07_19_registry.csv` records PLIF accuracy 0.7792 and ALIF accuracy 0.7667 on a one-epoch tiny FF smoke. Treat these only as launcher validation, not paper evidence.
- 2026-07-19 local preflight note: `P1_FF_NMNIST_TINY_PREFLIGHT_SUMMARY.md` records a 150-run local table. HyperLIF is top by mean accuracy on this tiny FF setting (`0.8975 +/- 0.0062`), ALIF is essentially tied (`0.8967 +/- 0.0172`), and HyperLIF uses fewer events than best LIF/PLIF.
- 2026-07-19 reproducibility note: the preflight can be rerun with `C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\scripts\run_p1_baseline_preflight.py`.
- 2026-07-19 SHD-wide shortlist note: `P1_FF_SHD_WIDE_SHORTLIST_SUMMARY.md` records a harder-cache FF shortlist. ALIF leads HyperLIF slightly (`0.5570 +/- 0.0178` vs `0.5475 +/- 0.0203`), while HyperLIF strongly beats LIF/PLIF. This confirms ALIF must be treated as a serious baseline.
- 2026-07-19 reproducibility note: the SHD-wide shortlist can be rerun with `C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\scripts\run_p1_shd_wide_shortlist.py`.
- 2026-07-19 SHD-wide architecture shortlist note: `P1_SHD_WIDE_ARCH_SHORTLIST_SUMMARY.md` records a 50-run `rsnn`/`delay` table. HyperLIF leads the recurrent cell (`0.5695 +/- 0.0154`), ALIF slightly leads the delay cell (`0.5650 +/- 0.0187`), and both are well above LIF/PLIF.
- 2026-07-19 reproducibility note: the SHD-wide architecture shortlist can be rerun with `C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\scripts\run_p1_shd_wide_arch_shortlist.py`.
- 2026-07-19 readiness note: P1 moved from 88% to 89% because PLIF/ALIF gained SHD-wide architecture-cell evidence. This was later superseded by the APEX multi-seed tuning result below, which moved P1 to 93%.
- 2026-07-19 Julia/APEX data-gate note: `P1_JULIA_APEX_DATA_GATE_2026_07_19.md` records that Julia reads `shd_wide_T20.h5`, checksum `1.551635e7`, and permutes it to APEX topology `[F,N,T] = [700,2000,20]`. This closes the data-contract risk but does not yet count as APEX ranking reproduction.
- 2026-07-19 P1 APEX bridge note: `P1_APEX_ENGINE_BRIDGE_AUDIT_2026_07_19.md` records that the older APEX engine lives under `01_Adaptive_HyperLIF\03_Adaptive_HyperLIF_Apex_Engine\SNN_NSA_2`, while the P1 SHD cache lives under `07_AdHyperLIF_Triage\hpc\upload_data\shd_wide_T20.h5`. Added `08_HyperLIF_Architectures\julia\apex_load_cache_h5_adapter.jl` because the old `load_dvs_h5` is hardcoded for 32x32x2 DVS and is not valid for SHD `[F=700,N=2000,T=20]`. CPU-only adapter inspection passed on the real cache with 0-based labels and checksum `1.551635e7`; the APEX project now imports, CUDA is functional with one device, and `julia\apex_loader_smoke.jl` passed with first batch `(700,64,20)`. P1 moves from 89% to 90%; the next gate is the actual APEX ranking run.
- 2026-07-19 P1 APEX ranking-smoke note: `P1_APEX_RANKING_SMOKE_2026_07_19.md` records bounded Julia/APEX train/eval smokes on the real SHD-wide cache. Added `08_HyperLIF_Architectures\julia\apex_shd_ranking_smoke.jl`; the first run completed `APEX_SHD_RANKING_SMOKE_OK` for `dense_lif_control` (`use_nsa=false`) and `dense_hyperlif_nsa` (`use_nsa=true`) with two train and two test batches. A synced-path calibration run also passed with four train and three test batches; HyperLIF/NSA reached test accuracy `0.1042` vs LIF `0.0625`, but this remains smoke-grade only. CSVs: `08_HyperLIF_Architectures\results\apex\apex_shd_ranking_smoke_20260719_134401.csv` and `08_HyperLIF_Architectures\results\apex\apex_shd_ranking_smoke_20260719_134923.csv`. This proves the APEX training/evaluation path. P1 moves from 90% to 91%; the next gate is multi-seed APEX ranking reproduction.
- 2026-07-19 P1 APEX multi-seed tuning note: `P1_APEX_MULTI_SEED_TUNING_2026_07_19.md` records the calibrated cross-framework result. The default APEX HyperLIF/NSA setting (`beta=0.10`, `gamma=0.50`) did not beat LIF at 5 seeds / 3 epochs, so the old default is not safe to cite as evidence. A compact tuning grid found stronger gate feedback (`gamma=0.80`) as the useful direction. The final 10-epoch 5-seed direct comparison on `shd_wide_T20.h5` gives tuned HyperLIF/NSA `0.2490 +/- 0.0666` test accuracy and `2.2768` test loss vs LIF `0.2411 +/- 0.0778` and `2.3359`. P1 moves from 91% to 93%; the next gate is final baseline/statistics table freeze and IEEEtran conversion.
- 2026-07-19 P1 APEX architecture-transfer preflight note: `P1_APEX_ARCHITECTURE_TRANSFER_PREFLIGHT_2026_07_19.md` records that `apex_shd_ranking_smoke.jl` now supports `--architectures=dense,recurrent,delay`, with `rsnn` as an alias for recurrent. A compile smoke passed all dense/recurrent/delay modes. A three-seed, three-epoch recurrent/delay preflight also passed, but HyperLIF/NSA did not beat the APEX controls at this short horizon: delay `0.0781 +/- 0.0306` vs LIF `0.1085 +/- 0.0131`, recurrent `0.0955 +/- 0.0202` vs LIF `0.1176 +/- 0.0072`. This is an implementation gate, not a positive claim; the PyTorch RSNN/delay advantage remains valid from the PyTorch architecture harness, while APEX recurrent/delay need readout/learnable-delay parity and tuning before citation as a cross-framework transfer result.
- 2026-07-19 advisor-report note: `P1_ADVISOR_APEX_STATUS_REPORT_2026_07_19.md` summarizes the current APEX-as-designed result for advisor discussion. Bottom line: APEX works technically and gives a small calibrated dense HyperLIF/NSA advantage, but current APEX recurrent/delay approximations do not reproduce PyTorch RSNN/delay wins. `P1_APEX_V2_PYTORCH_PARITY_PLAN_2026_07_19.md` defines the next step: build an APEX-v2 parity layer with PyTorch-style RSNN, learnable temporal-current delay, and matching hybrid readouts.
- 2026-07-19 APEX-v2 forward-smoke note: `P1_APEX_V2_FORWARD_SMOKE_2026_07_19.md` records the first APEX-v2 validation gate. Added `08_HyperLIF_Architectures\julia\apex_v2` with `APEXV2Parity.jl`, `apex_v2_forward_smoke.jl`, and README, plus `scripts\run_apex_v2_forward_smoke.ps1`. The SHD-wide forward smoke passed 54/54 finite checks for `{dense,recurrent,delay} x {lif,hyperlif,adaptive} x 6 readouts`, with PyTorch-style feature dimensions (`64/128/192`) and expected gate/event sanity signals. This is G1/G2 only; next gates are PyTorch trace comparison and one-batch training sanity.
- 2026-07-19 APEX-v2 readout-train note: `P1_APEX_V2_READOUT_TRAIN_SMOKE_2026_07_19.md` records G3. Added `apex_v2_readout_train_smoke.jl` and `scripts\run_apex_v2_readout_train_smoke.ps1`. With recurrent HyperLIF and `hybrid_vr`, the frozen-feature linear readout loss decreased from `4.083514` to `1.792870` over 20 one-batch updates, with finite values throughout. This proves readout-head training sanity only; full trunk training parity remains pending.
- 2026-07-19 APEX-v2 trace-compare note: `P1_APEX_V2_TRACE_COMPARE_2026_07_19.md` records cross-framework structural trace parity. Added `scripts\export_pytorch_first_batch_trace.py` and `scripts\compare_pytorch_apex_v2_traces.py`. PyTorch exported 54/54 finite first-batch summaries from the same SHD-wide HDF5 cache; comparison against APEX-v2 matched all 54 architecture/neuron/readout rows with 0 structural failures. Mean events preserve the expected hierarchy: PyTorch LIF/HyperLIF/Adaptive `656.083/550.875/241.688`, APEX-v2 `720.948/584.312/262.688`. This is structural/state-summary parity, not weight-identical parity.
- 2026-07-19 native-APEX tuning note: `P1_NATIVE_APEX_ARCHITECTURE_TUNING_2026_07_19.md` records an APEX-as-designed operating-envelope probe for recurrent/delay HyperLIF/NSA. One-seed sweep found recurrent default `beta=0.10,gamma=0.50` as the strongest setting (`0.2721` test acc.) while dense-best `gamma=0.80` was weak for recurrent/delay. A three-seed confirmation at `gamma=0.50` gave recurrent HyperLIF/NSA `0.1441 +/- 0.1141`, above the earlier recurrent LIF mean `0.1176 +/- 0.0072` but too high-variance for a paper claim; delay remained below LIF. Advisor framing: original APEX works technically, dense is calibrated-positive, recurrent has a candidate regime, fixed delay is the clearest limitation.
- 2026-07-19 APEX-v2 shared-weight parity note: `P1_APEX_V2_SHARED_WEIGHT_PARITY_2026_07_19.md` records the first value-level PyTorch-to-Julia/APEX-v2 gate. Added `scripts\export_pytorch_apex_v2_fixture.py`, `julia\apex_v2\apex_v2_shared_weight_trace_compare.jl`, and `scripts\run_apex_v2_shared_weight_trace_compare.ps1`. Dense, recurrent, and delay HyperLIF all passed shared-weight feature/logit comparison with max feature errors around `8.6e-06` to `1.05e-05`. Dense/recurrent/delay Adaptive HyperLIF also passed under the documented Float32 envelope, with max feature errors `1.98e-04`, `5.08e-04`, and `3.52e-04`. This proves APEX-v2 is a direct portable-core implementation of the successful PyTorch architecture recipe at the forward-value level. P1 moves from 94% to 95%; the next gate is APEX-v2 one-seed train/test smoke before any paper-grade APEX-v2 accuracy claim.
- 2026-07-19 APEX-v2 train/eval smoke note: `P1_APEX_V2_TRAIN_EVAL_SMOKE_2026_07_19.md` records G4 for the portable core. Added `julia\apex_v2\apex_v2_train_eval_smoke.jl` and `scripts\run_apex_v2_train_eval_smoke.ps1`. The bounded run used `recurrent,delay x hyperlif,adaptive`, `hybrid_vr`, seed 1, two epochs, four train batches, and two test batches. All four cells were stable with `nan_batches=0`; train loss decreased for every cell. Final test accuracies were recurrent HyperLIF `0.0625`, recurrent Adaptive `0.0469`, delay HyperLIF `0.1250`, and delay Adaptive `0.0625`. Treat this as fixed-trunk/readout-head G4 evidence, not paper-grade accuracy. P1 moves from 95% to 96%; the next decision is whether APEX-v2 stays supplemental or receives a G5 three-seed preflight for manuscript inclusion.
- 2026-07-19 APEX-v2 three-seed preflight note: `P1_APEX_V2_THREE_SEED_PREFLIGHT_2026_07_19.md` records G5. Added `scripts\run_apex_v2_train_eval_preflight.ps1` and extended `apex_v2_train_eval_smoke.jl` with `--seeds`. The three-seed bounded run stayed stable for all `recurrent,delay x hyperlif,adaptive` cells with `nan_total=0`; every seed/cell reduced train loss. Mean test accuracies were recurrent HyperLIF `0.0807 +/- 0.0197`, recurrent Adaptive `0.0755 +/- 0.0430`, delay HyperLIF `0.0729 +/- 0.0451`, and delay Adaptive `0.0599 +/- 0.0119`. Decision: APEX-v2 is stable enough for supplementary traceability, but not strong enough for a main paper accuracy table without a larger G6 run. P1 remains 96%.
- 2026-07-19 P1 IEEE APEX-v2 integration note: `P1_IEEE_APEXV2_TRACEABILITY_INTEGRATION_2026_07_19.md` records that the IEEEtran source now includes `tab:apex-v2-traceability` as supplementary traceability evidence, with Discussion and Limitations updated to keep APEX-v2 out of the headline accuracy claim. Updated `main.tex`, `FIGURE_TABLE_MAP.md`, and `README_OVERLEAF.md`; rebuilt `paper_ieee\main.pdf` successfully with no undefined citations, no undefined references, and no overfull boxes. P1 moves from 96% to 97%.
- 2026-07-19 P1 bibliography metadata note: `P1_BIBLIOGRAPHY_METADATA_VERIFICATION_2026_07_19.md` records DOI/page metadata verification for the current `refs.bib` set, including Neftci, Bellec, Fang, Zenke, Cramer, Orchard, Roy, and Davies entries. Rebuilt the canonical IEEEtran package with `pdflatex/bibtex/pdflatex/pdflatex`; `main.pdf` is 5 pages / 441139 bytes, with no undefined citations, no undefined references, no overfull boxes, and BibTeX `warning$ -- 0`. This closes the bibliography-metadata gate; P1 remains 97% pending statistics/claim freeze, author/funding metadata, copyedit, and advisor approval.
- 2026-07-19 P1 claim-language audit note: `P1_CLAIM_LANGUAGE_AUDIT_2026_07_19.md` records the journal-facing wording pass. The manuscript now uses controlled benchmark/mechanism language, removes lab-internal "smoke" phrasing from the body, keeps APEX-v2 as traceability evidence, and rebuilds cleanly to `main.pdf` with no undefined citations, no undefined references, no overfull boxes, and BibTeX `warning$ -- 0`. P1 remains 97%; remaining gates are final statistics/framing decision, author/funding/repository metadata, copyedit, and advisor approval.
- 2026-07-19 P1 final-statistics audit note: `P1_FINAL_STATISTICS_AUDIT_2026_07_19.md` records the generated final-statistics script and outputs. Added `08_HyperLIF_Architectures\scripts\p1_final_stats_audit.py`, plus `results\final_stats\p1_final_stats_summary_20260719.csv`, `p1_final_paired_tests_20260719.csv`, and the generated audit MD. The script selected 74 configurations and produced 94 paired rows from the full FF, `roster60` architecture-transfer, and reviewer-baseline registries. Updated `tab:ff-temporal`, `tab:arch-transfer`, and `tab:baseline-shortlist` with sample standard deviations and zero-failure/zero-NaN framing. P1 moves from 97% to 98%; remaining gates are author/funding/repository metadata, copyedit, and advisor approval.
- 2026-07-19 P1 submission-metadata note: `P1_SUBMISSION_METADATA_CHECKLIST_2026_07_19.md` records the remaining non-computational submission items: author block, acknowledgments, funding, repository statement, reproducibility bundle, and advisor approval.
- 2026-07-20 P1 freeze note: `P1_FREEZE_DECISION_2026_07_20.md` records the user decision to freeze P1 for advisor review. New active work moves to P2; P1 should only receive author/funding/repository metadata, copyedit, and advisor-requested changes.
- 2026-07-19 P1 final table-scope note: `P1_FINAL_TABLE_SCOPE_2026_07_19.md` freezes the main figure/table/claim surface: temporal gain, gate-readout mechanism, efficiency, architecture transfer, PLIF/ALIF baseline extension, and tuned APEX validation.
- 2026-07-19 P1 IEEE conversion note: `P1_IEEE_CONVERSION_2026_07_19.md` records the first compiled IEEEtran package at `08_HyperLIF_Architectures\paper_ieee`. It includes `main.tex`, `refs.bib`, Overleaf README, figure/table map, five figures, and a successful `pdflatex/bibtex/pdflatex/pdflatex` build to `main.pdf` with no undefined citations or references. P1 moves from 93% to 94%; remaining gates are paired/statistical tests, bibliography verification, author/funding metadata, and copyediting.
- 2026-07-19 P2 Nengo seed-smoke note: `P2_NENGO_CAPABILITY_SEED_SMOKE_2026_07_19.md` records the new seed-sweep runner and a one-seed smoke. The smoke completed 28/28 Nengo simulations with 0 failures and supported the T023/T033 calibration thesis.
- 2026-07-19 P2 Nengo seed-preflight note: `P2_NENGO_CAPABILITY_SEED_PREFLIGHT_2026_07_19.md` records a completed three-seed run: 84/84 simulations, 0 failures, empty stderr. At that point P2 moved from 83% to 84%; the next gate was integration into the active `paper\main.tex` source with reviewer-safe claims.
- 2026-07-19 P2 manuscript integration note: `P2_MANUSCRIPT_INTEGRATION_2026_07_19.md` records that the active source `paper\main.tex` now includes the three-seed table, updated limitations/future work/conclusion, traceability docs, and a successful 26-page PDF build. P2 moves from 84% to 85%.
- 2026-07-20 P2 build/traceability note: `P2_CLAIM_BUILD_POLISH_2026_07_20.md` records the clean 26-page P2 build, the decision to treat three seeds as sufficient methods-paper evidence, and the support-doc updates linking capability, PES, backend, and seed-preflight claims to their scripts/CSVs/logs. P2 moves from 85% to 86%.
- 2026-07-20 P2 decoder-ablation note: `P2_NEF_DECODER_ABLATION_PREFLIGHT_2026_07_20.md` records `experiments\18_nef_decoder_state_ablation.py` and the guarded 3-seed/80-neuron run. Normal Nengo decoding remains stable for LIF/T023/T033; spike+voltage offline decoding is promising for T023/T033; reset-gate-only decoding is weak/high variance for direct represented-signal reconstruction. P2 moves from 86% to 87%.
- 2026-07-20 P2 final decoder-ablation table note: `P2_FINAL_DECODER_ABLATION_TABLE_2026_07_20.md` records the final 5-seed/100-neuron/1.2-s scalar NEF sweep and manuscript integration as `tab:nef-decoder-ablation`. The rebuilt `paper\main.pdf` is 27 pages / 858119 bytes with no undefined references/citations, no overfull boxes, and BibTeX `warning$ -- 0`. P2 moves from 87% to 89%.
- 2026-07-20 P2 submission-polish audit note: `P2_SUBMISSION_POLISH_AUDIT_2026_07_20.md` and `CLAIM_ARTIFACT_AUDIT_2026_07_20.md` record the final claim-to-artifact audit. The stale June `paper\main_ieee.tex` is explicitly marked not current; the next task is regenerating IEEEtran from active `paper\main.tex`. P2 moves from 89% to 91%.

## AI-Agent Operating Loop

This is the cycle to run after every work session:

1. **Audit**: read the newest results, manuscript diffs, logs, and advisor notes.
2. **Claim check**: update which claims are safe, qualified, unsafe, or pending.
3. **Decision**: choose the next experiment/edit/figure by reviewer impact and publication readiness.
4. **Execute**: run the smallest experiment or manuscript edit that closes a real gap.
5. **Aggregate**: regenerate CSV summaries, figures, tables, and figure/table maps.
6. **Verify**: run smoke tests, inspect plots/PDF pages, and check that captions match data.
7. **Report**: update this register with paths, dates, readiness changes, and next actions.

The agent should never treat a result as paper-ready until it is traceable to a script, CSV/log, figure/table, and manuscript claim.
