# ACC 2027 — advisor package v14 (2026-09-21)

**Paper:** *Online PES Decoder Learning in Neuromorphic Residual UAV Attitude Control* (Contreras, Sandoval, Garcia Carrillo).
The current version is `paper/v14_2026-09-21_izhikevich/ACC2027_v14_2026-09-21.pdf` (7 pages); `ACC2027_v14_overleaf.zip` in the same
folder uploads to Overleaf as is (10 files, verified by a clean-room compile). Start with
`paper/v14_2026-09-21_izhikevich/AUDIT_v14_2026-09-21.md` (what changed from v13, the limits of the new numbers, and the audit output), then
`experiments/final_robustness_gating_2026-09-20/REPORT_IZHIKEVICH_A3.md` (the complete Izhikevich comparison) and
`experiments/final_robustness_gating_2026-09-20/README.md` (all experiments, results, figure index).

## What is new in v14 (relative to the first 2026-09-21 package, paper v13)

The Izhikevich basis was rerun **in the same circumstances as CMG**: tuned PD+ff (ρ = 3), true-attitude error, the same saturation-aware gate and
authority (β 0.5 X2, 0.2 CF2), realistic noise and hover bursts, both airframes. Reduced grid of 33 runs (~9 min), declared before it was run
(PREREGISTRATION §10); the full grid (~415 runs) was not run.

* On the tuned baseline the fixed-PD ranking reverses. Full3/Hard45: X2 +5.7/+9.8 % (CMG +12.4/+13.8), CF2 +6.3/+6.7 % (CMG +5.4/+7.3;
  inside the single-run scatter). Roll/Yaw360: X2 −812/−1455 %, CF2 −84/−1026 % (CMG +78/+42, +60/+20). Five-mission geometric-mean error
  **×2.6 (X2) and ×1.8 (CF2) the baseline's** (CMG ×0.63, ×0.78).
* **Effort** 0.36 (X2) / 0.14 (CF2) of the axis bound vs 0.032 / 0.015 for CMG (~10×; it was 3× on the fixed-PD baseline). The Izhikevich residual sits on a ±βℓ rail in
  35–48 % of the samples on every mission (CMG: under 1 %); its effort does not depend on the mission, CMG's follows the baseline error (Spearman +1.0).
* The saturation-aware gate is **not CMG-specific**: X2 Hardstep −16.9 % ungated → −1.5 % gated; on CF2 at β 0.2 the ungated Izhikevich residual diverges
  (119° mean error) and the gate turns it into −0.5 %.
* Noise (seeds 1–3) and hover bursts: the error floor persists (Roll −135 % X2 / −25 % CF2 under noise; quiet-phase error ×4.8 / ×2.4), the burst-phase reduction is close to CMG's (+12.2 vs +14.4 %; +5.5 vs +5.9 %).
* Changes in the paper: abstract's last sentence, Sec. IV-E, the last block of Table II (with the reduced-grid disclosure in its footnote), one clause of the conclusion; a few sentences
  were tightened and two figures shortened by 0.25 in to stay at 7 pages. Every CMG number is unchanged.

**Limits, stated in the paper and in the report.** (1) The Izhikevich runner reproduces the archived one bit for bit on X2 but **missed the declared 1e-9 tolerance on CF2 (3e-4)**: the two
runners differ by ~5e-20 N·m in the residual arithmetic, which a chaotic spiking cell amplifies (a 1e-14 rad initial offset moves a CF2 mean by 0.5 %); amendment A3.1.
(2) The single-run scatter of the spiking cell was measured with a 24-run ensemble: s.d. 1.4 % of the error at worst, so differences below **4 points** of the PD+ff error are not interpreted (A3.2,
written after seeing the campaign; the reason is in the amendment). (3) Moderate noise, noise seeds 4–10, 0.5×/2× bursts, CF2 at β 0.5 and the other neuron families at ρ = 3 were not run.

## What the earlier experiments established (unchanged)

Baseline for everything: PD + desired-rate feedforward at bandwidth ×3. "Gated" = the residual is zeroed on an axis already at its torque limit when it would oppose the baseline (Eq. (gate);
the decoder still learns) — the output rule, unrelated to the internal "gate" state of the CMG units.

* The paper's CF2 ρ=3 row had been run at β = 0.05, not the β = 0.5 in Table I. It is now disclosed.
* With the gate, noise-free geometric-mean error reduction is **37.3 % (X2, β 0.5)** and **22.4 % (CF2, β 0.2)**. CF2 at β 0.5 reaches 36.5 % noise-free but **diverges on Hardstep under sensor noise**
  (15/15 seeds; rotor-level saturation the torque-box gate cannot see), so β 0.2 was selected by a rule fixed beforehand and confirmed on held-out seeds.
