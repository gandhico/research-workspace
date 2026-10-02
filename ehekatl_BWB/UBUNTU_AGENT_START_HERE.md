# EHEKATL BWB research transfer and Ubuntu/X-Plane handoff

**Prepared:** 2026-09-17 (America/Denver)  
**Windows research root:** `C:\Research\ehekatl_BWB`  
**Working controller project:** `C:\Research\ehekatl_BWB\project`  
**Current controller-development stage:** Stage 5 (`CURRENT`)  
**Purpose:** preserve the full research context and give an Ubuntu agent a safe,
reproducible starting point for X-Plane work.

## Read this first

Copy the **entire** `ehekatl_BWB` directory. Do not transfer only the plots or
only the Python package. The original ZIP archives, dissertation sources,
controller history, logs, paper evidence, negative results and stage gates are
part of the scientific record.

Before any controller analysis or X-Plane action, the Ubuntu agent must read,
in this order:

1. `project/AGENTS.md`
2. `project/docs/CONTROL_DEVELOPMENT_PROCESS.md` in full
3. this handoff
4. `project/docs/LAST_SESSION_HANDOFF.md`
5. `project/elevon_allocation/README.md`
6. `project/elevon_allocation/MISSION_COMPARISON_REPORT.md`
7. `project/paper/ijcopi/IJCOPI_EXPERIMENT_GATES.md`

`project/docs/CONTROL_DEVELOPMENT_PROCESS.md` is the authoritative controller
record. This handoff is a compact index, not a replacement for that history.
Stage 5 remains active. A successful offline simulation, a successful program
exit, or a stable fitted model does not advance the stage.

## Non-negotiable safety and evidence rules

- Preserve the original backstepping controller as the recovery-capable
  baseline and permanent fallback.
- Do not alter the proven legacy aggregate CTRL routing without a dedicated
  sign/routing gate. The historical working mapping is intentionally unusual.
- Do not command independent elevons until the exact `.acf`, individual surface
  indices, signs, limits, writable mechanism, ownership and restoration path
  are verified.
- `elevon_allocation/xplane_shadow_allocator.py` is read-only. It contains no
  `sendCTRL` or `sendDREF` call. Keep it read-only until the surface gates below
  pass.
- Never widen a command, rate or safety limit to make a failing test pass.
- A safety stop is failed validation evidence. Automatic re-engagement is not
  proof of recovery.
- The current elevon results use a synthetic transparent effectiveness prior.
  They are not identified EHEKATL, X-Plane, wind-tunnel or physical-flight
  results.
- The existing direct LQR and DeePC flights used separate simulator reloads.
  They support feasibility, not controller superiority.

## Three coordinated research workstreams

### A. Revised English dissertation / arXiv edition

**Title:** *Design and Control of the EHEKATL Blended-Wing-Body Aircraft*

| Item | Location | Status |
|---|---|---|
| Immutable Spanish source | `dissertation/source_es/` | Preserve unchanged |
| English LaTeX working copy | `dissertation/source_en/` | Complete machine-translated working draft |
| Compiled English PDF | `dissertation/output/pdf/EHEKATL_English_Dissertation_2026.pdf` | 188 pages; compiled and visually checked |
| Translation audit | `dissertation/tmp/translation_audit.json` | Structural parity passed; language detector is conservative |
| Translation tooling | `dissertation/tools/` | Reproducible scripts retained |
| Status record | `dissertation/TRANSLATION_STATUS.md` | Read with the qualifications below |

The PDF is ready for author review, but it is **not yet an arXiv-ready final**.
It still requires human technical copy-editing, terminology and citation review,
rights/attribution checking for figures, removal or translation of embedded
Spanish artwork, bibliography repair, and a clean arXiv source-package test.
Do not describe machine translation plus visual QA as professional language
editing.

### B. IJCOPI LQR--DeePC paper

**Title:** *From Offline Optimality to Real-Time Simulation Flight: Delay-Aware
LQR and Constrained DeePC for an EHEKATL Blended-Wing-Body Aircraft*

