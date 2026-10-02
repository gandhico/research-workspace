# EHEKATL BWB XP12 Controller Development Record

Last updated: 2026-09-17 (America/Denver)

## Purpose and authority

This document prevents repeated experiments, conflicting bridges, undocumented
gain changes, and conclusions unsupported by flight evidence. It is the
authoritative record for the EHEKATL BWB controller work in this directory.

Read this entire file before every work session. Update it after every material
analysis, code change, or X-Plane run. Work only on the stage marked `CURRENT`.
Never advance a stage merely because code runs or an offline calculation is
stable. A stage advances only after all its listed evidence exists and its gate
is explicitly changed to `PASS`.

“100% validated” means 100% of the declared acceptance criteria for the current
stage have been satisfied with reproducible evidence. It does not mean that a
controller is mathematically guaranteed safe in every possible flight state.

## Canonical locations

Project root:

```text
/home/ubuntu/GHYN/Xplane_controllers/EHEKATL_BWB_XP12
```

Canonical controller locations after the 2026-07-10 cleanup:

```text
backstepping/
pid/
lqr/
```

The Python environment remains at its original path to preserve its embedded
absolute paths:

```text
backstepping/ehekatl_xplane12_backstepping_bridge/.venv/
```

Shared logs:

```text
logs/
```

Standard shell entry, from any directory:

```bash
cd /home/ubuntu/GHYN/Xplane_controllers/EHEKATL_BWB_XP12
source backstepping/ehekatl_xplane12_backstepping_bridge/.venv/bin/activate
mkdir -p logs
```

Invoke every canonical script using its complete project-relative path under
`backstepping/`, `pid/`, `lqr/`, or `scripts/`.

## Non-negotiable project conclusions

1. Backstepping is the demonstrated recovery-capable baseline and must be
   preserved. Its ability to recover from large disturbances is a design asset.
2. Recovery capability is not the same as clean linear-model identification.
   Saturated and large-attitude samples must not be used to fit a local LQR
   model.
3. The documented XPlaneConnect vector is `[aileron, elevator, rudder,
   throttle]`, but the working original controller uses `routing=legacy`, which
   sends its logical pitch output in CTRL index 0 and logical roll output in CTRL
   index 1. Do not “correct” this mapping without an isolated sign/routing test.
4. Body rates should come from X-Plane P/Q/R datarefs with explicitly recorded
   units. Finite differences are fallback measurements, not preferred model-ID
   signals.
5. A controller safety `WAIT` state that sends only a captured trim value does
   not stabilize the aircraft. Automatic re-engagement after a violation is not
   accepted as safe recovery behavior.
6. Closed-loop backstepping tracking data alone cannot reliably separate plant
   dynamics from controller dynamics. Identification excitation must be known,
   independently logged, and applied around a stabilizing baseline.
7. No LQR is presently validated for X-Plane flight.

## Work completed and evidence

### Original backstepping implementation

The original controller is in:

```text
backstepping/Backstepping.py
backstepping/run_backstepping_xp12.py
```

Original parameters used in the dissertation-style run:

```text
roll setpoint       0 deg
pitch setpoint      6 deg
K roll/pitch        0.001 / 0.001
Ku roll/pitch       33 / 39
tau roll/pitch      0.03 / 0.03
frequency           10 Hz
routing             legacy
throttle            -998 (preserve current)
```

Trusted reference supplied by the user:

```text
logs/backstepping_original_dissertation_20260709_210205.csv
```

Observed reference statistics:

```text
samples             959
duration            95.8 s
sample rate          10.0 Hz
pitch range          -26.28 to +16.93 deg
roll range           -38.79 to +38.53 deg
aileron/CTRL0 range  -0.3636 to +1.0093
elevator/CTRL1 range -1.1934 to +1.2030
```

The unwrapped control columns can exceed ±1 even though the sent command may be
clipped, so analysis must distinguish raw controller output from actual CTRL.

Another original-controller run:

```text
logs/original_backstepping_20260709_205609.csv
```

It contained major excursions and saturation (approximately 45.9 deg maximum
absolute pitch and 57.9 deg maximum absolute roll). It is recovery evidence,
but not a clean near-trim validation or identification dataset.

### Earlier canonical LQR work

Existing implementation:

```text
lqr/LQR.py
lqr/run_lqr_xp12.py
lqr/identify_pitch_model.py
```

The canonical controller currently contains fixed gains:

```text
K_LON = (1.58255059, -2.53350077, -1.84584039, -22.06327663)
K_LAT = (0.11366923, 2.95176288, -0.16714788, 2.67770629)
```

Their originating A/B model, trim condition, Q/R weights, airspeed, altitude,
and independent validation dataset are not recorded beside them. They therefore
remain unvalidated for this X-Plane aircraft configuration.

Important flight evidence:

```text
logs/lqr_pitch_lqr_20260709_202343.csv
duration 44.6 s; max |pitch| 53.0 deg; max |roll| 111.9 deg

logs/lqr_pitch_lqr_20260709_202936.csv
duration 45.5 s; max |pitch| 15.4 deg; max |roll| 13.5 deg;
engaged fraction about 0.74; repeated oscillation/divergence guards
```

These runs do not validate the fixed-gain LQR.

### Pitch excitation and first-order identification

Excitation log:

```text
logs/pitch_id_20260709_204150.csv
```

Measured results:

```text
rows                         656
duration                     44.99 s
engaged fraction             0.256
identification samples       157
pitch range                  -22.75 to +26.66 deg
pitch-rate range             -77.62 to +76.07 deg/s
input range                  -0.015 to +0.015 stick
fit                          q_dot = a*q + b*u_e
a                            -0.82515
b                            659.152
RMS q_dot residual           54.042 deg/s^2
recommended kq               1.2415e-05
```

This dataset is rejected for final model design because it spent most of its
time disengaged, left the intended local envelope, and has a large residual.

### Incorrect duplicate LQR added during earlier work

The following files were added to the backstepping experiment directory:

```text
LQR.py
identify_lqr_model.py
lqr_model.json
run_lqr_xp12.py
```

They fit a four-state model to closed-loop backstepping data. The identified
model was controllable and its calculated LQR closed-loop eigenvalues were
inside the unit circle, but that proves only stability of the fitted model. It
does not validate the controller against X-Plane. The suggested initial clip of
0.25 was too aggressive compared with the subsequent evidence. Status:
`REJECTED FOR FLIGHT`; retained as an auditable record under
`archive/rejected_lqr_model_attempt/`.

## Shell and documentation mistakes already encountered

Do not repeat these:

- `^[[200~python` is a bracketed-paste escape sequence accidentally included in
  the command.
- `ython3` is a missing leading `p`.
- A trailing `~` after a CSV filename changes the filename.
- `logs/pitch_id_YYYYMMDD_HHMMSS.csv` is a placeholder, not a real file.
- Before the cleanup, `run_pid_xp12.py` was requested from a directory where
  that file did not exist. The organized path is now `pid/run_pid_xp12.py`.
- Running a bare `python3 run_lqr_xp12.py` from the project root fails; use the
  explicit retained path `lqr/run_lqr_xp12.py` for CLI inspection only until
  identification is approved.

Before presenting a command, verify the target with `test -f` or `--help`.

## Stage-gated methodology

### Stage 0 — Consolidate history and rules

Status: `PASS`

Acceptance criteria:

- [x] Canonical and experimental paths documented.
- [x] Existing logs and important outcomes documented.
- [x] Rejected model and reason documented.
- [x] Persistent read-before-work instruction added in `AGENTS.md`.
- [x] Stage gates and non-advancement rule documented.

Evidence: this document and `AGENTS.md` exist and are readable in the current
working directory.

### Stage 1 — Validate repeatable backstepping baseline

Status: `PASS`

Objective: establish a repeatable, recovery-capable baseline at a single,
recorded X-Plane configuration before injecting identification signals.

Required acceptance criteria:

- [x] Record aircraft version/configuration, payload, fuel, weather, failures,
      starting altitude, indicated/true airspeed, throttle state, and initial
      attitude/rates.
- [x] Confirm P/Q/R dataref units with a controlled diagnostic.
- [x] Confirm exact legacy CTRL routing and signs without changing controller
      gains.
- [x] Capture at least three comparable 60-second backstepping runs from the
      same defined trim envelope.
- [x] Every run has at least 99% expected samples and no logging gaps above 2.5
      nominal periods.
- [x] Every run records actual CTRL commands, raw outputs, attitudes, P/Q/R,
      airspeed, altitude, setpoints, saturation flags, and recovery events.
- [x] Define numerical tracking/recovery thresholds from the three-run evidence;
      do not invent thresholds after seeing only one favorable run.
- [x] All three runs satisfy those frozen thresholds.
- [x] Independently reproduce the summary report from the saved CSV files.

The original historical logs did not satisfy these criteria. The replacement
rich baselines and controlled recovery logs listed below now provide the
required evidence. Stage 1 passed on 2026-07-10. LQR synthesis remains blocked;
only Stage 2 identification-experiment design is authorized next.

Historical Stage 1 implementation action: extend a copy/wrapper of the original backstepping runner
to add measurements and metadata without changing the original Backstepping
equations, gains, routing, or commanded outputs. Validate the enhanced logger in
`--dry-run`/read-only form before its first closed-loop baseline capture.

Implementation started: `run_backstepping_baseline_xp12.py` is the instrumented
runner. It defaults to observe-only and requires explicit `--engage` before it
sends controls. It requires configuration metadata and declared P/Q/R units.
Its CLI/import, X-Plane read-only capture, timing, and numeric-equivalence checks
have passed. This paragraph records the earlier implementation state.

Static validation completed 2026-07-09:

```text
Python compilation                    PASS
CLI construction/help                 PASS
observe-only default                  PASS
original default gains                PASS
legacy raw mapping                    PASS
wrapper clipping behavior             PASS
X-Plane read-only measurement capture PASS (availability/timing only)
numeric command equivalence from captured X-Plane inputs PASS
P/Q/R declared-unit confirmation       PASS (`deg_s`)
```

The first observe-only measurement diagnostic was captured with the following
command. It did not send controller commands. The
`UNKNOWN-stage1-diagnostic` metadata intentionally prevents it from being
mistaken for one of the three fully documented baseline runs:

```bash
cd /home/ubuntu/GHYN/Xplane_controllers/EHEKATL_BWB_XP12
source backstepping/ehekatl_xplane12_backstepping_bridge/.venv/bin/activate
python3 backstepping/run_backstepping_baseline_xp12.py \
  --duration 10 \
  --hz 10 \
  --rate-units deg_s \
  --aircraft-config UNKNOWN-stage1-diagnostic \
  --payload UNKNOWN-stage1-diagnostic \
  --fuel UNKNOWN-stage1-diagnostic \
  --weather UNKNOWN-stage1-diagnostic \
  --failures UNKNOWN-stage1-diagnostic \
  --test-id stage1_observe_only_01 \
  --out logs/stage1_observe_only_01.csv
```

Diagnostic analysis completed 2026-07-10:

```text
rows                                      100
elapsed span                              9.898815654 s
mean dt, excluding first sample           0.099988037 s
minimum / maximum dt                      0.098808153 / 0.100131414 s
maximum deadline lateness                 0.001269488 s
missing P/Q/R samples                     0
missing IAS/TAS samples                   0
engaged samples                           0
metadata/test-id/routing mismatches       0
maximum legacy CTRL mapping error         0
maximum original-equation output error    0
```

This passes the logger availability, timing, observe-only, legacy mapping, and
original-equation equivalence checks. It does not prove that the declared
`deg_s` P/Q/R units are correct because the capture did not include an
independent controlled-rate reference. Do not add `--engage` yet. The next
permitted work is a read-only controlled-motion diagnostic comparing P/Q/R
against attitude kinematics, followed by analysis of the saved log.

Session update:

```text
Date/time: 2026-07-09
Current stage: Stage 1
Objective: create and statically validate enhanced baseline logger
Files changed: AGENTS.md, CONTROL_DEVELOPMENT_PROCESS.md,
               run_backstepping_baseline_xp12.py
Exact command: Python compile/help and local assertion suite (see work record)
Input conditions/configuration: offline; no X-Plane command sent
Output log: none
Measured results: static checks passed
Acceptance criteria evaluated: software prerequisites only
Result: INCONCLUSIVE for Stage 1
Reason: no X-Plane observe-only capture or repeated baseline flight evidence yet
Next allowed action within the same stage: run observe-only diagnostic above
```

Follow-up analysis:

```text
Date/time: 2026-07-10 (America/Denver)
Current stage: Stage 1
Objective: evaluate stage1_observe_only_01.csv before any engaged baseline run
Files changed: docs/CONTROL_DEVELOPMENT_PROCESS.md only
Exact command: read-only CSV timing, availability, mapping, and equation checks
Input conditions/configuration: saved diagnostic log; no X-Plane command sent
Output log: logs/stage1_observe_only_01.csv (existing input evidence)
Measured results: 100 rows; mean dt 0.099988037 s; max gap 0.100131414 s;
                  all samples disengaged; no missing P/Q/R or airspeed;
                  zero legacy-mapping and controller-equation error
Acceptance criteria evaluated: logger prerequisites only
Result: PASS for observe-only logger diagnostic; INCONCLUSIVE for Stage 1
Reason: P/Q/R units and three repeatable engaged baselines remain unproven
Next allowed action within the same stage: read-only controlled-motion P/Q/R unit diagnostic
```

Controlled-motion P/Q/R diagnostic:

```text
Date/time: 2026-07-10 09:52 America/Denver
Current stage: Stage 1
Objective: determine whether X-Plane P/Q/R samples are deg/s or rad/s
Files changed: docs/CONTROL_DEVELOPMENT_PROCESS.md only
Exact input log: logs/stage1_pqr_units_20260710_095224.csv
Input conditions/configuration: observe-only manual controlled motion;
                                configuration metadata intentionally UNKNOWN
Output log: logs/stage1_pqr_units_20260710_095224.csv
Measured results:
  rows / elapsed span                         515 / 29.941169720 s
  attitude change phi/theta/psi               +11.029926 / +1.390697 / -16.626968 deg
  deg/s kinematic prediction                  +11.025042 / +1.388206 / -16.547811 deg
  rad/s kinematic prediction                  +631.688400 / +79.538368 / -948.119741 deg
  best fitted scale relative to deg/s         0.998743 / 0.998559 / 1.001395
  deg/s one-step RMSE phi/theta/psi           0.001816 / 0.000417 / 0.003403 deg
  rad/s one-step RMSE phi/theta/psi           1.272856 / 0.175171 / 2.540772 deg
  engaged samples                             0
  mean / maximum sample interval              0.058251303 / 0.072186934 s
  achieved fraction of requested 20 Hz        0.858350
  maximum accumulated deadline lateness       4.244029130 s
Acceptance criteria evaluated: P/Q/R unit confirmation; logger timing diagnostic
Result: PASS for P/Q/R=`deg_s`; FAIL for requested 20 Hz sample completeness
Reason: full Euler/body-rate kinematics independently distinguish the unit scale;
        blocking acquisition cannot sustain the requested 20 Hz rate
Next allowed action within the same stage: retain the demonstrated 10 Hz rate
        for baseline captures, or optimize acquisition before requiring 20 Hz;
        obtain complete configuration metadata before an engaged baseline
```

Configuration screenshots reviewed 2026-07-10:

```text
Evidence directory: archive/screenshots/
Aircraft display name: EHEKATL BWB G33
Aircraft class / manufacturer: Experimental / GHYN
Design studio: preliminary
Aircraft file: Aircraft/GHYN/EHEKATL BWB 5 1.acf
Aircraft internal version: 1
Engines: Twin Engine; start with engines running enabled
Livery/variant selector: Default
X-Plane: 12.4.3-r2, build 124311, Intel 64-bit, Vulkan

Weight units: US Customary
CG: Default; UI reports no payload stations and does not allow CG adjustment
Payload: no payload stations shown
Internal fuel: 0.0 lb
Empty / displayed total / maximum weight: 14 / 14 / 22 lb
Holdover time: 0 min
Crew oxygen: 1841 psi

Weather source / preset: Manual / VFR Broken
Visibility / precipitation: 20.0 sm / none
Airport temperature / altimeter: 47 F / 29.92 inHg
Cloud: Broken Cumulus, 8,000--10,000 ft MSL
Visible winds: approximately 166 M at 1 kt gusting 2 kt near ground;
               225 T at 2 kt gusting 2 kt aloft; 270 T at 4 kt higher aloft
Runway / wave: Dry / 3.0 ft

Not established by screenshots: failure state and random-failure setting;
stabilized starting altitude, IAS/TAS, throttle, autopilot/autothrottle state,
artificial-stability or augmentation state, and unshown weather turbulence/shear
```

The displayed configuration is evidence but is not yet frozen as the baseline
condition. For repeatability, prefer Manual/Clear weather with zero wind,
gust, turbulence, shear, and precipitation unless there is a research reason
to identify in disturbed air. Capture the missing failure and flight-state
evidence before the first engaged baseline.

Configuration follow-up, 2026-07-10:

```text
User-confirmed failures: none
Weather screenshot: archive/screenshots/Screenshot from 2026-07-10 11-02-51.png
Weather source / preset: Manual / Clear
Cloud layers / wind layers: none shown
Visibility / precipitation: 40.0 sm / none
Airport temperature / altimeter: 47 F / 29.92 inHg
Runway / wave: Dry / 3.0 ft
```

The Manual/Clear atmosphere and no-failure state are accepted for the baseline
configuration. Fuel/weight intent and the stabilized altitude, IAS/TAS,
throttle, autopilot/autothrottle, and augmentation states must be unambiguously
recorded before the three engaged captures.

User confirmation, 2026-07-10: EHEKATL is intentionally modeled as a scale
aircraft. The displayed 0.0 lb internal fuel and 14 lb total weight are expected
model values, not configuration errors. Freeze these values for the baseline
series.

Rich baseline logger update, 2026-07-10:

```text
Current stage: Stage 1 — unchanged
Objective: collect identification-grade measurements during repeatable baseline runs
Files changed: backstepping/run_backstepping_baseline_xp12.py,
               scripts/analyze_stage1_baseline.py,
               tests/test_backstepping_baseline.py,
               docs/RICH_IDENTIFICATION_MISSION.md
X-Plane dataref authority: /home/ubuntu/Xplane12/X-Plane 12/Resources/plugins/DataRefs.txt
Measurements added: angular acceleration, explicit IAS/TAS units, AOA/beta,
                    flight path, local/body velocity, local acceleration,
                    load factors, total moments, AGL/VVI, mass/fuel, Mach,
                    density/dynamic pressure, pilot and realized control ratios,
                    trims/configuration, both throttles, AP/AT/servo state
Static command-equivalence tests: PASS
Measurement extraction tests: PASS
Full offline suite: 23 tests PASS
Simulator command sent: none
Stage result: INCONCLUSIVE; Stage 1 remains CURRENT
Next allowed action: 10-second observe-only rich-field availability and timing check at 10 Hz
```

Rich observe-only result:

```text
Date/time: 2026-07-10 11:17 America/Denver
Current stage: Stage 1
Objective: validate rich measurement availability, timing, and command equivalence
Exact input log: logs/stage1_rich_observe_20260710_111755.csv
Rows / achieved fraction: 100 / 1.000000
Elapsed span / maximum gap: 9.898438530 / 0.100076485 s
Engaged fraction: 0.000000
Missing rich fields or values: none
Metadata variants/placeholders: none
Maximum roll/pitch equation error: 0 / 0
Result: PASS for rich observe-only software gate

Observed flight condition was not a steady trim baseline:
  altitude start/end                         4877.197 / 5048.851 m
  IAS start/end                              104.874 / 95.478 kt
  pitch range                                9.825 to 16.559 deg
  roll range                                 -15.312 to -4.212 deg
  P/Q/R ranges                               -9.384..24.085 / -5.930..3.143 /
                                               -2.409..-0.622 deg/s
  vertical speed range                       12.946 to 18.473 m/s
  engine throttles                           0.669723 / 0.669723, constant
  autopilot / servos / autothrottle          off / off / off
  mass                                       6.350295 kg, constant

Acceptance criteria evaluated: rich logger prerequisites only
Stage result: INCONCLUSIVE; three comparable engaged baselines remain required
Reason: the measurement system passed, but this observe-only aircraft motion is
        outside a suitable repeatable start envelope for the baseline series
Next allowed action: establish and freeze a near-setpoint start envelope at
        10 Hz before issuing the first 60-second engaged baseline command
```

Baseline 1 start-gate attempt:

```text
Date/time: 2026-07-10 11:23 America/Denver
Requested run: stage1_baseline_01_20260710_112356
Output log: logs/stage1_baseline_01_20260710_112356.csv
Rows: 1
Start gate: BLOCKED
Controls sent: none
Reasons: altitude outside envelope; IAS outside envelope; pitch outside envelope;
         both engine throttles outside envelope
Measured start: altitude 962.765 m; IAS 0.0 kt; pitch -0.330 deg;
                roll 0.992 deg; P/Q/R 0/0/0 deg/s; throttles 0/0
Result: SAFE BLOCK, not a baseline run
Next allowed action: place the aircraft in flight inside the frozen start
        envelope, with both throttles near 0.669723, then retry Baseline 1
```

Baseline 1 second start-gate attempt:

```text
Date/time: 2026-07-10 11:25 America/Denver
Output log: logs/stage1_baseline_01_20260710_112534.csv
Rows / controls sent: 1 / none
Start gate: BLOCKED for the same ground/idle condition
Measured start: altitude 962.761 m; IAS 0.0 kt; pitch -0.467 deg;
                roll 0.769 deg; throttles 0/0; AP/AT off
Result: SAFE BLOCK, not a baseline run
Conclusion: the XPlaneConnect instance at 127.0.0.1:49009 still reports the
            aircraft on the ground with engines idle
Next allowed action: verify the active X-Plane flight and XPlaneConnect instance,
        resume/unpause in-flight simulation, then use an observe-only state check
        before another engaged Baseline 1 attempt
```

Baseline 1 completed capture:

```text
Date/time: 2026-07-10 11:32 America/Denver
Output log: logs/stage1_baseline_01_20260710_113259.csv
Frozen start envelope used:
  altitude 2100 +/- 300 m; IAS 95 +/- 5 kt; pitch error <= 7 deg;
  roll error <= 3 deg; |P,Q,R| <= 3 deg/s; throttle 0.16 +/- 0.04;
  autopilot, servos, and autothrottle off
Start gate / engagement: PASS / 100 percent
Rows / expected fraction: 600 / 1.000000
Elapsed span / maximum gap: 59.896098035 / 0.102571267 s
Missing rich fields or values: none
Metadata variants/placeholders: none
Maximum original-equation error: 0
Saturation flags: 0

Observed ranges:
  altitude                              2148.609 to 2397.890 m
  IAS                                   81.689 to 93.512 kt
  pitch                                 -0.283 to 6.496 deg
  roll                                  -0.016 to 0.391 deg
  P / Q / R                             -3.203..0.198 /
                                        -20.926..36.742 /
                                        -0.034..0.150 deg/s
  vertical speed                        0.087 to 4.081 m/s
  AOA / beta                            -1.009..0.494 / -0.015..-0.004 deg
  dynamic pressure                      1080.081 to 1415.457 Pa
  sent CTRL0 / CTRL1                    -0.0156..0.1958 / -0.0115..0.0009

Result: PASS for software/timing/completeness and command-equivalence criteria.
Tracking/recovery result: not yet graded; thresholds will be frozen only after
three comparable runs as required by Stage 1.
Next allowed action: reset to the same start envelope and capture Baseline 2.
```

Replacement reproducible baseline set (stage 2m saved situation):

```text
Saved situation check: logs/stage1_stage2m_check_20260710_121321.csv
  altitude 1707.822..1708.411 m; IAS 38.891..39.066 kt;
  pitch 1.402..2.125 deg; roll -1.369..-1.507 deg;
  |P,Q,R| < 1 deg/s; vertical speed -0.037..0.286 m/s;
  throttle 0.0235; automation off

Replacement Baseline 1:
Date/time: 2026-07-10 12:14 America/Denver
Output log: logs/stage1_baseline_new_01_20260710_121415.csv
Rows / expected fraction: 600 / 1.000000
Elapsed span / maximum gap: 59.898080105 / 0.102210659 s
Start gate / engagement: PASS / 100 percent
Missing rich fields or values: none
Metadata variants/placeholders: none
Equation error / saturation events: 0 / none
Observed altitude / IAS: 1696.780..1703.718 m / 38.821..38.897 kt
Observed pitch / roll: 1.307..1.326 deg / 0.032..0.032 deg
Result: PASS for repeatability, timing, completeness, and command equivalence
Tracking thresholds: not yet frozen; this is the first of three comparable runs
Next allowed action: reload the saved stage 2m situation and capture replacement Baseline 2
```

Replacement Baseline 2:

```text
Date/time: 2026-07-10 12:18 America/Denver
Output log: logs/stage1_baseline_new_02_20260710_121831.csv
Rows / expected fraction: 600 / 1.000000
Elapsed span / maximum gap: 59.897291664 / 0.103016073 s
Start gate / engagement: PASS / 100 percent
Missing rich fields or values: none
Metadata variants/placeholders: none
Equation error / saturation events: 0 / none
Observed altitude / IAS: 1696.598..1703.546 m / 38.821..38.895 kt
Observed pitch / roll: 1.307..1.326 deg / 0.032..0.032 deg
Result: PASS for repeatability, timing, completeness, and command equivalence
Tracking thresholds: not yet frozen; one comparable run remains required
Next allowed action: reload the saved stage 2m situation and capture replacement Baseline 3
```

Replacement Baseline 3:

```text
Date/time: 2026-07-10 12:20 America/Denver
Output log: logs/stage1_baseline_new_03_20260710_122051.csv
Rows / expected fraction: 600 / 1.000000
Elapsed span / maximum gap: 59.898562091 / 0.102585080 s
Start gate / engagement: PASS / 100 percent
Missing rich fields or values: none
Metadata variants/placeholders: none
Equation error / saturation events: 0 / none
Observed altitude / IAS: 1696.004..1702.976 m / 38.821..38.887 kt
Observed pitch / roll: 1.307..1.324 deg / 0.032..0.032 deg
Result: PASS for repeatability, timing, completeness, and command equivalence
```

Independent three-run summary, generated by
`scripts/summarize_stage1_baselines.py`:

```text
Runs: 3; rows per run: 600; all engaged: PASS; all start gates: PASS
Same configuration metadata: PASS; saturation-free: PASS
Cross-run mean spans:
  altitude 0.749515 m; IAS 0.007214 kt; pitch 0.001787 deg;
  roll 0.000004 deg; P 0.000003 deg/s; Q 0.000258 deg/s;
  R 0.000917 deg/s; vertical speed 0.000872 m/s;
  CTRL0 0.000056; CTRL1 0.0000001
```

Stage 1 data-quality/repeatability sub-gate: `PASS`.
Stage 1 full gate: `CURRENT — NOT YET PASSED`. The three steady runs do not
provide disturbance/recovery evidence from which to freeze a recovery threshold,
and the legacy routing/sign confirmation still needs an isolated test. Do not
start Stage 2 excitation or LQR synthesis until those remaining criteria are
addressed.

Isolated routing/sign checks, 2026-07-10:

```text
Pitch test: logs/stage1_pitch_sign_20260710_122614.csv
  30/30 engaged samples; start gate PASS; raw pitch output positive;
  legacy sent CTRL0 positive and clipped at +0.02; no saturation ambiguity
  over the wrapper clip; no meaningful short-window pitch-rate response

Roll test: logs/stage1_roll_sign_20260710_122647.csv
  30/30 engaged samples; start gate PASS; raw roll output positive;
  legacy sent CTRL1 positive and clipped at +0.02; no saturation ambiguity
  over the wrapper clip; no meaningful short-window roll-rate response

Result: PASS for legacy command-index/routing confirmation and controller
command-sign recording; plant-response sign remains intentionally unclaimed
because the 3-second clipped tests were too short to identify aircraft response.
```

The remaining Stage 1 evidence is a deliberately designed, longer recovery
test with frozen initial disturbance and abort criteria. It must be performed
before identification excitation; the short sign checks are not recovery
validation.

Roll recovery test result, 2026-07-10:

```text
Input log: logs/stage1_recovery_roll_20260710_123831.csv
Rows / expected fraction: 600 / 1.000000
Elapsed span / maximum gap: 59.897849090 / 0.101341680 s
Start gate / engagement: PASS / 100 percent
Missing rich fields / equation error / saturation flags: none / 0 / none

Initial state:
  roll -0.695 deg; pitch 1.783 deg; P -0.041 deg/s; Q 0.575 deg/s;
  IAS 39.300 kt; altitude 1706.433 m; throttle 0.023529

Observed response:
  roll -15.152 to +12.670 deg
  roll rate P -51.833 to +62.324 deg/s
  pitch -4.395 to +1.783 deg
  pitch rate Q -17.997 to +12.179 deg/s
  CTRL1 -0.391745 to +0.470456

Frozen recovery criteria:
  peak |roll| < 15 deg                         FAIL (15.152)
  final 10 s |roll| < 2 deg                   FAIL (15.152 maximum)
  final 10 s |P| < 5 deg/s                    FAIL (62.324 maximum)
  no uncontrolled divergence/recovery cycling FAIL

Result: `FAIL` for Stage 1 recovery. The intended approximately 5-degree
initial offset was not present, but the controller nevertheless produced large
excursions from a much smaller initial roll offset. This is adverse safety
evidence and must not be repeated with wider limits or larger disturbance.
Stage 1 remains `CURRENT — NOT YET PASSED`; Stage 2 remains blocked.
Next allowed action: offline diagnosis of the logged routing, realized control,
timing, and coupled response. No further engaged recovery or excitation run.
```

