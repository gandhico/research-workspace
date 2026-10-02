# Tiny benchmark — synthetic temporal task

Roster across seeds=[0, 1], epochs=12, hidden=96, dt=0.001. Pipeline de-risk run (toy task) — **not** a capability claim. Real datasets: see `data/tonic_adapter.py`.

| config | accuracy | macro-F1 | events/sample | active | stable |
|---|---:|---:|---:|---:|---:|
| HyperLIF.voltage | 0.875 ± 0.004 | 0.871 | 1.06 | 0.69 | 1.00 |
| AdHyperLIF.origin.static | 0.875 ± 0.000 | 0.873 | 0.85 | 0.51 | 1.00 |
| AdHyperLIF.event.t0.95 | 0.871 ± 0.017 | 0.870 | 1.21 | 0.71 | 1.00 |
| AdHyperLIF.hybridG | 0.867 ± 0.008 | 0.864 | 1.11 | 0.69 | 1.00 |
| HyperLIF.hybridG | 0.865 ± 0.006 | 0.863 | 1.06 | 0.69 | 1.00 |
| AdHyperLIF.voltage | 0.846 ± 0.008 | 0.843 | 1.11 | 0.69 | 1.00 |
| ALIF | 0.821 ± 0.004 | 0.815 | 0.81 | 0.69 | 1.00 |
| LIF | 0.746 ± 0.042 | 0.738 | 1.61 | 0.68 | 1.00 |
