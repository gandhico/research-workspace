# Ubuntu/X-Plane night mission plan

**Prepared:** 2026-09-17 (America/Denver)  
**Priority:** close the IJCOPI LQR–DeePC paper; preserve control-allocation work
for the next research stage.  
**Current controller-development stage:** Stage 5 (`CURRENT`)  
**Aircraft:** EHEKATL BWB G33 scale model in X-Plane 12  
**Required safety baseline:** the proven backstepping controller remains the
permanent fallback.

## Decision before running anything

The current eight-page IJCOPI manuscript is already complete as a bounded
real-time feasibility and implementation-gap paper. It can be submitted
without another X-Plane run. Its supported conclusion is that delay-aware LQR
and constrained DeePC both executed safely at 35 Hz, while the existing data do
not prove that DeePC is superior.

Run the IJCOPI missions below only if the intended paper claim is strengthened
to a paired comparison. Do not describe the older separate-reload LQR and
DeePC demonstrations as a matched experiment.

The control-allocation missions are a separate workstream. Tonight, they may
advance only through the surface-provenance, read-only and low-authority gates
that the exact aircraft file supports. An aggregate yoke/CTRL flight is not
evidence for independent elevon allocation.

## 1. Ubuntu setup and integrity

Unzip each archive into a new directory. Do not overwrite the live X-Plane
checkout.

```bash
mkdir -p /home/ubuntu/GHYN/transfers
cd /home/ubuntu/GHYN/transfers
unzip EHEKATL_IJCOPI_Ubuntu_20260917.zip -d ijcopi_transfer
unzip EHEKATL_Control_Allocation_Ubuntu_20260917.zip -d allocation_transfer
```

Verify each package from inside its extracted root:

```bash
sha256sum -c PACKAGE_SHA256SUMS.txt
```

Read, in order:

1. `UBUNTU_XPLANE_NIGHT_MISSION_PLAN.md`;
2. `project/AGENTS.md`;
3. `project/docs/CONTROL_DEVELOPMENT_PROCESS.md` in full;
4. `UBUNTU_AGENT_START_HERE.md`;
5. `project/paper/ijcopi/IJCOPI_EXPERIMENT_GATES.md` for the IJCOPI archive;
6. `project/elevon_allocation/README.md` for the allocation archive.

Create a new Linux environment; do not copy a Windows virtual environment:

```bash
cd project
python3 -m venv ../.venv-control-linux
source ../.venv-control-linux/bin/activate
python -m pip install --upgrade pip
python -m pip install numpy scipy matplotlib pillow python-docx
python -m unittest discover -s tests -p 'test_*.py' -v
python -m unittest discover -s deepc/tests -p 'test_*.py' -v
```

Expected transferred baseline: 84 core tests and 7 DeePC tests pass. The
allocation archive also has 5 focused tests:

```bash
python -m unittest \
  elevon_allocation.test_allocator \
  elevon_allocation.test_mission_comparison -v
```

Before using X-Plane, archive and hash the live aircraft file expected at:

```text
Aircraft/GHYN/EHEKATL BWB 5 1.acf
```

Record the X-Plane build, aircraft hash, payload, fuel, weather, failures,
artificial stability, simulator speed, replay state and saved situation in
`project/docs/CONTROL_DEVELOPMENT_PROCESS.md`.

## 2. Frozen IJCOPI operating condition

All paired confirmation data must use the existing R3 condition:

| Quantity | Frozen value |
|---|---:|
| Altitude | 1700 m, tolerance ±100 m |
| Indicated airspeed | 39 kt, tolerance ±2 kt |
| Approximate dynamic pressure | 240 Pa |
| Pitch setpoint | 1.3 deg |
| Roll setpoint | 0 deg |
| Controller/sample rate | 35 Hz |
| Backstepping fallback update | 10 Hz |
| Maximum absolute pitch/roll | 10 deg |
| Maximum absolute body rate | 20 deg/s |
| Roll command perturbation limit | 0.0002 |
| Roll slew limit | 0.00005 per sample |
| Artificial stability | enabled and recorded |
| Weather | manual/clear frozen configuration |
| Failures | none |
| Simulator state | live, 1× speed, not paused, not replay |