Manual-disturbance clarification and controlled-recovery redesign:

```text
User confirmed that the manual disturbance was applied during the run. The
input was not independently measured or time-tagged, so the failed run remains
safety evidence but cannot be used as a repeatable recovery-performance test.

Offline timing review: response remained near baseline through approximately
30 s, followed by coupled excursions; peak |roll| and |P| occurred near 54.4
and 54.5 s. The final near-zero roll interval was shorter than the frozen
10-second recovery requirement.

Implemented controlled Stage-1 recovery pulse:
  axis: logical roll, mapped to legacy CTRL1
  waveform: one half-sine pulse, zero at both endpoints
  start / duration / amplitude: 10.0 s / 0.5 s / 0.005 normalized command
  total command limit: 0.5
  abort envelopes: |pitch| 10 deg, |roll| 10 deg, max |P,Q,R| 20 deg/s
  abort behavior: pulse latches off; backstepping remains active; no restart
  logging: baseline commands, pulse, final commands, active/latch/reason fields
  wrapper: scripts/run_stage1_recovery_roll.sh
  offline suite: 25 tests PASS; zero-pulse backstepping equivalence retained

Next allowed action: reload the clean stage 2m saved situation and run exactly
one controlled recovery test using the wrapper. Do not add any manual input.
```

Controlled roll-recovery run 1:

```text
Date/time: 2026-07-10 12:50 America/Denver
Input log: logs/stage1_recovery_roll_20260710_125016.csv
Rows / expected fraction: 600 / 1.000000
Elapsed span / maximum gap: 59.897975315 / 0.101468144 s
Start gate / engagement: PASS / 100 percent
Pulse samples / observed window: 5 / 10.0001..10.4001 s
Requested / sampled pulse peak: 0.005 / 0.0047559
Pulse latch / abort reason: none / none
Actual maximum additive CTRL1 delta: 0.0047559

Roll response:
  roll -0.3013..+0.1594 deg; P -0.5386..+1.0787 deg/s
  final 10 s max |roll| 0.02192 deg                     PASS
  final 10 s max |P| 0.00342 deg/s                      PASS
  peak |roll| < 15 deg                                  PASS
  pulse ended with roll/P already inside recovery band  PASS

Other observed response:
  pitch -4.2063..+2.0985 deg; Q -17.0079..+2.1108 deg/s
  pitch/Q transient occurred before the roll pulse and remained inside the
  frozen 10-deg / 20-deg/s abort envelope.

Result: PASS for controlled roll-recovery run 1. Two identical repeats from
the clean saved stage 2m situation are required before freezing the recovery
repeatability conclusion. No manual input is permitted during those runs.
```

Controlled roll-recovery run 2:

```text
Date/time: 2026-07-10 12:56 America/Denver
Input log: logs/stage1_recovery_roll_20260710_125651.csv
Rows / expected fraction: 600 / 1.000000
Elapsed span / maximum gap: 59.898611717 / 0.102149442 s
Start gate / engagement: PASS / 100 percent
Pulse samples / window / peak: 5 / 10.0001..10.4001 s / 0.0047560
Pulse latch / abort reason: none / none
Roll / P ranges: -0.0100..+0.1605 deg / -0.5239..+0.5639 deg/s
Final 10 s max |roll| / |P|: 0.02194 deg / 0.00351 deg/s
Frozen criteria: PASS
Repeatability versus run 1: pulse timing/amplitude and final recovery agree;
all response values remain well inside the frozen envelope.
Result: PASS for controlled roll-recovery run 2. One repeat remains.
```

Controlled roll-recovery run 3:

```text
Date/time: 2026-07-10 13:00 America/Denver
Input log: logs/stage1_recovery_roll_20260710_130046.csv
Rows / expected fraction: 600 / 1.000000
Elapsed span / maximum gap: 59.897372268 / 0.102494958 s
Start gate / engagement: PASS / 100 percent
Pulse samples / window / peak: 5 / 10.0001..10.4001 s / 0.0047560
Pulse latch / abort reason: none / none
Roll / P ranges: -0.0109..+0.1580 deg / -0.5258..+0.5521 deg/s
Final 10 s max |roll| / |P|: 0.02199 deg / 0.00363 deg/s
Frozen criteria: PASS
Result: PASS for controlled roll-recovery run 3.
```

Frozen Stage 1 thresholds and gate decision:

```text
Baseline data thresholds:
  samples >= 99 percent; maximum gap <= 0.25 s; 100 percent engaged;
  complete rich measurements and metadata; zero equation error;
  no saturation; three runs from the same saved situation

Recovery thresholds declared before the controlled runs:
  peak |roll| < 15 deg; final 10 s |roll| < 2 deg;
  final 10 s |P| < 5 deg/s; no abort, latch, or uncontrolled cycling

Observed three-run recovery maxima:
  peak |roll| <= 0.3014 deg; peak |P| <= 1.0788 deg/s;
  final 10 s |roll| <= 0.0220 deg;
  final 10 s |P| <= 0.0037 deg/s; no abort/latch in any run

Decision: Stage 1 PASS. Evidence supports a repeatable, recovery-capable
backstepping baseline for the small declared roll pulse at the saved stage 2m
condition. This does not claim global recovery capability or validate LQR.
```

### Stage 2 — Backstepping-stabilized system-identification excitation

Status: `PASS`

Add small, independently logged pitch and roll excitation on top of the working
backstepping command. Do not replace backstepping with open-loop trim. Freeze
amplitude, slew, envelope, abort, and latch-off rules before flight. Require
multiple repeat runs and sufficient excitation inside the local envelope.

Initial roll experiment design frozen 2026-07-10:

```text
Design record: docs/STAGE2_EXPERIMENT_DESIGN.md
Implementation: backstepping/run_backstepping_baseline_xp12.py
Observe-only wrapper: scripts/run_stage2_roll_id_observe.sh
Engaged pilot wrapper: scripts/run_stage2_roll_id.sh
Excitation: logical-roll tapered multisine, 0.003 peak bound;
            0.10/0.20/0.35/0.55/0.80 Hz; 10--50 s in a 60 s run
Safety: 10 deg pitch/roll, 20 deg/s body rate, 0.5 command limit;
        latched excitation abort with backstepping retained
Logging: baseline command, excitation, final command, active/latch/reason,
         full rich state and configuration data
Offline suite: 26 tests PASS
Simulator command sent during design: none
Next allowed action: observe-only Stage 2 waveform/measurement validation
```

Stage 2 roll observe-only gate:

```text
Date/time: 2026-07-10 13:11 America/Denver
Input log: logs/stage2_roll_id_observe_20260710_131141.csv
Rows / expected fraction: 600 / 1.000000
Elapsed span / maximum gap: 59.898238282 / 0.115943596 s
Engaged samples: 0; X-Plane controls sent: none
Rich fields / metadata / equation equivalence: PASS / PASS / zero error
Excitation active samples/window: 399 / 10.1001..49.9001 s
Observed excitation range: -0.0022946..+0.0020234
Maximum excitation-to-CTRL1 mapping error: 1.27e-17
All five designed frequency components present: PASS

The observe-only aircraft exceeded the 10-degree pitch envelope after the
40-second excitation window ended; the identification latch activated for the
last 59 rows. This confirms abort behavior but reflects uncontrolled
observe-only drift, not an excitation response, because no commands were sent.

Result: PASS for waveform, logging, timing, routing, and latch-software gate.
Engaged pilot remains unauthorized until the clean saved stage 2m situation is
reloaded and its start gate passes. Exactly one pilot run is authorized next.
```

Stage 2 engaged roll pilot:

```text
Date/time: 2026-07-10 13:16 America/Denver
Input log: logs/stage2_roll_id_20260710_131644.csv
Rows / expected fraction: 600 / 1.000000
Elapsed span / maximum gap: 59.897937954 / 0.101680635 s
Start gate / engagement: PASS / 100 percent
Excitation active samples/window: 399 / 10.1001..49.9001 s
Excitation range: -0.0022946..+0.0020234; routing error 2.17e-19
Excitation latch / abort: none / none
State safety envelopes: PASS

Informativeness check: FAIL
  roll range 0.03169..0.03204 deg; P range 0.003814..0.003840 deg/s
  response spectra at designed frequencies are comparable to the three
  no-excitation baselines, so roll signal-to-noise is insufficient

Realized-control-path evidence:
  sent CTRL1 follows excitation with correlation 0.999995
  X-Plane yoke_roll_ratio and total_roll_ratio remain exactly 0 throughout
  X-Plane yoke_pitch_ratio and total_pitch_ratio remain fixed at 0.1484375
  getCTRL values remain fixed at CTRL0=0.1484375 and CTRL1=0 during excitation

Conclusion: the planned command was calculated and handed to XPlaneConnect but
was not observed in X-Plane's realized control ratios. Do not repeat the pilot,
increase amplitude, or collect training/validation runs. Diagnose control
ownership/override, command persistence, saved-situation state, and the correct
realized actuator datarefs offline/read-only before another engaged test.
```

Control-path diagnostic prepared: `scripts/diagnose_xplane_control_path.py`.
It reads joystick/per-axis overrides, yoke and total control ratios, flight-
control outputs, and all nonzero aileron/elevator/rudder surface-array entries.
First read-only attempt timed out because XPlaneConnect was not responding; no
command or override was sent. Reload/resume X-Plane before retrying.

Control-ownership diagnosis, 2026-07-10 13:34--13:36 America/Denver:

```text
Read-only log: logs/stage2_roll_authority_readonly_20260710_133427.csv
Bounded test log: logs/stage2_roll_authority_engaged_20260710_133545.csv
Diagnostic implementation: scripts/test_roll_control_authority.py
Command bound / duration: +0.005 / 0.5 s; roll-axis override only
Restoration: initial yoke_roll_ratio=0 and override_joystick_roll=0 restored

Observed during command:
  override_joystick_roll                         1
  yoke_roll_ratio                               +0.005
  FC_roll / total_roll_ratio                     0 / 0
  ail1_def / ail2_def                            all zero
  roll / P                                       unchanged

Subsequent read-only state diagnosis:
  sim/time/paused                                1
  sim/time/sim_speed                             0
  sim/operation/prefs/replay_mode                 7
  artificial stability on / roll contribution    1 / 0
  torque tube split                              0
  general and individual aileron failures        0
  joystick/flight-control/surface overrides       0 after restoration

Conclusion: the connected simulator was paused and in replay mode. X-Plane
accepted the writable yoke dataref value but did not advance its flight-control
or physics pipeline. This explains the zero realized roll and invalidates the
test as a control-authority result; it is a safe diagnostic, not Stage-2
identification evidence. The diagnostic now blocks engagement when paused,
sim speed is zero, or replay mode is nonzero.

Next allowed action: exit replay, unpause the clean stage 2m flight, confirm
paused=0, sim_speed>0, replay_mode=0 read-only, then repeat the same bounded
0.005/0.5-second authority test. Do not repeat the multisine pilot yet.
```

Live roll-authority confirmation and runner correction, 2026-07-10 13:43:

```text
Pre-test live gates: paused=0; sim_speed=1; replay_mode=0
Output log: logs/stage2_roll_authority_engaged_20260710_134344.csv
Command: +0.005 yoke roll for 0.5 s; per-axis roll override only
Initial state: roll +0.0331 deg; P -0.0036 deg/s
Realized response:
  maximum commanded total_roll_ratio             +0.005
  maximum absolute ail1/ail2 deflection           0.150 deg
  maximum observed positive P                     +0.486 deg/s
  roll increased to                               +0.254 deg
Restoration: override returned to 0; physical joystick regained ownership
Result: PASS — command-to-surface and surface-to-aircraft roll authority exist

Stage-2 runner correction:
  scripts/run_stage2_roll_id.sh now requests explicit roll-axis ownership
  runner takes ownership only after the start gate passes
  initial roll input and ownership are restored in a finally block
  pitch, yaw, and throttle ownership are unchanged
  paused, zero-speed, and replay states are now start-gate failures
  compilation / six focused tests / shell syntax / CLI: PASS

The original Stage-2 pilot remains rejected because it ran without persistent
roll ownership and its later diagnostic context was paused/replay. One
replacement pilot with explicit roll ownership is authorized next; it is not a
training or validation dataset until its safety and informativeness gates pass.
```

Replacement Stage-2 roll pilot 2, 2026-07-10 13:47:

```text
Output log: logs/stage2_roll_id_20260710_134740.csv
Rows / elapsed / maximum gap: 600 / 59.878645420 s / 0.100978515 s
Start gate / engagement: PASS / 100 percent
Paused / replay / zero-speed samples: 0 / 0 / 0
Excitation latch / saturation: none / none
State ranges: roll -0.0098..+0.0628 deg; P -0.1900..+0.1857 deg/s;
              pitch -1.5902..+1.8848 deg; Q -9.7263..+9.0155 deg/s
Safety result: PASS

Realized-input gate: FAIL
  correlation sent CTRL1 versus total_roll_ratio     -0.019
  correlations at one-to-three sample lags           -0.012..-0.118
  CTRL1 range                                         -0.00103..+0.00328
  realized total roll range                           -0.00153..+0.00226

Although roll/P spectra were above the frozen no-excitation baselines, the
unknown realized-input mismatch makes this log unacceptable for model fitting.
Holding override_joystick_roll does not make XPlaneConnect's CTRL packet persist
as the roll dataref. The separately verified authority test did persist because
it wrote sim/joystick/yoke_roll_ratio directly.

Correction: the runner still sends the complete CTRL vector for unchanged
pitch/yaw/throttle behavior, then writes its same bounded logical-roll command
directly to sim/joystick/yoke_roll_ratio while roll ownership is active. Seven
focused offline tests, compilation, and wrapper syntax pass. One final
replacement pilot is authorized; require strong commanded-to-realized agreement
before accepting any Stage-2 identification dataset.
```

Replacement Stage-2 roll pilot 3, 2026-07-10 13:51:

```text
Output log: logs/stage2_roll_id_20260710_135148.csv
Rows / elapsed / maximum gap: 600 / 59.860652280 s / 0.100333255 s
Start gate / engagement: PASS / 100 percent
Paused / replay / zero-speed samples: 0 / 0 / 0
Roll command realization at expected one-sample lag: correlation 0.866477 PASS
Roll / P ranges: -0.0465..+0.0727 deg / -0.3331..+0.3059 deg/s
Roll and P response spectra: all five frequencies strongly above baseline

Safety latch: FAIL
  planned / realized excitation samples             400 / 253
  first latch time                                  35.300 s
  reason                                             body-rate envelope exceeded
  Q immediately before / at trigger                 +17.629 / +20.187 deg/s
  pitch range                                        -3.991..+2.994 deg
  saturation                                         none

Result: REJECTED for identification because a safety latch is failed evidence
and the full planned excitation was not realized. Do not widen the 20-deg/s
limit or fit a model from this partial record.

Offline diagnosis: the persistent roll path is now verified, but the pitch
backstepping command still has poor agreement with realized pitch control
(best observed correlation only about 0.25 over tested lags). Physical pitch
input can overwrite the stabilizing pitch command between updates, producing
the longitudinal oscillation that triggered the latch.

Offline correction implemented: for identification only, the wrapper now
temporarily owns both roll and pitch joystick axes and directly persists the
same bounded legacy-routed backstepping outputs to their verified yoke datarefs.
Yaw and throttle ownership remain unchanged. Both axes restore their captured
initial values and ownership in the finally block. Legacy and corrected routing
tests, compilation, wrapper syntax, and eight focused tests pass.

Next allowed action: reload the clean stage 2m steady flight. Before any new
multisine pilot, perform a short bounded pitch command-authority/stabilization
check and verify commanded-to-realized pitch agreement plus automatic ownership
restoration. Stage 2 remains CURRENT and no dataset is accepted for fitting yet.
```

Pitch authority and trim-relative stabilization gate, 2026-07-10 14:05--14:08:

```text
Pitch authority log: logs/stage2_pitch_authority_engaged_20260710_140528.csv
Test: captured steady yoke pitch +0.148537; applied +0.005 increment for 0.5 s
Realized total pitch reached +0.153537; elevator magnitude increased from
4.4561 to 4.6061 deg; positive Q response reached +0.4669 deg/s.
Pitch ownership restored to 0; physical input resumed. Result: PASS.

First owned-axis zero-excitation check:
  log: logs/stage2_owned_stabilization_20260710_140707.csv
  result: FAIL for clean handoff despite no latch; initial pitch command fell
  from approximately +0.149 trim to +0.00245 and caused Q=-13.851 deg/s.
  diagnosis: persistent ownership removed the physical joystick's hidden trim
  contribution; the original controller assumed that contribution remained.

Trim-relative correction: capture CTRL0/CTRL1 before ownership, apply the same
backstepping equations and gains to input perturbations, then add captured trim
as feed-forward. This is Stage-2-only; default original behavior is unchanged.
Nine focused tests, compilation, CLI, and wrapper syntax: PASS.

Trim-relative zero-excitation check:
  log: logs/stage2_owned_stabilization_20260710_140852.csv
  captured trim: CTRL0 +0.149377; CTRL1 +0.000452273
  rows / elapsed / max gap: 100 / 9.884491429 s / 0.103374689 s
  pitch / roll: +1.2048..+1.2577 / +0.0107..+0.0335 deg
  Q / P: -0.1238..+0.1578 / -0.0817..+0.0631 deg/s
  latch / pause / replay / zero speed: none
  both pitch and roll ownership restored: PASS
Result: PASS for clean owned-axis stabilization handoff.

Because artificial stability is enabled and contributes to total controls,
system identification must use logged total_pitch_ratio/total_roll_ratio as
the realized plant inputs, while retaining sent commands for audit. One new
multisine pilot is authorized next under the unchanged frozen safety envelope.
```

Accepted trim-relative Stage-2 roll design pilot, 2026-07-10 14:09:

```text
Output log: logs/stage2_roll_id_20260710_140937.csv
Captured trim: CTRL0 +0.149537; CTRL1 +0.000460293
Rows / elapsed / maximum gap: 600 / 59.803894188 s / 0.108397897 s
Start gate / engagement: PASS / 100 percent
Paused / replay / zero-speed samples: 0 / 0 / 0
Planned / realized excitation samples: 400 / 400
Excitation range: -0.0022946..+0.0020234
Latch / abort / saturation: none / none / none
Pitch / Q: +1.1942..+1.2602 deg / -0.1594..+0.1669 deg/s
Roll / P: -0.0194..+0.0430 deg / -0.2438..+0.1506 deg/s
Both owned axes restored: PASS

Frequency-domain realized total_roll_ratio amplitudes:
  0.10 Hz  0.0001601; phase versus excitation +172.4 deg
  0.20 Hz  0.0001580; phase versus excitation +149.0 deg
  0.35 Hz  0.0001607; phase versus excitation +130.5 deg
  0.55 Hz  0.0001815; phase versus excitation +124.5 deg
  0.80 Hz  0.0001146; phase versus excitation +112.7 deg

Roll response amplitude versus frozen no-excitation baseline maximum:
  103x / 284x / 858x / 312x / 880x at the five frequencies
P response amplitude versus baseline maximum:
  3145x / 7133x / 13425x / 24910x / 34877x

Decision: PASS as the Stage-2 roll experiment design pilot. The negative raw
time-domain command/total correlation is explained by closed-loop/artificial-
stability phase opposition; realized input remains independently measured and
informative at every designed frequency. Do not use this design pilot for model
training. Freeze the design and collect at least two separate roll training runs
and two held-out roll validation runs from fresh reloads of stage 2m before
Stage 3. Pitch experiment design and its independent datasets are still required.

Next allowed action: reload clean stage 2m, confirm live steady flight, and run
Roll Training Run 1 with the frozen implementation and parameters unchanged.
```

Roll Training Run 1 start attempt, 2026-07-10 14:15:

```text
Diagnostic log: logs/stage2_roll_training_01_20260710_141541.csv
Rows: 1; controls sent: none; ownership changes: none
Start gate: BLOCKED — altitude outside frozen 1700 +/-150 m envelope
Measured start: altitude 1861.876 m; IAS 38.230 kt; pitch 1.155 deg;
roll 0.0335 deg; P/Q/R -0.00065/+0.00288/+0.0140 deg/s; throttle 0.023529;
paused=0; sim_speed=1; replay=0
Result: safe block, not Roll Training Run 1. Do not widen the frozen altitude
envelope for a 11.876 m exceedance. Reload clean stage 2m and retry unchanged.
```

Roll Training Run 1 retry, 2026-07-10 14:19:

```text
Diagnostic log: logs/stage2_roll_training_01_20260710_141908.csv
Rows: 1; controls sent: none; ownership changes: none
Start gate: BLOCKED — altitude and IAS outside frozen envelopes
Measured start: altitude 1526.315 m (required 1550..1850 m);
IAS 46.059 kt (required 34..44 kt); pitch 2.537 deg; roll 0.0226 deg;
P/Q/R +0.00595/-0.05495/-0.13738 deg/s; throttle 0.023529;
paused=0; sim_speed=1; replay=0
Result: safe block, not a training run. This does not match the previously
verified stage 2m reload near 1708 m and 39 kt. Load that exact saved situation
and verify its altitude/IAS before retrying; frozen gates remain unchanged.
```

Accepted Roll Training Run 1, 2026-07-10 14:22:

```text
Output log: logs/stage2_roll_training_01_20260710_142240.csv
Captured trim: CTRL0 +0.173292; CTRL1 +0.000454241
Rows / elapsed / maximum gap: 600 / 59.830953606 s / 0.101567997 s
Start gate / engagement: PASS / 100 percent
Paused / replay / zero-speed samples: 0 / 0 / 0
Planned / realized excitation samples: 400 / 400
Excitation range: -0.0022946..+0.0020234
Latch / abort / saturation: none / none / none
Pitch / Q: -0.2927..+1.3359 deg / -0.2817..+3.6490 deg/s
Roll / P: -0.0704..+0.0568 deg / -0.1480..+0.1647 deg/s
Commanded-to-realized roll correlation at one-sample lag: 1.000000
Both owned axes restored: PASS

Roll response amplitude versus frozen baseline at five frequencies:
  294x / 860x / 2370x / 769x / 2716x
P response amplitude versus frozen baseline:
  3326x / 13103x / 40121x / 83875x / 212975x

Decision: PASS and ACCEPTED as Roll Training Run 1. Keep this file in the
training partition. Do not use held-out validation runs for fitting or design
selection. Next allowed action: reload clean stage 2m and collect Roll Training
Run 2 with every frozen parameter unchanged and a distinct test_id.
```

Accepted Roll Training Run 2, 2026-07-10 14:26:

```text
Output log: logs/stage2_roll_training_02_20260710_142615.csv
Captured trim: CTRL0 +0.145905; CTRL1 +0.000465158
Rows / elapsed / maximum gap: 600 / 59.846995141 s / 0.102658102 s
Start gate / engagement: PASS / 100 percent
Paused / replay / zero-speed samples: 0 / 0 / 0
Planned / realized excitation samples: 400 / 400
Excitation range: -0.0022946..+0.0020234
Latch / abort / saturation: none / none / none
Pitch / Q: +1.2844..+1.3033 deg / -0.0107..+0.0097 deg/s
Roll / P: -0.0726..+0.0668 deg / -0.1466..+0.2035 deg/s
Commanded-to-realized roll correlation at one-sample lag: 1.000000
Both owned axes restored: PASS

Roll response amplitude versus frozen baseline at five frequencies:
  300x / 886x / 2509x / 893x / 3650x
P response amplitude versus frozen baseline:
  3241x / 12671x / 42307x / 96914x / 287960x

Decision: PASS and ACCEPTED as Roll Training Run 2. The required roll training
partition is complete. The two subsequent roll runs are held-out validation
data and must not be used to fit the model, choose its order, select states,
estimate delays, or tune regularization. Next allowed action: reload clean
stage 2m and collect Roll Validation Run 1 unchanged with a validation test_id.
```

Accepted held-out Roll Validation Run 1, 2026-07-10 14:30:

```text
Output log: logs/stage2_roll_validation_01_20260710_143047.csv
Captured trim: CTRL0 +0.143012; CTRL1 +0.000447980
Rows / elapsed / maximum gap: 600 / 59.816578715 s / 0.101756506 s
Start gate / engagement: PASS / 100 percent
Paused / replay / zero-speed samples: 0 / 0 / 0
Planned / realized excitation samples: 400 / 400
Excitation range: -0.0022946..+0.0020234
Latch / abort / saturation: none / none / none
Pitch / Q: +1.2148..+1.2848 deg / -0.0499..+0.1744 deg/s
Roll / P: -0.0740..+0.0646 deg / -0.1498..+0.2022 deg/s
Commanded-to-realized roll correlation at one-sample lag: 1.000000
Both owned axes restored: PASS

Data-quality decision: PASS and ACCEPTED into the held-out validation partition.
This run was checked only for safety, completeness, realized-input fidelity,
and excitation richness. Its response must not influence model structure,
training, delay selection, state selection, or tuning. Next allowed action:
reload clean stage 2m and collect held-out Roll Validation Run 2 unchanged.
```

Accepted held-out Roll Validation Run 2, 2026-07-12 13:54 America/Denver:

```text
Output log: logs/stage2_roll_validation_02_20260712_135450.csv
Captured trim: CTRL0 +0.148675; CTRL1 +0.000474254
Rows / elapsed / maximum gap: 600 / 59.803815296 s / 0.101845205 s
Start gate / engagement: PASS / 100 percent
Paused / replay / zero-speed samples: 0 / 0 / 0
Planned / realized excitation samples: 400 / 400
Excitation range: -0.0022946..+0.0020234
Latch / abort / saturation: none / none / none
Pitch / Q: +1.3008..+1.3457 deg / -0.00948..+0.00951 deg/s
Roll / P: -0.0703..+0.0659 deg / -0.1478..+0.2006 deg/s
Commanded-to-realized roll correlation at one-sample lag: 1.000000
Both owned axes restored: PASS

Roll response amplitude versus frozen baseline at five frequencies:
  299x / 876x / 2466x / 843x / 3292x
P response amplitude versus frozen baseline:
  3087x / 12749x / 41976x / 92612x / 262597x

Data-quality decision: PASS and ACCEPTED into the held-out validation partition.
The frozen roll dataset is complete: two training runs and two held-out
validation runs. Validation Run 2 was checked only for safety, completeness,
realized-input fidelity, and excitation richness; its response must not
influence model structure, training, delay selection, state selection, or
tuning. Stage 2 remains CURRENT because pitch experiment design and independent
pitch training/validation datasets are still required. Next allowed action:
design the pitch identification pilot offline under the existing Stage-2
safety methodology; do not fit a plant model or synthesize LQR yet.
```

Pitch experiment software design frozen, 2026-07-12:

```text
Design record: docs/STAGE2_PITCH_EXPERIMENT_DESIGN.md
Observe-only wrapper: scripts/run_stage2_pitch_id_observe.sh
Engaged pilot wrapper: scripts/run_stage2_pitch_id.sh
Axis/path: logical pitch / legacy CTRL0; realized input total_pitch_ratio
Waveform: 0.003-bound tapered multisine, 0.10/0.20/0.35/0.55/0.80 Hz,
          active from 10 to 50 s in a 60 s run
Stabilization: unchanged backstepping with verified trim-relative ownership
Safety: unchanged 10-deg attitude, 20-deg/s rate, 0.5 total-command limits
Simulator command sent during design: none
Next allowed action: run the observe-only pitch waveform/measurement check.
Do not run the engaged pitch pilot until that log passes its offline audit.
```

Pitch observe-only gate, 2026-07-12 13:59 America/Denver:

```text
Output log: logs/stage2_pitch_id_observe_20260712_135949.csv
Rows / elapsed / maximum gap: 600 / 59.839335450 s / 0.101109704 s
Engaged samples / controls sent / ownership changes: 0 / none / none
Excitation samples / window: 400 / 10.0000..49.9000 s
Excitation range: -0.0022946..+0.0020234
Maximum excitation-to-CTRL0 pitch-routing error: 4.34e-19
Identification latch / abort: none / none
Observed pitch / Q: +1.3590..+1.4021 deg / -0.0130..+0.0127 deg/s
Result: PASS for waveform, timing, metadata, pitch routing, and latch software.
This observe-only log is software evidence, not aircraft-response evidence.
Next allowed action: reload/confirm the clean steady stage 2m condition and run
exactly one engaged pitch design pilot with scripts/run_stage2_pitch_id.sh.
```

