# P2 Final Decoder-Ablation Table - 2026-07-20

## Decision

The decoder-ablation preflight is promoted into a bounded manuscript result.
The final claim is scalar and NEF-specific:

> In a five-seed scalar NEF communication channel, calibrated HyperLIF-family
> neurons expose useful low-rate state readouts through reset-gate and combined
> state features.

This is not a closed-loop control claim and not a high-dimensional decoder
claim.

## Final Run

Command:

```powershell
.\.venv\Scripts\python.exe experiments\18_nef_decoder_state_ablation.py --seeds 0,1,2,3,4 --n-neurons 100 --duration 1.2
```

Outputs:

- `results\csv\18_nef_decoder_state_ablation.csv`
- `results\csv\18_nef_decoder_state_ablation_summary.csv`
- `results\logs\18_nef_decoder_state_ablation.txt`

Fit settings:

- Seeds: `0,1,2,3,4`
- Neurons: `100`
- Duration: `1.2 s`
- Ridge: `0.01`
- Minimum feature scale: `0.05`
- Z-score clipping: `20`

## Manuscript Integration

Added `tab:nef-decoder-ablation` to:

`C:\00_Research_\Neural_Networks_and_Learning\04_Adaptive_HyperLIF_Nengo\05_Adaptive_HyperLIF_Nengo_Paper\paper\main.tex`

Updated abstract, contribution list, capability section, readiness interpretation,
bridge-to-control paragraph, limitations, future work, and conclusion.

## Main Numbers

Normal Nengo decoded output:

- LIF: `0.2269 +/- 0.0004` at `100.5 Hz`.
- HyperLIF T023: `0.2273 +/- 0.0047` at `40.3 Hz`.
- Adaptive T033: `0.2339 +/- 0.0012` at `53.3 Hz`.

Best HyperLIF-family state readouts:

- HyperLIF T023 reset gate: `0.1110 +/- 0.0064`.
- HyperLIF T023 spikes + voltage + gate: `0.1106 +/- 0.0212`.
- Adaptive T033 reset gate: `0.1269 +/- 0.0073`.
- Adaptive T033 spikes + voltage: `0.0973 +/- 0.0161`.
- Adaptive T033 spikes + voltage + gate: `0.1167 +/- 0.0141`.

Interpretation:

- The broad Nengo-suite capability claim remains supported by the 9-app
  capability matrix plus the 3-seed 7-app preflight.
- The final decoder-ablation table adds a state-readout layer: the probeable
  reset gate is useful for scalar NEF decoding at low firing rates.
- Residual-control targets remain future work for P3.

## Build Verification

Rebuilt with:

```powershell
.\scripts\build_paper.ps1
```

Verified:

- `paper\main.pdf`: 27 pages, 858119 bytes.
- `paper\main.log`: no undefined references/citations and no overfull boxes.
- `paper\main.blg`: `warning$ -- 0`.

## Readiness

P2 moves from 87% to 89%.

Remaining work:

- Final claim-to-artifact audit.
- IEEE/Overleaf packaging pass.
- Advisor copyedit and metadata.
