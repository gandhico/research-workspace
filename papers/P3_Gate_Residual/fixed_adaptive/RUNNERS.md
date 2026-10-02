# P3 (fixed_adaptive) — Runners / Launchers, mapped to the paper

Consolidates `docs\runner_commands.md` (exact CLI flags) and
`docs\2026_07_05_results_params_runners.md` (the mechanism-section correction) against
`main2.tex`'s actual tables. All numbers below verified exact against
`results\logs\*_summary.json`.

## Table ↔ command ↔ result file

| Paper item | Command | Result file(s) | Confidence |
|---|---|---|---|
| Table `tab:hard45` (Hard45 Controller Comparison, CF2) | `runners\run_rotor_level.py --quad bitcraze_crazyflie_2 --controller {classical,direct_lif,direct_hyperlif,direct_adaptive_hyperlif,nengo_lifrate} --mission hard45 --sim-time 45 --blend 0.50 --direct-scale control --activity-mode gate --gate-gain 100000 --save-csv --save-figures` (§4 of `runner_commands.md`) | `results\logs\bitcraze_crazyflie_2_hard45_{controller}_dt0.0005_T45_s1_*_summary.json` | **Confirmed** — `direct_hyperlif` summary has `qerr_mean=0.28203`, `qerr_max=0.55861`, matching the table's `0.2820`/`0.5586` exactly |
| Table `tab:gate_sweep` (Gate-Gain Sweep) | `results\gate_gain_sweep_20260703\gate_gain_sweep.py` | `results\gate_gain_sweep_20260703\sweep_cf2_hard45.json`, `sweep_x2_hard45.json` | High — filenames and folder name directly match the table's purpose and date range |
| Table `tab:cross_quad` (Cross-Quad CF2 vs X2) | Same `run_rotor_level.py` invocations, `--quad skydio_x2` vs `--quad bitcraze_crazyflie_2`, `--controller direct_hyperlif` | `results\logs\skydio_x2_hard45_direct_hyperlif_*` + the CF2 rows above | High — same naming convention |
| §"Gate-residual mechanism" / §"Adaptive HyperLIF equals HyperLIF" (the corrected equivalence sections, `sec_mujoco_gate_mechanism.tex`) | `python learned_gate_experiment.py --neuron adaptive_hyperlif --methods classical,fixed_gate,online_pes,eprop_anneal` (self-contained pipeline, per `docs\2026_07_05_results_params_runners.md` §4) | Values cross-checked against `..\learned\docs\full_results_dossier.md` §5 — bit-for-bit identical across both documents | **Confirmed** — same 0.266117/0.038258/etc. values appear in both P3 sources independently |
| Fig. `fig:cf2_qerr`, `fig:hard45_qerr`, `fig:gate_dynamics` | `--save-figures` flag on the corresponding `run_rotor_level.py` invocation above | `paper\figures\compare_*.pdf` (present) | Confirmed present |
| Fig. `fig:platforms` (platforms illustration) | — | **Missing**, commented out tonight (see below) | Not a data plot — no command regenerates it |
| Fig. `fig:x2_hard45_extra` (Euler/torque diagnostics, Skydio) | `run_rotor_level.py --quad skydio_x2 --controller direct_hyperlif --mission hard45 --save-figures` (same run as the main comparison, different plot extraction) | **Missing**, commented out tonight | Regeneratable — rerun the command and re-extract the euler/torque plot panels |

## Other runner scripts (present, not all directly cited in the current paper)

| Script | Role |
|---|---|
| `runners\run_benchmark_sweep.py` | Multi-controller/mission sweep (`--preset smoke/full/rotor/quick`) — used for exploration beyond the single-run comparisons above |
| `runners\compare_conductance_residual.py` / `_v2.py` | One-off comparison plots, not part of the main pipeline (per `CODE_MAP.md`) |
| `runners\make_comparison_figures.py` | Figure generation from sweep output |

## External dependency (not included, not proprietary)

`docs\project_map.md` documents `models\` as symlinked from `../models/mujoco_menagerie/`
— that folder doesn't exist on this machine (confirmed tonight: no `models\` folder at all,
not even a broken symlink). This is Google DeepMind's **public, open-source** asset repository
(`github.com/google-deepmind/mujoco_menagerie`), not part of this research — same dependency
`..\learned\` needs. Clone it before running any command below:
`git clone https://github.com/google-deepmind/mujoco_menagerie models` from this project's root.

## Reproducing Table 1 end-to-end

```powershell
conda activate hyperlif
cd C:\Research\papers\P3_Gate_Residual\fixed_adaptive
foreach ($c in 'classical','direct_lif','direct_hyperlif','direct_adaptive_hyperlif','nengo_lifrate') {
  python runners\run_rotor_level.py --quad bitcraze_crazyflie_2 --controller $c --mission hard45 `
    --sim-time 45 --blend 0.50 --direct-scale control --activity-mode gate --gate-gain 100000 `
    --save-csv --save-figures
}
```

## Fixed tonight (see `papers\_planning\ADVISOR_REVIEW_2026-08-18.md` for full detail)
- `main2.tex` Contributions/Results-opening no longer contradicts the paper's own equivalence result.
- 3 missing figures commented out with `TODO` markers so the PDF builds (7 pages, clean).
