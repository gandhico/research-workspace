# P2 NEF Decoder-Ablation Preflight - 2026-07-20

Status update: this preflight was superseded later on 2026-07-20 by
`P2_FINAL_DECODER_ABLATION_TABLE_2026_07_20.md`. The final paper result uses a
5-seed, 100-neuron, 1.2-s scalar NEF channel and is now included as
`tab:nef-decoder-ablation` in the P2 manuscript. Keep the 3-seed note as the
diagnostic trail that motivated the final run.

## Purpose

Close the first part of the open P2 gate:

> Add NEF ensemble tuning/decoder validation for theta_event=0.95,
> origin-aware calibration, and Adaptive candidate.

This preflight does not change the manuscript claim surface yet. It tests
whether internal state features from calibrated HyperLIF-family ensembles can
decode the represented signal in Nengo.

## New Runner

`C:\00_Research_\Neural_Networks_and_Learning\04_Adaptive_HyperLIF_Nengo\05_Adaptive_HyperLIF_Nengo_Paper\experiments\18_nef_decoder_state_ablation.py`

Outputs:

- `results\csv\18_nef_decoder_state_ablation.csv`
- `results\csv\18_nef_decoder_state_ablation_summary.csv`
- `results\logs\18_nef_decoder_state_ablation.txt`

Command used:

```powershell
.\.venv\Scripts\python.exe experiments\18_nef_decoder_state_ablation.py --seeds 0,1,2 --n-neurons 80 --duration 1.0
```

The decoder fit standardizes features on the training split, applies a minimum
feature scale of `0.05`, clips z-scores at `20`, and uses ridge `0.01`.

## Main Results

Three candidates were tested: native LIF, calibrated HyperLIF T023, and
calibrated Adaptive T033.

Normal Nengo decoded output remains stable:

- LIF: `0.1543 +/- 0.0008` test RMSE at `103.3` Hz.
- HyperLIF T023: `0.1542 +/- 0.0025` test RMSE at `41.2` Hz.
- Adaptive T033: `0.1561 +/- 0.0009` test RMSE at `54.2` Hz.

Offline spike+voltage decoders are promising for the calibrated HyperLIF-family
neurons:

- HyperLIF T023 spike+voltage: `0.1128 +/- 0.0021`.
- Adaptive T033 spike+voltage: `0.0824 +/- 0.0061`.

Gate-only decoding is not robust for direct represented-signal reconstruction:

- HyperLIF T023 reset gate: `0.3556 +/- 0.2533`.
- Adaptive T033 reset gate: `0.2691 +/- 0.2820`.

Adding the reset gate to voltage/spike features worsened this direct signal
decoder in the current setup, so the reset gate should not be claimed as a
better general NEF representation channel from this result.

## Interpretation

This supports the P2 calibration story without overclaiming:

- Calibrated HyperLIF/Adaptive can match normal Nengo decoding at substantially
  lower firing rates.
- Voltage plus filtered spikes may expose a useful low-rate state readout.
- Reset-gate value is better treated as a readiness/control signal candidate,
  not as a direct represented-signal decoder in this preflight.

## Decision

Do not add this as a main manuscript result yet.

Recommended next fork:

- If P2 needs one more result table, run a larger decoder-ablation study with
  more seeds/neurons/duration and a target-definition pass that separates
  represented-signal decoding from readiness/residual decoding.
- If the paper is already long enough, keep this as support for Limitations and
  Future Work, and move gate-state residual decoding to the fused P3 control
  paper.
