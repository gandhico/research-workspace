# ACC 2027 — advisor package (2026-09-21)

**Paper:** *Online PES Decoder Learning in Neuromorphic Residual UAV Attitude Control* (Contreras, Sandoval, Garcia Carrillo).
The current version is `paper/v13_2026-09-20_robustness/ACC2027.pdf` (7 pages); `ACC2027_v13_overleaf.zip` in the same folder
uploads to Overleaf as is. Start with `paper/v13_2026-09-20_robustness/AUDIT_v13_2026-09-20.md` (what changed, what was cut for
the page limit, how each review recommendation was handled) and then
`experiments/final_robustness_gating_2026-09-20/README.md` (all new experiments, results, figure index).

## What the new experiments established

Baseline for everything below: PD + desired-rate feedforward at bandwidth ×3 (the paper's primary baseline). "Gated" = the
residual is zeroed on an axis that is already at its torque limit when it would oppose the baseline (Eq. (gate); the decoder
still learns). This is the output rule, unrelated to the internal "gate" state of the CMG units.

* The paper's CF2 ρ=3 row had been run at β = 0.05, not the β = 0.5 in Table I. It is now disclosed.
* With the gate, noise-free geometric-mean error reduction is **37.3 % (X2, β 0.5)** and **22.4 % (CF2, β 0.2)**. CF2 at
  β 0.5 reaches 36.5 % noise-free but **diverges on Hardstep under sensor noise** (15/15 seeds; rotor-level saturation the
  torque-box gate cannot see), so β 0.2 was selected by a rule fixed beforehand and confirmed on held-out seeds.
* **Under noise** the benefit survives only where the baseline error exceeds the noise floor (Full3/Hard45: +11 % X2, +4 % CF2);
  Roll/Yaw360 (baseline 0.1–0.3 mrad) are neutral to slightly negative. Geometric mean falls to 2.3 % / 1.0 %.
* Disturbance bursts: burst-phase error −14 % (X2), −6 % (CF2).
* **Hardstep is never a gain** (12 gate configurations, −2.1 % … +0.3 %): the residual helps braking and hurts the settling tail,
  which occurs on an unsaturated axis.
* Supplement (reference only): on the same baseline **Izhikevich-PES** is much worse than CMG — its residual chatters at ~0.37 of
  the torque bound whatever the error, raising Roll/Yaw360 error ~10–15×. Figures: `experiments/final_robustness_gating_2026-09-20/figures_out/izh_compare/`.

## Integrity

* `experiments/final_robustness_gating_2026-09-20/PREREGISTRATION.md`: hypotheses, decision rules and priors sealed (SHA-256)
  before any campaign result; dated amendments A1/A2 follow, including one clarification written after seeing selection-stage
  results (disclosed in place). `verify_seal.py` re-checks the hashes.
* `run_validation.py`: the new runner reproduces the archived Table II ρ=3 block **bit for bit** (worst relative error 5e-15).
* `audit_v13.py`: 46 checks tying every number in the manuscript to the data (all pass).
* Every run has `summary.json` + `manifest.json` (configuration and source hashes). `MANIFEST_SHA256.txt` hashes this package.

## Layout

| path | content |
|---|---|
| `paper/v13_2026-09-20_robustness/` | manuscript source, PDF, Overleaf zip, `tools/` (build, page budget, audits) |
| `experiments/final_robustness_gating_2026-09-20/` | this campaign: code, sealed pre-registration, summaries of 597+19+20 runs, analysis, figures |
| `experiments/baseline_restatement_2026-09-16/` | baseline ladder, Hardstep analysis (why 97–99 % of the mean is slew) |
| `experiments/nengo_nef_replication_2026-08-29/` | the simulation code (runners, Nengo CMG/neuron-family augmentors) and archived summaries |
| `experiments/gate_gain_sweep_…`, `six_dof_…`, `theory_certificate_…` | earlier studies (code, docs, summaries) |
| `src/gra_control/`, `models/`, `third_party/` | control library, MuJoCo models (Menagerie X2/CF2 + the 1.5× CF2 rotor design) |
| `docs/`, `scripts/`, `tests/`, `configs/`, `figures/` | project documentation and utilities |

## Not included, and why

* **Raw traces (~50 GB):** every run is deterministic and regenerable with the scripts; per-run summaries are included.
  The optional second zip (`…_traces_for_figures_…zip`) holds the ~30 traces needed to regenerate every figure.
* Other paper versions, older share packages, `frozen_archives/`, the stale presentation, and `SOTA/` (third-party PDFs).

## Reproducing

```text
python -m venv .venv && .venv\Scripts\activate           # Python 3.13 was used; 3.11+ should work
pip install -r requirements_frozen.txt                   # mujoco 3.12.0, nengo 4.1.0, numpy 2.5.2, pandas 3.0.5, matplotlib 3.11.1
pip install -e .                                         # the gra_control package

cd experiments\final_robustness_gating_2026-09-20
python run_validation.py                                 # 20 cells, ~5 min at 4 workers; must print PASS
python run_campaign.py --campaign nominal                # 35 runs (see README.md for the other campaigns and amendments)
python audit_v13.py                                      # needs the final_*.csv files (included)
```

* Never use more than 4 parallel runs (each Nengo/CMG run needs a few hundred MB; 10 in parallel exhausted 16 GB).
* To regenerate figures, extract the traces zip into the root of this package first.
* Older analysis scripts hard-code the author's project root (`C:\Research\papers\ACC2027_Gate_Residual_Control`). Run
  `python tools\rebase_paths.py` to list them and `python tools\rebase_paths.py --apply` to point them at this folder. The
  campaign scripts in `final_robustness_gating_2026-09-20` use relative paths and need no change.
* The archived runners under `experiments/nengo_nef_replication_2026-08-29/` were **not modified**; they are hashed in the run manifests.