Accepted Stage-2 pitch design pilot, 2026-07-12 14:01 America/Denver:

```text
Output log: logs/stage2_pitch_id_20260712_140143.csv
Captured trim: CTRL0 +0.148675; CTRL1 +0.000474254
Rows / elapsed / maximum gap: 600 / 59.825451241 s / 0.101638057 s
Start gate / engagement: PASS / 100 percent
Paused / replay / zero-speed samples: 0 / 0 / 0
Planned / realized excitation samples: 400 / 400
Excitation range: -0.0022946..+0.0020234
Latch / abort / saturation: none / none / none
Pitch / Q: +1.2470..+1.3907 deg / -0.1513..+0.1875 deg/s
Roll / P: -0.0587..+0.6008 deg / -2.0311..+0.2439 deg/s
Commanded-to-realized pitch correlation at one-sample lag: 0.99999999997
Both owned axes restored: PASS

Pitch response amplitude versus frozen baseline at five frequencies:
  12.2x / 29.0x / 49.9x / 66.8x / 75.7x
Q response amplitude versus frozen baseline:
  30.0x / 103.9x / 315.1x / 1092.4x / 1476.5x

Decision: PASS as the Stage-2 pitch experiment design pilot. Exclude this pilot
from model fitting. Freeze the implementation and parameters unchanged. Collect
two pitch training runs followed by two held-out pitch validation runs, each
from a fresh reload of the clean stage 2m situation. Validation responses must
not influence model structure, delay/state choice, filtering, or tuning.
Next allowed action: reload clean stage 2m and collect Pitch Training Run 1 with
STAGE2_RUN_LABEL=pitch_training_01 and scripts/run_stage2_pitch_id.sh.
```

Accepted Pitch Training Run 1, 2026-07-12 14:07 America/Denver:

```text
Output log: logs/stage2_pitch_training_01_20260712_140739.csv
Captured trim: CTRL0 +0.150498; CTRL1 +0.000475253
Rows / elapsed / maximum gap: 600 / 59.849018342 s / 0.102265154 s
Start gate / engagement: PASS / 100 percent
Paused / replay / zero-speed samples: 0 / 0 / 0
Planned / realized excitation samples: 400 / 400
Excitation range: -0.0022946..+0.0020234
Latch / abort / saturation: none / none / none
Pitch / Q: +1.2753..+1.4247 deg / -0.1600..+0.2093 deg/s
Roll / P: -0.0016..+0.0175 deg / -0.0549..+0.0106 deg/s
Commanded-to-realized pitch correlation at one-sample lag: 0.99999999998
Both owned axes restored: PASS
Pitch response versus frozen baseline: 11.5x / 29.4x / 50.2x / 66.1x / 72.1x
Q response versus frozen baseline: 31.8x / 112.0x / 329.4x / 1109.9x / 1461.0x
Decision: PASS and ACCEPTED as Pitch Training Run 1. Keep it exclusively in
the training partition. Next allowed action: fresh reload of clean stage 2m,
then Pitch Training Run 2 with STAGE2_RUN_LABEL=pitch_training_02 and every
frozen parameter unchanged.
```

Accepted Pitch Training Run 2, 2026-07-12 14:15 America/Denver:

```text
Output log: logs/stage2_pitch_training_02_20260712_141515.csv
Captured trim: CTRL0 +0.149685; CTRL1 +0.000472807
Rows / elapsed / maximum gap: 600 / 59.832899461 s / 0.102639461 s
Start gate / engagement: PASS / 100 percent
Paused / replay / zero-speed samples: 0 / 0 / 0
Planned / realized excitation samples: 400 / 400
Excitation range: -0.0022946..+0.0020234
Latch / abort / saturation: none / none / none
Pitch / Q: +1.2789..+1.4265 deg / -0.1553..+0.1860 deg/s
Roll / P: -0.0141..+0.0007 deg / -0.0006..+0.0502 deg/s
Commanded-to-realized pitch correlation at one-sample lag: 0.99999999998
Both owned axes restored: PASS
Pitch response versus frozen baseline: 12.1x / 28.6x / 49.6x / 64.0x / 69.0x
Q response versus frozen baseline: 32.5x / 108.7x / 326.8x / 1069.3x / 1373.3x
Decision: PASS and ACCEPTED as Pitch Training Run 2. The pitch training
partition is complete. Freeze all model-design choices against these two
training logs only; do not inspect held-out response for tuning. Next allowed
action: fresh reload of clean stage 2m, then held-out Pitch Validation Run 1
with STAGE2_RUN_LABEL=pitch_validation_01 and unchanged parameters.
```

Accepted held-out Pitch Validation Run 1, 2026-07-12 14:20 America/Denver:

```text
Output log: logs/stage2_pitch_validation_01_20260712_142028.csv
Captured trim: CTRL0 +0.149665; CTRL1 +0.000475443
Rows / elapsed / maximum gap: 600 / 59.828848168 s / 0.100977952 s
Start gate / engagement: PASS / 100 percent
Paused / replay / zero-speed samples: 0 / 0 / 0
Planned / realized excitation samples: 400 / 400
Excitation range: -0.0022946..+0.0020234
Latch / abort / saturation: none / none / none
Pitch / Q: +1.2763..+1.4225 deg / -0.2142..+0.1745 deg/s
Roll / P: -0.0009..+0.0303 deg / -0.0984..+0.0081 deg/s
Commanded-to-realized pitch correlation at one-sample lag: 0.99999999998
Both owned axes restored: PASS
Pitch response versus frozen baseline: 11.6x / 27.4x / 48.7x / 62.8x / 67.4x
Q response versus frozen baseline: 32.6x / 104.3x / 328.7x / 1049.9x / 1362.8x
Data-quality decision: PASS and ACCEPTED into the held-out validation
partition. These response values were checked only for excitation richness and
must not influence model structure or tuning. Next allowed action: fresh reload
of clean stage 2m, then held-out Pitch Validation Run 2 with
STAGE2_RUN_LABEL=pitch_validation_02 and unchanged parameters.
```

Accepted held-out Pitch Validation Run 2, 2026-07-12 14:23 America/Denver:

```text
Output log: logs/stage2_pitch_validation_02_20260712_142348.csv
Captured trim: CTRL0 +0.143572; CTRL1 +0.000458202
Rows / elapsed / maximum gap: 600 / 59.836861928 s / 0.101889562 s
Start gate / engagement: PASS / 100 percent
Paused / replay / zero-speed samples: 0 / 0 / 0
Planned / realized excitation samples: 400 / 400
Excitation range: -0.0022946..+0.0020234
Latch / abort / saturation: none / none / none
Pitch / Q: +1.1846..+1.3234 deg / -0.1490..+0.1939 deg/s
Roll / P: -0.0039..+0.0535 deg / -0.1808..+0.0223 deg/s
Commanded-to-realized pitch correlation at one-sample lag: 0.99999999997
Both owned axes restored: PASS
Pitch response versus frozen baseline: 12.6x / 28.9x / 49.1x / 63.7x / 71.0x
Q response versus frozen baseline: 31.5x / 107.8x / 326.7x / 1077.5x / 1453.7x
Data-quality decision: PASS and ACCEPTED into the held-out validation
partition. Its response was checked only for excitation richness and did not
influence model structure or tuning.

Stage-2 gate decision: PASS. The frozen allocation is complete for both axes:
two roll training plus two held-out roll validation runs, and two pitch training
plus two held-out pitch validation runs. All eight accepted datasets passed
their safety, completeness, realized-input, and richness gates. Stage 3 is now
CURRENT. No further identification flight is authorized unless Stage-3 offline
diagnostics expose a specifically documented data deficiency.
```

### Stage 3 — Identify and independently validate plant models

Status: `PASS`

Training-only structure freeze, 2026-07-12:

```text
Candidate family: continuous local angle/rate model
  angle_dot = rate
  rate_dot = a_angle*angle + a_rate*rate + b*realized_total_control
Per-run trim: mean of the pre-excitation 0..10 s interval
Fit window: 10..50 s excitation interval
Candidate realized-input delays: 0, 1, 2, and 3 samples at nominal 10 Hz
Selection evidence: leave-one-training-run-out q_dot/p_dot error plus
                    cross-run multi-step prediction; validation logs unopened
Frozen state structure: [angle perturbation, body-rate perturbation]
Frozen input: measured total_pitch_ratio or total_roll_ratio perturbation
Frozen delay: 3 samples (nominal 0.3 s) for both axes
Reason: two-sample candidates slightly improved one-step error but their
        cross-run free predictions diverged severely; three-sample candidates
        were the only stable/useful multi-step candidates for both axes
Implementation: scripts/identify_stage3_models.py
Next allowed action: fit pooled training models with the frozen structure, then
evaluate unchanged models on the two held-out validation logs per axis.
```

Stage-3 fit and independent validation result, 2026-07-12:

```text
Implementation: scripts/identify_stage3_models.py
Machine-readable result: configs/stage3_models.json
Paper-readable report: docs/STAGE3_MODEL_REPORT.md
Offline tests: 31 PASS
Roll A: [[0, 1], [-1.799965, -0.035987]]
Roll B: [[0], [-286.518155]]
Pitch A: [[0, 1], [-4.699647, -0.202786]]
Pitch B: [[0], [-210.642895]]
Input delay: 3 samples / nominal 0.3 s for both axes
Controllability: rank 2/2 for both axes
Held-out prediction: comparable to training at 0.1/0.5/1.0/2.0 s horizons
Residual limitation: colored; lag-1 correlation 0.823 roll / 0.777 pitch
Damping limitation: substantial relative uncertainty, especially roll
Decision: PASS for local short-horizon model synthesis at the frozen operating
          condition; not a global/high-fidelity model claim
Mandatory Stage-4 action: coefficient-uncertainty sweep, delay-aware replay,
                          actuator bounds/slew, and held-out comparisons
Simulator command sent: none
```

Identify longitudinal and lateral models using training runs and evaluate them
on separate validation runs. Record units, delays, trim, A/B matrices,
uncertainty, residuals, whiteness/correlation checks, controllability, and
multi-step prediction performance. Reject models that only reproduce their
training data.

### Stage 4 — Offline LQR synthesis and replay

Status: `PASS`

Intermediate Stage-4 attitude-state synthesis, 2026-07-12:

```text
Implementation: scripts/synthesize_stage4_lqr.py
Machine-readable result: configs/stage4_lqr_design.json
Report: docs/STAGE4_LQR_DESIGN_REPORT.md
Offline tests: 33 PASS
State: angle, rate, and three prior commands; nominal delay 0.3 s
Limits: |u perturbation| <= 0.003; slew <= 0.0005/sample at 10 Hz
Roll K:  [0.0008744492, -0.0015549728, 0.0485960530,
          0.0475990244, 0.0457516334]
Pitch K: [0.0013164881, -0.0006435013, 0.0189824485,
          0.0173657542, 0.0149767632]
Uncertainty/delay sweep: 81 cases per axis; zero unstable cases
Worst spectral radius: roll 0.98577; pitch 0.98938
Matched disturbance replay: converged; zero saturation
All eight saved-log command replays: zero saturation
Decision: PASS for offline attitude-state candidate; INCONCLUSIVE for Stage 4
Reason: Stage 5 requires a separately frozen inner-rate implementation; flying
        the combined angle/rate gain would improperly skip that gate
Next allowed action: synthesize/audit delay-aware rate-only gains and exact
runtime replay. No X-Plane LQR command is authorized.
```

Stage-4 inner-rate completion, 2026-07-12:

```text
Runtime controller: lqr/delay_aware_lqr.py
Exact replay: scripts/replay_stage4_runtime.py
Replay result: configs/stage4_runtime_replay.json
Offline tests: 37 PASS
Roll-rate K:  [-0.0013356924, 0.0386158946, 0.0384771760, 0.0383389558]
Pitch-rate K: [-0.0007568628, 0.0167721460, 0.0164354559, 0.0161055246]
Angle feedback in inner-rate laws: exactly zero
Full-plant nominal spectral radius: roll 0.98086; pitch 0.98372
Worst uncertainty/delay radius: roll 0.99321; pitch 0.99375
Unstable cases: 0/81 per axis
Exact runtime replay peak perturbation: roll 0.000252; pitch 0.000160
Exact runtime replay saturation: zero across all eight logs
Decision: Stage 4 PASS
Next allowed action: Stage-5 observe-only implementation/state gate followed by
one small, single-axis pitch-rate pilot. Combined or attitude LQR remains blocked.
```

Record Q/R choices, gains, poles, actuator constraints, trim/feed-forward,
robustness/sensitivity results, and replay comparisons against held-out logs.
No X-Plane commands during this stage.

### Stage 5 — Inner body-rate loop validation

Status: `CURRENT`

Stage-5 pitch-rate runner preparation, 2026-07-12:

```text
Runner: lqr/run_stage5_rate_lqr_xp12.py
Observe wrapper: scripts/run_stage5_pitch_rate_observe.sh
Engaged pilot wrapper: scripts/run_stage5_pitch_rate_pilot.sh
Default: observe-only; --engage required to send controls
Tested axis: pitch rate only; outer angle feedback exactly zero
Roll stabilization: original backstepping roll law retained
Pitch command: captured trim + frozen delay-aware rate-LQR perturbation
Reference pilot: one +0.2 deg/s half-sine Q reference, 10..12 s in 30 s
Limits: |pitch perturbation| <=0.003; slew <=0.0005/sample at 10 Hz
Ownership: both pitch and roll persistent while engaged; always restored
Safety: 10-deg pitch/roll and 20-deg/s body-rate envelopes; pause/replay gates
Latch behavior: permanently cancel experiment and hand pitch to backstepping
                recovery; no automatic LQR re-engagement and no passive trim
Static verification: compilation, CLI, shell syntax, 39 offline tests PASS
Simulator command sent during preparation: none
Next allowed action: 30-second observe-only waveform/state/command audit.
The engaged pilot remains blocked until that saved log passes.
```

Stage-5 pitch-rate observe-only gate, 2026-07-12 14:48 America/Denver:

```text
Output log: logs/stage5_pitch_rate_observe_20260712_144824.csv
Rows / elapsed / maximum gap: 300 / 29.862478389 s / 0.100881881 s
Engaged samples / controls sent / ownership changes: 0 / none / none
Reference samples / window / peak: 20 / 10.0001..11.9001 s / +0.2000 deg/s
Hypothetical LQR perturbation peak: 0.000145157
Hypothetical maximum slew: 0.000023046/sample
Latch / abort: none / none
Pitch / Q: +1.1032..+1.1253 deg / -0.00744..+0.00959 deg/s
Roll / P: +0.0338..+0.0345 deg / -0.00522..-0.00153 deg/s
Simulator paused / speed / replay: 0 / 1 / 0 throughout
Result: PASS for timing, reference waveform, limits/slew, logging, and safety.
Next allowed action: exactly one engaged pitch-rate pilot with the frozen wrapper.
The pilot remains subject to the live start gate and latched backstepping fallback.
```

Stage-5 pitch-rate pilot start attempt, 2026-07-12 14:54 America/Denver:

```text
Diagnostic log: logs/stage5_pitch_rate_pilot_20260712_145456.csv
Rows: 1
Controls sent / ownership changes: none / none
Start gate: BLOCKED — altitude outside frozen 1700 +/-150 m envelope
Measured start: altitude 1871.871 m; IAS 38.846 kt; pitch +1.3123 deg;
roll +0.0331 deg; P/Q/R -0.00282/-0.00223/+0.12784 deg/s;
throttle 0.023529; paused=0; sim_speed=1; replay=0
Captured trim: CTRL0 +0.146036; CTRL1 +0.000432142
Decision: safe block, not a controller experiment and not pilot evidence.
Do not widen the altitude envelope. Reload the exact clean stage 2m situation,
verify altitude inside 1550..1850 m, and retry the same frozen pilot once.
```

Stage-5 pitch-rate pilot 1, 2026-07-12 15:20 America/Denver:

```text
Output log: logs/stage5_pitch_rate_pilot_20260712_152026.csv
Rows / elapsed / maximum gap: 300 / 29.802937699 s / 0.101186218 s
Start gate / engagement: PASS / 100 percent
Reference samples / window / peak: 20 / 10.0001..11.9001 s / +0.2000 deg/s
Q full range / active positive peak: -0.07523..+0.08893 / +0.05716 deg/s
Active-window Q-reference RMSE: 0.11998 deg/s
Post-pulse 12..20 s max |Q| / final 5 s max |Q|: 0.07132 / 0.04009 deg/s
LQR perturbation range / peak: -0.0001287..+0.0000645 / 0.0001287
Maximum perturbation slew: 0.00002574/sample
Sent-to-realized pitch correlation at one-sample lag: 0.999999994
Pitch / roll: +1.2112..+1.5542 deg / -0.0008..+0.0278 deg
P / R: -0.0907..+0.0062 / -0.1657..-0.1451 deg/s
Altitude / IAS: 1709.18..1712.77 m / 38.10..38.28 kt
Latch / abort / saturation: none / none / none
Both owned axes restored: PASS
Safety decision: PASS; controller remained bounded and fallback was not needed
Tracking decision: FAIL / INADEQUATE for the declared +0.2-deg/s pilot
Reason: active positive Q reached only 0.0572 deg/s and active RMSE was 0.1200
Decision: do not collect repeats and do not widen command/safety limits. Reopen
offline rate-weight selection using this design pilot as tuning evidence, rerun
the complete coefficient/delay/limit audit, and reserve future repeated runs as
independent confirmation of the frozen replacement gain.
Next allowed action: offline-only reweighting within the existing 0.003 command
and 0.0005/sample slew limits. No further LQR flight until that audit passes.
```

Stage-5 pilot interpretation refinement, 2026-07-12:

```text
Offline check: increasing rate weight or lengthening the nonzero Q-reference
did not make the rate-only architecture track the reference adequately without
approaching behavior that compensates the angle-stiffness state.
Conclusion: sustained Q-reference tracking is not the correct Stage-5 gate for
a zero-angle-feedback damper. Adding integral/angle action now would skip Stage 6.
Gain/limit decision: unchanged; do not increase the 0.003 command bound.
Replacement experiment concept: zero Q reference plus a small, independently
logged bounded actuator disturbance, then measure LQR rate damping/recovery.
Required before flight: freeze pulse and numerical acceptance criteria using
offline model/uncertainty evidence; verify fallback and observe-only waveform.
Persistent concise handoff: docs/LAST_SESSION_HANDOFF.md
Next allowed action: offline design only. No further LQR flight authorized yet.
```

Stage-5 replacement pitch-rate damping experiment frozen, 2026-07-12:

```text
Offline design: scripts/design_stage5_rate_pulse.py
Result: configs/stage5_pitch_rate_pulse_design.json
Reference: Q reference fixed at zero throughout
Disturbance: +0.0005 normalized pitch-command half-sine, 10.0..10.5 s
Controller history: records actual final perturbation including disturbance
Run: 30 s at 10 Hz; unchanged trim, ownership, fallback, and safety envelopes
Uncertainty audit: all 81 pitch coefficient/delay cases
Predicted peak |Q| range: 0.02430..0.03045 deg/s
Worst final 5 s |Q| / |pitch perturbation|: 0.01219 deg/s / 0.00549 deg
Worst command / slew / saturation: 0.000471 / 0.000301/sample / zero
Frozen pilot acceptance criteria declared before flight:
  300 samples; max gap <=0.25 s; 100 percent engagement; start gate PASS
  no latch, abort, saturation, pause, replay, or ownership-restoration failure
  realized total-pitch input follows sent command at expected one-sample lag
  peak post-pulse |Q| >=0.020 deg/s (measurable response gate)
  final 5 s max |Q| <=0.020 deg/s
  final 5 s max pitch perturbation from pre-pulse mean <=0.010 deg
  pitch/roll remain inside 10 deg and all body rates inside 20 deg/s
Static verification: wrapper syntax, compilation, 40 offline tests PASS
Next allowed action: replacement observe-only waveform/history/logging audit.
No engaged replacement pilot until the observe-only log passes.
```

Replacement observe-only attempt 1, 2026-07-12 15:27 America/Denver:

```text
Output log: logs/stage5_pitch_rate_observe_20260712_152732.csv
Rows / elapsed / maximum gap: 300 / 29.797245077 s / 0.110497397 s
Controls sent / ownership changes: none / none
Zero Q reference: PASS
Sampled disturbance: 4 nonzero samples; peak +0.000475588
Pre-latch candidate peak / slew: 0.000472418 / 0.000294362 per sample PASS
Safety latch: sample 104 at 10.4001 s; body-rate envelope exceeded
Rate discontinuity: P +0.00441 to +31.7490 deg/s in one sample while roll
                    changed only -0.00009 deg; Q simultaneously -0.00009 to
                    -4.35393 deg/s
Decision: FAIL as observe-only gate evidence. No control was sent, so the
disturbance waveform did not cause the aircraft response. Treat the abrupt rate
sample as adverse measurement/connection evidence; do not ignore the latch.
Logging correction: preserve bounded LQR candidate in lqr_sent_perturbation and
separately log final_pitch_perturbation when backstepping fallback is selected.
Next allowed action: static verification, reload clean stage 2m, then repeat
observe-only once. Engaged replacement pilot remains blocked.
```

Replacement observe-only attempt 2, 2026-07-12 15:31 America/Denver:

```text
Output log: logs/stage5_pitch_rate_observe_20260712_153150.csv
Rows / elapsed / maximum gap: 300 / 29.821778419 s / 0.101130419 s
Controls sent / ownership changes: none / none
Q reference: exactly zero throughout PASS
Disturbance samples / window / peak: 5 / 10.0001..10.4001 s / +0.000475637
LQR candidate peak / maximum slew: 0.000451954 / 0.000294667 per sample
Separated LQR/final perturbation disagreement: zero (no fallback selected)
Latch / abort: none / none
Pitch / Q: +1.0829..+1.2881 deg / -0.03840..+0.05178 deg/s
Roll / P: +0.0466..+0.0938 deg / +0.00275..+0.00503 deg/s
Paused / sim speed / replay: 0 / 1 / 0 throughout
Result: PASS for corrected waveform, timing, history, logging, bounds, and latch.
Next allowed action: exactly one engaged replacement pitch-rate damping pilot
under the frozen response and safety criteria. No parameter changes authorized.
```

Stage-5 pitch-rate damping pilot 2, 2026-07-12 15:32 America/Denver:

```text
Output log: logs/stage5_pitch_rate_pilot_20260712_153258.csv
Rows / elapsed / maximum gap: 300 / 29.830505704 s / 0.100075988 s
Start gate / engagement: PASS / 100 percent
Disturbance samples / peak: 5 / +0.000475620
Sent-to-realized pitch correlation at one-sample lag: 0.999999996
LQR perturbation peak / maximum slew: 0.000500468 / 0.000305930
Latch / abort / saturation: none / none / none
Both owned axes restored: PASS
Peak post-pulse |Q|: 0.055294 deg/s                  PASS (>=0.020)
Final 5 s max |Q|: 0.014718 deg/s                   PASS (<=0.020)
Pre-pulse mean pitch: +1.224999 deg
Final 5 s max pitch perturbation: 0.021395 deg       FAIL (<=0.010)
Pitch full range: +1.2038..+1.2679 deg
Roll / P: -0.0068..+0.1513 deg / -0.5186..+0.0381 deg/s
Altitude / IAS: 1712.36..1714.77 m / 39.189..39.218 kt
Safety decision: PASS; bounded response and rate damping observed
Frozen response decision: FAIL because residual pitch offset exceeded the
                          predeclared 0.010-deg limit
Decision: REJECTED as Stage-5 validation pilot. Do not relax the pitch threshold
or collect repeats. Use this design-pilot evidence only to reduce disturbance
amplitude offline while preserving a separately frozen measurable-Q gate.
Next allowed action: offline-only replacement pulse design and full uncertainty
audit. No further LQR flight is authorized.
```

Stage-5 reduced-pulse replacement design frozen, 2026-07-12:

```text
Design implementation/result: scripts/design_stage5_rate_pulse.py /
                              configs/stage5_pitch_rate_pulse_design.json
Change from rejected pilot: disturbance amplitude reduced from 0.0005 to 0.0002
Unchanged: gains, 0.5-s half-sine duration, zero Q reference, command/slew
           limits, safety envelopes, ownership, fallback, and pitch-offset gate
Uncertainty cases: 81
Predicted peak |Q| range: 0.009719..0.012177 deg/s
Worst final 5 s |Q| / pitch perturbation: 0.004874 deg/s / 0.002193 deg
Worst command / slew / saturation: 0.0001883 / 0.0001204/sample / zero
Frozen replacement-pilot response gates declared before flight:
  peak post-pulse |Q| >=0.008 deg/s
  final 5 s max |Q| <=0.012 deg/s
  final 5 s max pitch perturbation from pre-pulse mean <=0.010 deg (unchanged)
  all prior completeness, timing, safety, realization, and restoration gates
Static verification: compilation, wrapper syntax, 40 offline tests PASS
Next allowed action: reload clean stage 2m and run reduced-pulse observe-only
gate. Engaged reduced-pulse pilot remains blocked until observe-only PASS.
```

Reduced-pulse observe-only gate, 2026-07-12 15:37 America/Denver:

```text
Output log: logs/stage5_pitch_rate_observe_20260712_153728.csv
Rows / elapsed / maximum gap: 300 / 29.816066293 s / 0.103131895 s
Controls sent / ownership changes: none / none
Q reference: zero throughout PASS
Disturbance samples / window / sampled peak: 5 / 10.0009..10.4001 s / +0.000190238
LQR candidate peak / maximum slew: 0.000183973 / 0.000119265 per sample
Separated LQR/final perturbation disagreement: zero
Latch / abort: none / none
Pitch / Q: +1.1229..+1.2903 deg / -0.04496..+0.04356 deg/s
Roll / P: +0.0444..+0.0798 deg / +0.00260..+0.00492 deg/s
Paused / sim speed / replay: 0 / 1 / 0 throughout
Result: PASS for reduced waveform, timing, history, logging, limits, and latch.
Next allowed action: exactly one engaged reduced-pulse damping pilot under the
predeclared response/safety gates. No parameter changes authorized.
```

Stage-5 reduced-pulse damping pilot 3, 2026-07-12 15:38 America/Denver:

```text
Output log: logs/stage5_pitch_rate_pilot_20260712_153830.csv
Rows / elapsed / maximum gap: 300 / 29.832440669 s / 0.102464999 s
Start gate / engagement: PASS / 100 percent
Disturbance samples / peak: 5 / +0.000190244
Sent-to-realized pitch correlation at one-sample lag: 0.999999981
LQR perturbation peak / maximum slew: 0.000209491 / 0.000121688
Latch / abort / saturation: none / none / none
Both owned axes restored: PASS
Peak post-pulse |Q|: 0.034917 deg/s                  PASS (>=0.008)
Final 5 s max |Q|: 0.012606 deg/s                   FAIL (<=0.012)
Pre-pulse mean pitch: +1.234786 deg
Final 5 s max pitch perturbation: 0.036237 deg       FAIL (<=0.010)
Pitch full range: +1.2027..+1.2829 deg
Roll / P: -0.0069..+0.1328 deg / -0.4516..+0.0379 deg/s
Altitude / IAS: 1711.90..1714.43 m / 39.122..39.170 kt
Safety decision: PASS; response remained bounded and rate disturbance measurable
Frozen response decision: FAIL; both final-rate and pitch-return gates missed
Decision: REJECTED as Stage-5 validation evidence. Do not round 0.012606 down,
relax either threshold retrospectively, or run another live pilot today.
Interpretation: pitch offset did not scale down with pulse amplitude, supporting
the architectural fact that a zero-angle-feedback rate damper does not regulate
attitude. Attitude return is a Stage-6 property, but this pilot remains failed
under its declared Stage-5 criteria.
Next allowed action: offline-only Stage-5 claim/experiment redesign. Separate
rate-damping acceptance from Stage-6 attitude-return acceptance, freeze future
training/validation allocation and thresholds using design-pilot evidence, and
perform static/offline audits before any further flight.
```

Corrected Stage-5 validation claim and allocation frozen, 2026-07-12:

```text
Plan: docs/STAGE5_RATE_VALIDATION_PLAN.md
Stage-5 claim: return of body rate to its measured pre-pulse baseline
Stage-6 claim: attitude tracking/return; explicitly not required in Stage 5
Pitch delta-rate definition: Q minus mean Q for t<10 s
Frozen pitch gates: peak |delta_Q| >=0.008 deg/s;
                    final 5 s max |delta_Q| <=0.015 deg/s;
                    final 5 s RMS(delta_Q)/peak <=0.35
All existing completeness, safety, realization, limit, and restoration gates
remain unchanged. Attitude drift remains reported and safety-bounded.
Design pilots excluded: stage5_pitch_rate_pilot_20260712_152026.csv,
                        stage5_pitch_rate_pilot_20260712_153258.csv,
                        stage5_pitch_rate_pilot_20260712_153830.csv
Required new pitch evidence: two held-out confirmation runs from fresh reloads;
both must pass without gain/threshold changes
Required roll evidence: offline design + observe-only + excluded design pilot +
two held-out confirmation runs
Next allowed action: static analyzer/wrapper preparation for pitch confirmation
run 1. No live run until implementation checks pass and clean stage 2m reload.
```

