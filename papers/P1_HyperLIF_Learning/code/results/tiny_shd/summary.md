# Tiny benchmark — synthetic temporal task

Roster across seeds=[0, 1, 2], epochs=15, hidden=64, dt=0.001. Pipeline de-risk run (toy task) — **not** a capability claim. Real datasets: see `data/tonic_adapter.py`.

| config | accuracy | macro-F1 | events/sample | active | stable |
|---|---:|---:|---:|---:|---:|
| HyperLIF.voltage | 0.792 ± 0.006 | 0.786 | 0.83 | 0.68 | 1.00 |
| HyperLIF.hybridG | 0.761 ± 0.009 | 0.752 | 0.79 | 0.67 | 1.00 |
| AdHyperLIF.event.t0.95 | 0.701 ± 0.010 | 0.685 | 1.55 | 0.71 | 1.00 |
| AdHyperLIF.origin.static | 0.683 ± 0.019 | 0.671 | 1.62 | 0.60 | 1.00 |
| AdHyperLIF.event.tadapt | 0.678 ± 0.014 | 0.668 | 1.42 | 0.69 | 1.00 |
| AdHyperLIF.origin.gated | 0.674 ± 0.048 | 0.658 | 1.27 | 0.53 | 1.00 |
| AdHyperLIF.event.t1.00 | 0.668 ± 0.037 | 0.658 | 1.36 | 0.66 | 1.00 |
| AdHyperLIF.hybridG | 0.667 ± 0.006 | 0.647 | 1.37 | 0.66 | 1.00 |
| AdHyperLIF.voltage | 0.650 ± 0.032 | 0.635 | 1.39 | 0.66 | 1.00 |
| LIF | 0.635 ± 0.026 | 0.626 | 5.09 | 0.61 | 1.00 |
| ALIF | 0.614 ± 0.028 | 0.601 | 1.63 | 0.62 | 1.00 |
