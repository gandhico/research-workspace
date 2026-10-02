# Tiny benchmark — synthetic temporal task

Roster across seeds=[0, 1], epochs=12, hidden=96, dt=0.001. Pipeline de-risk run (toy task) — **not** a capability claim. Real datasets: see `data/tonic_adapter.py`.

| config | accuracy | macro-F1 | events/sample | active | stable |
|---|---:|---:|---:|---:|---:|
| HyperLIF.voltage | 0.681 ± 0.015 | 0.673 | 0.76 | 0.64 | 1.00 |
| HyperLIF.hybridG | 0.677 ± 0.006 | 0.664 | 0.76 | 0.64 | 1.00 |
| AdHyperLIF.origin.static | 0.648 ± 0.031 | 0.638 | 1.49 | 0.55 | 1.00 |
| LIF | 0.633 ± 0.050 | 0.624 | 5.57 | 0.68 | 1.00 |
| AdHyperLIF.event.t0.95 | 0.615 ± 0.006 | 0.597 | 1.47 | 0.65 | 1.00 |
| ALIF | 0.613 ± 0.008 | 0.606 | 1.65 | 0.64 | 1.00 |
| AdHyperLIF.hybridG | 0.590 ± 0.006 | 0.573 | 1.37 | 0.64 | 1.00 |
| AdHyperLIF.voltage | 0.585 ± 0.023 | 0.568 | 1.37 | 0.64 | 1.00 |
