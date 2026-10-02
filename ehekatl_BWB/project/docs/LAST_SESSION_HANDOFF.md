# EHEKATL BWB current handoff

Last updated: 2026-08-10 (America/Denver)

## Research direction

The paper now studies the gap between nominal offline LQR optimality and
real-time X-Plane implementation, then compares frozen LQR with regularized
constrained DeePC. Paper organization is indexed in `paper/README.md`, with
claims in `paper/CLAIMS_MATRIX.md` and dataset roles/hashes in
`paper/DATASET_REGISTRY.csv`.

## Gate status

```text
Stages 0--4                                  PASS for declared local scope
Stage 5 inner body-rate validation           CURRENT
Stage 6 attitude-loop validation             BLOCKED
Stage 7 combined/recovery comparison         BLOCKED
DeePC X-Plane status                         NOT ENGAGED / NOT AUTHORIZED
```

## LQR result retained

The R3 discrete-cascade roll LQR integrated safely, but the immutable matched
flight pair achieved an integral ratio of 0.888807 against backstepping, below
the frozen 0.70 requirement. The approximately 9--11 percent effect was too
small for a statistically powered separate-run campaign. Stage 5 did not pass.

## DeePC progress

Training/design source only:

```text
logs/rich_R3_roll_dualrate_pilot_20260712_193416.csv
SHA256 05b7aef1bb6f36fba5fce208e3b750c85d9fe69a364aaf2a97960781eb5ed08e
```

Frozen candidate:

```text
Output                         P only
Sample rate                    35 Hz
Tini / prediction horizon      5 / 5 samples
lambda_g                       10
Qy / Ru / Rdu                  1 / 0.01 / 0.02
Command / slew limits          0.0002 / 0.00005 per sample
```

Offline evidence:

```text
Temporal scaled P NRMSE                     0.29257
243-case worst DeePC/LQR integral ratio     0.895344 PASS (<=0.90)
243-case median DeePC/LQR integral ratio    0.788056
Worst peak ratio                            0.928154 PASS (<=1.10)
Maximum sent command / base slew            4.39288e-5 / 9.96963e-6
Optimizer convergence                       243/243 cases PASS
Single-runtime audit maximum                 11.36 ms PASS (<28.57 ms)
Packaged/design command identity             exact; max error 0
Focused DeePC tests                          6 PASS
Held-out confirmation responses opened      none
```

Important failures remain visible:

- Multi-output P/roll/total-roll reconstruction failed; only P is predicted.
- The first Ru/Rdu=0.01/0.05 candidate missed the robust gate at 0.906534.
- The longer Tini=15/N=20 optimizer missed the 35-Hz runtime gate.
- No offline result is an X-Plane performance claim.

Canonical DeePC artifacts:

```text
deepc/configs/rich_R3_deepc_runtime.json
deepc/src/r3_roll_runtime.py
configs/rich_R3_deepc_uncertainty_replay.json
configs/rich_R3_deepc_runtime_identity.json
configs/rich_R3_deepc_hyperparameter_scan.json
```

## X-Plane installation repair

On 2026-07-15 X-Plane reported an invalid default forest mesh:

```text
Resources/default scenery/1200 forests/*/broad_tmp.for
Wrong number of vertices and/or indices for mesh (REN_forest.cpp:292)
```

The official X-Plane 5.4.0-r1 updater scanned and repaired the existing install:

```text
/home/ubuntu/Xplane12/X-Plane 12
```

The updater completed normally. The NVIDIA launcher remains unchanged:

```text
/home/ubuntu/.local/share/applications/xplane12-nvidia.desktop
/home/ubuntu/run-xplane12.sh
NVIDIA GeForce GTX 980 Ti selected through PRIME/Vulkan environment variables
```

This scenery problem was unrelated to the controller work; no research script
modified the X-Plane installation.

## DeePC observe-integration update — 2026-08-10

The structurally observe-only integration is implemented:

```text
Runner:   scripts/run_rich_r3_roll_deepc_observe_xp12.py
Wrapper:  scripts/run_rich_r3_roll_deepc_observe.sh
Analyzer: scripts/analyze_rich_r3_roll_deepc_observe.py
Tests:    tests/test_r3_roll_deepc_observe.py
```

The runner has no `--engage` option, no `sendCTRL`/`sendDREF` call, and always
logs controls-sent and ownership-requested as zero. It logs exact pre/post
runtime histories, hypothetical command and fallback selection, convergence,
iterations, safety/live state, acquisition timing, and optimizer runtime.
Compilation, CLI, shell syntax, 78 project tests, and 9 focused DeePC tests pass.

A read-only live snapshot found X-Plane connected, unpaused, out of replay, and
with ownership clear, but the aircraft was outside R3: altitude 2439.30 m, IAS
124.79 kt, roll 25.41 deg, P/Q/R -0.082/+1.573/+3.305 deg/s. No formal observe
run and no control command were issued.