Stage-5 confirmation tooling prepared, 2026-07-12:

```text
Analyzer: scripts/analyze_stage5_rate_run.py
Confirmation label input: STAGE5_RUN_LABEL in scripts/run_stage5_pitch_rate_pilot.sh
Static verification: shell syntax, compilation, 40 offline tests PASS
Reproducibility check: analyzer applies the frozen corrected gates to excluded
design pilot stage5_pitch_rate_pilot_20260712_153830.csv and returns PASS.
Important: this does not retroactively convert that design pilot into validation
evidence; it only verifies the corrected metric implementation.
Next allowed action: fresh clean stage 2m reload, then Pitch Rate Confirmation 1
with STAGE5_RUN_LABEL=pitch_rate_confirmation_01. No gain/threshold changes.
```

Held-out Pitch Rate Confirmation Run 1, 2026-07-12 15:50 America/Denver:

```text
Output log: logs/stage5_pitch_rate_confirmation_01_20260712_155011.csv
Analyzer: scripts/analyze_stage5_rate_run.py (frozen before collection)
Rows / start / engagement / safety / live gates: PASS
Sent-to-realized pitch correlation at one-sample lag: 0.999999972 PASS
Pre-pulse mean Q: +0.000447861 deg/s
Peak post-pulse |delta_Q|: 0.0173185 deg/s       PASS (>=0.008)
Final 5 s max |delta_Q|: 0.0205351 deg/s         FAIL (<=0.015)
Final 5 s RMS |delta_Q|: 0.00989595 deg/s
Final RMS / peak decay ratio: 0.571408            FAIL (<=0.35)
Final pitch offset (reported, not gated): 0.018510 deg
Disturbance / total LQR perturbation peak: 0.000190241 / 0.000194955
Pitch / Q: +1.2849..+1.3243 deg / -0.01458..+0.02099 deg/s
Roll / P: -0.0041..+0.0720 deg / -0.2448..+0.0244 deg/s
Altitude / IAS: 1719.43..1722.09 m / 38.964..38.994 kt
Latch / abort / saturation: none / none / none
Both axes restored: PASS
Decision: FAIL under the predeclared held-out rate-recovery gates. Do not
collect Pitch Confirmation Run 2, relax thresholds, or advance to roll.
Next allowed action: offline diagnosis of persistent rate residual/model mismatch
using design logs and this failed held-out run. Any controller change reopens
Stage-4 robustness/replay and requires newly allocated confirmation evidence.
```

Stage-4 inner-rate redesign after failed held-out confirmation, 2026-07-12:

```text
Offline diagnosis: post-pulse Q retained natural oscillation while late LQR
corrections were only approximately 1e-6..15e-6; response was not correlated
with lateral P and was not driven by the completed disturbance pulse
Design change: inner-rate Bryson scale 2.0 -> 1.0 deg/s
Unchanged: plant models, delay, command limit 0.003, slew 0.0005/sample,
           safety, trim/history, ownership, and fallback
New roll-rate K: [-0.0027262310, 0.0788174356, 0.0785343024, 0.0782521863]
New pitch-rate K: [-0.0019913193, 0.0441278087, 0.0432419710, 0.0423739160]
Nominal full-plant radius: roll 0.96259; pitch 0.97361
Worst 2-sigma/delay radius: roll 0.97925; pitch 0.98728
Unstable linear cases: 0/81 per axis
Combined +/-1-deg, +/-1-deg/s stress saturation: 2.5 percent roll / 2.0 percent pitch
Exact eight-log runtime replay peak: roll 0.000473; pitch 0.000411; saturation zero
Reduced pitch-pulse 81-case audit: peak |Q| 0.00923..0.01129 deg/s;
  worst final |Q| 0.001896 deg/s; pitch offset 0.000725 deg; saturation zero
Static/runtime tests: 40 PASS
Stage decision: Stage 4 re-audit PASS for the revised inner-rate gains; Stage 5
remains CURRENT and all confirmation allocation restarts because gain changed
Next allowed action: fresh reload and new observe-only gate with revised gain.
No engaged revised-gain run until observe-only PASS.
```

Revised-gain observe-only gate, 2026-07-12 16:01 America/Denver:

```text
Output log: logs/stage5_pitch_rate_observe_20260712_160108.csv
Rows / elapsed / maximum gap: 300 / 29.801054300 s / 0.101467028 s
Controls sent / ownership changes: none / none
Disturbance samples / window / peak: 5 / 10.0001..10.4001 s / +0.000190243
LQR candidate peak / maximum slew: 0.000250061 / 0.000122743 per sample
Latch / abort: none / none
Pitch / Q: +1.2657..+1.4697 deg / -0.04761..+0.05579 deg/s
Roll / P: +0.0752..+0.1877 deg / +0.00390..+0.00699 deg/s
Paused / sim speed / replay: 0 / 1 / 0 throughout
Result: PASS for revised-gain waveform, timing, limits, history, logging, and
safety. Next allowed action: one revised-gain pitch-rate design pilot, excluded
from confirmation evidence, with unchanged thresholds and fallback.
```

Validate one axis at a time, with small initial disturbances, latched aborts,
manual reset, conservative command and slew limits, and repeated passes.

### Stage 6 — Single-axis attitude-loop validation

Status: `BLOCKED BY STAGE 5`

Add the outer attitude loop only after its associated rate loop passes. Validate
pitch and roll separately with frozen criteria and repeated runs.

### Stage 7 — Combined attitude and recovery comparison

Status: `BLOCKED BY STAGE 6`

Validate combined operation, then compare LQR and backstepping on matched
disturbances. Preserve backstepping as the recovery benchmark; do not claim LQR
superiority based only on small-signal tracking.

## Session update template

### Cleanup session — 2026-07-10

```text
Date/time: 2026-07-10 (America/Denver)
Current stage: Stage 1 — unchanged
Objective: reorganize project files only
Files changed: controller paths, documentation, runner guide, and archive layout
Exact command: offline filesystem reorganization and CLI/test verification
Input conditions/configuration: no X-Plane session; no flight command sent
Output log: none
Measured results: recorded in the cleanup verification report
Acceptance criteria evaluated: none of the Stage 1 flight criteria
Result: INCONCLUSIVE for Stage 1; project cleanup only
Reason: no simulator research or identification was authorized
Next allowed action within the same stage: retain the previously documented Stage 1 process
```

Revised-gain pitch-rate design pilot, 2026-07-12 16:02 America/Denver:

```text
Output log: logs/stage5_pitch_rate_design_revised_20260712_160222.csv
Start/engagement/safety/realization/restoration: PASS
Peak |delta_Q|: 0.016793 deg/s                         PASS (>=0.008)
Final 5 s max |delta_Q|: 0.011145 deg/s               PASS (<=0.015)
Final RMS/peak decay ratio: 0.387619                 design-only FAIL vs old 0.35
Final pitch offset: 0.024678 deg (reported; not Stage-5 gate)
Decision: excluded design evidence; revised gain is safe and materially improves
the previous held-out failure, but persistent background oscillation makes 0.35
too brittle. Offline metric review froze the future confirmation decay ceiling
at 0.45; no gain, command, safety, or final-rate threshold changed. Existing
confirmation evidence remains invalid for the revised gain. Next: fresh reload,
new observe-only gate, then Pitch Rate Confirmation 1 restarted.
```

Revised-gain observe-only gate 2, 2026-07-12 16:06 America/Denver:

```text
Output log: logs/stage5_pitch_rate_observe_20260712_160610.csv
Rows / elapsed / maximum gap: 300 / 29.819787225 s / 0.100539585 s
Controls sent / ownership changes: none / none
Disturbance samples / window / sampled peak: 5 / 10.0001..10.4001 s / +0.000190239
LQR candidate peak / maximum slew: 0.000138760 / 0.000116209 per sample
Latch / abort: none / none
Pitch / Q: +1.2691..+1.3947 deg / -0.03210..+0.03420 deg/s
Roll / P: +0.0301..+0.0350 deg / +0.00232..+0.00448 deg/s
Paused / sim speed / replay: 0 / 1 / 0 throughout
Result: PASS. Next allowed action: restarted held-out Pitch Rate Confirmation 1
with revised gain and frozen 0.45 decay ceiling.
```

Restarted revised-gain Pitch Rate Confirmation Run 1, 2026-07-12 16:07:

```text
Output log: logs/stage5_pitch_rate_confirmation_01_revised_20260712_160741.csv
Analyzer: scripts/analyze_stage5_rate_run.py with frozen 0.45 decay ceiling
Rows / start / engagement / safety / realization / restoration: PASS
Pre-pulse mean Q: +0.002418625 deg/s
Peak post-pulse |delta_Q|: 0.0194643 deg/s                  PASS (>=0.008)
Final 5 s max |delta_Q|: 0.0180477 deg/s                    FAIL (<=0.015)
Final RMS/peak decay ratio: 0.543065                        FAIL (<=0.45)
Final pitch offset: 0.027405 deg (reported, not gated)
Latch / abort / saturation: none / none / none
Decision: FAIL. Stronger gain did not resolve the late residual oscillation;
do not collect Confirmation Run 2 and do not raise gains or limits.
Interpretation: the scalar pre-pulse-mean metric is confounded by background
Q oscillation/cross-axis dynamics. Next action is offline redesign using a
matched no-pulse baseline/residual or explicit disturbance-response estimator.
Any new metric must be frozen before new confirmation data.
```

Matched-baseline diagnosis and tooling, 2026-07-12:

```text
Diagnosis: failed confirmation differs materially from the closest no-pulse
observe-only trajectory, but observe-only did not own actuators and therefore is
not a valid controlled baseline. A scalar pre-pulse-mean metric cannot isolate
pulse response from controller/aircraft background dynamics.
Tooling added: STAGE5_DISTURBANCE_AMPLITUDE environment override in the pilot
wrapper and scripts/run_stage5_pitch_rate_baseline.sh.
Required paired design evidence: fresh zero-disturbance engaged LQR baseline,
then fresh reduced-pulse engaged LQR run; estimate pulse-induced incremental Q
and recovery from the paired trajectories before freezing a new metric.
Static verification: shell syntax and 40 offline tests PASS.
No simulator command sent during diagnosis/tooling.
Next allowed action: reload clean stage 2m and collect the zero-disturbance
engaged baseline. Do not collect another confirmation run yet.
```

Controlled zero-disturbance paired baseline, 2026-07-12 16:17 America/Denver:

```text
Output log: logs/stage5_pitch_rate_zero_excitation_baseline_20260712_161705.csv
Rows / elapsed / maximum gap: 300 / 29.827158829 s / 0.101179239 s
Start gate / engagement / ownership restoration: PASS / 100 percent / PASS
Disturbance pulse: zero throughout
Q background range / RMS: -0.01728..+0.01568 deg/s / 0.00650 deg/s
Pitch range: +1.2979..+1.3468 deg
LQR perturbation peak / saturation: 0.00003166 / zero
Latch / abort: none / none
Paused / sim speed / replay: 0 / 1 / 0
Decision: PASS as the controlled no-disturbance paired baseline. This log is not
a pulse-response validation run. Next allowed action: fresh reload, then one
matched reduced-pulse engaged run using the revised gain.
```

Paired reduced-pulse run 1 and baseline comparison, 2026-07-12 16:23:

```text
Pulse log: logs/stage5_pitch_rate_paired_pulse_01_20260712_162306.csv
Baseline: logs/stage5_pitch_rate_zero_excitation_baseline_20260712_161705.csv
Pulse run safety/start/engagement/realization/restoration: PASS
Single-run peak |delta_Q|: 0.023221 deg/s; final max 0.025648; decay 0.62359
Single-run frozen gates: final max/decay FAIL; no validation acceptance
Naive paired residual after pre-window mean removal:
  Q incremental peak/final max/ratio: 0.02753 / 0.02934 / 0.56868
  pitch incremental peak/final max: 0.03551 / 0.04452 deg
  P and roll incremental residuals are also large (0.04047 deg/s / 0.01362 deg)
Diagnosis: the two fresh reloads have materially different pre-pulse P/roll and
coupled trajectories; one baseline/pulse subtraction pair is not an identified
disturbance response. Do not freeze a metric or claim damping from this pair.
Decision: INCONCLUSIVE paired evidence; safe pulse run retained for audit only.
No further live collection authorized until an offline metric handles initial
condition/cross-axis mismatch, for example matched-state model residuals or
multiple randomized baseline/pulse pairs with pre-gate matching.
```

Stage-5 frozen-model residual diagnosis, 2026-07-12:

```text
Implementation: scripts/analyze_stage5_model_residual.py
Artifact: configs/stage5_model_residual_analysis.json
Offline tests: 41 PASS
Pitch model beta: [-4.6996473, -0.2027859, -210.6428948]
Controlled zero-pulse baseline residual RMS (pre/post/final):
  0.04617 / 0.09413 / 0.09573 deg/s^2
Paired pulse residual RMS (pre/pulse/post/final):
  0.08618 / 0.06474 / 0.08511 / 0.10456 deg/s^2
Revised confirmation residual RMS (pre/pulse/post/final):
  0.03308 / 0.10932 / 0.03925 / 0.09526 deg/s^2
Interpretation: post/final residual dynamics are large and persistent in the
controlled zero-pulse baseline and revised confirmation. The Stage-3 local
model does not explain the engaged background dynamics; Q/R changes alone are
not a defensible solution. This is evidence of missing states, time variation,
cross-axis/artificial-stability effects, or measurement artifacts.
Decision: retain Stage 5 as unresolved; do not claim validated LQR flight and do
not collect more confirmation runs until model/metric scope is resolved.
Next allowed analysis: compare additional states/datarefs, assess LPV/gain
scheduling and hybrid backstepping+LQR options, and evaluate whether a nonlinear
or robust controller is justified. Workflow gates remain unchanged.
```

Rich-dataref read-only diagnostic after XPlaneConnect recovery, 2026-07-12 17:23:

```text
Output log: logs/rich_dataref_observe_20260712_172301.csv
Controls sent / ownership changes: none / none
Requested channels: 35; finite samples: 83/83 for every channel
Rows / elapsed: 83 / 9.944488425 s
Mean / minimum / maximum intersample interval:
  0.121274249 / 0.107081707 / 0.149286483 s
Effective sample rate: 8.245774 Hz
Gaps above 0.25 s: zero
Artificial stability: enabled throughout
Paused / sim speed / replay: 0 / 1 / 0 throughout
Control/surface/moment/override channels: available and finite
Result: PASS for connectivity and channel availability; FAIL for the declared
        10-Hz timing requirement (83 samples versus nominal 100)
Decision: no LQR control run authorized. Preserve this diagnostic as timing
          evidence and optimize/audit read-only request batching offline.
Next allowed action: static/offline batching correction, then repeat the same
read-only rich-dataref diagnostic and require the timing gate to pass before
rich-mission or further Stage-5 flight collection.
```

Rich-dataref batching correction and repeated timing gate, 2026-07-12 17:24:

```text
Implementation: scripts/diagnose_rich_mission_datarefs.py
Change: bounded read batches increased from 6 to 12 channels, reducing six
        sequential request/response transactions to three per sample
Static verification: compilation, CLI help, and wrapper shell syntax PASS
Output log: logs/rich_dataref_observe_20260712_172421.csv
Controls sent / ownership changes: none / none
Rows / elapsed: 100 / 9.898331826 s
Effective sample rate: 10.001685 Hz
Mean / minimum / maximum intersample interval:
  0.099983150 / 0.098386900 / 0.101135993 s
Gaps above 0.25 s: zero
Requested channels: 35; non-finite values: zero
Artificial stability: enabled throughout
Paused / sim speed / replay: 0 / 1 / 0 throughout
All joystick/axis/flight-control/surface override flags: zero throughout
Result: PASS for read-only rich-dataref availability and 10-Hz timing.
Decision: the dataref prerequisite is complete, but this does not authorize an
          excitation or LQR confirmation flight.
Next allowed action: offline implementation and freeze of the rich-mission
logger, operating-regime gates, paired allocation, and analysis plan described
in docs/RICH_LQR_IDENTIFICATION_MISSION_V2.md; observe-only validation must
precede any newly designed live maneuver.
```

Rich-mission observe-only implementation and first exact gate, 2026-07-12 17:30:

```text
Campaign configuration: configs/rich_mission_campaign.json
Pure gate/allocation helpers: scripts/rich_mission.py
Observe-only runner/wrapper: scripts/run_rich_mission_observe_xp12.py /
                             scripts/run_rich_mission_observe.sh
Frozen analyzer: scripts/analyze_rich_mission_observe.py
Tests: tests/test_rich_mission.py
Allocation: six regimes, nine declared runs per regime, 54 unique run IDs;
            training/validation roles fixed before collection
Safety property: observe runner exposes no --engage argument and contains no
                 sendCTRL/sendDREF control path
Static verification: compilation, CLI, shell syntax, 45 offline tests PASS
Output log: logs/rich_R3_observe_01_20260712_173024.csv
Controls sent / ownership changes: none / none
Rows / expected / completeness: 95 / 100 / 95 percent
Mean / maximum dt: 0.106149157 / 0.149133238 s
Non-finite values: zero; metadata and observe-only flags: PASS
Altitude / IAS: 1739.91..1740.68 m / 38.205..38.294 kt
Pitch / roll: +1.167..+1.421 deg / -8.815..-7.806 deg
P / Q / R: -0.0033..+0.0055 / +0.4825..+0.5955 /
             -3.8672..-3.4861 deg/s
Result: FAIL. Completeness was below the frozen 99-percent threshold, and the
        aircraft violated the frozen roll and body-rate start envelopes.
Decision: no excitation or control run authorized. Increase read-only batch
          size from 24 to 48 offline to reduce acquisition transactions; retain
          all gates unchanged.
Next allowed action: reload the clean stage 2m R3 situation, verify near-level
state, and repeat the exact observe-only gate. Do not widen the start envelope.
```

Rich-mission R3 observe-only gate PASS, 2026-07-12 17:34:

```text
Output log: logs/rich_R3_observe_01_20260712_173445.csv
Frozen analyzer: scripts/analyze_rich_mission_observe.py
Controls sent / ownership changes: none / none
Rows / expected / completeness: 100 / 100 / 100 percent
Mean / maximum dt: 0.099984438 / 0.100172530 s
Non-finite values: zero
Metadata / timing / frozen R3 start gate: PASS / PASS / PASS
Altitude / IAS: 1719.56..1720.65 m / 38.353..38.366 kt
Pitch / roll: +1.405..+1.433 deg / -0.098..-0.086 deg
P / Q / R: +0.0021..+0.0041 / -0.0106..+0.0094 /
             -0.1680..-0.1663 deg/s
Dynamic pressure mean: 238.603 Pa
AOA / beta means: +0.9210 / -0.01161 deg
Acquisition time: 0.02354..0.07481 s
Result: PASS for the exact R3 observe-only availability, state, metadata, and
        timing prerequisite. This is not excitation or controller validation.
Next allowed action: offline implementation/freeze of the controlled trim/state
confirmation and the two fresh-reload no-excitation engaged-baseline procedure.
No excitation run is authorized yet.
```

R3 trim and zero-excitation baseline preparation, 2026-07-12 17:41:

```text
Frozen campaign update: configs/rich_mission_campaign.json
Rich baseline channels added to canonical logger: augmentation switch,
  actuator deflection times, primary surface deflections, and override states
Trim analyzer: scripts/analyze_rich_r3_trim.py
Baseline analyzer: scripts/analyze_rich_r3_baseline.py
Observe wrapper: scripts/run_rich_r3_baseline_observe.sh
Engaged wrapper: scripts/run_rich_r3_baseline.sh
Frozen baseline: 30 s at 10 Hz; original backstepping gains; legacy routing;
  trim-relative commands; both axes owned only when engaged; zero recovery
  pulse and zero identification excitation; unchanged 10-deg attitude and
  20-deg/s body-rate safety envelopes
Static verification: compilation, shell syntax, 45 offline tests PASS
All-sample trim check on rich_R3_observe_01_20260712_173445.csv: PASS
Exact observe-baseline log: logs/rich_R3_baseline_observe_20260712_174155.csv
Rows / mean dt / maximum gap: 300 / 0.099681212 / 0.100956461 s
Engagement: zero; controls/ownership sent: none
Rich channels finite / zero excitation / safety: PASS / PASS / PASS
Independent first-row frozen R3 start gate: PASS; no reasons
Result: PASS for trim confirmation and exact baseline observe-only gate.
Decision: Engaged R3 Baseline 1 is authorized only after a fresh clean stage 2m
          reload. No excitation is authorized. Baseline 2 requires another
          separate fresh reload after Baseline 1 is analyzed and passes.
```

Rich-mission R3 Engaged Baseline 1, 2026-07-12 17:45:

```text
Output log: logs/rich_R3_baseline_01_20260712_174514.csv
Controller: original backstepping stabilization, trim-relative legacy routing
Excitation / recovery pulse: exactly zero / exactly zero
Captured trim: CTRL0 +0.152131; CTRL1 +0.000492064
Start gate / engagement: PASS / 100 percent
Rows / mean dt / maximum gap: 300 / 0.099785765 / 0.101011697 s
Rich channel finite / safety / saturation: PASS / PASS / zero
Pitch / roll: +1.3035..+1.5234 / -0.0015..+0.0432 deg
P / Q / R: -0.1413..+0.0129 / -0.5509..+0.0209 /
             -0.1679..-0.1342 deg/s
Altitude / IAS: 1711.07..1714.10 m / 38.102..38.325 kt
Sent CTRL0 / CTRL1: +0.145207..+0.152042 /
                    -0.000859..+0.000540
Identification active / recovery active samples: 0 / 0
Both axis overrides restored to their initial zero states: PASS
Frozen analyzer result: PASS
Decision: accepted as R3 no-excitation Baseline 1 training evidence. Baseline 2
          is authorized only after a new clean stage 2m reload and remains the
          separately allocated validation baseline. No excitation authorized.
```

Rich-mission R3 Engaged Baseline 2, 2026-07-12 17:48:

```text
Output log: logs/rich_R3_baseline_02_20260712_174845.csv
Allocation: R3 baseline replicate 2 / held-out validation
Controller: original backstepping stabilization, trim-relative legacy routing
Excitation / recovery pulse: exactly zero / exactly zero
Captured trim: CTRL0 +0.147313; CTRL1 +0.000495823
Start gate / engagement: PASS / 100 percent
Rows / mean dt / maximum gap: 300 / 0.099770092 / 0.102807830 s
Rich channel finite / safety / saturation: PASS / PASS / zero
Pitch / roll: +1.3014..+1.3396 / -0.0200..+0.2925 deg
P / Q / R: -0.9965..+0.0980 / -0.0906..+0.0092 /
             -0.2246..+0.0077 deg/s
Altitude / IAS: 1714.29..1717.03 m / 38.676..38.772 kt
Sent CTRL0 / CTRL1: +0.146085..+0.147282 /
                    -0.008659..+0.001120
Identification active / recovery active samples: 0 / 0
Both axis overrides restored to their initial zero states: PASS
Frozen analyzer result: PASS
Decision: accepted as R3 no-excitation Baseline 2 validation evidence. The R3
          paired baseline allocation is complete. Baseline 1 and 2 exhibit
          different natural/coupled transient axes, so excitation amplitude and
          response metrics must be frozen from offline background/coupling
          analysis before any pitch or roll excitation run.
Next allowed action: offline analysis of both accepted baseline logs and frozen
R3 single-axis excitation design. No excitation is authorized yet.
```

R3 single-axis excitation design and observe gates, 2026-07-12 17:55:

```text
Design implementation: scripts/design_rich_r3_excitation.py
Frozen artifact: configs/rich_R3_excitation_design.json
Accepted baseline inputs: rich_R3_baseline_01_20260712_174514.csv and
                          rich_R3_baseline_02_20260712_174845.csv
Waveform: tapered multisine, 10..50 s in a 60-s 10-Hz run; 2-s ramps;
          frequencies 0.10, 0.20, 0.35, 0.55, 0.80, 1.10 Hz
Selection gates: minimum realized-input spectral SNR 2.0 and minimum predicted
                 body-rate SNR 5.0, using the smallest passing candidate
Pitch selection: amplitude 0.001; minimum input spectral SNR 2.7527;
                 nominal rate RMS/peak 0.09385/0.19620 deg/s
Roll selection: amplitude 0.0002; minimum input spectral SNR 19.9991;
                nominal rate RMS/peak 0.04418/0.08902 deg/s
Coefficient/delay audit: 81 cases per axis
Pitch uncertainty peak-rate range: 0.11882..0.45818 deg/s
Roll uncertainty peak-rate range: 0.02925..0.55254 deg/s
All predictions remain far inside the unchanged 20-deg/s safety envelope.
Pitch observe log: logs/rich_R3_pitch_observe_20260712_175427.csv
  600 rows; max gap 0.101589 s; 399 active samples; peak hypothetical
  excitation 0.000661820; all waveform/timing/rich/safety/start gates PASS
Roll observe log: logs/rich_R3_roll_observe_20260712_175559.csv
  600 rows; max gap 0.101371 s; 399 active samples; peak hypothetical
  excitation 0.000132376; all waveform/timing/rich/safety/start gates PASS
Controls sent / ownership changes in both observe runs: none / none
Engaged wrappers: scripts/run_rich_r3_pitch.sh and scripts/run_rich_r3_roll.sh
Frozen engaged analyzer: scripts/analyze_rich_r3_excitation_observe.py requires
  completeness/timing, 100-percent engagement, exact waveform/axis, no latch,
  abort, recovery pulse or saturation, safety/start gates, rich finite data,
  and >=0.99 one-sample sent-to-realized control correlation
Static verification: shell syntax, compilation, 46 offline tests PASS
Decision: R3 Pitch Training Run 1 is authorized after a fresh clean stage 2m
          reload. Pitch Validation Run 2 remains held out. Roll collection is
          blocked until the two allocated pitch runs are evaluated unchanged.
```

R3 Pitch Training Run 1 safety pass / richness fail, 2026-07-12 18:02:

```text
Output log: logs/rich_R3_pitch_training_01_20260712_180253.csv
Captured trim: CTRL0 +0.151756; CTRL1 +0.000475884
Start / engagement / timing / safety: PASS / 100 percent / PASS / PASS
Rows / maximum gap: 600 / 0.101011691 s
Active excitation samples / peak: 399 / 0.000661880
Sent-to-realized pitch correlation at one-sample lag: 0.999999999975
Latch / abort / saturation / recovery pulse: none / none / none / zero
Both axis overrides restored: PASS
Frozen execution analyzer: PASS
Pitch / Q: +1.2949..+1.4215 deg / -0.3126..+0.0802 deg/s
Roll / P: -0.0891..+0.0051 deg / -0.0204..+0.3032 deg/s
Post-run training-only spectral diagnosis at 0.10, 0.20, 0.35, 0.55,
0.80, and 1.10 Hz:
  realized total-pitch amplitudes = 6.15e-5, 3.95e-5, 6.24e-5,
                                    1.36e-4, 2.02e-4, 2.30e-4
  worst ratio to accepted-baseline spectral amplitude = 0.6774
  pitch-rate spectral response worst baseline ratio = 8.4208
Surface audit: selected left/right elevator deflection channels remained
               identically zero although total pitch input varied
Decision: safe run retained as redesign evidence but rejected as allocated
          training evidence. The planned >=2 realized-input spectral margin
          was not achieved at the low frequencies, and the surface mapping is
          incomplete. Do not open held-out Pitch Validation Run 2 and do not
          increase amplitude beyond the frozen candidate range.
Next allowed action: offline redesign that marks uninformative low-frequency
closed-loop components explicitly, verifies the distributed BWB pitch-surface
datarefs, and repeats all static/observe gates before restarting pitch training.
No further excitation flight is authorized yet.
```

R3 pitch surface-map correction and revised observe gate, 2026-07-12 18:09:

```text
Authoritative sources: X-Plane 12.4.3 DataRefs.txt and active
  Aircraft/GHYN/EHEKATL BWB 5 1.acf
Aircraft geometry: elevator surfaces assigned to wing slots 2--5; aileron
  surfaces assigned to wing slots 6--7. Horizontal-stabilizer elevator
  channels used by the first logger are not active for this BWB.
Read-only live array result: elv1_def/elv2_def are length 56 with active indices
  8--15, 18--19, 25--26, 35--36; representative elevator value -4.552681 deg.
Canonical logger update: representative distributed elevator and aileron array
  indices added; no controller equation, gain, routing, or limit changed.
Revised design implementation/artifact:
  scripts/design_rich_r3_pitch_revised.py /
  configs/rich_R3_pitch_revised_design.json
Training evidence used for redesign only: rich_R3_pitch_training_01_20260712_180253.csv
Revised frequencies: 0.35, 0.55, 0.80, 1.10 Hz
Unchanged amplitude/window/ramp: 0.001 / 10..50 s / 2 s
Projected realized-input spectral SNR: 3.825..23.747; gate >=2
Uncertainty/delay audit: 81 cases; predicted peak Q 0.1551..0.6700 deg/s
Peak excitation command: 0.000919333; unchanged safety envelope
Revised observe log: logs/rich_R3_pitch_observe_20260712_180907.csv
Rows / max gap / active samples: 600 / 0.107612662 s / 399
Hypothetical excitation peak: 0.000919287
Timing, exact frequencies, waveform, rich channels, start, safety, latch,
recovery, and saturation gates: PASS
Controls sent / ownership changes: none / none
Distributed elevator representative channels: finite at -4.552681 deg
Static verification: compilation, shell syntax, 47 offline tests PASS
Decision: revised Pitch Training Run 1 allocation restarts and is authorized
          after a fresh clean R3 reload. Held-out pitch validation and all roll
          flight remain blocked until the restarted training run passes realized
          spectral richness and surface-response checks.
```

R3 revised Pitch Training Run 1 accepted, 2026-07-12 18:13:

```text
Output log: logs/rich_R3_pitch_training_01_revised_20260712_181333.csv
Execution analyzer: scripts/analyze_rich_r3_excitation_observe.py
Richness analyzer/artifact: scripts/analyze_rich_r3_pitch_training.py /
                            configs/rich_R3_pitch_training_01_analysis.json
Captured trim: CTRL0 +0.143547; CTRL1 +0.000454888
Start / engagement / safety / restoration: PASS / 100 percent / PASS / PASS
Rows / maximum gap: 600 / 0.102752461 s
Active excitation samples / peak: 399 / 0.000919314
Sent-to-realized input correlation at one-sample lag: 0.999999999928
Latch / abort / recovery / saturation: none / none / zero / none
Realized total-pitch spectral amplitudes at 0.35/0.55/0.80/1.10 Hz:
  0.00011648 / 0.00019515 / 0.00026317 / 0.00031152
Realized input spectral SNR: 4.764 / 18.146 / 18.775 / 21.429 PASS
Q response spectral amplitudes: 0.01358 / 0.02078 / 0.02660 /
                                0.03058 deg/s
Q response spectral SNR: 17.417 / 31.856 / 21.906 / 26.933 PASS
Four representative distributed elevator channels each moved 0.053833 deg
peak-to-peak and correlated -0.9999999999 with total pitch input: PASS
Static/offline tests: 47 PASS
Decision: accepted as restarted R3 pitch training evidence. The earlier
          six-frequency run remains rejected/redesign-only. Do not open or
          inspect held-out pitch validation until training-only state selection,
          delay, filtering, and model coefficients are frozen. Roll remains blocked.
Next allowed action: offline R3 expanded longitudinal candidate/model fitting
using only Baseline 1 training data and this accepted pitch training log.
```

R3 pitch training-only candidate freeze, 2026-07-12:

```text
Implementation/artifact: scripts/identify_rich_r3_pitch.py /
                         configs/rich_R3_pitch_model.json
Inputs opened: rich_R3_pitch_training_01_revised_20260712_181333.csv only
Validation files opened: none
Candidate families: local angle/rate/control; aerodynamic AOA/TAS;
  cross-axis P/R/beta; distributed-surface aerodynamic/coupled
Candidate delays: 0, 1, 2, 3, 4 samples; 25 total candidates
Selection: opposite 10--30 / 30--50 s temporal holdouts with recursive
  0.1/0.5/1.0/2.0-s rate prediction and scaled condition <1e4
Selected predictor: local [pitch, Q, total_pitch_ratio], delay 3 samples
Beta: [-7.631572468, -1.410839561, -274.511020054]
Training qdot RMSE / NRMSE: 0.0978057 deg/s^2 / 0.512291
Bidirectional temporal one-step NRMSE: 0.512626
Bidirectional recursive-horizon mean NRMSE: 0.734991
Residual lag-1 correlation: 0.684116 (colored; limitation retained)
Scaled condition number: 2.2371
Result: expanded AOA/speed/coupling/surface candidates improved some one-step
        errors but produced substantially worse recursive predictions. They are
        rejected for this dataset. The three-sample local predictor is frozen
        for independent validation.
Claim boundary: short-horizon qdot/rate predictor only. This does not establish
  full expanded-state dynamics or authorize new LQR synthesis.
Static/offline tests: 48 PASS
Decision: held-out revised Pitch Validation Run 1 is authorized after a fresh
          clean R3 reload with unchanged waveform, controller, limits, and
          analyzers. Its data must not alter the frozen selection before scoring.
```

R3 pitch validation-design run and confirmation gate freeze, 2026-07-12 18:26:

```text
Output log: logs/rich_R3_pitch_validation_01_revised_20260712_182600.csv
Execution/richness gates: PASS / PASS
Rows / max gap / engagement: 600 / 0.106456832 s / 100 percent
Realized-input correlation: 0.999999999960
Input spectral SNR: 4.996 / 18.968 / 19.991 / 22.564
Q-response spectral SNR: 18.026 / 32.973 / 22.464 / 27.721
Distributed elevator motion/correlation: 0.055575 deg peak-to-peak /
                                         -0.9999999999
Latch / abort / saturation / recovery: none / none / none / zero
Both overrides restored: PASS
Frozen-model scorer/artifact: scripts/validate_rich_r3_pitch_model.py /
  configs/rich_R3_pitch_validation_01_model_score.json
No refit or reselection performed.
Validation qdot NRMSE: 0.524834; training 0.512291; ratio 1.02448
Validation recursive mean NRMSE: 0.768386; training temporal 0.734991;
  ratio 1.04544
Validation recursive rate NRMSE at 0.1/0.5/1.0/2.0 s:
  0.28775 / 0.72892 / 0.91946 / 1.13742
Residual lag-1 correlation: 0.759397 (colored limitation persists)
Decision: strong independent comparability evidence, but formal model PASS is
          not claimed because no numeric training/validation ratio was frozen
          before this run. Reclassify this run as validation-metric design
          evidence rather than retrospectively creating a threshold.
Frozen future confirmation gate: configs/rich_R3_pitch_validation_gate.json
  qdot NRMSE ratio <=1.15; recursive mean NRMSE ratio <=1.15;
  |residual lag-1| <=0.85; execution and richness PASS; no refit/reselection;
  one new fresh-reload confirmation required
Static/offline tests: 49 PASS
Next allowed action: fresh clean R3 reload and one new pitch confirmation with
the unchanged model, waveform, controller, limits, and frozen gate. Roll stays blocked.
```

R3 final pitch confirmation PASS and roll observe re-audit, 2026-07-12 18:33:

```text
Pitch confirmation log: logs/rich_R3_pitch_confirmation_01_revised_20260712_183326.csv
Execution / richness / frozen model gate: PASS / PASS / PASS
Rows / maximum gap / engagement: 600 / 0.101966531 s / 100 percent
Excitation peak / realized-input correlation: 0.000919317 /
                                                0.999999999902
Input spectral SNR: 4.837 / 17.939 / 20.415 / 22.152
Q-response spectral SNR: 18.161 / 31.746 / 23.807 / 26.964
Distributed elevator motion/correlation: 0.051939 deg peak-to-peak /
                                         -0.9999999999
Latch / abort / saturation / recovery: none / none / none / zero
Both overrides restored: PASS
Confirmation artifacts:
  configs/rich_R3_pitch_confirmation_01_richness.json
  configs/rich_R3_pitch_confirmation_01_model_score.json
Frozen model qdot ratio: 0.997618 <=1.15 PASS
Frozen model recursive ratio: 0.969405 <=1.15 PASS
Frozen model residual lag-1: 0.594161 <=0.85 PASS
No refit/reselection: PASS
Decision: R3 pitch identification/model validation PASS for the declared
          local short-horizon predictor at R3. Colored residuals and the lack
          of full expanded-state dynamics remain explicit limitations. This is
          not LQR flight validation or authorization for new synthesis.

Corrected-logger roll observe log: logs/rich_R3_roll_observe_20260712_183504.csv
Rows / max gap / active samples: 600 / 0.101057353 s / 399
Hypothetical excitation peak: 0.000132380; selected amplitude 0.0002
Exact frequency/waveform, timing, corrected rich channels, start, safety,
latch, recovery, and saturation gates: PASS
Controls sent / ownership changes: none / none
Decision: R3 Roll Training Run 1 is authorized after a fresh clean R3 reload.
          Roll validation remains blocked pending training analysis/model freeze.
```

R3 Roll Training Run 1 accepted, 2026-07-12 18:40:

```text
Output log: logs/rich_R3_roll_training_01_20260712_184050.csv
Execution analyzer: scripts/analyze_rich_r3_excitation_observe.py
Richness analyzer/artifact: scripts/analyze_rich_r3_roll_training.py /
                            configs/rich_R3_roll_training_01_analysis.json
Captured trim: CTRL0 +0.146462; CTRL1 +0.000462229
Start / engagement / safety / restoration: PASS / 100 percent / PASS / PASS
Rows / maximum gap: 600 / 0.102312250 s
Active excitation samples / peak: 399 / 0.000132373
Sent-to-realized roll correlation at one-sample lag: 0.99999999999999
Latch / abort / recovery / saturation: none / none / zero / none
Realized roll-input spectral SNR at 0.10/0.20/0.35/0.55/0.80/1.10 Hz:
  2.432 / 13.916 / 16.615 / 33.628 / 39.180 / 53.933 PASS
P-response spectral SNR:
  8.817 / 21.836 / 17.208 / 34.330 / 24.010 / 35.404 PASS
Distributed/primary ailerons moved 0.008485 deg peak-to-peak with absolute
correlation 0.99999999999998 to total roll input: PASS
Static/offline tests: 50 PASS
Decision: accepted as R3 roll training evidence. Do not collect or inspect the
          held-out roll validation run until training-only roll state selection,
          delay, coefficients, recursive prediction, and model gate are frozen.
Next allowed action: offline training-only roll candidate/model fitting.
```

R3 roll training-only model and preflight gate freeze, 2026-07-12:

```text
Model implementation/artifact: scripts/identify_rich_r3_roll.py /
                               configs/rich_R3_roll_model.json
Inputs opened: rich_R3_roll_training_01_20260712_184050.csv only
Validation files opened: none
Candidate families: local roll/P/control; beta/TAS aerodynamic; coupled
  Q/R/alpha; measured distributed-aileron aerodynamic/coupled
Candidate delays: 0, 1, 2, 3, 4 samples; 25 total candidates
Selection: opposite 10--30 / 30--50 s temporal holdouts with recursive
  0.1/0.5/1.0/2.0-s rate prediction and scaled condition <1e4
Selected predictor: surface_aerodynamic
Fields: [roll, P, beta, TAS, distributed_ail1_wing2l]
Additional input delay: zero samples because measured surface deflection is the
  realized downstream actuator state, not the upstream total-control request
Beta: [-6.714388844, -3.867418497, 73.701725853, 0.471343322,
       7.900878479]
Training pdot RMSE / NRMSE: 0.0208716 deg/s^2 / 0.621611
Bidirectional temporal one-step NRMSE: 0.662599
Bidirectional recursive-horizon mean NRMSE: 0.713522
Residual lag-1 correlation: 0.774853 (colored; limitation retained)
Scaled condition number: 47.488
Claim boundary: short-horizon pdot/rate predictor only; not full expanded-state
  dynamics and not authorization for LQR synthesis/flight.
Preflight gate: configs/rich_R3_roll_validation_gate.json
  pdot NRMSE ratio <=1.25; recursive mean ratio <=1.25;
  |residual lag-1| <=0.90; execution/richness PASS; no refit/reselection
Static/offline tests: 51 PASS
Decision: one held-out Roll Validation Run 1 is authorized after a fresh clean
          R3 reload with unchanged waveform/controller/limits/analyzers.
```

R3 held-out Roll Validation Run 1 — model FAIL, 2026-07-12 18:52:

```text
Output log: logs/rich_R3_roll_validation_01_20260712_185227.csv
Execution / richness: PASS / PASS
Rows / max gap / engagement: 600 / 0.100896434 s / 100 percent
Excitation peak / realized-input correlation: 0.000132376 / 1.0000000000
Input spectral SNR: 3.336 / 12.601 / 15.227 / 33.678 / 40.310 / 52.701
P-response spectral SNR: 9.851 / 19.668 / 18.323 / 31.883 / 24.206 / 34.439
Aileron motion/correlation: 0.008476 deg peak-to-peak / abs 1.0000000000
Latch / abort / saturation / recovery: none / none / none / zero
Both overrides restored: PASS
Artifacts:
  configs/rich_R3_roll_validation_01_richness.json
  configs/rich_R3_roll_validation_01_model_score.json
Frozen no-refit model results:
  pdot NRMSE ratio 1.17112 <=1.25 PASS
  recursive mean NRMSE ratio 8.65371 >1.25 FAIL
  residual lag-1 0.771848 <=0.90 PASS
Recursive validation rate RMSE/NMRSE at 0.1/0.5/1.0/2.0 s:
  0.002415/0.4225, 0.023788/4.1623, 0.054152/9.4754,
  0.060797/10.6382
Decision: held-out roll model validation FAIL. Do not relax the threshold,
          refit on validation, collect a repeat, advance roll, or claim Stage-5
          completion. Execution and spectral richness remain useful evidence.
Post-failure offline diagnosis: all 25 training-fitted candidates fail held-out
  recursive prediction; the selected surface/aerodynamic model remains the
  least poor at mean NRMSE 6.1746. This is cross-reload time-domain model
  inadequacy, not an isolated selection mistake.
Next allowed action: offline redesign of the roll identification claim toward
  frequency-response/FRF estimation or a multi-run stochastic model that can
  represent reload variability, without increasing the 0.0002 excitation or
  widening safety limits. No further live roll collection is authorized yet.
```

R3 roll FRF redesign and pre-confirmation gate freeze, 2026-07-12:

```text
Implementation: scripts/analyze_rich_r3_roll_frf.py
Training reference: configs/rich_R3_roll_frf_reference.json
Metric-design comparison: configs/rich_R3_roll_frf_metric_design.json
Frozen gate: configs/rich_R3_roll_frf_gate.json
Inputs: accepted roll training log and failed time-domain validation log;
        no new flight and no refit of the failed predictor
Method: simultaneous harmonic regression over the steady 12..48 s window;
        complex FRF = P harmonic / realized total-roll harmonic
Training-to-validation magnitude ratios at 0.10/0.20/0.35/0.55/0.80/1.10 Hz:
  0.719 / 0.982 / 1.137 / 0.930 / 0.986 / 1.003
Phase differences (deg):
  +21.34 / -23.74 / +1.61 / -1.80 / +0.77 / -2.09
Decision: 0.10 and 0.20 Hz are excluded from the repeatable FRF claim because
          low-frequency magnitude/phase are not consistent across reloads.
          The 0.35--1.10 Hz response is a viable confirmation candidate.
Frozen future FRF gate, declared before new data:
  frequencies 0.35/0.55/0.80/1.10 Hz only
  validation/training magnitude ratio 0.80..1.25
  absolute phase difference <=10 deg
  realized-input SNR >=2 and P-response SNR >=5
  execution/richness PASS; training reference fixed; one fresh confirmation
Static/offline tests: 52 PASS
Claim boundary: repeatable local mid-frequency closed-loop roll FRF, not a
  validated recursive time-domain model and not authorization for LQR synthesis.
Next allowed action: one fresh-reload roll FRF confirmation with the unchanged
waveform, 0.0002 amplitude, controller, and safety limits. No other roll flight.
```

R3 roll FRF confirmation PASS, 2026-07-12 19:04:

```text
Output log: logs/rich_R3_roll_frf_confirmation_01_20260712_190405.csv
Execution / richness / frozen FRF gate: PASS / PASS / PASS
Rows / max gap / engagement: 600 / 0.101944085 s / 100 percent
Excitation peak / realized-input correlation: 0.000132373 /
                                                0.99999999999999
Input spectral SNR: 2.283 / 12.145 / 15.182 / 33.393 / 39.085 / 51.931
P-response spectral SNR: 9.381 / 22.663 / 17.444 / 32.848 / 23.627 / 34.416
Aileron motion/correlation: 0.008053 deg peak-to-peak / abs 1.0000000000
Latch / abort / saturation / recovery: none / none / none / zero
Both overrides restored: PASS
Artifacts:
  configs/rich_R3_roll_frf_confirmation_01_richness.json
  configs/rich_R3_roll_frf_confirmation_01_score.json
Frozen mid-frequency gate results at 0.35/0.55/0.80/1.10 Hz:
  magnitude ratios 1.1348 / 0.9813 / 0.9785 / 1.0185 PASS (0.80..1.25)
  phase differences -1.686 / +0.053 / +1.786 / -0.868 deg PASS (<=10)
Training reference unchanged / no refit: PASS
Decision: R3 roll mid-frequency closed-loop FRF validation PASS for 0.35--1.10 Hz.
  The 0.10/0.20 Hz band remains excluded, and the recursive time-domain roll
  model remains failed. This does not validate a roll LQR or complete Stage 5.
Next allowed action: offline low-order stable state-space/uncertainty realization
  from the validated FRF, with explicit rejection if it cannot also respect the
  failed time-domain evidence. No additional live roll run is authorized yet.
```

R3 roll stable-realization audit — REJECTED for LQR, 2026-07-12:

```text
Implementation/artifact: scripts/fit_rich_r3_roll_frf_realization.py /
                         configs/rich_R3_roll_frf_realization.json
Inputs: fixed training FRF and passed FRF confirmation; 0.35--1.10 Hz only
Candidates: static gain, stable first-order rate model, stable second-order model
Method: deterministic NumPy grid search with analytical optimal gain; no SciPy
Joint static fit: gain 104.94; relative complex RMSE 0.08183
Joint first-order fit: gain 105.03; tau 0.00635 s; pole -157.4 rad/s;
                       relative complex RMSE 0.07624
Joint second-order fit: gain 103.82; wn 41.36 rad/s; zeta 0.20;
                        relative complex RMSE 0.07231
Separate second-order fits: training wn 35.87 rad/s; confirmation 47.69 rad/s;
                            damping hits the lower search boundary in both
Decision: REJECTED FOR STATE-SPACE LQR. The apparent dynamics occur on roughly
  6--28 ms scales, well below the 0.1-s sample interval, and parameters shift
  materially between logs. A good four-point FRF interpolation is not a
  sample-resolved dynamic realization and cannot override the failed recursive
  time-domain evidence.
Retained claim: bounded empirical FRF only in 0.35--1.10 Hz.
Static/offline tests: 53 PASS
Next allowed action: offline design of a reduced-channel high-rate read-only
  diagnostic capable of resolving total roll, distributed aileron, P, and
  timing above the suspected bandwidth. No engaged high-rate excitation is
  authorized until read-only timing/noise/aliasing gates are frozen and passed.
```

R3 reduced-channel high-rate read-only gates, 2026-07-12 19:15:

```text
Runner/analyzer: scripts/run_rich_r3_roll_highrate_observe_xp12.py /
                 scripts/analyze_rich_r3_roll_highrate_observe.py
Channels: one batched read of altitude/attitude/IAS, P/P_dot/Q/R, yoke and
  total roll, distributed aileron indices, roll moment, artificial stability,
  overrides, pause/speed/replay; structurally no control-send path
Static verification: shell syntax, compilation, 54 offline tests PASS

50-Hz attempt: logs/rich_R3_roll_highrate_observe_20260712_191444.csv
Rows / effective rate: 497 / 49.6608 Hz PASS
Mean / max acquisition: 0.019516 / 0.061338 s
Maximum gap: 0.061479 s > frozen 0.050 s FAIL
Decision: preserve as failed timing evidence. Acquisition consumes nearly the
          full 20-ms period; do not use 50 Hz for an engaged design.

Offline redesign: 40 Hz, 400 nominal samples, >=99-percent completeness,
  39--41 Hz mean, maximum gap <=0.0625 s (2.5 periods). Nyquist 20 Hz remains
  above the suspected ~6.6-Hz FRF-fit mode. No safety or ownership gate changed.
40-Hz log: logs/rich_R3_roll_highrate_observe_20260712_191558.csv
Rows / effective rate: 400 / 40.0081 Hz
Mean / max dt: 0.0249949 / 0.0599675 s
Mean / max acquisition: 0.0153176 / 0.0597526 s
Completeness, timing, finite data, array values, live state, ownership clear,
artificial stability, safety, and observe-only gates: PASS
P range: -0.004751..-0.001627 deg/s
P_dot range: -0.04799..+0.05113 deg/s^2
Finite-difference P_dot vs X-Plane P_dot correlation: -0.0573 in near-steady
noise; not an acceptance failure, but derivative/filtering remains unresolved.
Decision: reduced-channel 40-Hz read-only acquisition is feasible. No engaged
high-rate excitation is authorized yet.
Next allowed action: offline high-rate excitation and derivative/filter design,
including aliasing/noise gates and unchanged 0.0002 roll amplitude/safety limits,
followed by another exact observe-only waveform audit.
```

R3 high-rate waveform design and observe gates, 2026-07-12 19:21:

```text
Design: configs/rich_R3_roll_highrate_design.json
Waveform/logger/analyzer: scripts/run_rich_r3_roll_highrate_observe_xp12.py /
  scripts/run_rich_r3_roll_highrate_observe.sh /
  scripts/analyze_rich_r3_roll_highrate_waveform.py
Derivative policy: P_dot audit-only; identification uses measured P, realized
  total roll, and distributed aileron directly
Amplitude/safety: unchanged 0.0002 / 10-deg attitude / 20-deg/s body rate

Initial 40-Hz design: 2/4/6/8/10/12 Hz; Nyquist 20 Hz; 30 s
Log: logs/rich_R3_roll_highrate_waveform_observe_20260712_192007.csv
Rows / effective rate: 1200 / 40.0015 Hz
Exact waveform, no controls, live/ownership/safety: PASS
Maximum gap: 0.065948 s > frozen 0.0625 s FAIL
Decision: retain as failed timing evidence; do not engage at 40 Hz.

Offline redesign before new data: 35 Hz; frequencies 2/4/6/8/10 Hz;
  Nyquist 17.5 Hz; max frequency 57.1 percent of Nyquist; 1050 nominal rows;
  maximum gap 0.0714286 s; unchanged amplitude/safety
Static verification: compilation, shell syntax, 55 tests PASS
Passing observe log: logs/rich_R3_roll_highrate_waveform_observe_20260712_192142.csv
Rows / effective rate / max gap: 1050 / 34.9995 Hz / 0.0658838 s
Active samples / peak hypothetical excitation: 699 / 0.000190152
Waveform reconstruction error: zero
Completeness, timing, exact waveform, window, amplitude, Nyquist, finite data,
live state, ownership clear, safety, and observe-only gates: PASS
Decision: 35-Hz reduced-channel waveform acquisition is feasible. No engaged
pilot is authorized yet because the original backstepping stabilizer must remain
at its validated 10-Hz update rate; running it at 35 Hz would change the baseline.
Next allowed action: offline dual-rate runner design with 35-Hz acquisition and
excitation, 10-Hz original backstepping updates/holds, latched excitation abort,
unchanged ownership/restoration, and static/observe-only verification.
```

Dual-rate runner preparation and observe attempt 1, 2026-07-12 19:26:

```text
Runner/wrapper/analyzer: scripts/run_rich_r3_roll_dualrate_xp12.py /
  scripts/run_rich_r3_roll_dualrate_observe.sh /
  scripts/analyze_rich_r3_roll_dualrate_observe.py
Architecture: 35-Hz one-batch acquisition and held excitation; original
  backstepping state/output updates only at 10 Hz and held between updates
Default: observe-only; explicit --engage required
Engaged safety design: both axes owned/restored; excitation permanently latches
  to zero on attitude/rate/simulator violation while backstepping remains active
Static verification: compilation, shell syntax, 56 tests PASS
Observe log: logs/rich_R3_roll_dualrate_observe_20260712_192601.csv
Controls sent / ownership changes: none / none
Rows / effective rate / max gap: 1050 / 35.0024 Hz / 0.0645607 s PASS
Backstepping updates: 300 exactly; baseline held between updates PASS
Waveform reconstruction error / peak: zero / 0.000196336 PASS
Timing, completeness, schedule, holds, waveform, amplitude, live state,
ownership clear, safety, finite data, and no latch: PASS
Frozen R3 start gate: FAIL — altitude, roll, and body rate outside envelope
Decision: observe attempt rejected; mechanical dual-rate evidence retained but
          no engaged pilot authorized. Do not widen the start gate.
Next allowed action: fresh clean R3 reload and repeat this exact observe-only
dual-rate gate. Engagement remains blocked until that saved log passes.
```

Dual-rate observe retry PASS and engaged-pilot tooling, 2026-07-12 19:30:

```text
Observe log: logs/rich_R3_roll_dualrate_observe_20260712_193051.csv
Controls sent / ownership changes: none / none
Frozen R3 start gate: PASS; no reasons
Rows / effective rate / max gap: 1050 / 35.0015 Hz / 0.0645136 s
Original backstepping updates: 300; held exactly between updates PASS
Excitation peak / waveform error: 0.000190185 / zero
Completeness, timing, mean rate, schedule, holds, waveform, amplitude,
engagement state, no latch, start, ownership clear, live state, safety, finite
data: PASS
Engaged wrapper: scripts/run_rich_r3_roll_dualrate_pilot.sh
Engaged analyzer extension requires 100-percent engagement/control sends,
  override ownership after first sample, >=0.99 one-sample sent-to-realized
  correlation, unchanged schedule/waveform/timing/safety, no latch, and restoration
Static verification: shell syntax, compilation, 56 tests PASS
Decision: exactly one dual-rate engaged design pilot is authorized after a fresh
          clean R3 reload. It is design evidence only, not LQR validation.
          No repeat or higher amplitude is authorized without analysis.
```

Dual-rate engaged roll pilot — realization FAIL, 2026-07-12 19:34:

```text
Output log: logs/rich_R3_roll_dualrate_pilot_20260712_193416.csv
Start / engagement / safety / ownership restoration: PASS / 100 percent /
  PASS / PASS
Rows / effective rate / max gap: 1050 / 35.00325 Hz / 0.0623583 s
Original backstepping updates / holds: 300 / PASS
Excitation peak / waveform error: 0.000197750 / zero
Latch / abort: none / none
Frozen sent-to-total-roll one-sample correlation: 0.850546 <0.99 FAIL
Decision: pilot rejected under the predeclared realization gate. Do not repeat,
          relax the gate, increase amplitude, or use it as validation evidence.

Offline diagnosis using the rejected design pilot:
  sent command -> yoke_roll correlation at one sample: 0.99999999999999;
    RMS mismatch 1.03e-11 (command write path is correct)
  sent command -> total_roll correlations at 0/1/2 samples:
    0.540 / 0.851 / 0.909; no lag reaches 0.99
  approximate total-roll / injected-excitation gain and phase:
    2 Hz 1.375 / +32.2 deg
    4 Hz 1.082 / +73.5 deg
    6 Hz 0.861 / +103.0 deg
    8 Hz 0.647 / +127.3 deg
    10 Hz 0.555 / +169.1 deg
  approximate P / total-roll gain and phase:
    2 Hz 100.3 / +7.3 deg; 4 Hz 84.9 / +20.1 deg;
    6 Hz 77.2 / +24.9 deg; 8 Hz 78.2 / +32.0 deg;
    10 Hz 78.6 / +41.3 deg
Interpretation: X-Plane accepts the high-rate yoke command, but artificial
  stability/control-path dynamics substantially reshape the realized total-roll
  input above the previously validated band. This explains why a yoke-command
  model cannot be treated as the plant input and why the 10-Hz realization was
  unidentifiable.
Next allowed action: offline augmentation/control-path model redesign using
  yoke command -> total roll -> distributed surface -> P as a cascaded system.
  P_dot remains audit-only. No further high-rate flight is authorized yet.
```

High-rate cascaded continuous-time realization audit, 2026-07-12:

```text
Implementation/artifact: scripts/fit_rich_r3_roll_highrate_cascade.py /
                         configs/rich_R3_roll_highrate_cascade.json
Source: rejected dual-rate pilot used as design evidence only
Frequencies/window: 2/4/6/8/10 Hz; steady 7..23 s
Method: simultaneous harmonic regression; physical complex FRFs for
  yoke -> total roll -> distributed aileron -> P; stable signed-gain
  first-order-plus-delay grid fits; exact cascade-closure audit
Yoke -> total roll fit: gain 1.146; tau 0.02659 s; delay 0;
  pole -37.61 rad/s; relative complex RMSE 0.09287
Total roll -> surface fit: gain 30.0000; tau at 0.001-s grid boundary;
  delay 0; relative complex RMSE 0.04162; measured stage essentially static
Surface -> P fit: gain 3.1637; tau 0.01131 s; delay 0.002 s;
  pole -88.41 rad/s; relative complex RMSE 0.06415
Cascade complex closure error: <4e-16 at every frequency
Decision: REJECTED FOR CONTINUOUS-TIME/STATE-SPACE LQR. All fitted dynamic time
  constants are at or below the 35-Hz sample period of 0.02857 s. Good harmonic
  fit and exact algebraic closure do not prove sample-resolved poles.
Static/offline tests: 57 PASS
Next allowed action: offline directly discrete-time cascade/ARX identification
  at 35 Hz with temporal holdouts, stability, order/delay selection, and no
  continuous-time pole inference. No new flight until that model and numeric
  confirmation gate are frozen.
```

