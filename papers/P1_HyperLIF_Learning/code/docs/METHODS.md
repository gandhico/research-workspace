# Methods (Phase 0 foundation)

## Neuron
PyTorch HyperLIF / Adaptive HyperLIF implemented as the exact **A-stable** discrete step shared
with the validated reference: gate update on the current `(v, r)`; conductance from the *updated*
`r`; exponential membrane update `v ← v·e^{-λΔt} + (d/λ)(1-e^{-λΔt})` with `λ=1/τ+G`,
`d=v_rest/τ+J/τ+G·v_reset_eff`. Events are emitted on an upward crossing of `event_threshold`
(readout only; no hard reset). Code: `src/adhyperlif_triage/neurons/hyperlif_torch.py`.

- **Conductance.** HyperLIF `G = reset_gain·r²`; Adaptive `G = (base_gain + gain_scaling·|J|)·r²`.
- **Origin (idea 1).** Gate-coupled reset `v_reset_eff = v_reset − delta_reset·r` — the symmetric
  mirror of the threshold hysteresis `θ_eff = v_thresh − γ·r`. `delta_reset=0` ⇒ exact reference.
- **Surrogate.** The smooth `(v,r)` path is differentiable; only the event crossing uses a
  fast-sigmoid surrogate gradient (`surrogate_beta`). The logistic gate uses `torch.sigmoid`
  (stable forward+backward) — the literal `1/(1+exp(-x))` matches forward but NaNs in float32
  backward at `alpha=100`; see `PARITY.md` / git history.

## Parity gate (validation)
`scripts/run_parity.py` checks the PyTorch neuron against `reference_numpy.py` (a frozen copy of
the validated Nengo-equivalent `stable` stepping) on step / stress / db_drive protocols in
float64. Pass criterion: `max|Δv|, max|Δr| < 1e-9` and zero event mismatch. Achieved ~1e-15/1e-14.

## Metrics
Task metrics (accuracy / macro-F1 / loss) arrive with the trainer. The differentiating
**dynamics** metrics already exist (`metrics/dynamics.py`): events/sample, spike-rate mean/std,
active/dead-neuron fraction, saturated fraction, gate mean/std, conductance mean, voltage range,
`outside_operating_fraction` (the audit stability check), nan_count.

## Reproducibility
Deterministic seeding (`utils/seeding.py`); per-run folders + flat registry
(`utils/run_io.py`); config-driven runner (`runner.py`). Every reported number will carry
dataset / tier / split / seed, and figures/CSVs regenerate from configs.