Do not widen a bound or change the operating point after viewing confirmation
results.

## 3. IJCOPI mission I0 — read-only installation check

Purpose: prove that the transferred controllers, logging schema and XPlaneConnect
path work without sending a control.

```bash
cd project
source ../.venv-control-linux/bin/activate
mkdir -p logs/night_campaign
STAMP=$(date +%Y%m%d_%H%M%S)

python -B lqr/run_lqr_direct_xp12.py \
  --duration 30 --io-hz 35 --fallback-hz 10 \
  --out "logs/night_campaign/I0_lqr_observe_${STAMP}.csv"

python -B deepc/run_deepc_direct_xp12.py \
  --duration 30 --io-hz 35 --fallback-hz 10 \
  --out "logs/night_campaign/I0_deepc_observe_${STAMP}.csv"
```

Pass only if both logs contain about 1050 rows, `controls_sent=0`, no NaN/Inf,
35 Hz mean timing, maximum gap no greater than 71.428572 ms, live simulator
state, and the R3 start gate passes. A failed connection is a failed I0 gate;
it is not permission to bypass logging or safety checks.

## 4. IJCOPI mission I1 — excluded direct design checks

Purpose: confirm each frozen controller independently after transfer. These
runs are design checks and must not enter the paired superiority estimate.

Reload the identical R3 saved situation before each command:

```bash
STAMP=$(date +%Y%m%d_%H%M%S)
bash lqr/run_lqr_direct.sh
bash deepc/run_deepc_direct.sh
```

The launchers use the existing two-pulse disturbance: 0.2 s half-sine pulses
at 10 s and 12 s, signs `+,-`, amplitude `0.00005`, additive after the selected
controller. Preserve that waveform exactly. Each strict analyser must pass;
otherwise stop and retain the failed run.

## 5. IJCOPI mission I2 — paired-runner validation

The transferred project does not falsely label an unvalidated switcher as
flight-ready. The Ubuntu agent must implement and test a single-session paired
runner before engaged use. Suggested files are:

```text
scripts/run_rich_r3_lqr_deepc_paired_xp12.py
scripts/analyze_rich_r3_lqr_deepc_paired.py
tests/test_rich_r3_lqr_deepc_paired.py
configs/rich_R3_lqr_deepc_paired_protocol.json
```

Required implementation contract:

- instantiate the frozen delay-aware LQR, frozen DeePC and backstepping
  fallback once at run start;
- update LQR and DeePC continuously from the same measurements, including when
  each is not selected, so their histories remain valid;
- use one ownership session and one captured trim; do not reload between
  controllers or pulse pairs;
- select only one controller at a time and log both proposed commands;
- retain the existing combined command/slew bounds and the permanent,
  non-reengaging backstepping fallback latch;
- log controller selection, pair number, order, pulse sign, both histories,
  runtime, start/safety states, realised yoke/surface input and restoration;
- restore the captured yoke and override states in a `finally` path;
- default to observe-only; require an explicit `--engage` flag;
- prohibit confirmation mode until unit tests, an observe-only rehearsal and
  one excluded engaged design pilot all pass.

Validate in this order:

1. deterministic unit/replay tests with no X-Plane connection;
2. one full 152 s observe-only schedule with `controls_sent=0`;
3. one engaged 4-pair design pilot, excluded forever from confirmation;
4. exact offline replay of the pilot, including controller histories;
5. restoration and permanent-fallback fault injection.

Do not start I3 if any I2 item fails.

## 6. IJCOPI mission I3 — required 24-pair confirmation

Purpose: produce the minimum currently powered data for a DeePC-versus-LQR
superiority claim.

Run one continuous R3 session of at least 152 s:

