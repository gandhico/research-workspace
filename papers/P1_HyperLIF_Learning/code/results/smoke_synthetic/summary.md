# Smoke benchmark — synthetic temporal task

Roster across seeds=[0], epochs=2, hidden=64, dt=0.001. Pipeline de-risk run (toy task) — **not** a capability claim. Real datasets: see `data/tonic_adapter.py`.

| config | accuracy | macro-F1 | events/sample | active | stable |
|---|---:|---:|---:|---:|---:|
| HyperLIF.hybridG | 0.978 ± 0.000 | 0.976 | 0.75 | 0.49 | 1.00 |
| HyperLIF.voltage | 0.867 ± 0.000 | 0.870 | 0.71 | 0.48 | 1.00 |
| AdHyperLIF.hybridG | 0.867 ± 0.000 | 0.859 | 0.71 | 0.51 | 1.00 |
| AdHyperLIF.event.t1.00 | 0.867 ± 0.000 | 0.867 | 0.56 | 0.42 | 1.00 |
| AdHyperLIF.event.t0.95 | 0.844 ± 0.000 | 0.847 | 0.77 | 0.49 | 1.00 |
| AdHyperLIF.event.tadapt | 0.800 ± 0.000 | 0.811 | 0.64 | 0.45 | 1.00 |
| LIF | 0.556 ± 0.000 | 0.464 | 0.78 | 0.44 | 1.00 |
| AdHyperLIF.voltage | 0.444 ± 0.000 | 0.410 | 0.53 | 0.39 | 1.00 |
| ALIF | 0.333 ± 0.000 | 0.318 | 0.43 | 0.41 | 1.00 |
