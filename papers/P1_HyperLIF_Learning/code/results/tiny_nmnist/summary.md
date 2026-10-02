# Tiny benchmark — synthetic temporal task

Roster across seeds=[0], epochs=2, hidden=64, dt=0.001. Pipeline de-risk run (toy task) — **not** a capability claim. Real datasets: see `data/tonic_adapter.py`.

| config | accuracy | macro-F1 | events/sample | active | stable |
|---|---:|---:|---:|---:|---:|
| AdHyperLIF.event.tadapt | 0.854 ± 0.000 | 0.852 | 1.07 | 0.66 | 1.00 |
| AdHyperLIF.event.t0.95 | 0.846 ± 0.000 | 0.840 | 1.10 | 0.64 | 1.00 |
| HyperLIF.hybridG | 0.842 ± 0.000 | 0.835 | 1.08 | 0.70 | 1.00 |
| AdHyperLIF.voltage | 0.838 ± 0.000 | 0.827 | 1.06 | 0.62 | 1.00 |
| AdHyperLIF.event.t1.00 | 0.829 ± 0.000 | 0.818 | 1.08 | 0.68 | 1.00 |
| HyperLIF.voltage | 0.825 ± 0.000 | 0.819 | 0.88 | 0.63 | 1.00 |
| AdHyperLIF.origin.static | 0.821 ± 0.000 | 0.811 | 0.97 | 0.55 | 1.00 |
| AdHyperLIF.origin.gated | 0.787 ± 0.000 | 0.770 | 1.10 | 0.60 | 1.00 |
| AdHyperLIF.hybridG | 0.758 ± 0.000 | 0.745 | 1.32 | 0.78 | 1.00 |
| LIF | 0.646 ± 0.000 | 0.620 | 1.56 | 0.66 | 1.00 |
| ALIF | 0.496 ± 0.000 | 0.458 | 0.72 | 0.61 | 1.00 |