R3 discrete 35-Hz cascade and confirmation gate freeze, 2026-07-12:

```text
Identification/artifact: scripts/identify_rich_r3_roll_discrete_cascade.py /
                         configs/rich_R3_roll_discrete_cascade.json
Source: rejected dual-rate pilot used as design/training evidence only
Validation files opened: none
Candidates per dynamic stage: ARX na=1..3, nb=1..3, delays 0..3; 36 each
Selection: stable discrete poles and condition <1e4 in full/opposite temporal
  folds; recursive 1/5/10/20-sample NRMSE; lowest order within 2.5 percent of
  best score
Selected yoke -> total: ARX(1,2), delay 0; beta
  [0.0560948, 0.3768872, 0.5983455]; pole 0.056095;
  temporal recursive mean NRMSE 0.472589; both folds stable
Selected total -> surface: static gain 30.00000017; relative RMSE 1.20e-7
Selected surface -> P: ARX(1,1), delay 0; beta [0.4085609, 2.1139128];
  pole 0.408561; temporal recursive mean NRMSE 0.316348; both folds stable
Claim boundary: directly discrete measured cascade at 35 Hz; no continuous-time
  pole inference and not yet LQR validation.
Confirmation gate: configs/rich_R3_roll_discrete_cascade_gate.json
  yoke->total and surface->P recursive NRMSE ratios <=1.25
  total->surface relative RMSE <=0.01
  sent->yoke one-sample correlation >=0.99
  execution/timing/schedule/safety PASS; no refit/reselection
Confirmation wrapper/scorer:
  scripts/run_rich_r3_roll_dualrate_confirmation.sh
  scripts/validate_rich_r3_roll_discrete_cascade.py
Static/offline tests: 58 PASS
Decision: exactly one fresh-reload dual-rate confirmation is authorized under
  the new cascaded-input claim. The earlier yoke==total gate remains failed and
  is not relaxed or reinterpreted.
```

R3 discrete 35-Hz cascade confirmation PASS, 2026-07-12 19:45:

```text
Output log: logs/rich_R3_roll_dualrate_confirmation_20260712_194543.csv
Execution/schedule/safety gate: PASS under cascaded-input claim
Rows / effective rate / max gap: 1050 / 35.00197 Hz / 0.0610238 s
Original backstepping updates / holds: 300 / PASS
Excitation peak / waveform error: 0.000190092 / zero
Start / engagement / latch / restoration: PASS / 100 percent / none / PASS
Legacy yoke==total one-sample correlation: 0.9060 (not claimed; prior failure retained)
Cascade score: configs/rich_R3_roll_discrete_cascade_confirmation_score.json
No refit or reselection: PASS
Yoke -> total recursive mean NRMSE: training 0.472589;
  confirmation 0.516035; ratio 1.09193 <=1.25 PASS
Surface -> P recursive mean NRMSE: training 0.316348;
  confirmation 0.351282; ratio 1.11043 <=1.25 PASS
Total -> surface relative RMSE: 6.38e-8 <=0.01 PASS
Sent -> yoke one-sample correlation: 1.0000000000 >=0.99 PASS
Decision: R3 directly discrete 35-Hz measured cascade validation PASS for the
  declared yoke -> total roll -> distributed surface -> P structure. This does
  not validate an LQR or continuous-time realization.
Static/offline tests: 59 PASS
Next allowed action: offline construction of the exact augmented discrete-state
  model including roll angle integration, upstream ARX memory/direct feedthrough,
  surface mapping, and P dynamics; then controllability, uncertainty, limits,
  and saved-log replay. No new flight authorized yet.
```

R3 discrete-cascade rate-LQR offline synthesis/replay, 2026-07-12:

```text
Synthesis/artifact: scripts/synthesize_rich_r3_roll_discrete_lqr.py /
                    configs/rich_R3_roll_discrete_lqr.json
Exact runtime/replay: lqr/discrete_cascade_roll_lqr.py /
                      scripts/replay_rich_r3_roll_discrete_lqr_runtime.py /
                      configs/rich_R3_roll_discrete_lqr_runtime_replay.json
State: [P error, total-roll perturbation, previous-yoke perturbation]
Input: next yoke perturbation at 35 Hz
Angle feedback: exactly zero
Discrete A:
  [[0.4085609, 3.5573847, 37.9455093],
   [0,         0.0560948,  0.5983455],
   [0,         0,          0        ]]
Discrete B: [[23.9012009], [0.3768872], [1]]
Controllability: rank 3/3
Fixed command/slew limits: 0.0002 / 0.00005 per 35-Hz sample
Offline rate-scale candidates: 0.01/0.02/0.03/0.05/0.10 deg/s
Selection: smallest candidate with zero raw saturation on both saved-log replays
Selected rate scale: 0.05 deg/s
K: [0.0002943999, 0.0027424435, 0.0292527861]
Nominal closed-loop poles: 0.368385, 0.058948, 0
Nominal spectral radius: 0.368385
Coefficient uncertainty: all combinations of 0.75/1.0/1.25 across five
  dynamic coefficients; 243 cases; worst radius 0.493595; unstable 0
Matched +/-0.005 and +/-0.010 deg/s P disturbances: zero saturation and converge
Exact runtime replay:
  design pilot peak command 0.00004478; zero magnitude/slew limiting
  confirmation peak command 0.00013052; zero magnitude limiting; two slew limits
Static/offline tests: 62 PASS
Decision: PASS for offline rate-only candidate synthesis, uncertainty, limits,
  exact runtime, and replay. No LQR flight is authorized.
Next allowed action: integrate this exact runtime into a default-observe-only
  roll-rate runner with captured trim, zeroed perturbation state, original pitch
  backstepping stabilization, and permanent fallback to original roll
  backstepping; pass exact observe-only state/history/timing gates before flight.
```

R3 discrete-cascade roll-LQR observe-only integration, 2026-07-12 19:57:

```text
Runner/wrapper: scripts/run_rich_r3_roll_lqr_observe_xp12.py /
                scripts/run_rich_r3_roll_lqr_observe.sh
Analyzer: scripts/analyze_rich_r3_roll_lqr_observe.py
Output log: logs/rich_R3_roll_lqr_observe_20260712_195722.csv
Control-write path: structurally absent; controls_sent=0 for every sample
Rows / effective rate / max gap: 1050 / 35.00255 Hz / 0.0641102 s
Original fallback updates / hold audit: 300 / PASS at 10 Hz
Captured initial P/total-roll/yoke perturbations and initial command: all zero
Exact sample-by-sample runtime replay maximum error: 0
Peak absolute hypothetical LQR command / maximum slew:
  2.40853e-6 / 8.42401e-7
Fixed command/slew bounds: PASS; no limiting required
Start envelope, live state, ownership, safety, finite data: PASS
Fallback latch: none; original roll/pitch backstepping remained hypothetical
Static/offline tests after analyzer serialization repair: 63 PASS
Decision: PASS for exact observe-only integration, initialization, scheduling,
  runtime identity, bounds, fallback audit, and safety. This is not an engaged
  LQR flight result and does not complete Stage 5.
Next allowed action: offline/static implementation and review of a dedicated
  default-observe engaged-capable pilot runner. It must retain original pitch
  backstepping, permanent latched roll-backstepping fallback, unchanged
  0.0002 command and 0.00005/sample slew limits, start/abort/restoration gates,
  and require explicit engagement. No engaged flight until that runner and its
  analyzer pass static tests and preflight review.
```

R3 discrete-cascade roll-LQR engaged-pilot preflight freeze, 2026-07-12:

```text
Guarded runner/wrapper: scripts/run_rich_r3_roll_lqr_pilot_xp12.py /
                        scripts/run_rich_r3_roll_lqr_pilot.sh
Strict analyzer: scripts/analyze_rich_r3_roll_lqr_pilot.py
Default mode: observe-only; --engage is mandatory for control writes
I/O / fallback schedule: 35 Hz / original backstepping at 10 Hz with hold
Pitch control: original backstepping throughout
Roll control: exact frozen discrete-cascade LQR; unchanged perturbation command
  limit 0.0002 and slew limit 0.00005 per sample
Safety: existing start and abort envelopes unchanged
Fallback: any abort or non-finite LQR output permanently latches original roll
  backstepping for the remainder of the run; automatic re-engagement absent
Restoration: trim yokes and both override datarefs restored in finally; explicit
  post-run override/yoke readback recorded and required by analyzer
Analyzer additionally requires exact runtime replay, exact command selection,
  monotonic latch, no latch for a validation PASS, timing/schedule, initial zero
  state, engagement, bounds, live state, ownership, safety, and finite data.
Static verification: Python compile PASS; shell syntax PASS; CLI/default audit
  PASS; 65 tests PASS.
Decision: preflight implementation/static review PASS. This is not flight
  evidence and Stage 5 remains current.
Next allowed action: fresh clean R3 reload, verify the start state, then exactly
  one 30-second engaged pilot using `bash scripts/run_rich_r3_roll_lqr_pilot.sh`.
  Analyze with `scripts/analyze_rich_r3_roll_lqr_pilot.py --require-engaged`.
  Do not repeat, raise limits, or retune based on the run without first recording
  its result and returning to offline analysis.
```

R3 discrete-cascade roll-LQR first engaged pilot, 2026-07-12 20:07:

```text
Exact command: bash scripts/run_rich_r3_roll_lqr_pilot.sh
Output log: logs/rich_R3_roll_lqr_pilot_20260712_200705.csv
Frozen analyzer command:
  backstepping/ehekatl_xplane12_backstepping_bridge/.venv/bin/python -B
  scripts/analyze_rich_r3_roll_lqr_pilot.py --require-engaged
  logs/rich_R3_roll_lqr_pilot_20260712_200705.csv
Rows / effective rate / max gap: 1050 / 35.00247 Hz / 0.0649988 s
Original fallback updates / hold audit: 300 / PASS
Start gate / engagement / live state / safety: PASS / PASS / PASS / PASS
Fallback latch: none
Exact runtime replay maximum error: 0
Peak LQR perturbation command / maximum slew:
  4.08479e-7 / 3.16962e-7; both far inside unchanged limits
Initial perturbation/history state: exactly zero
Ownership: both axes initially clear; both override readbacks zero after exit;
  roll and pitch yoke restoration errors exactly zero
State excursion: P-error range -0.0007956..+0.0014199 deg/s;
  roll range -0.004462..+0.010470 deg
All frozen analyzer checks: PASS
Decision: PASS for safe engaged integration, exact implementation, scheduling,
  fallback availability, bounds, and restoration. Because the run contained no
  declared disturbance and only a 0.00142-deg/s peak P error, it is not evidence
  of disturbance rejection, damping improvement, or Stage-5 performance.
Do not repeat this quiescent pilot or reinterpret it as performance validation.
Next allowed action: offline-only freeze of a small matched roll-disturbance
  experiment and quantitative LQR-versus-original-backstepping comparison using
  the validated cascade, unchanged limits/envelopes, and one future fresh-reload
  confirmation. No further flight until waveform, metric, gates, and wrapper are
  frozen and statically audited.
```

R3 roll-LQR matched-disturbance offline freeze, 2026-07-12:

```text
Design script/artifact: scripts/design_rich_r3_roll_lqr_disturbance.py /
                        configs/rich_R3_roll_lqr_disturbance_design.json
Plant: validated 35-Hz discrete cascade plus roll-angle integration
Controllers: exact bounded LQR at 35 Hz versus original roll backstepping at
  10 Hz with hold; identical additive actuator-side disturbance
Uncertainty: 0.75/1.0/1.25 grid on five cascade coefficients; 243 cases
Rejected precursor 1: amplitude 0.0001, duration 0.5 s; worst peak ratio 1.269
  and integral ratio 0.832 failed performance gates.
Rejected precursor 2: amplitude 0.0001, duration 0.2 s; performance passed but
  combined controller-plus-disturbance slew 8.336e-5 exceeded 5e-5.
Frozen waveform: + then - half-sines at 10.0 and 12.0 s; duration 0.2 s each;
  amplitude 0.00005; injection after selected controller; no clipping allowed
Primary metric: integral |P| from 10 to 18 s, LQR/baseline <=0.70
Peak direct-response non-degradation guard: LQR/baseline <=1.10
Offline worst integral ratio: 0.576736 PASS
Offline worst peak ratio: 1.060749 PASS
Minimum baseline peak |P|: 0.002317 deg/s >=0.0015 PASS
Maximum sent command / sent slew: 4.9093e-5 / 4.1682e-5 PASS
Maximum LQR roll excursion: 0.001214 deg; no clipping; final-state gates PASS
Decision: offline waveform/model/uncertainty/metric freeze PASS. This is not
  flight performance evidence.
Next allowed action: implement a default-observe matched baseline/LQR runner and
  frozen paired scorer, then pass static and observe-only waveform audits. No
  engaged disturbance run is authorized yet.
```

R3 matched-disturbance runner freeze and observe attempt 1, 2026-07-12 20:21:

```text
Extended guarded runner: scripts/run_rich_r3_roll_lqr_pilot_xp12.py
Wrappers: scripts/run_rich_r3_roll_matched_observe.sh,
  scripts/run_rich_r3_roll_matched_baseline.sh,
  scripts/run_rich_r3_roll_matched_lqr.sh
Auditors: scripts/analyze_rich_r3_roll_matched_run.py and
  scripts/score_rich_r3_roll_matched_pair.py
Static compile/shell/default audit: PASS; 67 tests PASS
Observe log: logs/rich_R3_roll_matched_observe_20260712_202132.csv
No engagement and no controls sent: PASS
Rows/rate/max gap: 1050 / 35.00206 Hz / 0.0639122 s PASS
Exact waveform/runtime/selection, 300 fallback updates/holds, combined command
  magnitude/slew, no latch, live state, safety, finite data: PASS
Peak hypothetical sent perturbation / slew: 4.89778e-5 / 2.94721e-5 PASS
Start gate: FAIL solely because altitude was 1800.705 m, 100.705 m above the
  1700-m R3 target and 0.705 m outside the unchanged +/-100-m envelope.
Decision: FAIL as observe-gate evidence; mechanics pass but start state does not.
No control was sent. Do not widen the envelope or authorize engaged disturbance.
Next allowed action: fresh clean R3 reload and repeat this exact observe-only
  audit once. No code, waveform, metric, gain, or limit changes.
```

R3 matched-disturbance observe retry PASS, 2026-07-12 20:24:

```text
Exact command: bash scripts/run_rich_r3_roll_matched_observe.sh
Output log: logs/rich_R3_roll_matched_observe_20260712_202405.csv
Controls sent / engagement: none / observe-only
Rows / effective rate / max gap: 1050 / 35.00083 Hz / 0.0592489 s
Fallback updates/hold: 300 / PASS
Exact waveform error: 0
Peak hypothetical sent perturbation / maximum combined slew:
  4.89378e-5 / 2.17278e-5 PASS
Exact LQR runtime replay, selection, magnitude, slew, start, live state,
ownership, safety, finite data, and no-latch gates: all PASS
Decision: exact matched-disturbance observe-only gate PASS. No controls were sent;
this is mechanics evidence, not performance evidence.
Next allowed action: fresh clean R3 reload and exactly one engaged matched
original-backstepping baseline using
`bash scripts/run_rich_r3_roll_matched_baseline.sh`, followed by the frozen
per-run analyzer with `--mode baseline --require-engaged`. Do not run the LQR
member until the baseline passes and a second fresh reload is completed.
```

R3 matched original-backstepping baseline attempt 1 FAIL, 2026-07-12 20:26:

```text
Exact command: bash scripts/run_rich_r3_roll_matched_baseline.sh
Output log: logs/rich_R3_roll_matched_baseline_20260712_202634.csv
Rows / effective rate / max gap: 1050 / 35.00192 Hz / 0.0582124 s PASS
Start, engagement, schedule/hold, live state, safety, finite data, restoration:
  PASS
Failure at sample 0, t=0.001723 s: the original-backstepping command changed
  from captured yoke trim by -6.51206e-5, exceeding the unchanged 5e-5 combined
  slew limit. The guard permanently latched with `combined command limit
  exceeded`; both planned pulses were disabled (zero nonzero waveform samples).
Initial roll / P: 0.002101 deg / 0.001472 deg/s
Overrides and yokes restored exactly; no safety-envelope excursion.
Decision: FAIL as matched-baseline evidence. The guard behaved correctly, but
  the disturbance was never realized. Do not score, repeat, or run the LQR pair
  member. Do not relax the slew limit.
Next allowed action: offline redesign and static/observe audit of bounded startup
  transfer into original backstepping (or an equivalently justified clean-start
  method) while retaining the 5e-5 total slew limit and unchanged waveform.
```

R3 matched bounded-startup redesign and observe gate, 2026-07-12 20:29:

```text
Implementation: original backstepping still updates at 10 Hz; its requested
  perturbation is applied through the same fixed +/-0.0002 magnitude and
  0.00005-per-35-Hz-sample slew bounds used in the frozen offline simulation.
No gain, disturbance, safety envelope, or limit changed.
Full 243-case offline rerun: PASS; worst integral ratio 0.576736, worst peak
  ratio 1.060749, maximum total slew 4.16820e-5, no clipping.
Static compile/shell tests: PASS; 68 tests PASS.
Observe log: logs/rich_R3_roll_matched_observe_20260712_202948.csv
Rows/rate/max gap: 1050 / 35.00163 Hz / 0.0610806 s PASS
Exact waveform/runtime/selection, start, live state, no latch, safety: PASS
Peak hypothetical selected command / combined slew: 4.88096e-5 / 2.50397e-5
Bounded-baseline channel initial / peak / max slew:
  5e-5 / 0.0002 / 5.000000000000001e-5; PASS within 1e-15 numeric tolerance
Decision: bounded-startup offline/static/observe redesign PASS. No controls sent.
Next allowed action: fresh clean R3 reload and exactly one matched bounded
baseline retry using `bash scripts/run_rich_r3_roll_matched_baseline.sh`, then
the frozen `--mode baseline --require-engaged` audit. LQR member remains blocked
until that retry passes. Do not change or relax any gate.
```

R3 matched bounded original-backstepping baseline PASS, 2026-07-12 20:34:

```text
Exact command: bash scripts/run_rich_r3_roll_matched_baseline.sh
Output log: logs/rich_R3_roll_matched_baseline_20260712_203402.csv
Rows / effective rate / max gap: 1050 / 35.00381 Hz / 0.0581442 s
Start, engagement, 300 fallback updates/holds, exact waveform, selection,
runtime audit, no latch, live state, safety, finite data, restoration: PASS
Peak sent perturbation / maximum sent slew:
  0.0002 / 5.000000000000002e-5 PASS within numeric tolerance
Frozen baseline performance prerequisites:
  peak |P| over 10--18 s: 0.00551255 deg/s >=0.0015 measurable PASS
  integral |P| over 10--18 s: 0.00498162 deg
  final-five-second max |P|: 0.00156192 deg/s <=0.002 settled PASS
Decision: PASS as the frozen matched baseline member. Do not repeat or refit.
Next allowed action: fresh clean R3 reload and exactly one matched LQR member
using `bash scripts/run_rich_r3_roll_matched_lqr.sh`, followed by the frozen
per-run analyzer and paired scorer against this exact baseline file.
```

R3 matched roll-LQR member and paired score FAIL, 2026-07-12 20:37:

```text
Exact command: bash scripts/run_rich_r3_roll_matched_lqr.sh
LQR log: logs/rich_R3_roll_matched_lqr_20260712_203707.csv
Frozen baseline: logs/rich_R3_roll_matched_baseline_20260712_203402.csv
LQR rows / effective rate / max gap: 1050 / 34.98778 Hz / 0.0517758 s
LQR execution: exact waveform/runtime/selection, start, engagement, 300
  fallback updates/holds, limits, no latch, live state, safety, restoration PASS
LQR peak sent perturbation / maximum slew: 4.81753e-5 / 2.16519e-5 PASS
Frozen paired score, no refit or metric change:
  baseline peak |P| / integral |P| / final max |P|:
    0.00551255 deg/s / 0.00498162 deg / 0.00156192 deg/s
  LQR peak |P| / integral |P| / final max |P|:
    0.00489870 deg/s / 0.00442770 deg / 0.00144665 deg/s
  peak ratio 0.888644 <=1.10 PASS
  integral ratio 0.888807 >0.70 FAIL
  both final settling gates PASS
Decision: FAIL for the declared matched disturbance-performance claim despite
  safe and correct execution. The observed integral improvement is about 11.1%,
  materially below the frozen 30% requirement. Do not relax the gate, repeat
  either pair member, or claim Stage-5 roll performance validation.
Scorer deprecation-only change from np.trapz to np.trapezoid reproduces identical
numbers; 68 tests PASS.
Next allowed action: offline-only residual/trajectory diagnosis of the two
immutable pair logs versus the validated cascade and uncertainty predictions.
No new flight, gain increase, limit change, or Stage-6 advancement authorized.
```

R3 matched-pair offline residual/trajectory diagnosis, 2026-07-12:

```text
Script/artifact: scripts/diagnose_rich_r3_roll_matched_pair.py /
                 configs/rich_R3_roll_matched_pair_diagnosis.json
Immutable logs only; no refit, metric change, or new flight.
Command realization: sent-to-yoke one-sample correlation is effectively 1.0 in
  both runs; RMSE 8.75e-12 baseline and 8.34e-12 LQR. Not a routing failure.
Validated cascade one-step P residual over 10--18 s:
  baseline RMSE 0.000609 deg/s, NRMSE 0.06054
  LQR RMSE 0.000514 deg/s, NRMSE 0.05555
Thus the local measured cascade remains adequate at one step for both runs.
Pre-pulse P means differ by 0.001594 deg/s across reloads; pre-pulse standard
deviations are 0.000482 and 0.000553 deg/s.
Cumulative LQR/baseline integral-|P| ratio as quiet tail is included:
  through 12 s 0.7041; 14 s 0.7874; 16 s 0.8225; 18 s 0.8888
This monotonic degradation after the short pulses shows that reload-specific
background motion dominates the long 10--18-s integral comparison.
Baseline reached the fixed 0.0002 command bound for 25 samples; LQR reached it
for zero samples. The zero-state offline baseline history therefore did not
represent the flight baseline operating history, despite correct local plant
prediction and safe bounded execution.
Decision: frozen performance FAIL remains. The diagnosis does not authorize
post-hoc shortening of the window or reinterpret the 12-s ratio as a pass.
Static tests: 69 PASS.
Next allowed action: offline-only redesign of a matched-state/statistically
identifiable performance experiment that accounts for background variation and
bounded-baseline operating history before metrics are frozen. No new flight,
gain/limit change, or Stage-6 advancement yet.
```

R3 statistical matched-state experiment proposal, 2026-07-12:

```text
Script/artifact: scripts/design_rich_r3_roll_statistical_comparison.py /
                 configs/rich_R3_roll_statistical_comparison_design.json
Failed pair is used as design evidence only; frozen 0.8888/0.70 failure retained.
Local estimator: fit a linear P trend over 0.5 s before each pulse, subtract it
  over the next 1.0 s, sign-align positive/negative pulses, then average.
Retrospective design-only results:
  baseline sign-aligned peak/integral: 0.004810 deg/s / 0.00145452 deg
  LQR sign-aligned peak/integral: 0.005011 deg/s / 0.00132217 deg
  local integral ratio: 0.9090 (about 9.1-percent improvement)
  opposite-sign correlations: baseline 0.858, LQR 0.949
Two pulses per controller are insufficient for a confidence bound.
Proposed waveform: six alternating +/-0.00005, 0.2-s half-sines at
  7/10/13/16/19/22 s; unchanged 35-Hz I/O and all limits/envelopes.
Proposed primary gate: paired-pulse bootstrap 95-percent upper confidence bound
  for LQR/baseline sign-aligned integral ratio <1.0; quality gates include six
  pulses/run, correlation >=0.75, response SNR >=3, baseline peak >=0.0015,
  final settling, exact waveform, unchanged command/slew, safety/restoration.
Decision: offline metric/waveform proposal only; not flight authorized.
Static tests: 70 PASS.
Next required: moving-block bootstrap power audit from immutable background
residuals and 243-case repeated-waveform command/safety audit. Only after those
pass may wrappers and an observe-only gate be developed. No flight yet.
```

R3 six-pulse safety and prospective-power audits, 2026-07-12:

```text
Safety script/artifact: scripts/audit_rich_r3_roll_six_pulse_safety.py /
  configs/rich_R3_roll_six_pulse_safety_audit.json
All 243 coefficient cases, both controllers: PASS
Maximum sent command / slew: 4.87967e-5 / 4.16820e-5
Maximum roll / final-five-second |P|: 0.001214 deg / 2.997e-6 deg/s
Sent-limit exceedances: zero
Power script/artifact: scripts/audit_rich_r3_roll_statistical_power.py /
  configs/rich_R3_roll_statistical_power_audit.json
Method: deterministic moving-block residual bootstrap using immutable measured
background; 1000 virtual six-pulse experiments, 500 resamples each.
Median estimated ratio: 0.82073; 5--95-percent range 0.4673--1.5128
Median bootstrap upper 95-percent bound: 1.28261
Power for upper bound <1: 0.272 versus required 0.80: FAIL
Decision: six-pulse proposal is safe in the frozen model but statistically
underpowered and rejected for flight. Do not implement wrappers, collect data,
or weaken the confidence/power gates.
Next allowed action: offline-only pulse-count/power redesign or conclude that
the approximately 9-percent effect is not practically flight-identifiable under
the current separate-run protocol. No new flight or gain/limit change.
```

R3 pulse-count versus power conclusion, 2026-07-12:

```text
Script/artifact: scripts/audit_rich_r3_roll_pulse_count_power.py /
                 configs/rich_R3_roll_pulse_count_power.json
Method: same immutable moving-block residual source and upper-95-percent-bound
gate; independent controller resampling; 300 virtual experiments and 300
bootstrap resamples per tested count; required power 0.80.
Pulses/controller : minimum run seconds : median upper bound : power
  6  : 23 s  : 1.3067 : 0.293
  12 : 41 s  : 1.2678 : 0.203
  24 : 77 s  : 1.1909 : 0.190
  48 : 149 s : 1.1129 : 0.190
No tested count qualifies. Although the interval narrows, even 48 pulses and a
149-s minimum run remain unable to place the 95-percent upper ratio below 1 with
useful probability. Longer separate-run exposure is not justified for the
observed approximately 9--11-percent effect.
Decision: reject further separate-run pulse flight testing for this controller
candidate. Do not extrapolate, add repetitions, or collect longer flights.
Next allowed action: offline controller/model redesign aimed at a materially
larger robust effect while retaining existing gains/limits as the failed frozen
reference. No new flight, Stage-5 pass, or Stage-6 advancement authorized.
```

R3 propulsion operating-point coverage audit, 2026-07-12:

```text
Audit/artifact: scripts/audit_rich_r3_propulsion_operating_point.py /
                configs/rich_R3_propulsion_operating_point_audit.json
User-reported desired/current ACS indication: approximately 0.17
Existing propulsion-aware R3 evidence: three logs, all exactly 0.023529 throttle
  per engine; IAS 38.26--38.74 kt; dynamic pressure 235--244 Pa.
Coverage decision: FAIL. The current LQR cannot be claimed at 0.17 throttle.
High-rate matched logs contained IAS only and omitted throttle/thrust/TAS/density.
Instrumentation added read-only at 35 Hz: TAS, density, computed dynamic pressure,
  ENGN_thro, ENGN_thro_use, N1, and POINT_thrust for both engines.
Read-only snapshot: logs/rich_R3_propulsion_observe_20260712_205807.csv
  350 samples, mean 35.008 Hz, but max gap 0.0844 s: timing FAIL
  ENGN_thro both engines 0.023529 constant
  thrust 2.474 N/engine; IAS 29.92 kt; TAS 16.63 m/s; qbar 146.0 Pa
The live X-Plane datarefs do not reproduce a 0.17 realized throttle indication.
This may be a different ACS command/display or nonlinear mapping; do not assume.
Decision: no scheduled model can be fitted from current evidence. Resolve the
ACS-to-X-Plane throttle definition and pass a read-only timing/availability gate
at the actual steady operating point before any new identification or control.
No flight-control experiment authorized. Static tests: 73 PASS before adding
ENGN_thro_use/N1 channels; final regression count recorded separately.
```

Throttle-handle/engine mapping snapshot, 2026-07-12 21:03:

