# EHEKATL BWB XP12 experiment results

Last consolidated: 2026-08-10. This is the readable index; the complete
chronology and every individual log remain in `CONTROL_DEVELOPMENT_PROCESS.md`.

## Current controller status

| Controller | Demonstrated result | Boundary |
|---|---|---|
| Backstepping | Repeatable R3 baseline and small-pulse recovery | Recovery reference, not a global guarantee |
| Historical fixed LQR | Large excursions and repeated safety disengagement | Rejected |
| Identified delay-aware LQR | Safe R3 integration; about 11.1% matched improvement | Failed required 30% improvement |
| Pitch/roll rate LQR | Bounded pilots; held-out pitch-rate recovery failures | Stage 5 unresolved |
| Frozen P-only DeePC | Offline robust pass, 35-Hz integration pass, one guarded pilot pass | Design evidence; superiority unconfirmed |

## Historical experiments

- Original Backstepping reference `backstepping_original_dissertation_20260709_210205.csv`:
  959 samples/95.8 s; pitch −26.28°..+16.93°, roll −38.79°..+38.53°.
  Another run reached about 45.9° pitch and 57.9° roll. These demonstrate
  recovery behavior but are not local identification data.
- Historical fixed LQR `lqr_pitch_lqr_20260709_202343.csv`: max |pitch| 53.0°,
  max |roll| 111.9°. Run `20260709_202936` repeatedly hit divergence guards.
- Early pitch ID `pitch_id_20260709_204150.csv`: only 25.6% usable ID samples,
  left the envelope, q-dot residual 54.0 deg/s². Rejected.
- Duplicate four-state LQR fitted to closed-loop Backstepping was stable only
  on its fitted model. Rejected and archived.

## Stage 1 — Backstepping baseline: PASS

- P/Q/R independently confirmed as deg/s; rich logger and legacy routing passed.
- Three 600-row replacement baselines (`stage1_baseline_new_01/02/03`) were
  complete, fully engaged, saturation-free, and highly repeatable.
- Three controlled roll recovery runs passed: peak |roll| ≤0.3014°, peak |P|
  ≤1.0788 deg/s, final-10-s |roll| ≤0.0220°, final-10-s |P| ≤0.0037 deg/s.
- An earlier unlogged manual-disturbance run failed and remains adverse evidence.

## Stage 2 — Stabilized identification: PASS

- Early excitation failures exposed paused/replay state, incomplete ownership,
  nonpersistent CTRL packets, and a hidden physical pitch-trim contribution.
- Direct owned yoke writes plus trim-relative commands corrected the path.
- Accepted allocation: two training and two held-out validation runs for each
  of roll and pitch. All eight passed safety, completeness, realized-input, and
  richness gates. Hashes are in `paper/DATASET_REGISTRY.csv`.

## Stage 3 — Local models: PASS

- State: angle and body-rate perturbation; measured total-control input; delay
  three 10-Hz samples (~0.3 s).
- Roll A=`[[0,1],[-1.799965,-0.035987]]`, B=`[[0],[-286.518155]]`.
- Pitch A=`[[0,1],[-4.699647,-0.202786]]`, B=`[[0],[-210.642895]]`.
- Both controllable and useful locally; colored residuals prevent a global claim.

## Stage 4 — Offline LQR: PASS

- Delay-aware rate-only controllers passed 81 coefficient/delay cases per axis
  with zero unstable cases and no saturation in eight-log runtime replay.
- The later 35-Hz R3 measured-cascade roll LQR passed offline uncertainty,
  bounds, exact replay, and integration prerequisites.

## Stage 5 LQR flight evidence: unresolved

- Initial pitch-rate reference pilot was safe but tracked poorly because a
  rate damper is not an attitude tracker.
- Pulse pilots remained bounded but multiple frozen recovery/offset gates failed.
- A held-out pitch confirmation failed final delta-Q and decay-ratio gates.
- R3 roll LQR quiescent pilot `rich_R3_roll_lqr_pilot_20260712_200705.csv` passed.
- Matched Backstepping/LQR logs `203402`/`203707`: integral ratio 0.888807,
  about 11.1% improvement versus required ≥30%. Performance FAIL.
- Longer separate-run comparisons were statistically underpowered.

## Operating points

- R3: ~39 kt, ~240 Pa, cockpit throttle ~0.02353.
- A 129-kt observation was outside all validated regimes.
- R4 instrumentation passed near 46.7 kt/353.5 Pa/throttle 0.04142, but its
  identification observe attempt started outside the state gate. No R3
  controller is validly transferred to R4.

## DeePC experiments

- Training source: `rich_R3_roll_dualrate_pilot_20260712_193416.csv`.
- Multi-output P/roll/total-roll reconstruction failed; P-only passed with
  scaled temporal NRMSE 0.29257.
- Frozen: 35 Hz, Tini/N=5/5, lambda_g=10, Qy/Ru/Rdu=1/0.01/0.02,
  command/slew=0.0002/0.00005.
- Long horizon failed runtime. First regularization missed robust gate at
  0.906534. Retuned candidate passed 243/243 cases: worst/median integral ratio
  0.895344/0.788056, worst peak ratio 0.928154, full convergence.
- Packaged/design runtime identity error: zero.
- First X-Plane observe run failed at 26.59 Hz. Equivalent runtime optimization
  corrected it. Accepted observe `rich_R3_roll_deepc_observe_20260810_122949.csv`:
  1050 rows, 35.002 Hz, 38.12-ms max gap, 7.57-ms max runtime, no writes.
- Guarded waveform observe `rich_R3_roll_deepc_pilot_observe_20260810_143609.csv`: PASS.
- Guarded pilot `rich_R3_roll_deepc_pilot_20260810_144136.csv`: 1050 rows,
  max runtime 7.52 ms, peak/final |delta P| 0.003590/0.001347 deg/s,
  realized correlation 0.999999999997, no safety/fallback/restoration failure.
- This is design evidence, not independent confirmation.

## DeePC/LQR prospective benchmark

- Separate reloads qualify only at 48 pulses/controller (~149 s each).
- Paired sign-aligned waveform remains underpowered through 24 pairs.
- Paired mean pulse IAE: 16 pairs power 0.7967 (FAIL vs 0.80); 24 pairs power
  0.93 but requires ~152 s and unvalidated controller switching.
- Decision: no confirmation flight; superiority remains unproven.

## Formal state

- Stages 0–4 PASS for declared local scope; Stage 5 CURRENT.
- Stages 6–7 blocked.
- Direct LQR/DeePC tests remain local R3 tests with mandatory start gates,
  bounds, Backstepping fallback, rich logging, and restoration.
