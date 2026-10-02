# Smoke benchmark — synthetic temporal task

Roster across seeds=[0, 1, 2], epochs=5, hidden=64, dt=0.001. Pipeline de-risk run (toy task) — **not** a capability claim. Real datasets: see `data/tonic_adapter.py`.

| config | accuracy | macro-F1 | events/sample | active | stable |
|---|---:|---:|---:|---:|---:|
| AdHyperLIF.hybridG|base | 1.000 ± 0.000 | 1.000 | 0.56 | 0.39 | 1.00 |
| AdHyperLIF.hybridG|vreset-0.3 | 1.000 ± 0.000 | 1.000 | 0.50 | 0.37 | 1.00 |
| AdHyperLIF.hybridG|vreset-0.6 | 1.000 ± 0.000 | 1.000 | 0.55 | 0.39 | 1.00 |
| AdHyperLIF.hybridG|dreset0.3 | 1.000 ± 0.000 | 1.000 | 0.59 | 0.41 | 1.00 |
| AdHyperLIF.hybridG|dreset0.6 | 1.000 ± 0.000 | 1.000 | 0.48 | 0.34 | 1.00 |
| AdHyperLIF.ev0.95|base | 1.000 ± 0.000 | 1.000 | 0.68 | 0.41 | 1.00 |
| AdHyperLIF.ev0.95|vreset-0.3 | 1.000 ± 0.000 | 1.000 | 0.57 | 0.36 | 1.00 |
| AdHyperLIF.ev0.95|dreset0.3 | 1.000 ± 0.000 | 1.000 | 0.50 | 0.32 | 1.00 |
| AdHyperLIF.ev0.95|vreset-0.6 | 0.993 ± 0.010 | 0.992 | 0.60 | 0.38 | 1.00 |
| AdHyperLIF.ev0.95|dreset0.6 | 0.993 ± 0.010 | 0.992 | 0.60 | 0.37 | 1.00 |
| AdHyperLIF.voltage|vreset-0.6 | 0.978 ± 0.018 | 0.976 | 0.53 | 0.37 | 1.00 |
| AdHyperLIF.voltage|base | 0.970 ± 0.028 | 0.970 | 0.53 | 0.38 | 1.00 |
| AdHyperLIF.voltage|dreset0.3 | 0.956 ± 0.048 | 0.958 | 0.55 | 0.38 | 1.00 |
| AdHyperLIF.voltage|dreset0.6 | 0.933 ± 0.036 | 0.932 | 0.51 | 0.36 | 1.00 |
| AdHyperLIF.voltage|vreset-0.3 | 0.919 ± 0.073 | 0.912 | 0.51 | 0.37 | 1.00 |
| LIF.voltage|base | 0.904 ± 0.105 | 0.907 | 0.56 | 0.37 | 1.00 |
| LIF.voltage|vreset-0.6 | 0.822 ± 0.094 | 0.815 | 0.50 | 0.37 | 1.00 |
| LIF.voltage|vreset-0.3 | 0.807 ± 0.069 | 0.802 | 0.55 | 0.37 | 1.00 |
