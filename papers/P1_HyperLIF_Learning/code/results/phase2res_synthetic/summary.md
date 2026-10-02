# Smoke benchmark — synthetic temporal task

Roster across seeds=[0], epochs=2, hidden=96, dt=0.001. Pipeline de-risk run (toy task) — **not** a capability claim. Real datasets: see `data/tonic_adapter.py`.

| config | accuracy | macro-F1 | events/sample | active | stable |
|---|---:|---:|---:|---:|---:|
| HyperLIF.hybridG | 1.000 ± 0.000 | 1.000 | 0.64 | 0.43 | 1.00 |
| AdHyperLIF.event.t0.95 | 1.000 ± 0.000 | 1.000 | 0.69 | 0.44 | 1.00 |
| AdHyperLIF.origin.static | 1.000 ± 0.000 | 1.000 | 0.52 | 0.37 | 1.00 |
| AdHyperLIF.hybridG | 0.956 ± 0.000 | 0.957 | 0.61 | 0.43 | 1.00 |
| HyperLIF.voltage | 0.867 ± 0.000 | 0.870 | 0.64 | 0.43 | 1.00 |
| AdHyperLIF.voltage | 0.844 ± 0.000 | 0.843 | 0.61 | 0.43 | 1.00 |
| LIF | 0.556 ± 0.000 | 0.507 | 0.81 | 0.42 | 1.00 |
| ALIF | 0.511 ± 0.000 | 0.494 | 0.46 | 0.42 | 1.00 |
