# P2 — Results, Equations, and Code Paths (for Overleaf porting)

Every claim below is validated against a named CSV — copy the value/equation directly into the
Overleaf draft, the code path is there if you need to re-derive or re-plot anything.

## Validated results

| Result / equation | Value | Code path | Evidence file |
|---|---|---|---|
| Python↔Nengo stepping parity | RMSE = 0, max\|Δ\| = 0, event mismatch = 0 (step + stress protocols) | `experiments/07_python_vs_nengo.py` | `07_python_vs_nengo.csv`, `07_parity_metrics.csv` |
| DB onset | `J_DB = (v_thresh-γ)(1+τG_b) = 2.4`, matches simulated collapse at `J≈2.3–2.4` | `experiments/03_current_sweep.py` | `03_db_analysis.csv`, `03_current_sweep.csv` |
| Fixed-gain latched voltage | `v*=J/(1+τG_b)`: predicted `1.3333` vs. simulated `1.3333` at `J=4` (exact) | `experiments/03_current_sweep.py` | `03_db_analysis.csv` |
| Adaptive avoids high-voltage latch | asymptotic open-gate voltage `0.625 < 0.8`; `β=80 > 62.5 = 1/(τ(v_thresh−γ))` | `experiments/03_current_sweep.py` | `03_db_analysis.csv`, `03_equilibria.csv` |
| Adaptive widens firing band, raises peak rate | `[1.6,3.5]`, 151 Hz vs. `[1.5,2.2]`, 73 Hz | `experiments/03_current_sweep.py` | `03_current_sweep.csv`, `tab_sweep.tex` |
| Integration scheme convergence | Both schemes first-order convergent to RK4 reference; gate error identical | `experiments/06_numerical_integration.py` | `06_integration_accuracy.csv` |
| Integration scheme stability | Exponential update unconditionally stable; explicit Euler overshoots at `λΔt>2` | `experiments/06_numerical_integration.py` | `06_stability.csv` |
| Backend portability | Custom neuron runs in NengoCore; rejected by OpenCL/Loihi without backend-specific work; NengoDL version-locked | `experiments/14_backend_portability_probe.py` | Summarized in `NENGO_CAPABILITY_FINDINGS.md` |
| 3-seed core capability preflight | 84/84 simulations, zero failures | `experiments/17_capability_seed_sweep.py` | `17_capability_seed_sweep.csv` + summary |
| 5-seed scalar NEF decoder ablation | Reset-gate decoder: `0.1110±0.0064` (T023), `0.1269±0.0073` (T033); combined-state: `0.1106±0.0212`, `0.1167±0.0141` | `experiments/18_nef_decoder_state_ablation.py` | `18_nef_decoder_state_ablation.csv` + summary |
| PES learning-rate/firing-rate trade | HyperLIF sparser in representation tasks; PES convergence slower than LIF at matched time | `experiments/15_pes_rate_matched.py` | `15_pes_rate_matched.csv` |

## Exploratory / needs-a-caveat-if-quoted

| Result | Caveat |
|---|---|
| Gate-state decoding (test RMSE `0.287`) | Single-neuron, scalar least-squares, fixed 70/30 split — not an ensemble/NEF claim |
| Adaptive HyperLIF operating ceiling (`J≳3.6`) | Empirical, parameter-dependent, not a full bifurcation analysis |
| Static origin calibration (θ=0.95) | Improves some app metrics, worsens others — an issue-finding result, not a clean win. Needs origin-aware gain/rate fitting before quoting as a benefit |

## Not yet in the current `.tex`, worth checking before your Overleaf pass

- `paper/main_ieee.tex` predates the capability/decoder-ablation results — if you're working
  from that file instead of `paper/main.tex`, the newer results above aren't in it yet.
- Table density: 27-page current PDF has several wide tables — you'll know better than me which
  belong in the main text vs. supplement for your target venue.

Full experiment-by-experiment map (all 16 scripts, not just the highlights above) is in
`P2_HyperLIF_Nengo_code.zip → RUNNERS.md`.
