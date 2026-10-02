# Gate r in the fixed-decoder CMG runs — logging bug, not dynamics

2026-09-11. Concerns `results/neuron_family_matched_45s/*/*/nengo-cmg-fixed/trace.csv`.

## Finding

In all 10 fixed-decoder CMG runs (2 platforms × 5 missions), `trace.csv`
writes `gate_0 … gate_5 = 0.0` at every sample. The full-rate neural archive
(`neural_trace_full_rate.npz`, 2 kHz, float64) of the same runs holds the true
gate, and it satisfies the model identity `a = clip(1e5 · r, 0, 1)` to 0.0
in every run. The CSV gate does not (errors up to 1.0).

| | archive r (true) | trace.csv r |
|---|---|---|
| resting value, every run | 3.73×10⁻⁶ = σ(−12.5) | 0.0 |
| max, Roll / Yaw360 | 4–5×10⁻⁶ | 0.0 |
| max, X2 Hard45 | 5.3×10⁻³ | 0.0 |
| max, Full3 / Hardstep / CF2 Hard45 | 1.0 (gates fully open) | 0.0 |

The 10 PES runs (`nengo-nef-pes`) are logged correctly: CSV and archive agree.

## Cause

`run_mujoco_nef.py`, `_neuron_state()` (lines 133–141). For a
`NengoNeuronFamilyAugmentor` — the class behind every `nengo-<family>-fixed`
controller, including `nengo-cmg-fixed` — the value written to the trace's
`gate_i` column is the unit's secondary state, looked up by name as
`adaptation`, `recovery` or `refractory_time` (the ALIF, Izhikevich and LIF
state names). The CMG's state is named `gate`, so the lookup falls through
to `np.zeros(6)`. `nengo-nef-pes` uses `NengoCMGPESAugmentor`, which returns
`augmentor.r` directly and is unaffected.

The simulation is unaffected: the logged activity, residual, decoder and all
summary metrics come from the true state. Only the `gate_i` trace columns
are wrong. (The same traces also carry `state_gate_0 … state_gate_5`, written
from the family's state dictionary; these were not checked here.) No
compiled metric in the paper reads them (the neuron-family
benchmark uses activity; `analyze_neural_archive.py` reads the archive).

## Why r is tiny but the activity is not

The CMG output is `a = clip(gate_gain · r, 0, 1)` with `gate_gain = 1e5`.
At rest the membrane settles at v ≈ 0.75, below `v_threshold = 1`, so the
gate target is σ(α(v − 1)) = σ(50 · (−0.25)) = σ(−12.5) = 3.7×10⁻⁶, and
a = 0.37. The unit reports activity from the sigmoid tail, well before the
gate "opens".

Once r grows, the threshold drops to `1 − γ r` (γ = 2) while the conductance
`g r²` shunts v toward 0.1; with r = 1 the argument is 50 · (0.1 + 1) = 55,
so an open gate holds itself open. Every gate that opened in these runs
stayed open.

## Handling

- `paper_figs_cmg_fixed_2026-09-11/make_cmg_fixed_figs.py` now takes r from
  the archive, aligned by matching the logged activity to 1e-9.
- `compare_fixed_pes.py` (this folder) reads the archive for both modes.
- The canonical runner is not modified (hashed in the audit). If the runs are
  ever repeated, fix `_neuron_state` to read `states["gate"]` for the CMG
  family.