| Item | Location | Status |
|---|---|---|
| Editable manuscript source | `project/paper/ijcopi/IJCOPI_MANUSCRIPT.md` | Complete bounded manuscript |
| Double-blind Word manuscript | `project/paper/ijcopi/EHEKATL_LQR_DeePC_IJCOPI_2027_Double_Blind.docx` | Official 2027 template; 8 pages; rendered and visually checked |
| Rendered review PDF | `project/paper/ijcopi/qa_render_2027_verified/EHEKATL_LQR_DeePC_IJCOPI_2027_Double_Blind.pdf` | Verified review copy |
| Submission readiness | `project/paper/ijcopi/IJCOPI_SUBMISSION_READINESS.md` | Requirements and author-side actions |
| Experiment gates | `project/paper/ijcopi/IJCOPI_EXPERIMENT_GATES.md` | Authoritative strengthening plan |
| Claims matrix | `project/paper/CLAIMS_MATRIX.md` | Claim/evidence boundary |
| Dataset registry | `project/paper/DATASET_REGISTRY.csv` | Registered logs and provenance |
| Reproducible figures/metrics | `project/paper/generated/` | Generated from registered evidence |

Current supported conclusion: delay-aware LQR and constrained DeePC both ran
safely at 35 Hz behind the common safety/fallback/restoration interface. DeePC
solved within the 28.57 ms period in the accepted direct demonstration. The
evidence does not establish DeePC superiority.

The strongest additional IJCOPI experiment is not another unmatched flight.
First validate within-session controller switching, DeePC history warm-up and
backstepping handoff in observe-only mode and one excluded design pilot. Then,
only after freezing hashes, order randomisation, waveform, exclusions and the
primary metric, collect **24 within-session sign-balanced pulse pairs per
controller at R3**. Report the paired effect and its 95% interval. The bounded
feasibility manuscript can be submitted without this superiority experiment;
the experiment is required to strengthen the comparative claim.

### C. Backstepping + constrained allocation + distributed elevons

**Proposed title:** *Covariance-Aware Optimal Control Allocation for an
Adaptive-Backstepping EHEKATL Blended-Wing-Body Aircraft with Distributed
Elevons*

Important naming qualification: the live Python baseline is currently a
backstepping-inspired scalar empirical controller. Do not call it the fully
implemented adaptive law until it is reconciled with the CCE vector/regressor
equations and parameter update law.

The proposed architecture is:

```text
reference / manoeuvre
  -> estimator and envelope monitor
  -> backstepping virtual moment [L_c, M_c, N_c]
  -> constrained allocator using B_eff and its covariance
  -> eight independent elevons + two rudders
  -> X-Plane aircraft / later wind-tunnel model
  -> measured state, moments and actual surface positions
```

Current software and evidence:

| Item | Location | Evidence |
|---|---|---|
| Allocator | `project/elevon_allocation/allocator.py` | Fixed mixer, constrained QP, covariance-aware QP |
| Five-manoeuvre campaign | `project/elevon_allocation/simulate_maneuvers.py` | 1,800 offline runs |
| Mission comparison | `project/elevon_allocation/mission_comparison.py` | Same mission and outer controller for grouped ACS and QP |
| Paired uncertainty campaign | `project/elevon_allocation/mission_campaign.py` | 20 paired trials |
| Read-only X-Plane bridge | `project/elevon_allocation/xplane_shadow_allocator.py` | Proposed commands only; zero writes |
| Tests | `project/elevon_allocation/test_*.py` | Five focused tests pass |
| Report | `project/elevon_allocation/MISSION_COMPARISON_REPORT.md` | Methods, tables, plots and limits |
| Raw/results package | `project/elevon_allocation/results/` | CSV, JSON, PNG and PDF |

## Numerical mission definition

Both architectures use the same 70 s, 35 Hz attitude programme: trim, climb,
right survey turn, level leg, reversing turn, descent and flare. They use the
same uncertain plant draw, sensor/process noise, gusts at 23 s and 46 s,
outer-loop controller, surface/rate limits and reference. At 32 s,
`elevon_L4` is jammed at zero.

- **Thesis grouped ACS:** inner pairs move as elevators, outer pairs move as
  ailerons and both rudders share one directional command. It is fault-unaware.
- **Distributed QP:** the same virtual acceleration request is allocated across
  eight elevons and two rudders. The jam is detected, the failed command is
  pinned to zero and demand is redistributed under position/rate constraints.

Representative same-seed result:

| Architecture | Attitude RMSE [deg] | Peak error [deg] | Post-fault RMSE [deg] | Allocation RMSE [deg/s^2] | Surface RMS [-] | Total variation [-] |
|---|---:|---:|---:|---:|---:|---:|
| Thesis grouped ACS | 2.1583 | 5.9031 | 2.4409 | 0.3204 | 0.02964 | 4.8992 |
| Distributed elevon QP | 2.1159 | 5.8421 | 2.3702 | 0.1683 | 0.02749 | 4.4288 |

Twenty paired trials, positive values favouring the distributed QP:

| Metric | Mean reduction | Approximate 95% interval |
|---|---:|---:|
| Overall attitude RMSE | 2.32% | 2.18% to 2.46% |
| Peak attitude error | 1.01% | 0.94% to 1.08% |
| Post-fault attitude RMSE | 3.40% | 3.22% to 3.58% |
| Allocation RMSE | 70.74% | 66.59% to 74.89% |
| Surface RMS command | 9.07% | 8.51% to 9.62% |
| Command total variation | 11.65% | 11.32% to 11.98% |

Interpretation: the architecture primarily improves post-fault moment
realisation and actuator use; closed-loop attitude gains are deliberately
modest because the outer loop is conservative and only one of ten effectors is
lost. This is the scientifically useful result. Do not advertise it as a
physical-aircraft performance prediction.

## Reproduce the Windows numerical results

```powershell
Set-Location 'C:\Research\ehekatl_BWB\project'
& 'C:\Research\ehekatl_BWB\.venv-control\Scripts\python.exe' -m unittest elevon_allocation.test_allocator elevon_allocation.test_mission_comparison -v
& 'C:\Research\ehekatl_BWB\.venv-control\Scripts\python.exe' -m elevon_allocation.simulate_maneuvers --trials 30 --output 'elevon_allocation\results'
& 'C:\Research\ehekatl_BWB\.venv-control\Scripts\python.exe' -m elevon_allocation.mission_comparison --output 'elevon_allocation\results\mission_comparison'
& 'C:\Research\ehekatl_BWB\.venv-control\Scripts\python.exe' -m elevon_allocation.mission_campaign --trials 20 --output 'elevon_allocation\results\mission_comparison'
```

## Transfer layout on Ubuntu

Keep the transferred research tree separate from the live X-Plane checkout
until the hashes and paths are audited. A safe example is:

```text
/home/ubuntu/GHYN/ehekatl_BWB/                         transferred research root
/home/ubuntu/GHYN/ehekatl_BWB/project/                 transferred working project
/home/ubuntu/GHYN/Xplane_controllers/EHEKATL_BWB_XP12  existing live X-Plane project
```

Do not blindly overwrite the live X-Plane directory. Compare it to the
transferred `project/` first. The process document was originally written
against the live path and still records that path for historical commands.

From the transferred root:

```bash
cd /home/ubuntu/GHYN/ehekatl_BWB
sha256sum -c UBUNTU_TRANSFER_SHA256SUMS.txt
```

Create a new Linux environment rather than copying either Windows virtual
environment:

```bash
cd /home/ubuntu/GHYN/ehekatl_BWB/project
python3 -m venv ../.venv-control-linux
source ../.venv-control-linux/bin/activate
python -m pip install --upgrade pip
python -m pip install numpy scipy matplotlib pillow
python -m unittest discover -s tests -v
python -m unittest elevon_allocation.test_allocator elevon_allocation.test_mission_comparison -v
python -m elevon_allocation.mission_comparison --output elevon_allocation/results/mission_comparison
python -m elevon_allocation.mission_campaign --trials 20 --output elevon_allocation/results/mission_comparison
```

The historical live project also contains a venv at
`backstepping/ehekatl_xplane12_backstepping_bridge/.venv/`. Preserve it for the
old scripts because embedded absolute paths may depend on it. Use the new
environment for the portable offline allocation package.

## X-Plane preparation and first allowed actions

The Windows transfer does not contain the aircraft `.acf`. The controller
history identifies the expected live file as:

```text
Aircraft/GHYN/EHEKATL BWB 5 1.acf
```

Before editing it:

1. Copy it to an immutable archive and record its SHA-256 hash.
2. Record X-Plane version, aircraft internal version, payload, fuel, weather,
   failures, artificial stability, saved situation and exact modification.