User-ready verification later on 2026-08-10 also blocked safely: altitude
1868.92 m, IAS 114.95 kt, pitch 7.376 deg, roll 0.013 deg, and P/Q/R
+0.0155/+0.1764/-0.0913 deg/s. The simulator was live, artificial stability
was enabled, and overrides were clear, but altitude, IAS, and pitch failed the
frozen R3 start gate. No capture and no control command were issued.

The R3 state was subsequently restored and P2 observe integration passed after
one runtime correction and one unchanged timing confirmation:

```text
Rejected pre-optimization log: logs/rich_R3_roll_deepc_observe_20260810_122507.csv
  798 rows / 26.587 Hz; optimizer 22.77 ms median, 41.36 ms max: FAIL
  Safe, exact, bounded, and ownership-clear; timing/completeness failed.
Rejected isolated-gap log: logs/rich_R3_roll_deepc_observe_20260810_122825.csv
  1050 rows / 35.002 Hz; optimizer 3.59 ms median, 7.25 ms max;
  one 87.36-ms gap caused by an 84.60-ms XPlaneConnect acquisition: FAIL.
Accepted confirmation: logs/rich_R3_roll_deepc_observe_20260810_122949.csv
  1050 rows / 35.002 Hz; maximum gap 38.12 ms;
  optimizer median/p95/max 3.79/5.48/7.57 ms;
  exact replay/history error 0; all checks PASS; no controls sent.
```

The correction only precomputes constant optimizer matrices and replaces scalar
`np.clip` temporaries with equivalent scalar comparisons. Frozen parameters,
commands, constraints, and gates are unchanged; exact identity error remains 0.

## Next authorized action

P2 observe-only integration is `PASS`. P3 guarded design-pilot preparation is
implemented and statically passes:

```text
Frozen protocol: deepc/configs/rich_R3_deepc_pilot.json
Runner: scripts/run_rich_r3_roll_deepc_pilot_xp12.py
Observe wrapper: scripts/run_rich_r3_roll_deepc_pilot_observe.sh
Engaged wrapper: scripts/run_rich_r3_roll_deepc_pilot.sh
Analyzer: scripts/analyze_rich_r3_roll_deepc_pilot.py
Stimulus: paired +/-0.00005 half-sines at 10 and 12 s, 0.2 s each
Limits: command 0.0002; slew 0.00005/sample; unchanged safety envelopes
Static regression: 81 project tests and 13 focused DeePC tests PASS
```

The first readiness check for the guarded runner found altitude 1604.29 m,
IAS 39.93 kt, roll -16.13 deg, and P/Q/R +0.101/+1.968/-6.910 deg/s. Roll and
body-rate start gates failed. The no-control waveform audit was not started.

Next: reload the clean R3 situation, let it settle, then run the exact
observe-only guarded waveform audit and analyzer. The engaged pilot remains
blocked until that saved log passes. Held-out confirmation responses remain
closed.

Guarded waveform observe gate subsequently passed:

```text
Log: logs/rich_R3_roll_deepc_pilot_observe_20260810_143609.csv
Rows/rate/max gap: 1050 / 35.0025 Hz / 46.98 ms
Runtime median/p95/max: 3.54 / 5.26 / 8.03 ms
Peak hypothetical combined perturbation / slew: 5.05395e-5 / 2.30833e-5
Replay/history/selection errors: exactly 0
Latch/safety/ownership/control writes: none / PASS / clear / none
Decision: PASS. Exactly one guarded engaged P3 design pilot is authorized after
a fresh read-only R3 start-gate pass. It is design evidence, not confirmation.
```

The single guarded P3 design pilot passed:

```text
Log: logs/rich_R3_roll_deepc_pilot_20260810_144136.csv
SHA256: b37ed92326cf9c9ba8149a0551bb0c6af8a4a57f6c66b00a352463e111a30f66
Rows/rate/max gap: 1050 / 35.0024 Hz / 42.10 ms
Runtime median/p95/max: 3.62 / 5.17 / 7.52 ms
Peak |delta P| / final-5-s max: 0.003590 / 0.001347 deg/s PASS
Sent-to-realized lag-1 correlation: 0.999999999997 PASS
Peak perturbation / max slew: 3.76264e-5 / 2.19556e-5 PASS
Replay/history/selection error: 0
Fallback/latch/safety event: none; both owned axes restored exactly
Decision: P3 PASS as design-only evidence; excluded from confirmation.
```

Next authorized work is offline P4 common-benchmark and prospective power
design using the frozen backstepping/LQR/DeePC contract. Do not use this pilot
as confirmation, do not tune the controller from future confirmation responses,
and do not collect a benchmark until the protocol and power gate pass.

