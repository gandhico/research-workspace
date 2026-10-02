# Smoke benchmark — synthetic temporal task

Roster across seeds=[0], epochs=3, hidden=64, dt=0.001. Pipeline de-risk run (toy task) — **not** a capability claim. Real datasets: see `data/tonic_adapter.py`.

| config | accuracy | macro-F1 | events/sample | active | stable |
|---|---:|---:|---:|---:|---:|
| AdHyperLIF.event.t0.95 | 0.533 ± 0.000 | 0.485 | 1.59 | 0.72 | 1.00 |
| AdHyperLIF.origin.gated | 0.489 ± 0.000 | 0.447 | 1.50 | 0.62 | 1.00 |
| ALIF | 0.422 ± 0.000 | 0.379 | 1.81 | 0.72 | 1.00 |
| HyperLIF.voltage | 0.422 ± 0.000 | 0.389 | 0.88 | 0.75 | 1.00 |
| AdHyperLIF.voltage | 0.422 ± 0.000 | 0.339 | 1.16 | 0.58 | 1.00 |
| AdHyperLIF.event.t1.00 | 0.422 ± 0.000 | 0.391 | 1.43 | 0.70 | 1.00 |
| HyperLIF.hybridG | 0.378 ± 0.000 | 0.309 | 0.92 | 0.73 | 1.00 |
| AdHyperLIF.origin.static | 0.356 ± 0.000 | 0.212 | 1.58 | 0.63 | 1.00 |
| AdHyperLIF.hybridG | 0.333 ± 0.000 | 0.167 | 1.38 | 0.66 | 1.00 |
| AdHyperLIF.event.tadapt | 0.311 ± 0.000 | 0.199 | 1.70 | 0.73 | 1.00 |
| LIF | 0.267 ± 0.000 | 0.259 | 6.02 | 0.67 | 1.00 |
