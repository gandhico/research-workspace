# Candidate Results: Nengo-Universal HyperLIF Pass

Date: 2026-07-04

This note summarizes the first priority candidate benchmark from
`experiments/11_origin_aware_calibration_sweep.py`. The purpose is not to claim
final optimality, but to identify the current HyperLIF / Adaptive HyperLIF model
most likely to work broadly across ordinary Nengo applications.

## Sweep Scope

- Source matrix: `results/csv/11_full_tuning_candidate_matrix.csv`
- Evaluated subset: priority-1 candidates with `implementation = core_params`
- App suite: communication channel, function representation, 2D transform,
  working memory, oscillator, and PES learning
- Runs completed: 126 app-candidate combinations
- Failures: 0
- Summary output: `results/csv/12_origin_aware_calibration_summary.csv`
- Figures: `fig_candidate_robustness_heatmap`,
  `fig_candidate_score_events`, `fig_candidate_rate_calibration`

The robustness score is the mean normalized app penalty plus penalties for app
failures and strongly bad app metrics. Lower is better.

## Current Recommendation

Use this as the current Paper 3 universal-candidate model:

```python
FastReadoutHyperLIFNengo(
    event_threshold=0.95,
    v_reset=-0.6,
    min_voltage=-2.0,
    rate_to_current=140.0,
    reset_gain=100.0,
)
```

Candidate ID: `T023`

Interpretation: HyperLIF with θ_event=0.95 needs origin-aware readout/gain
calibration. The earlier static-origin result at `rate_to_current=80` was not a
clean failure of the neuron dynamics; it was mostly a calibration mismatch. At
`rate_to_current=140`, the same origin policy becomes much more balanced across
Nengo apps.

## Ranked Top Candidates

| Rank | ID | Candidate | Score | Bad apps | Mean event rate |
|---:|---|---|---:|---:|---:|
| 1 | T001 | LIF native reference | 0.679 | 0 | 22.60 |
| 2 | T023 | HyperLIF θ=0.95, origin, rate_to_current=140 | 1.252 | 0 | 24.39 |
| 3 | T033 | Adaptive θ=0.95, origin, rate_to_current=140 | 1.902 | 1 | 26.16 |
| 4 | T002 | HyperLIF θ=1.00 | 1.908 | 1 | 17.94 |
| 5 | T008 | HyperLIF θ=0.95, mild origin | 2.759 | 2 | 30.28 |
| 6 | T020 | HyperLIF θ=0.95, origin, rate_to_current=40 | 2.852 | 2 | 31.70 |

LIF remains the native baseline and still wins overall. Among HyperLIF-family
models, T023 is currently the strongest general-purpose candidate because it has
no bad app columns in this suite.

## Key Observations

1. Static origin helps only after gain calibration.
   The θ=0.95 origin baseline at `rate_to_current=80` improved communication and
   PES, but hurt function representation, transform, memory, and oscillator
   metrics. Raising `rate_to_current` to 140 gives the best broad result.

2. Adaptive HyperLIF is promising but not yet universal.
   The best adaptive candidate, T033, improves communication and PES relative to
   some HyperLIF variants, but still crosses the bad-app threshold on 2D
   transform and remains weaker on memory/oscillator robustness.

3. More events are not automatically better.
   Candidates with higher mean event rates often score worse. The model needs
   enough events for readout, but excessive activity appears to destabilize
   decoder quality across tasks.

4. The current result is a candidate-selection result, not a final universal
   guarantee.
   We have a strong smoke-suite winner, but still need seed sweeps, explicit
   rate-curve fitting, and larger app coverage before claiming general Nengo
   compatibility.

## Immediate Next Steps

1. Freeze T023 as the default HyperLIF candidate for Paper 3 app experiments.
2. Run a seed sweep for T001, T002, T023, and T033 on the six-app suite.
3. Add an empirical rate-curve calibration pass for the exact origin policy.
4. Tune memory/oscillator-specific stress cases, because these remain the weak
   points for non-LIF neurons.
5. Keep T033 as the adaptive candidate, but treat it as second-line until the
   adaptive gain law is tuned for transform and memory.
