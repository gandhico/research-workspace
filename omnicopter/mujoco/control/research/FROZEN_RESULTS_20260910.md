# Frozen result: neuromorphic residual control on the omnicopter

**Freeze ID:** `NRCTRL-OMNI-2026-09-10-R1`  
**Frozen at:** 2026-09-10T17:31:12-06:00  
**Status:** immutable reference result

## Accepted conclusion

> PD es mejor en seguimiento nominal cuando la planta virtual coincide exactamente
> con su modelo; CMG-PES es mejor en rechazo de perturbaciones e incertidumbre.

This conclusion is conditional on the tested missions, controller configurations and
plant regimes below. It must not be shortened to a universal ranking of PD and CMG-PES.

## Frozen evidence

### Exact-model nominal campaign

- 25/25 missions completed by each of PD, canonical CMG-PES, Nengo-PD and
  canonical Nengo-CMG-PES, with zero reported saturation.
- Mean position RMSE: PD `0.001029 m`; canonical CMG-PES `0.011579 m`.
- Mean attitude RMSE: PD `0.0260 deg`; canonical CMG-PES `0.0629 deg`.
- The aggregate includes the canonical CMG-PES startup transient and is a nominal
  tracking result, not a disturbance-rejection ranking.
- Direct/Nengo conformance: PD is numerically identical; canonical CMG-PES differs
  by at most `9.762e-9 m` in mission position RMSE, `3.653e-7 deg` in mission
  attitude RMSE and `2.047e-8 N` in peak motor command.

### Post-disturbance windows on the exact-model plant

| Mission and analysis window | Position RMSE, PD -> CMG | CMG reduction | Attitude RMSE, PD -> CMG | CMG reduction |
|---|---:|---:|---:|---:|
| `hover_push`, `t >= 4 s` | 0.018088 -> 0.010551 m | 41.7% | 0.4412 -> 0.2929 deg | 33.6% |
| `circle_yaw_push`, `t >= 22 s` | 0.012024 -> 0.006276 m | 47.8% | 0.2941 -> 0.1967 deg | 33.1% |

### Held-out synthetic-mismatch batch

- MuJoCo at 500 Hz; held-out seeds 10, 11 and 12; three missions per controller.
- Mismatch includes mass, inertia, motor gain/lag and persistent external force/torque.
- Overall position RMSE: PD+feedforward `0.218231 m`; revised CMG-PES `0.098259 m`
  (55.0% reduction).
- Overall attitude RMSE: PD+feedforward `4.67160 deg`; revised CMG-PES `3.42779 deg`
  (26.6% reduction).
- Revised CMG-PES won all 9/9 paired cases against PD in both position and attitude.
- This is synthetic robustness evidence, not yet aerodynamic identification or
  hardware validation.

## Immutable artifact locations

- `control/output/comparison_four_controllers_interpreted_20260910/`
- `control/output/tracking_pd_vs_cmg_final_20260910/`
- `control/research/output/heldout_500hz_batch_20260910/`
- `control/research/output/nominal_500hz_check_20260910/`

The source campaigns used by the comparison are also retained under their dated
directory names. Future runs must use a new directory and a new freeze ID; they must
not overwrite these paths. File integrity is recorded in
`control/research/SHA256SUMS_FROZEN_20260910.txt`.

## Interpretation rules for later work

1. Report nominal tracking, startup transient, post-disturbance recovery and
   held-out robustness separately.
2. Identify the controller as canonical or revised CMG-PES in every table and plot.
3. Treat direct/Nengo agreement as backend validation, not as controller superiority.
4. Keep simulation-only results separate from aerodynamic and physical-twin evidence.
5. Any extension, rerun or corrected analysis receives a new version; this result
   remains unchanged as the reference baseline.