P4 prospective benchmark design was completed and rejected for flight:

```text
Separate-reload ratio audit:
  artifact configs/rich_R3_deepc_separate_power.json
  power at 6/12/24/48 pulses per controller: 0.317/0.460/0.630/0.843
  first qualifying count: 48; minimum 149 s per controller

Close-spaced paired sign-aligned-waveform audit:
  artifact configs/rich_R3_deepc_paired_power.json
  no count through 24 pairs qualified; maximum power 0.623

Close-spaced paired mean per-pulse IAE audit:
  artifact configs/rich_R3_deepc_paired_iae_power.json
  power at 4/6/8/12/16/24 pairs: 0.440/0.487/0.630/0.763/0.797/0.930
  16 pairs FAIL the 0.80 gate; first qualifying count 24, minimum 152 s
```

Decision: no P4 benchmark flight. The qualifying designs require excessive
exposure and, for pairing, unvalidated live controller switching and history
handoffs. Do not round 0.7967 to 0.80, reduce the confidence/power gate, or use
the design pilot as confirmation. The supported result remains offline robust
feasibility plus safe single-pilot integration, not X-Plane superiority.

Next authorized work is paper synthesis from registered evidence, or an
offline controller/experiment redesign that creates a materially larger and
more identifiable effect without changing safety/command limits. No user or
simulator action is currently required.

## Standardized direct controller tests — 2026-08-10

LQR and DeePC now mirror the Backstepping project layout and API:

```text
lqr/LQRController.py             SetPoint/update/output/clear facade
lqr/run_lqr_direct_xp12.py       canonical guarded rich logger
lqr/run_lqr_direct.sh            timestamped run + automatic analysis
deepc/DeePC.py                   SetPoint/update/output/clear facade
deepc/run_deepc_direct_xp12.py   canonical guarded rich logger
deepc/run_deepc_direct.sh        timestamped run + automatic analysis
```

The launchers use the validated paired pulse, preserve R3 gates, limits,
Backstepping fallback and restoration, and write `logs/direct_*.csv`. Static
verification: shell syntax, compilation, both CLIs, three interface identity
tests, and 84 full project tests PASS. No simulator run was performed during
this restructuring. Consolidated results and schematic plan:
`docs/EXPERIMENT_RESULTS_SUMMARY.md` and
`docs/CONTROLLER_TEST_AND_RESEARCH_PLAN.md`.

When observe integration is ready, use a fresh clean R3 situation near 1700 m,
39 kt, about 240 Pa dynamic pressure, throttle 0.02353, pitch about 1.3 deg,
roll within 5 deg, all body rates within 1 deg/s, artificial stability enabled,
automation off, live/unpaused, replay off, Manual/Clear weather, and no failures.

Authoritative full history: `docs/CONTROL_DEVELOPMENT_PROCESS.md`.

## Direct DeePC live attempt — 2026-08-10

The canonical direct DeePC launcher was invoked against the connected live
EHEKATL BWB. Its frozen start gate blocked on altitude, roll, and body rate
before axis ownership or any control write. No flight log was created and no
controller performance claim follows. The direct LQR and DeePC wrappers were
then corrected to detect a missing/empty log after a start block and exit with
a concise message instead of launching an analyzer on a nonexistent file.

After a fresh clean R3 reload, the direct DeePC demonstration passed every
frozen guarded-pilot check. Log `logs/direct_deepc_20260810_150657.csv` contains
1050 samples at 35.0014 Hz with a 50.09-ms maximum gap. Optimizer median/p95/max
runtime was 4.02/5.36/7.90 ms. Peak and final-5-s absolute delta-P were
0.004163 and 0.001311 deg/s; sent-to-realized lag-one correlation was
0.999999999990. Peak perturbation/slew were 4.6094e-5/2.1260e-5. Replay,
history, and selection errors were zero; no latch, fallback, saturation, or
safety event occurred; both axes restored. SHA256:
`d326b6dacee04f9938be503036049d592a71e8f8275e7c84d397c073da29f662`.
This is functionality/demonstration evidence, not independent superiority
confirmation. Reload clean R3 before any direct LQR run.

The subsequent fresh-reload direct LQR demonstration also passed every frozen
direct-run check. Log `logs/direct_lqr_20260810_151244.csv` contains 1050
samples at 35.0040 Hz with a 42.23-ms maximum gap. Peak command/slew were
4.6696e-5/2.1706e-5. Descriptive peak and final-5-s absolute delta-P were
0.005622 and 0.001496 deg/s. Exact waveform and runtime replay passed; no latch,
fallback, safety event, or restoration failure occurred. SHA256:
`91385f3cb897e2e326612ea28b2e2630c653216b18be2317fe74dc25aff93600`.
The DeePC and LQR direct demonstrations began from separate reloads and are not
a matched or powered superiority comparison.