- 8 s initial stabilisation and DeePC-history warm-up;
- 24 six-second blocks, indexed `j = 0,...,23`;
- pulse 1 begins at `8 + 6j + 1` s;
- pulse 2 begins at `8 + 6j + 4` s;
- each pulse is a 0.2 s half-sine of magnitude `0.00005`;
- pair sign is positive for even `j` and negative for odd `j`;
- controller order is LQR→DeePC for even `j` and DeePC→LQR for odd `j`;
- no reload, trim recapture or controller reset is allowed inside the run;
- both controllers continue shadow updates throughout;
- use a one-second post-pulse response window and the remaining time as frozen
  washout; flag, do not silently delete, contaminated windows.

This produces 24 pulses per controller, sign balanced and order balanced. The
primary estimand is the ratio

```text
mean per-pulse integral absolute detrended roll-rate error over 1 s:
DeePC / LQR
```

The predeclared performance decision is:

- superiority only if the upper limit of the paired 95% confidence interval is
  below 1.0 and every timing, safety, realisation, replay and restoration gate
  passes;
- otherwise report feasibility without superiority, including the point
  estimate, interval, exclusions and all failed gates.

The confidence interval must use paired resampling of complete pulse pairs or
an equivalently predeclared paired method. Never round a failing value to make
it pass. Never retune LQR, DeePC, the pulse or exclusion rules after opening I3.

If validated switching cannot be completed, the fallback design is 48 pulses
per controller in separate-reload runs, but this is slower and weaker against
reload-specific background variation. Do not substitute the old single direct
runs for either design.

## 7. IJCOPI data required to close the paper

The campaign is complete only when all items exist:

1. frozen protocol JSON and SHA-256 hashes of runner, controllers and configs;
2. raw 35 Hz CSV with all 24 pairs and no overwritten rows;
3. machine-readable gate report for start state, timing, command/slew,
   safety, fallback, controller histories, exact replay and restoration;
4. per-pulse table with pair, order, sign, pre-pulse baseline, 1 s IAE, peak,
   final error, command energy, maximum slew and contamination flag;
5. paired effect estimate, 95% interval and sensitivity with flagged pairs
   included/excluded according to the frozen rule;
6. runtime table for both controllers: median, p95, p99, maximum and deadline
   misses on the same computer;
7. publication figures: overlaid pulse responses, paired IAE slope/forest plot,
   runtime distributions and gate summary;
8. updated `paper/DATASET_REGISTRY.csv`, `paper/CLAIMS_MATRIX.md`, manuscript
   Results/Discussion/Limitations and the development-process record;
9. regenerated DOCX/PDF and a complete page-by-page visual inspection.

If I3 cannot pass safely tonight, close the existing bounded paper instead of
forcing a superiority claim.

## 8. Control allocation — first Ubuntu actions

Run the transferred numerical baseline first:

```bash
cd project
source ../.venv-control-linux/bin/activate
python -m unittest \
  elevon_allocation.test_allocator \
  elevon_allocation.test_mission_comparison -v
python -m elevon_allocation.mission_comparison \
  --output elevon_allocation/results/mission_comparison
python -m elevon_allocation.mission_campaign \
  --trials 20 \
  --output elevon_allocation/results/mission_comparison
```

Then perform the existing read-only X-Plane shadow mission:

```bash
mkdir -p logs
python -m elevon_allocation.xplane_shadow_allocator \
  --duration 20 --hz 20 \
  --roll-setpoint 0 --pitch-setpoint 0 \
  --output "logs/elevon_allocator_shadow_$(date +%Y%m%d_%H%M%S).csv"
```

Pass only with a complete log, valid aircraft state and `controls_sent=0` in
every row. Confirm the source still contains no `sendCTRL` or `sendDREF` call.

## 9. Control allocation — surface/effectiveness missions

Proceed sequentially; never skip a gate.

### A0 — aircraft and surface provenance

- archive and hash the `.acf`;
- create a separate experimental aircraft variant;
- record each of eight elevons and two rudders: ID, side, span station, native
  role, realised-deflection index, command mechanism, sign, neutral, min/max,
  rate limit, failure mask and restoration behaviour.

### A1 — paused one-surface map

With the aircraft paused and all other surfaces held neutral, exercise one
surface at a time using `0,+a,-a,0`, where

