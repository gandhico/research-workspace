# Figures Checklist

Drop PDF or EPS exports here before building main.tex.
The \includegraphics calls in main.tex use these exact filenames.

| Filename                        | Source                                        | Status  |
|---------------------------------|-----------------------------------------------|---------|
| hyperlif_dynamics.pdf           | plot v(t), r(t) from any single-neuron sim    | TODO    |
| arch_A_block_diagram.pdf        | draw with TikZ or export from diagrams/       | TODO    |
| arch_B_block_diagram.pdf        | draw with TikZ or export from diagrams/       | TODO    |
| hard45_qerr_comparison.pdf      | run_benchmark_sweep → save_figures            | TODO    |
| yaw360_tracking.pdf             | run_rotor_level --mission yaw360 --save-figures | TODO  |
| roll360_failure.pdf             | run_rotor_level --mission roll360 --save-figures | TODO |
| gate_state_timeseries.pdf       | dashboard --save-figures during hard45 run    | TODO    |

All figures should use a consistent color scheme:
  - Classical PD:              blue  (#1f77b4)
  - Direct LIF:                green (#2ca02c)
  - Direct HyperLIF:           orange (#ff7f0e)
  - Adaptive HyperLIF:         red   (#d62728)
  - Rotor Residual HyperLIF:   purple (#9467bd)

Use 300 DPI minimum for raster; PDF/EPS preferred for IEEE submission.