```text
Log: logs/rich_R3_throttle_mapping_observe_20260712_210356.csv
Read-only 100 samples at 10.0007 Hz; max gap 0.10051 s.
Simulator state: paused=1, sim_speed=0 throughout; not trim/flight evidence.
Standard X-Plane mappings at the paused snapshot:
  cockpit throttle handle 0.023529
  calibrated hardware throttle 0.0
  engine-used throttle ratio 0.025647
  legacy ENGN_thro / ENGN_thro_use 0.023529 / 0.025647
  POINT_thrust 2.166 N/engine; reported N1 97.656 percent
  IAS 36.98 kt; TAS 20.59 m/s; qbar 223.89 Pa
  pitch 0.397 deg; AOA 1.165 deg
None of the standard channels equals the reported cockpit 0.162 indication.
It may be a custom ACS/plugin value or different scale. Because the simulator
was paused and the hardware channel was zero, no causal throttle mapping is
established.
Decision: do not command more throttle based on the 0.162 interpretation. Use
measured IAS/qbar/AOA as the operating-point definition. Next allowed action is
an unpaused, steady, read-only mapping snapshot at the user's desired condition;
then choose R3 (~39 kt/~240 Pa) or a new R4 (~48 kt) identification campaign.
No existing R3 LQR may be reused at R4 without new model validation.
```

Unpaused throttle mapping and regime classification, 2026-07-12 21:12:

```text
Log: logs/propulsion_mapping_unpaused_20260712_211255.csv
Read-only: 100 samples, 10.0018 Hz, max gap 0.10031 s; paused=0, sim_speed=1.
Steady mapping:
  cockpit/ENGN_thro 0.389562
  engine-used/ENGN_thro_use 0.424623
  POINT_thrust 10.207 N per engine
  hardware throttle dataref 0 (not the active command source)
Flight state: IAS 129.237 kt; TAS 71.383 m/s; qbar 2702.83 Pa;
  altitude 1473.95 m; pitch -0.681 deg; AOA -0.546 deg.
Mapping conclusion: standard cockpit throttle and engine-used channels respond
and are suitable for scheduling. The earlier 0.023529 condition was a real low
throttle operating point; the unexplained 0.162 was not captured here.
Regime conclusion: 129 kt / 2703 Pa is far outside R3 (39 kt/~240 Pa) and R4
(48 kt/~360--380 Pa), with negative AOA. No existing controller/model is valid.
Decision: do not engage backstepping/LQR or collect identification at this point.
Manually reduce throttle and stabilize near R4: altitude 1700 m, IAS 48 kt,
positive AOA about 0.5--2 deg, low body rates. Then repeat read-only mapping.
```

Proposed R4 read-only attempt 1, 2026-07-12 21:21:

```text
Log: logs/R4_propulsion_regime_observe_20260712_212135.csv
Read-only 100 samples at 10.0026 Hz; live/unpaused; no controls sent.
Altitude 1748.3--1771.1 m; IAS 74.69--76.80 kt; qbar 893--956 Pa.
Pitch 0.12--4.38 deg; mean Q +0.362 deg/s: not steady/level.
Cockpit/engine-used throttle 0.11335/0.12355; thrust mean 5.14 N/engine.
AOA about -0.315 deg; sign should not be used as a gate until aircraft-specific
convention/trim is established.
Decision: FAIL R4 regime gate. Speed and qbar are far above 48 kt/~370 Pa and
the aircraft is pitching/climbing. No identification or controller engagement.
Next: manually reduce cockpit throttle (0.035--0.05 suggested only as a starting
range), hold approximately 48 kt, near-zero Q, and nearly constant altitude;
then repeat the exact read-only gate.
```

Proposed R4 read-only attempt 2, 2026-07-12 21:24:

```text
Log: logs/R4_propulsion_regime_observe_20260712_212407.csv
Live read-only 100 samples at 10.0021 Hz; no controls sent.
Altitude 1703.4--1709.9 m; IAS 56.70--57.08 kt; qbar 521--528 Pa.
Pitch 1.02--1.45 deg; Q -0.0766..+0.0427 deg/s; state nearly steady.
Cockpit/engine-used throttle 0.051454/0.056085; thrust 3.163 N/engine.
Decision: steadiness and altitude acceptable for trim development, but speed is
8.7--9.1 kt above frozen R4 48-kt target. No identification yet.
Interpolation from measured 39- and 57-kt steady points suggests cockpit throttle
about 0.037--0.040; use 0.038 only as manual starting trim, allow settling, then
repeat read-only once before freezing R4.
```

R4 trim and expanded high-rate instrumentation PASS, 2026-07-12 21:26:

```text
10-Hz trim log: logs/R4_propulsion_regime_observe_20260712_212601.csv
IAS 46.16--47.40 kt; qbar 345--364 Pa; altitude 1716--1728 m;
cockpit/used throttle 0.041418/0.045146; AOA +0.318..+0.344 deg.
The first 10-s window retained pitch motion, so it was not alone sufficient.
35-Hz gate log: logs/R4_highrate_propulsion_observe_20260712_212640.csv
Rows/rate/max gap/max acquisition: 350 / 35.00683 Hz / 0.058176 s /
  0.058086 s: timing PASS against 0.07143-s gap limit.
IAS 46.57--46.80 kt; qbar 352.03--355.04 Pa; altitude 1755--1765 m;
Q -0.0341..+0.0693 deg/s; cockpit/used throttle 0.041418/0.045146;
mean thrust 3.156 N/engine; all expanded propulsion channels finite.
No controls sent; live/unpaused; ownership clear.
Decision: PASS for a new higher-authority R4 operating point and read-only 35-Hz
instrumentation. Freeze nominal R4 as approximately 46.7 kt, 353.5 Pa,
0.04142 cockpit throttle, and 0.04515 engine-used ratio at ~1760 m.
Claim boundary: trim/instrumentation only. Existing R3 model/LQR is not valid at
R4. Next allowed action: offline freeze of an R4-specific identification waveform,
start/abort gates, and default-observe runner; pass observe-only before any
engaged R4 identification. No LQR engagement at R4.
```

R4 fast-path freeze and observe attempt 1, 2026-07-12 21:31:

```text
Strategy/configs: configs/rich_R4_roll_fastpath.json and
  configs/rich_R4_roll_highrate_design.json
Frozen excitation: 35-Hz 2/4/6/8/10-Hz multisine, amplitude 0.0001, 20 s,
  original stabilization at 10 Hz. One design run and one confirmation maximum.
Predicted response scaling versus R3: 0.736; unchanged safety/limit rules.
Observe runner/analyzer: scripts/run_rich_r4_roll_dualrate_observe.sh /
  scripts/analyze_rich_r4_roll_dualrate_observe.py
Static tests: 75 PASS. Dynamic-pressure derivation was added to the reused
dual-rate runner; analyzer can derive it for immutable older logs.
Observe log: logs/rich_R4_roll_dualrate_observe_20260712_213132.csv
No controls sent. Timing/schedule PASS: 1050 rows, 34.9943 Hz, max gap 62.62 ms,
300 original-controller updates/holds.
Start state had drifted out of R4: altitude 1981.7 m, IAS 50.51 kt, roll
-19.48 deg, Q 2.40 deg/s, R -6.65 deg/s. Existing abort gate latched the
hypothetical waveform off for roll-envelope exceedance; excitation remained zero.
Decision: FAIL observe evidence due aircraft state; safety behavior correct.
Do not modify/repeat code or widen gates. Manually restore frozen R4 trim
(~1760 m, 46--48.5 kt, roll within 5 deg, body rates within 1 deg/s), then repeat
the exact observe-only gate once. No engaged identification yet.
```

End-of-session checkpoint, 2026-07-12:

```text
All material results, failures, immutable log names, claim boundaries, and next
gates are recorded above and in docs/LAST_SESSION_HANDOFF.md.
Regression suite: 75 PASS at last static run.
Frozen R4 identification config: configs/rich_R4_roll_fastpath.json and
configs/rich_R4_roll_highrate_design.json
Last attempted log: logs/rich_R4_roll_dualrate_observe_20260712_213132.csv
Last attempt sent no controls and failed only because aircraft state had drifted
far outside R4 before start; safety latch operated correctly.
First action next session: manually restore ~1760 m, IAS 46--48.5 kt, cockpit
throttle near 0.0414, |roll|<=5 deg and all body rates <=1 deg/s; then run exactly
`bash scripts/run_rich_r4_roll_dualrate_observe.sh` and score with
`scripts/analyze_rich_r4_roll_dualrate_observe.py`. No engaged run before PASS.
```

Append or update the current-stage evidence using this structure:

```text
Date/time:
Current stage:
Objective:
Files changed:
Exact command:
Input conditions/configuration:
Output log:
Measured results:
Acceptance criteria evaluated:
Result: PASS / FAIL / INCONCLUSIVE
Reason:
Next allowed action within the same stage:
```

## Paper-directed organization update — 2026-07-15

```text
Date/time: 2026-07-15 (America/Denver)
Current stage: Stage 5 — unchanged
Objective: organize subsequent research around the LQR implementation-gap and
           constrained regularized DeePC paper narrative
Files changed: paper/README.md, paper/CLAIMS_MATRIX.md,
               docs/PAPER_RESEARCH_PLAN.md, deepc/README.md,
               docs/CONTROL_DEVELOPMENT_PROCESS.md
Exact command: offline documentation and non-destructive directory scaffolding
Input conditions/configuration: existing immutable logs, configs, manuscript
                                handoff, and authoritative development record
Output log: none
Measured results: paper question, contribution boundaries, common R3 comparison
                  contract, evidence rules, and phased DeePC workflow frozen
Acceptance criteria evaluated: organization/provenance only; no flight gate
Result: PASS for paper-directed organization; INCONCLUSIVE for Stage 5
Reason: no controller was synthesized, changed, or flown
Next allowed action within the same stage: P0 dataset/evidence normalization and
        offline-only P1 DeePC feasibility using existing R3 evidence; keep held-out
        confirmation data closed during design selection. No new X-Plane control
        run is authorized. The preserved R4 observe retry remains optional until
        the paper requires operating-point generalization.
```

## P0 R3 DeePC evidence registry and initial rank audit — 2026-07-15

```text
Date/time: 2026-07-15 (America/Denver)
Current stage: Stage 5 — unchanged
Objective: normalize R3 evidence roles and test whether existing 35-Hz training
           data have sufficient Hankel rank for offline DeePC feasibility
Files changed: paper/DATASET_REGISTRY.csv, paper/README.md,
               deepc/analysis/audit_r3_deepc_data.py,
               deepc/configs/README.md, deepc/src/README.md,
               deepc/tests/README.md,
               configs/rich_R3_deepc_data_audit.json,
               docs/CONTROL_DEVELOPMENT_PROCESS.md
Exact command: backstepping/ehekatl_xplane12_backstepping_bridge/.venv/bin/python
               -B deepc/analysis/audit_r3_deepc_data.py
Input conditions/configuration: training/design log only,
  logs/rich_R3_roll_dualrate_pilot_20260712_193416.csv,
  SHA256 05b7aef1bb6f36fba5fce208e3b750c85d9fe69a364aaf2a97960781eb5ed08e;
  window 5..25 s; upstream yoke-roll input; candidate outputs P, roll, total roll
Output log: none; artifact configs/rich_R3_deepc_data_audit.json
Measured results: 700 samples; input Hankel full row rank for depths 15, 25,
  35, and 55; input nonzero condition 12.30, 16.62, 19.61, and 26.69;
  stacked input/output condition 1541.5, 2418.1, 3139.7, and 5323.6
Acceptance criteria evaluated: initial rank/conditioning feasibility only
Result: PASS for initial offline DeePC data feasibility; INCONCLUSIVE for
        controller synthesis and Stage 5
Reason: tested input Hankel matrices are full row rank, but joint conditioning,
        effective rank, normalization sensitivity, trajectory reconstruction,
        and closed-loop data interpretation remain unresolved
Next allowed action within the same stage: training-only scaled effective-rank,
        reconstruction, horizon, and regularization audit. Keep all registered
        validation/confirmation response files closed during design selection.
        No new X-Plane run is authorized.
```

## P1 R3 DeePC reconstruction and channel-selection audit — 2026-07-15

```text
Date/time: 2026-07-15 (America/Denver)
Current stage: Stage 5 — unchanged
Objective: test temporal behavioral reconstruction, scaling, output selection,
           horizons, and g-regularization using training/design evidence only
Files changed: deepc/analysis/audit_r3_deepc_reconstruction.py,
               deepc/analysis/audit_r3_deepc_channels.py,
               configs/rich_R3_deepc_reconstruction_audit.json,
               configs/rich_R3_deepc_channel_audit.json,
               deepc/configs/rich_R3_deepc_provisional.json,
               docs/CONTROL_DEVELOPMENT_PROCESS.md
Exact commands:
  backstepping/ehekatl_xplane12_backstepping_bridge/.venv/bin/python -B
    deepc/analysis/audit_r3_deepc_reconstruction.py
  backstepping/ehekatl_xplane12_backstepping_bridge/.venv/bin/python -B
    deepc/analysis/audit_r3_deepc_channels.py
Input conditions/configuration: immutable R3 35-Hz design/training log only;
  5..15 s behavioral library and 15..25 s temporal test; standardized from the
  library; 40 temporal windows; held-out response files opened: none
Output log: none; generated JSON artifacts listed above
Measured results: three-output P/roll/total-roll reconstruction failed with
  best mean scaled NRMSE 1.338..1.577 despite full rank. P-only formulations
  passed: best NRMSE 0.29257 at Tini=5/N=5/lambda_g=10; Tini=15/N=20 achieved
  0.29396 with rank 50/50. Eight tested channel/horizon candidates passed the
  provisional <=1.0 NRMSE and full-row-rank rule.
Acceptance criteria evaluated: training-only predictive and numeric feasibility
Result: PASS for a provisional P-only offline DeePC formulation; INCONCLUSIVE
        for optimization, constraints, runtime, held-out validation, and Stage 5
Reason: roll and total-roll are not repeatably predicted across the temporal
        split, but body-rate P is. Select the longest tested P-only horizon
        within 5 percent of the best NRMSE: Tini=15, N=20, lambda_g=10.
Next allowed action within the same stage: offline constrained DeePC optimization
        formulation and deterministic replay using the provisional P-only
        predictor. Treat roll, total roll, and distributed surface as safety/audit
        channels, not predicted DeePC outputs. Do not open held-out confirmation
        responses or authorize X-Plane control.
```

## P1 R3 constrained DeePC optimizer and runtime audit — 2026-07-15

```text
Date/time: 2026-07-15 (America/Denver)
Current stage: Stage 5 — unchanged
Objective: implement a dependency-free constrained DeePC optimizer and require
           deterministic convergence, command/slew feasibility, and 35-Hz runtime
Files changed: deepc/src/regularized_deepc.py,
               deepc/analysis/audit_r3_deepc_optimizer.py,
               deepc/tests/test_regularized_deepc.py,
               configs/rich_R3_deepc_optimizer_audit.json,
               configs/rich_R3_deepc_optimizer_fast_audit.json,
               deepc/configs/rich_R3_deepc_provisional.json,
               docs/CONTROL_DEVELOPMENT_PROCESS.md
Exact commands:
  backstepping/ehekatl_xplane12_backstepping_bridge/.venv/bin/python -B
    -m unittest deepc.tests.test_regularized_deepc
  backstepping/ehekatl_xplane12_backstepping_bridge/.venv/bin/python -B
    deepc/analysis/audit_r3_deepc_optimizer.py
Input conditions/configuration: training/design temporal fold only; P-only;
  lambda_g=10; Qy=1, Ru=0.01, Rdu=0.05; command/slew 0.0002/0.00005;
  80 cases; projected-gradient tolerance 1e-7; held-out files opened: none
Output log: none; optimizer audit JSON artifacts
Measured results:
  Initial Tini=15/N=20: 80/80 converged and all constraints passed, but runtime
    median/p95/max 27.01/55.60/61.13 ms versus 28.57-ms period: FAIL.
  Reduced Tini=5/N=5: 80/80 converged; all constraints passed; runtime
    median/p95/max 6.38/10.91/11.36 ms: PASS. Median/p95 self-predicted output
    cost ratio versus held input 0.1325/0.2944.
Acceptance criteria evaluated: optimizer convergence, fixed bounds, and strict
                                every-case 35-Hz computation deadline
Result: PASS for provisional short-horizon offline optimizer feasibility;
        INCONCLUSIVE for plant response, superiority, and Stage 5
Reason: the longer formulation is computationally rejected; the P-only 5/5
        formulation is both the best temporal-NRMSE candidate and meets the
        deadline with margin using the NumPy-only deterministic solver.
Next allowed action within the same stage: deterministic closed-loop offline
        replay against the validated R3 discrete cascade and frozen matched
        disturbance, including coefficient uncertainty, command/slew, runtime,
        and comparison with the immutable LQR/backstepping reference. No held-out
        response opening and no X-Plane control authorization.
```

## P1 R3 DeePC 243-case closed-loop uncertainty replay — 2026-07-15

```text
Date/time: 2026-07-15 (America/Denver)
Current stage: Stage 5 — unchanged
Objective: compare provisional DeePC against the frozen LQR on the validated R3
           cascade, matched disturbance, and identical 243 coefficient cases
Files changed: deepc/analysis/replay_r3_deepc_uncertainty.py,
               deepc/analysis/replay_r3_deepc_uncertainty_vectorized.py,
               configs/rich_R3_deepc_uncertainty_replay.json,
               docs/CONTROL_DEVELOPMENT_PROCESS.md
Exact command: backstepping/ehekatl_xplane12_backstepping_bridge/.venv/bin/python
               -B deepc/analysis/replay_r3_deepc_uncertainty_vectorized.py
Input conditions/configuration: frozen R3 discrete cascade; 0.75/1/1.25 grid
  over five coefficients; 243 cases; frozen +/-0.00005 paired half-sines at
  10 and 12 s; provisional P-only DeePC Tini=5/N=5/lambda_g=10;
  Qy/Ru/Rdu=1/0.01/0.05; held-out response files opened: none
Output log: none; artifact configs/rich_R3_deepc_uncertainty_replay.json
Measured results: all 243 cases converged; maximum combined sent command
  4.45068e-5; maximum base slew 8.97316e-6; zero limit violations;
  median DeePC/LQR integral ratio 0.806792; worst integral ratio 0.906534
  versus frozen <=0.90 gate FAIL; worst peak ratio 0.939231 <=1.10 PASS.
Acceptance criteria evaluated: prospective robust improvement, peak guard,
  convergence, magnitude, slew, and computation feasibility
Result: FAIL for the provisional DeePC robust-improvement claim; INCONCLUSIVE
        for DeePC generally and Stage 5
Reason: corrected trim-relative replay is competitive and passes every safety,
        feasibility, peak, and convergence gate, but 0.906534 must not be rounded
        down or reinterpreted as <=0.90. An earlier harness attempt produced a
        spurious ~13.6 median ratio because zero cascade P error was incorrectly
        mapped to negative absolute training bias; it is rejected as a coordinate
        implementation error and is not controller evidence.
Next allowed action within the same stage: training/model-only hyperparameter
        redesign aimed at a materially stronger worst-case effect while keeping
        the 0.90 gate, command/slew limits, disturbance, uncertainty set, and
        confirmation-data isolation unchanged. No X-Plane control authorized.
```

## P1 R3 DeePC hyperparameter redesign and frozen offline PASS — 2026-07-15

```text
Date/time: 2026-07-15 (America/Denver)
Current stage: Stage 5 — unchanged
Objective: redesign only DeePC input/slew penalties to achieve a materially
           stronger worst-case effect without changing any comparison gate
Files changed: deepc/analysis/tune_r3_deepc_hyperparameters.py,
               deepc/analysis/replay_r3_deepc_uncertainty_vectorized.py,
               configs/rich_R3_deepc_hyperparameter_scan.json,
               configs/rich_R3_deepc_uncertainty_replay.json,
               deepc/configs/rich_R3_deepc_provisional.json,
               docs/CONTROL_DEVELOPMENT_PROCESS.md
Exact commands:
  backstepping/ehekatl_xplane12_backstepping_bridge/.venv/bin/python -B
    deepc/analysis/tune_r3_deepc_hyperparameters.py
  backstepping/ehekatl_xplane12_backstepping_bridge/.venv/bin/python -B
    deepc/analysis/replay_r3_deepc_uncertainty_vectorized.py
Input conditions/configuration: fixed P-only Tini=5/N=5/lambda_g=10/Qy=1;
  Ru grid 0.001/0.003/0.01; Rdu grid 0.005/0.01/0.02/0.05; frozen plant,
  disturbance, 243 uncertainty cases, <=0.90 integral gate, <=1.10 peak gate,
  and command/slew limits; held-out response files opened: none
Output log: none; scan and frozen replay JSON artifacts
Measured results: low Rdu=0.005/0.01 candidates improved response but failed
  optimizer convergence and were rejected. Three Rdu=0.02 candidates passed.
  Best effect Ru/Rdu=0.001/0.02, worst ratio 0.892743. Predeclared selection
  chose least aggressive candidate within 2 percent of best: Ru/Rdu=0.01/0.02.
  Independent frozen rerun: worst/median integral ratio 0.895344/0.788056;
  worst peak ratio 0.928154; maximum sent command 4.39288e-5; maximum base slew
  9.96963e-6; all 243 cases converged; all unchanged gates PASS.
Acceptance criteria evaluated: frozen robust effect, peak non-degradation,
  convergence, magnitude, slew, and existing single-case runtime prerequisite
Result: PASS for frozen-model offline DeePC candidate; INCONCLUSIVE for X-Plane
        performance, held-out response, and Stage 5
Reason: selected controller improves the frozen LQR integral metric by at least
        10.47 percent across all modeled uncertainty cases and about 21.19
        percent at the median, without approaching command or slew bounds.
Next allowed action within the same stage: exact deterministic runtime packaging,
        replay identity tests, infeasibility/fallback tests, and default-observe
        integration design. Do not open confirmation responses or send controls.
```

## P1 R3 DeePC frozen runtime and identity gate — 2026-07-15

```text
Date/time: 2026-07-15 (America/Denver)
Current stage: Stage 5 — unchanged
Objective: package the selected DeePC as fixed runtime matrices and verify
           deterministic identity, constraints, and permanent fallback behavior
Files changed: deepc/analysis/freeze_r3_deepc_runtime.py,
               deepc/configs/rich_R3_deepc_runtime.json,
               deepc/src/r3_roll_runtime.py,
               deepc/tests/test_r3_roll_runtime.py,
               deepc/analysis/audit_r3_deepc_runtime_identity.py,
               configs/rich_R3_deepc_runtime_identity.json,
               docs/CONTROL_DEVELOPMENT_PROCESS.md
Exact commands:
  backstepping/ehekatl_xplane12_backstepping_bridge/.venv/bin/python -B
    deepc/analysis/freeze_r3_deepc_runtime.py
  backstepping/ehekatl_xplane12_backstepping_bridge/.venv/bin/python -B
    -m unittest deepc.tests.test_regularized_deepc deepc.tests.test_r3_roll_runtime
  backstepping/ehekatl_xplane12_backstepping_bridge/.venv/bin/python -B
    deepc/analysis/audit_r3_deepc_runtime_identity.py
Input conditions/configuration: frozen selected maps/normalization/weights;
  nominal validated cascade; exact 1050-sample matched-disturbance replay;
  held-out response files opened: none
Output log: none; frozen runtime JSON and identity artifact
Measured results: six focused tests PASS; non-finite input and forced optimizer
  non-convergence permanently request fallback; zero-history command zero;
  1050/1050 packaged commands exactly match design optimizer with maximum error
  0; peak command 1.438998e-5; no fallback latch in nominal replay.
Acceptance criteria evaluated: frozen-data provenance, history ordering,
  exact runtime identity, deterministic output, constraints, and failure latch
Result: PASS for offline frozen runtime packaging; INCONCLUSIVE for observe-only
        X-Plane integration, flight response, and Stage 5
Reason: the online candidate no longer reconstructs or tunes its behavioral
        model and exactly reproduces the selected offline optimizer. The combined
        identity audit times two optimizers and is not a runtime gate; the prior
        single-runtime every-case audit remains the computation prerequisite.
Next allowed action within the same stage: implement a structurally default-
        observe-only X-Plane integration with no control writes in observe mode,
        original pitch/backstepping hypothetical fallback, exact history/runtime
        logging, start/live/safety gates, and an offline/static analyzer. Do not
        engage or open held-out confirmation responses.
```

## X-Plane default-scenery repair and session checkpoint — 2026-07-15

```text
Date/time: 2026-07-15 (America/Denver)
Current stage: Stage 5 — unchanged
Objective: diagnose and repair X-Plane startup failure, then save a concise
           restart checkpoint without running a controller experiment
Files changed: X-Plane official updater replaced mismatched default-scenery
               files under Resources/default scenery/1200 forests/;
               docs/LAST_SESSION_HANDOFF.md and this record updated
Exact action: official X-Plane 5.4.0-r1 updater, Update X-Plane, destination
              /home/ubuntu/Xplane12/X-Plane 12, overwrite changed forest files
Input conditions/configuration: NVIDIA GTX 980 Ti PRIME/Vulkan environment;
  installer detected broad_tmp.for signature mismatch
Output log: /home/ubuntu/Desktop/X-Plane Installer Log.txt
Measured results: original Log.txt reported broad_tmp.for wrong mesh vertex/index
  count at REN_forest.cpp:292; updater scan found signature mismatch, installed
  replacements, advanced to Finish, and exited cleanly. Existing NVIDIA launcher
  and research project remained unchanged.
Acceptance criteria evaluated: installation repair only; no flight/controller gate
Result: PASS for X-Plane updater completion; INCONCLUSIVE for simulator flight
Reason: repair completed, but no post-repair research observe gate was requested
Next allowed action within the same stage: resume from docs/LAST_SESSION_HANDOFF.md;
  implement/static-audit the default-observe-only DeePC runner and analyzer.
  Do not run an experiment while the user is away and do not engage DeePC.
```

## P2 DeePC default-observe integration static gate — 2026-08-10

```text
Date/time: 2026-08-10 (America/Denver)
Current stage: Stage 5 — unchanged
Objective: implement and statically audit the frozen R3 DeePC observe-only
           X-Plane integration without creating a control-write path
Files changed: scripts/run_rich_r3_roll_deepc_observe_xp12.py,
               scripts/analyze_rich_r3_roll_deepc_observe.py,
               scripts/run_rich_r3_roll_deepc_observe.sh,
               tests/test_r3_roll_deepc_observe.py,
               docs/LAST_SESSION_HANDOFF.md,
               docs/CONTROL_DEVELOPMENT_PROCESS.md
Exact command: shell syntax; Python compilation and CLI; focused DeePC tests;
               full tests discovery; read-only X-Plane state snapshot
Input conditions/configuration: frozen deepc/configs/rich_R3_deepc_runtime.json;
  held-out response files opened: none; live snapshot only, no formal capture
Output log: none
Measured results: runner exposes no --engage option and contains no sendCTRL or
  sendDREF calls; exact pre/post histories, hypothetical selection, convergence,
  fallback, safety/live state, and timing are logged; 78 project tests PASS;
  9 focused DeePC tests PASS. X-Plane snapshot: altitude 2439.301 m, IAS
  124.789 kt, pitch 1.713 deg, roll 25.412 deg, P/Q/R -0.082/+1.573/+3.305
  deg/s; paused=0, speed=1, replay=0, artificial stability=1, overrides clear.
Acceptance criteria evaluated: P2 static structure, logging, CLI, regression,
  and current-state readiness only
Result: PASS for static observe integration; FAIL for live R3 readiness;
        INCONCLUSIVE for P2 online observe gate and Stage 5
Reason: software is ready, but the connected aircraft is far outside the frozen
        R3 start and safety envelopes. No formal observe run was attempted.
Next allowed action within the same stage: manually restore a fresh clean R3
  situation near 1700 m/39 kt/~240 Pa, throttle 0.02353, pitch ~1.3 deg,
  |roll|<=5 deg, body rates <=1 deg/s, artificial stability on, automation off,
  live/unpaused and replay off; then run exactly
  bash scripts/run_rich_r3_roll_deepc_observe.sh and score the immutable output
  with scripts/analyze_rich_r3_roll_deepc_observe.py. No control engagement.
```

## P2 DeePC R3 readiness check 2 — 2026-08-10

```text
Date/time: 2026-08-10 (America/Denver)
Current stage: Stage 5 — unchanged
Objective: verify the user-restored R3 state before the formal DeePC observe gate
Files changed: docs/LAST_SESSION_HANDOFF.md,
               docs/CONTROL_DEVELOPMENT_PROCESS.md
Exact command: read-only batched XPlaneConnect state snapshot and frozen
               start_reasons evaluation
Input conditions/configuration: connected live X-Plane; no ownership or writes
Output log: none
Measured results: altitude 1868.922 m; IAS 114.955 kt; pitch 7.376 deg;
  roll 0.013 deg; P/Q/R +0.0155/+0.1764/-0.0913 deg/s; paused=0; speed=1;
  replay=0; artificial stability=1; roll/pitch overrides=0
Acceptance criteria evaluated: frozen R3 start gate only
Result: FAIL for R3 readiness; INCONCLUSIVE for P2 online observe gate
Reason: altitude, IAS, and pitch were outside R3; the saved R3 condition did
        not load or did not reproduce its frozen operating point
Next allowed action within the same stage: restore the exact clean R3 situation
  near 1700 m, 39 kt, pitch ~1.3 deg and let it settle; repeat read-only check.
  No formal capture and no control engagement before the start gate passes.
```