3. Create a separate aircraft variant for the distributed-elevon experiment.
4. Build an authoritative surface table: ID, side, span station, role, sign,
   min/max deflection, slew, command path, measured-deflection dataref, failure
   mask and restoration behaviour.
5. Confirm whether X-Plane datarefs are actually writable for independent
   surfaces. If not, use a small X-Plane SDK plugin rather than pretending that
   aggregate `sendCTRL` validates allocation.

### Gate sequence for distributed surfaces

| Gate | Required evidence | Control writes |
|---|---|---|
| G0 aircraft provenance | Exact `.acf`, copy, SHA-256, version and configuration | None |
| G1 connectivity | XPlaneConnect responds; paused/replay/live state recorded | None |
| G2 surface map | Every realised elevon/rudder index and sign identified | None |
| G3 paused single-surface check | Requested vs realised index/zero/sign/limit | One surface, paused only |
| G4 low-authority live check | One surface at a time; frozen envelope and restoration | Minimal, predeclared |
| G5 effectiveness ID | Repeated balanced excitation at low/nominal/high dynamic pressure | Backstepping stabilised |
| G6 covariance model | Full ten-column `B_eff` covariance and held-out residuals | Offline analysis |
| G7 replay | QP, robust QP and fallback replay exactness | Offline/read-only |
| G8 excluded design pilot | One guarded pilot with permanent backstepping fallback | Frozen low authority |
| G9 confirmation | Paired, preregistered five-manoeuvre trials | Only after G0--G8 pass |

No later gate may be skipped because an earlier one “looks reasonable.”

### First Ubuntu X-Plane run: read-only shadow mode

With X-Plane 12 running, the EHEKATL aircraft loaded and XPlaneConnect enabled:

```bash
cd /home/ubuntu/GHYN/ehekatl_BWB/project
source ../.venv-control-linux/bin/activate
mkdir -p logs
python -m elevon_allocation.xplane_shadow_allocator \
  --duration 20 \
  --hz 20 \
  --roll-setpoint 0 \
  --pitch-setpoint 0 \
  --output "logs/elevon_allocator_shadow_$(date +%Y%m%d_%H%M%S).csv"
```

This reads roll/pitch/yaw, P/Q/R, IAS, pause and replay state; computes virtual
acceleration demand and proposed ten-surface commands; and logs
`controls_sent=0`. A failed connection or empty log is a connectivity result,
not permission to add writes.

Immediately after the run, verify the source still has no writes:

```bash
cd /home/ubuntu/GHYN/ehekatl_BWB/project
if rg -n 'sendCTRL|sendDREF' elevon_allocation/xplane_shadow_allocator.py; then
  echo 'FAIL: shadow source contains a write call'
else
  echo 'PASS: shadow source remains read-only'
fi
```

## Five-manoeuvre physical validation plan

After the ten-column effectiveness model and covariance are identified, compare
fixed grouping, weighted pseudoinverse, deterministic constrained QP and
covariance-aware/robust QP on:

1. symmetric elevon pitch doublet / pull-up recovery;
2. differential elevon roll doublet / bank reversal;
3. rudder doublet and Dutch-roll damping;
4. coordinated climbing/descending turn with coupled demand;
5. gust recovery with one elevon degraded, rate-limited or jammed.

Use repeated paired trials. Five manoeuvres are conditions, not five samples.
Report IAE, RMSE, peak, settling, command energy, total variation, allocation
residual, saturation, loads, compute time and safety events with 95% intervals.

The current covariance-aware allocator is an honest negative result: it stayed
feasible but was over-regularised and did not beat the ordinary constrained QP.
Do not tune it to force a win. Identify covariance from the aircraft and use a
preregistered robust/chance-constrained formulation.

## HyperLIF/CMG and sensor work

Keep HyperLIF/CMG as a separate later neuromorphic contribution. First freeze
the classical backstepping + allocation stack. Then use HyperLIF/CMG only as a
bounded residual estimator/allocator behind the same safety filter and compare
it fairly with LIF, adaptive LIF, Izhikevich/SRM-style spiking baselines and a
matched non-spiking recurrent baseline. Report accuracy, robustness, latency,
spike count/sparsity, compute/energy proxy and fallback events. Do not let a
neural residual bypass position, rate, load or envelope constraints.

Priority physical sensor additions for the EHEKATL platform:

| Layer | Recommended instrumentation | Research role |
|---|---|---|
| Flight state | Dual IMUs, GNSS/RTK, barometer, magnetometer | Redundant state estimation and integrity monitoring |
| Air data | Calibrated pitot-static plus five-hole probe | Angle of attack, sideslip and dynamic-pressure scheduling |
| Surface state | Absolute encoder on every elevon and rudder, at least 100--200 Hz | Actual deflection, backlash, rate, jam and allocation validation |
| Propulsion/power | RPM, current, voltage, motor/ESC temperature | Energy-aware control and fault detection |
| Loads/structure | Wing-root strain, selected hinge/servo loads, accelerometers | Load-aware allocation, aeroelasticity and flutter research |
| Navigation/logistics | Dual-band GNSS, geofence/remote-ID interface, payload mass/CG sensing | Repeatable mission and logistics research |
| Defence-oriented research | EO/IR or radar only as modular payloads with legal/safety review | Perception research; no control claim without integration evidence |

Five-hole air data and actual surface-position sensing are the highest priorities
for the allocation paper because they directly determine `B_eff`, covariance
and commanded-versus-realised evidence.

## Known blockers and unresolved issues

- No `.acf` is present in this Windows research transfer.
- Independent surface write indices and ownership are unverified.
- The offline effectiveness matrix is a research prior and omits servo
  dynamics, hinge moments, nonlinear aerodynamic tables, structural
  flexibility, airspeed/AoA dependence and ground effect.
- The covariance-aware penalty needs identified covariance and redesign.
- The mission comparison uses a simplified attitude plant; it is an
  architecture comparison, not a digital twin.
- The IJCOPI superiority gate is not passed; switching/history handoff and the
  24-pair confirmation remain undone.
- The English dissertation needs human technical editing and arXiv rights/build
  audit despite the complete review PDF.
- The project directory is not a Git repository. Preserve timestamps and the
  supplied checksum manifest, or initialise a new repository only after the
  transferred copy is verified.

## Key plots and tables

```text
project/elevon_allocation/results/mission_comparison/
  mission_attitude_comparison.png/.pdf
  mission_allocation_comparison.png/.pdf
  mission_surface_redistribution.png/.pdf
  mission_monte_carlo_improvement.png/.pdf
  mission_metrics_table.md
  mission_summary.csv/.json
  mission_monte_carlo.csv
  mission_monte_carlo_summary.json
  mission_timeseries.csv
```

## Ready-to-paste instruction for the Ubuntu agent

```text
Continue the EHEKATL work from the transferred research tree. First read
project/AGENTS.md and project/docs/CONTROL_DEVELOPMENT_PROCESS.md completely,
then read UBUNTU_AGENT_START_HERE.md and the linked reports. Preserve Stage 5,
the original backstepping fallback, all limits, all negative results and the
claim boundaries. Verify UBUNTU_TRANSFER_SHA256SUMS.txt. Do not overwrite the
live X-Plane project or edit the .acf until its exact path and hash are archived.
The first X-Plane task is the existing read-only elevon shadow logger; confirm
it contains no sendCTRL/sendDREF and produce a timestamped CSV with
controls_sent=0. Then audit the .acf and build a read-only surface map. Do not
engage independent elevons until gates G0-G8 in this handoff have objective
evidence. Record every result, command, input, hash and decision in
project/docs/CONTROL_DEVELOPMENT_PROCESS.md.
```

## Publication map

| Work | Best current target/role |
|---|---|
| Revised English dissertation | arXiv `eess.SY`, after rights/language/source audit |
| LQR--DeePC implementation-gap paper | IJCOPI, bounded feasibility now; stronger comparison after paired gate |
| Backstepping + elevon allocation | *Aerospace Science and Technology* or *AIAA Journal of Aircraft*; JGCD if theory dominates |
| HyperLIF/CMG residual augmentation | Separate neuromorphic/TAES-style paper after classical validation |
| Wind-tunnel effectiveness/covariance | Strong independent validation study and allocator update |

## Integrity files

`UBUNTU_TRANSFER_SHA256SUMS.txt` contains SHA-256 values for the key documents,
source files, results and deliverables named in this handoff. Regenerate it on
Windows with `tools/build_transfer_manifest.py` only after intentional changes,
then record the change in `project/docs/CONTROL_DEVELOPMENT_PROCESS.md`.
