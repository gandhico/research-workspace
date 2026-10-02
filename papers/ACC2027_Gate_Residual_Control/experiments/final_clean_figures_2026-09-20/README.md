# Clean canonical X2 Hard45 figures

This folder rebuilds two title-free, publication-scale figures from the frozen
primary comparison used in the ACC 2027 results table. It does **not** rerun a
simulation and does not edit the archived traces.

## Frozen inputs

- PD + reference-rate feedforward, bandwidth multiplier `rho=3`:
  `../nengo_nef_replication_2026-08-29/results/baselines_2026-09-10/tune/pdff/bw3/x2_hard45_classical`
- CMG-PES residual on the same baseline, `beta=0.5`:
  `../nengo_nef_replication_2026-08-29/results/baselines_2026-09-10/stretch/pdff/bw3/x2_hard45_nengo_nef_pes`

The archived full-rate summary means are 10.537051 mrad and 9.080333 mrad,
respectively, a 13.824% reduction. The utility asserts those values before it
plots. It also verifies equal timestamps and equal reference trajectories.

The selected CMG run did not save `neural_trace_full_rate.npz`. Therefore the
neuron-state figure uses the CMG variables saved every 0.005 s in `trace.csv`:
six membrane states, gates, activities, and the 18 decoder coefficients. This
sampling provenance is recorded explicitly rather than implying full-rate
neural telemetry.

## Reproduce

From PowerShell:

```powershell
$root = 'C:\Research\papers\ACC2027_Gate_Residual_Control'
$py = "$root\.venv\Scripts\python.exe"
$job = "$root\experiments\final_clean_figures_2026-09-20"
& $py "$job\make_clean_paper_figures.py"
```

Optional source and output overrides are available through `--source-root`
and `--output-root`. Run `--help` for details.

## Outputs

- `output/png/x2_hard45_attitude_detail_clean.png`
- `output/pdf/x2_hard45_attitude_detail_clean.pdf`
- `output/png/x2_hard45_neuron_states_clean.png`
- `output/pdf/x2_hard45_neuron_states_clean.pdf`
- `output/figure_provenance.json`

Both figures omit platform/mission suptitles and descriptive panel headings.
The tracking figure keeps only signal labels and a shared legend; an inset
retains the common 0-0.6 s initial transient while the main error axis resolves
the subsequent tracking difference. The JSON file records input/output hashes,
the full-rate summary values, decimated-trace means, and telemetry sampling.

## Audit note

The old `x2_hard45_attitude.png` in the paper package compares the earlier
fixed-PD runs (approximately 16.85 deg versus 7.91 deg). It is not the rho=3
primary comparison summarized above. The clean replacement here is the
code-aligned figure for the current primary table.
