# Paper-directed research plan: LQR implementation gap and DeePC

## Working title

From Nominal LQR Optimality to Data-Enabled Predictive Control: Constrained
Flight Control of the EHEKATL Blended-Wing-Body Aircraft in X-Plane 12

## Central narrative

The thesis-derived LTI model produces a mathematically stable and apparently
practical LQR after input-penalty selection. Real-time X-Plane implementation
exposes delay, control ownership, hidden artificial-stability dynamics,
distributed surfaces, operating-point dependence, constraints, and
reload-specific background motion. A reidentified delay-aware roll LQR is safe
but its measured matched-disturbance advantage is small and statistically
difficult to distinguish. The paper tests whether regularized constrained DeePC
can exploit measured behavior directly and deliver a larger, repeatable benefit
under the same interface, limits, safety supervisor, and held-out protocol.

## Contributions to test

1. Reproducible actuator-aware pre-X-Plane LQR feasibility study.
2. Experimental characterization of the nominal-to-real-time implementation
   gap in X-Plane 12.
3. Safe, provenance-controlled input-output data and a constrained regularized
   DeePC formulation for the EHEKATL BWB.
4. Frozen, common-protocol comparison of backstepping, LQR, and DeePC.

Backstepping is the recovery-capable supervisor and reference baseline. The main
optimization comparison is LQR versus DeePC; backstepping is not presented as a
new contribution.

## Common comparison contract

- Initial primary axis: R3 roll-rate regulation.
- Sampling: 35 Hz for measured roll cascade and candidate DeePC control.
- Manipulated variable: trim-relative yoke-roll perturbation.
- Primary output: body roll rate P; roll angle and realized-control channels are
  secondary constrained/audit outputs.
- Command bound: 0.0002 normalized perturbation.
- Slew bound: 0.00005 per 35-Hz sample.
- R3 nominal condition: approximately 39 kt and 240 Pa dynamic pressure.
- Safety: existing start/abort envelopes and permanent latched backstepping
  fallback; no automatic controller re-engagement.
- Comparison metrics: integrated absolute rate error, peak response, decay,
  control energy, bound utilization, fallback/constraint events, computation
  time, deadline misses, and uncertainty intervals across fresh reloads.

## Research phases

### P0 — Evidence normalization

Inventory existing datasets by source, role, operating point, sample rate,
signals, controller, excitation, gate result, and permitted use. Hash raw inputs
used by new DeePC analyses. Resolve the nominal-surface-degree versus normalized
X-Plane command distinction explicitly.

### P1 — Offline DeePC feasibility

Use only already accepted R3 training/design evidence. Define the DeePC input
and output channels, past/future horizons, persistent-excitation/rank checks,
normalization, regularization family, slack treatment, and hard constraints.
Keep held-out confirmation logs closed during design selection. Compare offline
replay against the frozen LQR and backstepping under identical disturbances.

Exit requirement: numerical conditioning, constraint satisfaction, runtime
budget, and robust effect-size audit pass before any online implementation.

### P2 — Observe-only online integration

Implement a default-observe DeePC runtime with no control-write path. Verify
sample timing, history initialization, optimization status, deterministic
fallback selection, command/slew feasibility, and exact offline/runtime replay.

### P3 — Guarded design pilot

One small, predeclared design pilot after all current stage gates permit it.
Exclude it from confirmation evidence. Freeze final controller and metrics from
design evidence only.

### P4 — Held-out common benchmark

Collect fresh-reload backstepping, frozen LQR, and frozen DeePC evidence using a
statistically powered protocol. Do not use separate-run tests if the prospective
power audit shows that reload variability dominates the expected effect.

### P5 — Manuscript synthesis

Generate tables and figures only from registered scripts and artifacts. Report
failed gates, computation cost, constraints, and operating-point limitations.
Do not claim global stability, global aircraft validity, or DeePC superiority
outside the tested envelope.

## Immediate authorized work

Stage 5 remains current. The immediate work is P0 and offline-only P1, which
falls within the already authorized controller/model redesign activity. The R4
observe retry remains preserved but is not required for the initial R3 DeePC
feasibility question. No new X-Plane control run is authorized by this plan.