* **Under noise** the benefit survives only where the baseline error exceeds the noise floor (Full3/Hard45: +11 % X2, +4 % CF2); Roll/Yaw360 are neutral to slightly negative. Geometric mean falls to 2.3 % / 1.0 %.
* Disturbance bursts: burst-phase error −14 % (X2), −6 % (CF2).
* **Hardstep is never a gain** (12 gate configurations, −2.1 % … +0.3 %): the residual helps braking and hurts the settling tail, which occurs on an unsaturated axis.

## Integrity

* `experiments/final_robustness_gating_2026-09-20/PREREGISTRATION.md`: hypotheses, decision rules and priors sealed (SHA-256) before any campaign result; dated amendments A1, A2 and A3 (A3.1, A3.2 and a clarification)
  follow, each written before the runs it governs except where it says otherwise (A3.2 and the clarification, and A2's criterion clarification, are disclosed in place). `verify_seal.py` re-checks the hashes.
* `run_validation.py`: the sealed runner reproduces the archived Table II ρ=3 block **bit for bit** (worst relative error 5e-15). `validate_izh_runner.py`: the Izhikevich adapter, bit-exact on X2, 3e-4 on CF2 (see above).
* `audit_v14.py`: 71 checks tying every number in the manuscript to the data, the Izhikevich numbers recomputed independently from the raw runs (all pass).
* Every run has `summary.json` + `manifest.json` (configuration and source hashes). `MANIFEST_SHA256.txt` hashes this package.

## Layout

| path | content |
|---|---|
| `paper/v14_2026-09-21_izhikevich/` | manuscript source, PDF, Overleaf zip, `AUDIT_v14…md`, `tools/` (build, page budget, `patch_v14.py` = how every new number entered the text) |
| `experiments/final_robustness_gating_2026-09-20/` | this campaign: code, sealed pre-registration, summaries of the runs, analysis, figures (`figures_out/izh_a3/` = Izhikevich vs CMG, both airframes) |
| `experiments/baseline_restatement_2026-09-16/` | baseline ladder, Hardstep analysis (why 97–99 % of the mean is slew) |
| `experiments/nengo_nef_replication_2026-08-29/` | the simulation code (runners, Nengo CMG/neuron-family augmentors) and archived summaries |
| `experiments/gate_gain_sweep_…`, `six_dof_…`, `theory_certificate_…` | earlier studies (code, docs, summaries) |
| `src/gra_control/`, `models/`, `third_party/` | control library, MuJoCo models (Menagerie X2/CF2 + the 1.5× CF2 rotor design) |
| `docs/`, `scripts/`, `tests/`, `configs/`, `figures/` | project documentation and utilities |

## Not included, and why

* **Raw traces (~50 GB):** every run is deterministic and regenerable with the scripts; per-run summaries are included. The optional second zip (`…_traces_for_figures_…zip`) holds the traces needed to regenerate every figure.
* Other paper versions, older share packages, `frozen_archives/`, the stale presentation, and `SOTA/` (third-party PDFs).

## Reproducing

```text
python -m venv .venv && .venv\Scripts\activate           # Python 3.13 was used; 3.11+ should work
pip install -r requirements_frozen.txt                   # mujoco 3.12.0, nengo 4.1.0, numpy 2.5.2, pandas 3.0.5, matplotlib 3.11.1
pip install -e .                                         # the gra_control package

cd experiments\final_robustness_gating_2026-09-20
python run_validation.py                                 # 20 cells, ~5 min at 4 workers; must print PASS
python run_campaign.py --campaign nominal                # 35 runs (see README.md for the other campaigns and amendments)
python validate_izh_runner.py                            # Izhikevich adapter vs the archived runner (X2 bit-exact; CF2 3e-4, see report)
python run_campaign_izh.py all                           # the 33 Izhikevich cases, ~9 min at 4 workers
python analyze_izh_a3.py ; python rail_fraction_izh.py ; python floor_izh.py ; python priors_a32.py ; python make_izh_report.py
python audit_v14.py                                      # needs the final_*.csv files (included) and the built v14 paper
```

* Never use more than 4 parallel runs (each Nengo/CMG run needs a few hundred MB; 10 in parallel exhausted 16 GB).
* To regenerate figures, extract the traces zip into the root of this package first.
* Older analysis scripts hard-code the author's project root (`C:\Research\papers\ACC2027_Gate_Residual_Control`). Run `python tools\rebase_paths.py` to list them and `python tools\rebase_paths.py --apply` to point
  them at this folder. The campaign scripts in `final_robustness_gating_2026-09-20` use relative paths and need no change.
* The archived runners under `experiments/nengo_nef_replication_2026-08-29/` were **not modified**; they are hashed in the run manifests.
