# Parity Gate — PyTorch neuron vs validated reference

**Status: PASS ✅**  ·  tolerance `max|Δ| < 1e-9`, zero event mismatch  ·  `dt = 1e-4`, float64

The PyTorch `HyperLIFLayer` (`src/adhyperlif_triage/neurons/hyperlif_torch.py`) is checked
against the vendored `reference_numpy.py` — a frozen copy of the `04_Adaptive_HyperLIF_Nengo`
`stable` stepping that is itself proven equal (RMSE = 0) to the Nengo `NeuronType` port
(`05_Adaptive_HyperLIF_Nengo_Paper/RESULTS_AUDIT.md`, result #1). Passing here means the
PyTorch model **is** the validated continuous-reset neuron, not an approximation of it.

| Model | Protocol | voltage RMSE | gate RMSE | max\|Δv\| | max\|Δr\| | events (ref/torch) | event mismatch |
|---|---|---:|---:|---:|---:|---:|---:|
| hyperlif | step | 9.06e-18 | 0.00e+00 | 1.11e-16 | 0.00e+00 | 1/1 | 0 |
| adaptive_hyperlif | step | 3.71e-16 | 1.76e-15 | 2.00e-15 | 1.18e-14 | 0/0 | 0 |
| hyperlif | stress | 3.47e-17 | 2.06e-17 | 2.22e-16 | 2.22e-16 | 2/2 | 0 |
| adaptive_hyperlif | stress | 6.30e-16 | 2.15e-15 | 4.22e-15 | 1.41e-14 | 18/18 | 0 |
| hyperlif | db_drive | 8.16e-17 | 0.00e+00 | 4.44e-16 | 0.00e+00 | 1/1 | 0 |
| adaptive_hyperlif | db_drive | 2.53e-15 | 8.02e-15 | 6.66e-15 | 2.81e-14 | 42/42 | 0 |

Protocols: **step** (J=1.4 pulse), **stress** (staircase ramp to J=4, exercises the
depolarization-block / adaptive-rescue regime), **db_drive** (sustained J=3.3 above J_DB).

> Regenerate with `python scripts/run_parity.py`. The origin extension (`delta_reset`) is
> inert here (`delta_reset=0`), so this gate validates the base dynamics shared by every variant.