## P2 DeePC online observe gate and timing correction — 2026-08-10

```text
Date/time: 2026-08-10 (America/Denver)
Current stage: Stage 5 — unchanged
Objective: pass the frozen 35-Hz DeePC observe-only integration gate at R3
Files changed: deepc/src/r3_roll_runtime.py,
               deepc/src/regularized_deepc.py,
               deepc/tests/test_r3_roll_runtime.py,
               paper/CLAIMS_MATRIX.md,
               docs/LAST_SESSION_HANDOFF.md,
               docs/CONTROL_DEVELOPMENT_PROCESS.md
Exact command: bash scripts/run_rich_r3_roll_deepc_observe.sh; score each log
  with scripts/analyze_rich_r3_roll_deepc_observe.py; offline identity and tests
Input conditions/configuration: frozen R3 runtime and gates; clean live R3;
  held-out confirmation responses opened: none; controls sent: none
Output logs:
  logs/rich_R3_roll_deepc_observe_20260810_122507.csv (rejected)
  logs/rich_R3_roll_deepc_observe_20260810_122825.csv (rejected)
  logs/rich_R3_roll_deepc_observe_20260810_122949.csv (accepted)
Measured results:
  Attempt 1: 798 rows, 26.587 Hz; runtime median/max 22.77/41.36 ms; FAIL
    completeness, rate, gap, and runtime. All non-timing checks passed.
  Runtime correction: precompute invariant Hessian/step/bounds and replace
    scalar np.clip temporaries with equivalent comparisons. Frozen output
    identity error remained exactly 0; failed-log replay runtime median/p95/max
    improved to 3.30/5.07/6.38 ms.
  Attempt 2: 1050 rows, 35.002 Hz; runtime median/max 3.59/7.25 ms; one
    87.36-ms sample gap from an 84.60-ms XPlaneConnect acquisition: FAIL.
  Unchanged confirmation: 1050 rows, 35.002 Hz; max gap 38.12 ms; runtime
    median/p95/max 3.79/5.48/7.57 ms; peak command 5.40957e-6; maximum slew
    2.79344e-6; replay/history error 0; every analyzer check PASS.
  Static regression: 78 project tests PASS; 10 focused DeePC tests PASS.
Acceptance criteria evaluated: P2 timing/completeness, start/live/safety state,
  no writes/ownership, optimizer convergence/deadline, command/slew, exact
  history/runtime replay, and fallback readiness
Result: PASS for P2 online observe-only integration; INCONCLUSIVE for X-Plane
        DeePC control performance and Stage 5
Reason: the accepted confirmation satisfies every frozen observe gate, while
  the two failed attempts remain visible. No control was sent in any attempt.
Next allowed action within the same stage: offline freeze and static audit of a
  P3 guarded design pilot with permanent backstepping fallback and restoration.
  Do not engage or open held-out confirmation responses before that gate passes.
```

## P3 DeePC guarded design-pilot static preparation — 2026-08-10

```text
Date/time: 2026-08-10 (America/Denver)
Current stage: Stage 5 — unchanged
Objective: freeze and statically audit a single guarded R3 DeePC design pilot
Files changed: deepc/analysis/freeze_r3_deepc_pilot.py,
  deepc/configs/rich_R3_deepc_pilot.json,
  scripts/run_rich_r3_roll_deepc_pilot_xp12.py,
  scripts/analyze_rich_r3_roll_deepc_pilot.py,
  scripts/run_rich_r3_roll_deepc_pilot.sh,
  scripts/run_rich_r3_roll_deepc_pilot_observe.sh,
  tests/test_r3_roll_deepc_pilot.py,
  docs/LAST_SESSION_HANDOFF.md, docs/CONTROL_DEVELOPMENT_PROCESS.md
Exact command: freeze protocol; shell syntax; Python compilation/CLI; focused
  and full regression tests; read-only R3 readiness check
Input conditions/configuration: accepted 243-case offline replay; held-out
  response files opened: none; no controller engagement
Output log: none
Measured results: paired +/-0.00005 half-sines frozen at 10/12 s for 0.2 s;
  command/slew 0.0002/0.00005; permanent fallback and restoration paths;
  81 project tests PASS; 13 focused DeePC tests PASS. Readiness snapshot:
  altitude 1604.288 m, IAS 39.930 kt, pitch 0.625 deg, roll -16.132 deg,
  P/Q/R +0.101/+1.968/-6.910 deg/s; live and out of replay.
Acceptance criteria evaluated: offline provenance, fixed stimulus/gates,
  default-observe behavior, explicit engagement, fallback/restoration structure,
  regression, and live readiness
Result: PASS for static P3 preparation; FAIL for R3 readiness; INCONCLUSIVE for
        the guarded observe waveform gate and engaged pilot
Reason: roll and body rate were outside the frozen start envelope. No run and
        no control command were issued.
Next allowed action within the same stage: reload clean R3 and pass exactly
  bash scripts/run_rich_r3_roll_deepc_pilot_observe.sh plus the frozen analyzer.
  Engaged pilot remains blocked until observe evidence passes.
```

## P3 DeePC guarded waveform observe gate — 2026-08-10

```text
Date/time: 2026-08-10 (America/Denver)
Current stage: Stage 5 — unchanged
Objective: verify the exact guarded design-pilot waveform, selection, timing,
           runtime, history, safety, and fallback plumbing without control writes
Files changed: docs/LAST_SESSION_HANDOFF.md,
               docs/CONTROL_DEVELOPMENT_PROCESS.md
Exact command: bash scripts/run_rich_r3_roll_deepc_pilot_observe.sh;
  analyze with scripts/analyze_rich_r3_roll_deepc_pilot.py
Input conditions/configuration: clean R3 start at 1708.624 m, 39.042 kt,
  pitch 1.242 deg, roll 0.031 deg, low body rates; frozen P3 protocol
Output log: logs/rich_R3_roll_deepc_pilot_observe_20260810_143609.csv
Measured results: 1050 rows; 35.0025 Hz; max gap 46.98 ms; runtime median/p95/max
  3.54/5.26/8.03 ms; peak hypothetical combined perturbation 5.05395e-5;
  max hypothetical slew 2.30833e-5; replay/history/selection error 0;
  full convergence; no latch, safety event, ownership request, or control write
Acceptance criteria evaluated: all frozen P3 pre-engagement observe gates
Result: PASS for P3 guarded waveform observe gate; INCONCLUSIVE for engaged
        X-Plane behavior and Stage 5
Reason: every pre-engagement criterion passed with no control sent
Next allowed action within the same stage: after a fresh read-only R3 start-gate
  pass, run exactly one engaged design pilot using
  bash scripts/run_rich_r3_roll_deepc_pilot.sh and the frozen analyzer. This
  pilot is excluded from future confirmation evidence. No parameter changes.
```

## P3 DeePC guarded design pilot — 2026-08-10

```text
Date/time: 2026-08-10 (America/Denver)
Current stage: Stage 5 — unchanged
Objective: execute exactly one frozen guarded DeePC design pilot at R3
Files changed: paper/DATASET_REGISTRY.csv, paper/CLAIMS_MATRIX.md,
               docs/LAST_SESSION_HANDOFF.md,
               docs/CONTROL_DEVELOPMENT_PROCESS.md
Exact command: bash scripts/run_rich_r3_roll_deepc_pilot.sh; analyze with
  scripts/analyze_rich_r3_roll_deepc_pilot.py --require-engaged
Input conditions/configuration: final start check 1729.128 m, 39.005 kt,
  pitch 1.315 deg, roll 0.161 deg, low body rates, live/unpaused, ownership clear;
  frozen paired +/-0.00005 pulses and unchanged guards
Output log: logs/rich_R3_roll_deepc_pilot_20260810_144136.csv
SHA256: b37ed92326cf9c9ba8149a0551bb0c6af8a4a57f6c66b00a352463e111a30f66
Measured results: 1050 rows; 35.0024 Hz; max gap 42.10 ms; runtime median/p95/max
  3.62/5.17/7.52 ms; peak |delta P| 0.00358968 deg/s; final-5-s max
  0.00134659 deg/s; sent-to-realized lag-1 correlation 0.999999999997;
  peak perturbation 3.76264e-5; max slew 2.19556e-5; exact replay/history/
  selection error 0; no fallback, latch, saturation, safety event, or restoration
  failure; every frozen analyzer check PASS
Acceptance criteria evaluated: all frozen P3 guarded design-pilot gates
Result: PASS for P3 guarded design pilot; INCONCLUSIVE for independent DeePC
        superiority, held-out confirmation, and Stage 5
Reason: one design pilot establishes safe integration and measurable recovery,
        but is deliberately excluded from confirmation evidence
Next allowed action within the same stage: offline P4 common-benchmark and
  prospective power design with frozen controller/metrics. No benchmark flight
  until that protocol passes; keep confirmation responses closed during design.
```

## P4 DeePC benchmark prospective-power decision — 2026-08-10

```text
Date/time: 2026-08-10 (America/Denver)
Current stage: Stage 5 — unchanged
Objective: determine whether a statistically powered R3 DeePC-versus-LQR
           confirmation benchmark is practical before collecting any flight
Files changed: deepc/analysis/audit_r3_deepc_separate_power.py,
  deepc/analysis/audit_r3_deepc_paired_power.py,
  deepc/analysis/audit_r3_deepc_paired_iae_power.py,
  configs/rich_R3_deepc_separate_power.json,
  configs/rich_R3_deepc_paired_power.json,
  configs/rich_R3_deepc_paired_iae_power.json,
  paper/CLAIMS_MATRIX.md, docs/LAST_SESSION_HANDOFF.md,
  docs/CONTROL_DEVELOPMENT_PROCESS.md
Exact command: execute the three deterministic moving-block bootstrap audits;
  compile audit scripts; run full regression suite
Input conditions/configuration: LQR metric-design log and DeePC design pilot
  only; 300 virtual experiments and 300 bootstrap resamples per count; frozen
  upper-95-percent ratio <1 and power >=0.80 rule; held-out responses unopened
Output log: none; generated JSON artifacts listed above
Measured results:
  Separate reload: power 0.317/0.460/0.630/0.843 at 6/12/24/48 pulses;
    first qualifier 48, at least 149 s per controller.
  Paired sign-aligned waveform: no qualifier through 24 pairs; max power 0.623.
  Paired mean per-pulse IAE: power 0.440/0.487/0.630/0.763/0.7967/0.930
    at 4/6/8/12/16/24 pairs; 16 FAIL; first qualifier 24 at least 152 s.
  Compilation PASS; 81 project tests PASS.
Acceptance criteria evaluated: prospective upper-confidence-bound power,
  practical duration, confirmation isolation, and protocol implementation risk
Result: FAIL for a practical P4 confirmation benchmark; INCONCLUSIVE for DeePC
        superiority and Stage 5
Reason: only long-exposure designs qualify, and the paired qualifier additionally
  requires unvalidated controller switching/history handoffs. The 0.7967 result
  is below 0.80 and is not rounded up. No flight is justified.
Next allowed action within the same stage: paper synthesis using registered
  evidence, or offline redesign aimed at a materially larger identifiable effect
  under unchanged limits. No benchmark flight or held-out response opening.
```

## Standardized direct LQR/DeePC controller structure — 2026-08-10

```text
Date/time: 2026-08-10 (America/Denver)
Current stage: Stage 5 — unchanged
Objective: expose LQR and DeePC with Backstepping-style APIs and simple direct
           guarded launchers while preserving rich logging and safety evidence
Files changed: lqr/LQRController.py, lqr/run_lqr_direct_xp12.py,
  lqr/run_lqr_direct.sh, lqr/README.md, deepc/DeePC.py,
  deepc/run_deepc_direct_xp12.py, deepc/run_deepc_direct.sh, deepc/README.md,
  tests/test_direct_controller_interfaces.py,
  docs/EXPERIMENT_RESULTS_SUMMARY.md,
  docs/CONTROLLER_TEST_AND_RESEARCH_PLAN.md,
  docs/LAST_SESSION_HANDOFF.md, docs/CONTROL_DEVELOPMENT_PROCESS.md
Exact command: shell syntax; Python compilation; both direct-runner CLIs;
  facade/runtime identity tests; full test discovery
Input conditions/configuration: offline/static only; frozen R3 controllers and
  existing guarded runners; held-out responses unopened
Output log: none
Measured results: both facades expose SetPoint/update/output/clear; direct
  launchers create timestamped rich CSVs and invoke frozen analyzers; start
  gates, command/slew limits, Backstepping fallback, ownership, restoration and
  measured inputs retained; 3 interface tests PASS; 84 project tests PASS
Acceptance criteria evaluated: structure/API identity, CLI, logging path,
  safety preservation, analyzer routing, regression
Result: PASS for standardized direct-test tooling; INCONCLUSIVE for any new
        flight performance or Stage 5
Reason: implementation is verified offline; no new simulator run was performed
Next allowed action within the same stage: from a fresh clean R3 reload, the
  user may run one canonical direct controller launcher and retain its log as
  demonstration evidence. Do not compare unmatched runs as superiority proof.
```

## Direct DeePC live start-gate attempt — 2026-08-10

```text
Date/time: 2026-08-10 (America/Denver)
Current stage: Stage 5 — unchanged
Objective: apply the canonical guarded DeePC controller directly to the live
           EHEKATL BWB only if the frozen R3 start gate passed
Files changed: lqr/run_lqr_direct.sh, deepc/run_deepc_direct.sh,
               docs/LAST_SESSION_HANDOFF.md,
               docs/CONTROL_DEVELOPMENT_PROCESS.md
Exact command: bash deepc/run_deepc_direct.sh
Input conditions/configuration: connected live X-Plane; no fresh R3 reload
Output log: none
Measured results: start gate BLOCKED for altitude outside R3, roll outside the
  start envelope, and body rate outside the start envelope; no ownership or
  controller command was issued. The wrapper then exposed a missing-log error
  by calling its analyzer after the safe block.
Acceptance criteria evaluated: frozen R3 start gate only
Result: FAIL for live readiness; INCONCLUSIVE for DeePC flight functionality
Reason: the aircraft was outside the validated local operating envelope
Correction: both direct wrappers now require a nonempty output log before
  invoking their frozen analyzer and report an ordinary start-block exit
Next allowed action within the same stage: reload and settle the exact clean R3
  situation, then run one canonical direct controller. Reload again before
  testing the other controller. Do not widen limits or compare unmatched runs.
```

## Direct DeePC real-flight demonstration — 2026-08-10

```text
Date/time: 2026-08-10 (America/Denver)
Current stage: Stage 5 — unchanged
Objective: execute the standardized guarded DeePC controller directly on the
           EHEKATL BWB from a fresh clean R3 reload
Files changed: paper/DATASET_REGISTRY.csv, docs/LAST_SESSION_HANDOFF.md,
               docs/CONTROL_DEVELOPMENT_PROCESS.md
Exact command: bash deepc/run_deepc_direct.sh
Input conditions/configuration: fresh R3; paired frozen disturbance; frozen
  P-only DeePC runtime, limits, safety, fallback, ownership and restoration
Output log: logs/direct_deepc_20260810_150657.csv
SHA256: d326b6dacee04f9938be503036049d592a71e8f8275e7c84d397c073da29f662
Measured results: 1050 rows; 35.0014 Hz; max gap 50.09 ms; optimizer
  median/p95/max 4.02/5.36/7.90 ms; peak/final-5-s |delta P|
  0.004163/0.001311 deg/s; sent-to-realized lag-one correlation
  0.999999999990; peak perturbation 4.6094e-5; max slew 2.1260e-5;
  replay/history/selection error zero; no fallback, latch, safety event or
  restoration failure; all frozen analyzer checks PASS
Acceptance criteria evaluated: standardized direct DeePC functionality and all
  frozen guarded design-pilot gates
Result: PASS as direct functionality/demonstration evidence; INCONCLUSIVE for
  independent superiority and Stage 5
Reason: the controller executed safely and exactly, but this user-requested
  direct run is not an independently powered comparison
Next allowed action within the same stage: fresh clean R3 reload, then one
  canonical direct LQR demonstration. Do not compare the unmatched trajectories
  as superiority evidence.
```

## Direct LQR real-flight demonstration — 2026-08-10

```text
Date/time: 2026-08-10 (America/Denver)
Current stage: Stage 5 — unchanged
Objective: execute the standardized guarded discrete-cascade roll LQR directly
           on the EHEKATL BWB from a fresh clean R3 reload
Files changed: paper/DATASET_REGISTRY.csv, docs/LAST_SESSION_HANDOFF.md,
               docs/CONTROL_DEVELOPMENT_PROCESS.md
Exact command: bash lqr/run_lqr_direct.sh
Input conditions/configuration: fresh R3; paired frozen disturbance; frozen
  measured-cascade LQR, limits, safety, fallback, ownership and restoration
Output log: logs/direct_lqr_20260810_151244.csv
SHA256: 91385f3cb897e2e326612ea28b2e2630c653216b18be2317fe74dc25aff93600
Measured results: 1050 rows; 35.0040 Hz; max gap 42.23 ms; peak command
  4.6696e-5; max slew 2.1706e-5; peak/final-5-s |delta P|
  0.005622/0.001496 deg/s; waveform and runtime replay errors zero; no
  fallback, latch, safety event or restoration failure; all 18 frozen analyzer
  checks PASS
Acceptance criteria evaluated: standardized direct LQR functionality and all
  frozen direct-run integration gates
Result: PASS as direct functionality/demonstration evidence; INCONCLUSIVE for
  independent superiority and Stage 5
Reason: the controller executed safely and exactly, but the LQR and DeePC
  demonstrations used separate reloads and are neither matched nor powered
Next allowed action within the same stage: offline descriptive reporting of the
  two direct demonstrations, or controller/experiment redesign within unchanged
  limits. Do not infer superiority from their unmatched response magnitudes.
```

## Paper synthesis package — 2026-08-10

```text
Date/time: 2026-08-10 (America/Denver)
Current stage: Stage 5 — unchanged
Objective: convert the registered LQR/DeePC evidence into a reproducible
           paper-facing analysis and complete bounded manuscript draft
Files changed: paper/generate_paper_results.py, paper/MANUSCRIPT_DRAFT.md,
  paper/CLAIMS_MATRIX.md, paper/README.md, paper/generated/*,
  docs/CONTROL_DEVELOPMENT_PROCESS.md
Exact command: backstepping/ehekatl_xplane12_backstepping_bridge/.venv/bin/python
  -B paper/generate_paper_results.py
Input conditions/configuration: immutable registered direct LQR/DeePC logs;
  frozen offline DeePC uncertainty replay and prospective power artifacts;
  no new X-Plane command or held-out flight response
Output artifacts: paper/generated/direct_demonstration_metrics.{json,csv},
  direct_controller_demonstrations.{png,pdf}, and
  offline_robustness_and_power.{png,pdf}; paper/MANUSCRIPT_DRAFT.md
Measured results: reproduced 1050-row direct runs at 35.0014/35.0040 Hz;
  DeePC/LQR descriptive IAE 0.019720/0.020252 deg; peak |delta P|
  0.004163/0.005622 deg/s; both safe/restored. DeePC runtime maximum 7.90 ms.
  Draft includes equations, methods, matched LQR failure, DeePC offline result,
  direct demonstrations, power failure, limitations, reproducibility and
  primary references. Direct plots explicitly state separate reloads.
Acceptance criteria evaluated: deterministic paper metric generation, evidence
  provenance, claim boundaries, and manuscript completeness
Result: PASS for first complete reproducible manuscript package; INCONCLUSIVE
  for venue formatting, author metadata, and DeePC superiority
Reason: scientific content and evidence package are assembled, while final
  submission metadata/template choices require author and target-venue input
Next allowed action within the same stage: author review, venue selection and
  template formatting; no additional flight is required for the bounded paper.
```

## IEEEtran manuscript conversion — 2026-08-10

```text
Date/time: 2026-08-10 (America/Denver)
Current stage: Stage 5 — unchanged
Objective: convert the bounded manuscript and generated evidence into an IEEE
           conference-format LaTeX source with figures and tables
Files changed: paper/ieee/ehekatl_lqr_deepc_ieee.tex,
               paper/ieee/README.md,
               docs/CONTROL_DEVELOPMENT_PROCESS.md
Simulator command sent: none
Inputs: paper/MANUSCRIPT_DRAFT.md, generated PDF figures, registered metrics,
        frozen LQR/DeePC parameters and primary references
Output: IEEEtran two-column source with abstract, keywords, equations, three
  tables, two PDF figures, discussion, limitations, conclusion, reproducibility
  statement and five IEEE-style bibliography entries
Measured results: referenced figure files exist; evidence values retained;
  placeholder author block is explicit
Acceptance criteria evaluated: IEEE source structure and evidence inclusion
Result: PASS for IEEE .tex generation; INCONCLUSIVE for compiled PDF
Reason: this execution environment has no pdflatex/latexmk or IEEEtran class
Next allowed action: replace author metadata and compile in Overleaf, TeX Live,
or MiKTeX using the commands in paper/ieee/README.md.
```

## Distributed elevon control-allocation offline study — 2026-09-17

```text
Date/time: 2026-09-17 (America/Denver)
Current stage: Stage 5 — unchanged
Objective: create a bounded numerical research prior for eight-elevon/two-rudder
  control allocation without altering or engaging the validated aggregate
  X-Plane control path
Files changed: elevon_allocation/allocator.py,
  elevon_allocation/simulate_maneuvers.py,
  elevon_allocation/test_allocator.py,
  elevon_allocation/xplane_shadow_allocator.py,
  elevon_allocation/README.md, elevon_allocation/results/*
Exact command: C:\Research\ehekatl_BWB\.venv-control\Scripts\python.exe -m
  elevon_allocation.simulate_maneuvers --trials 30 --output
  elevon_allocation\results; focused unit tests and static no-write audit
Input conditions/configuration: synthetic transparent effectiveness prior;
  five attitude manoeuvres; nominal, outer-elevon jam, left-rudder failure and
  degraded-outboard-pair cases; 30 Monte Carlo draws per cell; 35 Hz;
  no simulator command
Output artifacts: 1,800 trial rows, summary CSV/JSON and two PDF/PNG figures
Measured results: all three allocator constraint tests PASS. Relative to the
  fault-unaware fixed mixer, the constrained QP reduced mean allocation RMSE
  by about 72% for the outer-elevon jam, 66% for the left-rudder failure and
  61% for degraded outboard elevons. The covariance-aware allocator remained
  feasible but did not outperform the nominal constrained QP at the selected
  prior weight; this negative result is retained.
X-Plane connectivity: one read-only 1-second attempt returned WinError 10054;
  the created shadow script contains no sendCTRL or sendDREF call and sent no
  control. Independent elevon engagement remains blocked because the supplied
  project has no .acf file or verified writable per-surface mapping.
Acceptance criteria evaluated: offline architecture, constraints, failure
  reallocation, covariance term, deterministic reproduction and no-write
  shadow integration
Result: PASS for offline numerical architecture; INCONCLUSIVE for identified
  EHEKATL effectiveness, X-Plane distributed-surface behaviour, wind-tunnel
  behaviour and physical flight
Next allowed action within the current stage: paper synthesis or offline
effectiveness/covariance redesign. Do not engage independent surfaces until
the exact .acf, indices, signs, ownership and restoration path pass new
stage-gated read-only and low-authority tests.
```

## Grouped-ACS versus distributed-elevon mission — 2026-09-17

```text
Date/time: 2026-09-17 (America/Denver)
Current stage: Stage 5 — unchanged
Objective: compare the thesis primary-control grouping with independent
  allocation across eight elevons and two rudders on the same numerical mission
Files changed: elevon_allocation/mission_comparison.py,
  elevon_allocation/mission_campaign.py,
  elevon_allocation/test_mission_comparison.py,
  elevon_allocation/MISSION_COMPARISON_REPORT.md,
  elevon_allocation/README.md,
  elevon_allocation/results/mission_comparison/*
Exact commands: python -m elevon_allocation.mission_comparison; python -m
  elevon_allocation.mission_campaign --trials 20; focused unit tests
Input conditions/configuration: identical 70-second attitude mission, 35 Hz,
  paired uncertainty/noise seeds, common gusts, common outer-loop controller,
  left outer elevon jam at 32 s; synthetic effectiveness prior; no simulator
  command
Measured results: across 20 paired trials, independent allocation reduced
  allocation RMSE 70.74% (approximate 95% interval 66.59–74.89%), post-fault
  attitude RMSE 3.40% (3.22–3.58%), surface RMS command 9.07%, and total
  variation 11.65%. Five allocation/mission unit tests PASS.
Result: PASS for a bounded numerical architecture comparison; INCONCLUSIVE for
  identified EHEKATL, X-Plane, wind-tunnel or physical-flight performance
Next allowed action: identify the ten-column effectiveness matrix and
  covariance from the exact .acf and read-only/low-authority surface tests.
Stage 5 remains active; no independent-surface engagement is authorised.
```

## Ubuntu/X-Plane transfer package and surface-use plot — 2026-09-17

```text
Date/time: 2026-09-17 (America/Denver)
Current stage: Stage 5 — unchanged
Objective: preserve the complete research context for transfer to the Ubuntu
  X-Plane computer and make the actuator-redistribution mechanism visible
Files changed: elevon_allocation/mission_comparison.py,
  elevon_allocation/MISSION_COMPARISON_REPORT.md,
  elevon_allocation/README.md,
  elevon_allocation/results/mission_comparison/mission_surface_redistribution.*,
  elevon_allocation/results/mission_comparison/mission_metrics_table.md,
  ../UBUNTU_AGENT_START_HERE.md, ../tools/build_transfer_manifest.py,
  ../UBUNTU_TRANSFER_SHA256SUMS.txt, docs/CONTROL_DEVELOPMENT_PROCESS.md
Exact commands: run mission_comparison; run five focused allocator/mission
  tests; build transfer SHA-256 manifest; inspect generated PNG
Input conditions/configuration: unchanged synthetic research prior and paired
  70-second mission; no X-Plane connection and no simulator command
Measured results: representative numerical metrics reproduced exactly; 84 core
  tests and five focused allocation/mission tests PASS; 53 key transfer
  artifacts hashed; surface heat map shows the fault-unaware grouped command
  continuing at elevon_L4 while the distributed QP pins the failed effector to
  zero and redistributes demand; transfer handoff records all three workstreams,
  evidence boundaries, exact paths, Ubuntu setup and X-Plane gates
Result: PASS for reproducible visual/report/transfer packaging; INCONCLUSIVE for
  identified X-Plane or physical distributed-elevon performance
Next allowed action: on Ubuntu, verify the transfer hashes, read the complete
  process record, run the read-only shadow logger, archive/hash the exact .acf,
  and build a read-only surface index/sign map. No independent surface write is
  authorised.
```

## IJCOPI official-template review copy — 2026-09-17

```text
Date/time: 2026-09-17 (America/Denver)
Current stage: Stage 5 — unchanged
Objective: focus the publication workstream on the bounded LQR-versus-DeePC
  paper and produce a review copy in the official IJCOPI 2027 template
Files changed: paper/ijcopi/IJCOPI_MANUSCRIPT.md,
  paper/ijcopi/build_ijcopi_2027_docx.py,
  paper/ijcopi/EHEKATL_LQR_DeePC_IJCOPI_2027_Double_Blind.docx,
  paper/ijcopi/IJCOPI_SUBMISSION_READINESS.md,
  paper/ijcopi/qa_render_2027_verified/*,
  docs/CONTROL_DEVELOPMENT_PROCESS.md
Exact commands: compile and run build_ijcopi_2027_docx.py; render the DOCX
  with the document verification workflow; inspect all eight rendered pages;
  run the structural/word-count audit; run DeePC unit tests
Input conditions/configuration: existing frozen R3 evidence only; no new
  simulator connection, command, or controller engagement
Measured results: official-template eight-page double-blind DOCX; English
  abstract 141 words with six keywords; Spanish resumen 125 words with six
  palabras clave; Sections 1–11; two tables and two figures; no placeholder
  text, raw Markdown/LaTeX, tracked changes, or comments; 84/84 core,
  7/7 DeePC, and 5/5 allocation/mission tests pass
Scientific changes: added bilingual metadata and journal-local literature;
  documented frozen hyperparameter selection; specified the deterministic
  projected-gradient step, stopping tolerance, and iteration cap; added a
  frozen evidence-gate table; preserved failed LQR and paired-power gates
Result: PASS for a scientifically bounded IJCOPI review copy; no DeePC
  superiority claim is authorised by the current separate-reload evidence
Next allowed action: author review and unblinded submission metadata. An
  optional 24-pair order-balanced campaign may be performed only after the
  switching/history-handoff protocol is validated. Stage 5 remains active.
```