```text
a = min(1 degree, 5% of that surface's verified symmetric travel)
```

Use at least two seconds per plateau and record requested/realised deflection
at at least 100 Hz if available. Every surface must return to its captured
neutral and no other surface may move unexpectedly. Stop on an index, sign,
ownership or restoration mismatch.

### A2 — low-authority live surface checks

At R3 under backstepping stabilisation, repeat one surface at a time with a
smooth half-sine command of the same `a`, first positive then negative, with at
least five seconds of recovery. Freeze attitude/rate/load abort limits before
the first command. These are excluded design runs.

### A3 — effectiveness identification

Identify all ten actuator columns at three frozen conditions:

| Condition | Altitude | IAS | Role |
|---|---:|---:|---|
| R1 | 1400 m | 32 kt | low dynamic pressure |
| R3 | 1700 m | 39 kt | reference |
| R4 | 1700 m | 48 kt | higher effectiveness |

For every surface and condition, collect one training and one unopened
validation run using the same bounded, zero-mean multisine, superimposed on
backstepping. Balance positive/negative content, log requested and realised
surface position, P/Q/R, attitude, air data, total control, timing, ownership,
loads if available and every abort/restoration state. Estimate the full
three-by-ten effectiveness matrix, actuator dynamics and coefficient
covariance; validate temporally, not by random row shuffling.

### A4 — allocation replay and excluded pilot

Replay fixed grouping, weighted pseudoinverse, constrained QP and
covariance-aware/robust QP on the same held-out data. Preserve the current
negative covariance result unless identified covariance genuinely changes it.
Freeze the selected allocator, limits and fallback, then run one excluded
low-authority X-Plane pilot.

### A5 — five-manoeuvre paired confirmation

Only after A0–A4 pass, compare the thesis grouped ACS and distributed allocation
with repeated, order-balanced matched trials:

1. symmetric elevon pitch doublet / pull-up recovery;
2. differential elevon roll doublet / bank reversal;
3. rudder doublet / Dutch-roll damping;
4. coordinated climbing and descending turn with coupled demand;
5. gust recovery with one elevon degraded, rate-limited or jammed.

Five manoeuvres are conditions, not five samples. Collect enough paired repeats
for a predeclared 0.80-power target after a pilot variance estimate. Report IAE,
RMSE, peak, settling, allocation residual, command energy, total variation,
saturation, loads, solver time, fallback and safety events with 95% intervals.

## 10. Tonight's recommended stopping point

Priority order:

1. verify the IJCOPI archive and reproduce all tests;
2. run I0;
3. implement and validate I2;
4. run I3 only if I2 passes without relaxing any gate;
5. regenerate the manuscript with either the honest paired result or the
   existing bounded conclusion;
6. for allocation, reproduce the numerical campaign and complete only A0 plus
   the read-only shadow run unless the independent surface interface is already
   objectively verified.

Record every command, file hash, configuration, failure and decision in
`project/docs/CONTROL_DEVELOPMENT_PROCESS.md`.

## Ready-to-paste instruction for Ubuntu Codex

```text
Continue the EHEKATL work from this extracted archive. Read
UBUNTU_XPLANE_NIGHT_MISSION_PLAN.md, project/AGENTS.md and the complete
project/docs/CONTROL_DEVELOPMENT_PROCESS.md before acting. The immediate
priority is the IJCOPI LQR–DeePC paper. Preserve Stage 5, the frozen R3
operating condition, both controller configurations, all command/slew/safety
limits, the backstepping permanent fallback and all negative results. First
verify PACKAGE_SHA256SUMS.txt and run the transferred tests. Run mission I0.
Then implement the single-session paired runner exactly as mission I2 specifies,
with unit tests and observe-only default. Do not engage mission I3 until I2's
tests, rehearsal, excluded pilot, exact replay and restoration all pass. If I3
cannot pass safely, retain the bounded no-superiority paper. Keep distributed
elevon allocation separate: reproduce its offline results, run only the
read-only shadow logger, archive/hash the .acf and build the surface map before
any independent surface write. Append every action and result to the process
record.
```

