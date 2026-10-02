# ACC 2027 CMG--PES project status table

**Checkpoint:** 2026-08-31  
**Paper title:** *Online PES-Adapted Neuromorphic Membrane--Gate Residual
Control for Actuator-Constrained UAV Quaternion Attitude Tracking*  
**Primary repository:** `C:\Research\papers\ACC2027_Gate_Residual_Control`

This document separates completed evidence, integration tests, preliminary
implementations, and future work. A successful software smoke test is not
labeled as physical or paper-grade validation.

## 1. Research identity and architecture

| Item | Current definition | Status / interpretation |
|---|---|---|
| Baseline controller | Platform-native controller: quaternion PD for UAV/PD Hover, LQR for QUBE and the first Hover campaign, PID/SMC/NMPC for QCar | The residual augments rather than replaces the baseline. |
| Neural element | Continuous coupled membrane--gate (CMG) unit with state `(v,r)` | Custom dynamical neuron; non-spiking and not a conventional LIF reset model. |
| Directional encoding | Two units per residual axis: `+j` and `-j` | Three attitude channels give six CMG units. |
| Adaptive conductance | `g_i(J_i)=g_0+g_s|J_i|`; fixed form uses `g_i=g_0` | Neuron-level adaptation; conductance is present in both forms. |
| Gate dynamics | `tau_r rdot = sigmoid(alpha(v-v_th+gamma r))-r` | Gate and membrane are mutually coupled. |
| Membrane dynamics | `vdot=(v_rest-v+J)/tau + g(J)r^2(v_reset-v)` | Exponentially integrated at the neural timestep. |
| Decoder activity | `a_i=clip(k_r r_i,0,1)` | Decoder reads gate-derived activity; membrane affects it indirectly through coupling. |
| Decoder | `y=W a`, initially `W_0=[I,-I]` | Three outputs from six directional units. |
| Online adaptation | PES: `Delta W = eta(y*-y)a^T`, with leak and weight projection | Controller-level adaptation; this accounts for the large nominal improvement. |
| Residual law | `delta u=beta u_max elementwise clip(y,-1,1)` | Bounded neural correction. |
| Final command | `u=clip(u_0+delta u,u_min,u_max)` | Baseline-preserving additive residual architecture. |
| Legacy comparison | `(1-beta)u_0+beta u_neural` | Neural blending; retained only as historical evidence, not the final architecture. |
| Preferred name | Coupled membrane--gate (CMG) unit / CMG--PES residual controller | Historical files may still contain HyperLIF compatibility names. |

## 2. Evidence and implementation by platform

| Platform / backend | Baseline and residual interface | Missions available | Best established evidence | Evidence tier | Current limitation / next action |
|---|---|---|---|---|---|
| Skydio X2, MuJoCo rotor model | Quaternion PD body torque; six CMG units; four-rotor allocation | hover, roll, full3, hard45, hardstep, yaw360 | Complete matched 45 s PD/Nengo-PES campaign; 17.36--60.58% mean-error improvement on nontrivial missions | Strong nominal simulation / paper candidate | Single nominal run per condition; full repeated robustness/hold-out statistics remain desirable. |
| Crazyflie rotor-design, MuJoCo | Same quaternion-PD/CMG path; explicit four rotors at 1.5x declared actuator scale | Same six missions | Complete matched 45 s campaign; 17.33--60.60% mean-error improvement | Controller/actuator co-design simulation | Not stock CF2 hardware; must always be labeled the 1.5x rotor-authority design variant. |
| Stock Menagerie CF2 | Virtual collective/moment actuator interface | hard45 boundary study | Approximately 99.88% saturation; cannot execute Hard45 fairly | Actuator-feasibility boundary | Do not interpret as a controller failure or claim hardware applicability at stock authority. |
| QUBE Servo 3 pendulum, QLabs | LQR plus bounded voltage residual | balance/hold matrix | 3 trials per controller, stable tails and active PES; online-PES adaptive 1.0570+/-0.0015 deg versus LQR 1.0581+/-0.0012 deg | Valid virtual-twin transfer/safety result | Practically equivalent to LQR, not an improvement claim; next useful test is repeated reset-controlled disturbance rejection. |
| Quanser 3DOF Hover, physical, vendor LQR campaign | Vendor LQR plus four-motor CMG/PES voltage residual | hard45, full3, yaw360 | Final frozen improvements: +1.75%, +2.47%, +4.79% | First physical hardware validation, n=1 | Repeat trials needed; final frozen values are newer than the current manuscript table. |
| Quanser 3DOF Hover, physical, explicit quaternion-PD campaign | MuJoCo-matched quaternion PD; three torque residuals mapped to F/B/L/R voltages | roll, full3, hard45; yaw360/hardstep qualification attempted | Best valid matched pairs: roll +21.67%, full3 +1.57%, hard45 +1.56% | Physical follow-on evidence, n=1 | Yaw360 and canonical Hardstep do not yet have valid complete matched pairs; actuator/headroom and mission-shaping issues remain. |
| Quanser 3DOF Hover, Nengo live HIL GUI | Dedicated 200 Hz Q8 worker; ten 0.5 ms Nengo steps; six CMG neurons and built-in PES; 50 Hz GUI or strictly unarmed headless shadow mode | All six mission definitions plus deterministic hard-pulse profiles | Direct/Nengo equivalence and emulation passed; connected Q8 PD/Nengo qualification plus five Nengo shadow missions completed with 26,000 control rows, 260,000 neural samples, all physical DAC commands exactly zero, and 0.12--0.34% isolated deadline misses | Connected-hardware signal-path qualification; no new tracking claim | Zero-output gate passed. **Still not cleared for adaptive armed use:** reverify deliberate encoder-axis signs and complete staged baseline-only Hover/Roll qualification before low-authority single-axis CMG. |
| Pendulum, Hover, QCar MuJoCo XMLs | Shared controller API | Short integration missions | All software smoke paths complete and log correctly | Integration surrogate only | XMLs are not identified digital twins and support no physical-performance claims. |
| QCar2 hardware / Jetson | Existing camera lane estimate plus PID/SMC/NMPC steering | lane following; lane keeping planned | Existing conservative lane-following baseline and perception-only workflow | Baseline implementation | Canonical CMG residual and SNN/HyperLIF lane-keeping path not yet integrated or validated. |
| QDrone2 / QLabs | Earlier kinematic mirror and unresolved command-channel work | virtual-twin track | Kinematic-mirror deliverable exists | Incomplete virtual-twin integration | Authoritative dynamic command path remains unresolved; do not present as closed-loop validation. |

## 3. Complete Nengo/MuJoCo mission results

Mean shortest-path quaternion-angle error; every run is 45 s at `dt=0.0005 s`.

| Platform | Mission | PD baseline (rad) | Nengo CMG--PES (rad) | Mean improvement |
|---|---|---:|---:|---:|
| CF2 rotor design, 1.5x | roll | 0.051337 | 0.042439 | 17.33% |
| CF2 rotor design, 1.5x | full3 | 0.288383 | 0.126476 | 56.14% |
| CF2 rotor design, 1.5x | hard45 | 0.285449 | 0.132319 | 53.65% |
| CF2 rotor design, 1.5x | hardstep | 0.426182 | 0.347886 | 18.37% |
| CF2 rotor design, 1.5x | yaw360 | 0.075812 | 0.029870 | 60.60% |
| Skydio X2 | roll | 0.050565 | 0.041785 | 17.36% |
| Skydio X2 | full3 | 0.303275 | 0.131748 | 56.56% |
| Skydio X2 | hard45 | 0.294082 | 0.138007 | 53.07% |
| Skydio X2 | hardstep | 0.454528 | 0.359355 | 20.94% |
| Skydio X2 | yaw360 | 0.075863 | 0.029902 | 60.58% |
| Both platforms | hover | approximately zero | approximately zero | Not meaningful; equilibrium is already exact |

The Nengo implementation reproduces the archived direct CMG/PES mission
results to a worst mean-error difference of approximately 2.013 ppm.

## 4. Physical 3DOF Hover results

### 4.1 Frozen LQR-based hardware presentation set

| Mission | LQR baseline | CMG--PES | Improvement | Notes |
|---|---:|---:|---:|---|
| hard45 | 12.777 deg | 12.553 deg | 1.75% | Maximum error reduced approximately 31.9 to 24.3 deg. |
| full3 | 12.348 deg | 12.061 deg | 2.47% | Final frozen tracking pair; neuron figure comes from a later same-configuration run. |
| yaw360 | 6.123 deg | 5.830 deg | 4.79% | Completed frozen pair. |

### 4.2 Explicit quaternion-PD hardware follow-on

| Mission | PD baseline (deg) | PD+CMG (deg) | Best valid improvement | Residual cap | Status |
|---|---:|---:|---:|---:|---|
| roll, 5 s | 4.992 | 3.910 | 21.67% | 1.2 V/motor | Valid matched pair. |
| hard45, 25 s | 22.940 | 22.582 | 1.56% | 1.2 V/motor | Valid matched pair. |
| full3, 25 s | 21.706 | 21.365 | 1.57% | 1.2 V/motor | Valid matched pair. |
| yaw360 | -- | -- | -- | tested through staged allocator work | No valid complete matched pair in the compiled table; yaw-home matching and pitch/roll headroom are mandatory. |
| hardstep | -- | -- | -- | tested through staged/shaped variants | Canonical discontinuous mission exceeded the 55 deg roll boundary; shaped 0.7-scale/0.5 s transition is a separately named hardware-feasible variant. |

The LQR and PD tables are separate controller generations and must not be mixed
into one baseline comparison.

## 5. Neuron-family and mechanism conclusions

| Question | Current evidence-backed answer | Claim boundary |
|---|---|---|
| Does adaptive conductance cause the large gain? | No. Fixed- and adaptive-conductance CMG variants are numerically indistinguishable in the present amplified-gate regime. | This conclusion applies to the current parameterization and missions. |
| What causes the large nominal improvement? | Online PES decoder adaptation changes `W`; fixed-decoder cases provide only modest benefit. | Supported strongly in the nominal UAV simulations. |
| Is activity only the membrane or only the gate? | Output activity is gate-derived, but `v` and `r` are mutually coupled, so both internal states influence control. | Decoder does not receive `v` as an independent channel. |
| Is CMG inherently superior to LIF/ALIF/Izhikevich? | No universal superiority claim. In the matched 110-cell Nengo matrix, CMG-PES improves all ten platform/mission cells at mean normalized residual utilization 0.12; Izhikevich-PES has the larger average gain but uses 0.37 and much larger decoder movement. | CMG is the consistent low-authority solution in this representation. Repeated seeds, held-out weights, and CMG readout ablations remain required. |
| Is the unit spiking? | No; it is a continuous non-spiking custom Nengo neuron type. | Neuromorphic refers to the dynamical neuron/online decoder architecture, not emitted spike events. |

## 6. Software, environments, and authoritative paths

| Purpose | Environment / command root | Authoritative path | Status |
|---|---|---|---|
| ACC paper and MuJoCo | `C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe` | `C:\Research\papers\ACC2027_Gate_Residual_Control` | Active clean repository. |
| Canonical direct CMG | Same ACC environment | `src\gra_control\gate.py` | Stable; historical names retained only as aliases. |
| Nengo CMG neuron/PES | Same ACC environment; Nengo 4.1.0, Nengo GUI 0.6.0 | `experiments\nengo_nef_replication_2026-08-29\nengo_cmg.py` | Validated for MuJoCo mission reproduction. |
| Nengo MuJoCo GUI | Same ACC environment | `experiments\nengo_nef_replication_2026-08-29\launch_gui.py` | Complete; saved `.py.cfg`; live passive MuJoCo viewer supported. |
| Nengo matched results | Same ACC environment | `experiments\nengo_nef_replication_2026-08-29\results\neuron_family_matched_45s` | 110/110 45-s cells complete; 100 full-rate non-baseline neural archives plus compiled performance/authority/mechanism figures. |
| Hover LQR HIL | `C:\Research\hover3dof\.venv\Scripts\python.exe` | `C:\Research\hover3dof\runners\hover3dof_hil_cmg_control.py` | Hardware-tested and frozen. |
| Hover quaternion-PD HIL | Same Hover environment | `C:\Research\hover3dof\pd_cmg_focused_final_round_2026-08-28` | Hardware-tested; fixed-bias and stability-priority generations documented separately. |
| Hover Nengo GUI HIL | Same Hover environment, now with Nengo 4.1.0 and Nengo GUI 0.6.0 | `C:\Research\hover3dof\nengo_gui_hil_2026-08-29` | Emulated smoke and corrected direct/Nengo equivalence audit passed; Q8 dry-run remains mandatory before arming. |
| Pendulum QLabs | Conda `hyperlif` Python 3.11 plus Quanser PAL path | `C:\Research\pendulum` | Matched n=3 virtual-twin matrix complete. |
| QCar | Jetson Python/Quanser HAL for hardware; ACC environment for surrogate | `C:\Research\qcar` and ACC QCar surrogate | Baseline lane-following exists; neural perception/control integration pending. |
| Historical research | Mixed historical environments | `C:\Research\papers\P3_Gate_Residual` | Preserve for provenance; do not use as clean execution root. |
| Older Nengo inspiration | Historical Nengo repository | `D:\NMSU_backups\Backup\00_Research_\Neuromorphic_Embodied_AI\02_Coaxial_TriRotor_Nengo` | Reviewed for design patterns; not the canonical current implementation. |

## 7. Documents and deliverables

| Deliverable | Path | Current state |
|---|---|---|
| LaTeX manuscript | `paper\acc2027_neuromorphic_gate_residual_draft.tex` | Full working draft; title and architecture updated. Hardware table needs reconciliation with the newer frozen LQR set. |
| Built paper PDF | `output\pdf\acc2027_neuromorphic_gate_residual_draft.pdf` | Rebuilt 2026-08-31 with the matched neuron-family table; successful 11-page working draft, not yet ACC-length submission format. |
| Results explanation | `docs\RESULTS_EXPLAINED.md` | Detailed equations, missions, and plots. |
| Execution/code map | `docs\EXECUTION_AND_CODE_MAP.md` | Strong baseline reference but dated 2026-08-27; some Hover status is now superseded. |
| Session index | `docs\SESSION_INDEX_2026-08-27.md` | Cross-repository map; some historical caveats are superseded by later PD hardware work. |
| Presentation | `presentation\CMG_PES_Results.pptx` | Complete presentation deck with MuJoCo and Hover results. |
| MuJoCo Nengo GUI guide | `experiments\nengo_nef_replication_2026-08-29\GUI_GUIDE_2026-08-29.md` | Complete, including live MuJoCo viewer. |
| Full Nengo telemetry guide | `docs\NENGO_FULL_TELEMETRY_2026-08-31.md` | Cross-platform schemas, exports, plots, validation, and exact commands for MuJoCo and Hover. |
| Matched neuron-family report | `docs\NENGO_NEURON_FAMILY_BENCHMARK_2026-08-31.md` | Final 110-cell results, calibration, equations, effort-aware interpretation, and claim boundary. |
| Hover Nengo disturbance report | `docs\HOVER_NENGO_DISTURBANCE_STUDY_2026-08-31.md` | Complete/partial status, mission-specific pulse profiles, all raw/compiled/neural diagnostic paths. |
| Nengo data/results checkpoint | `docs\NENGO_DATA_AND_RESULTS_CHECKPOINT_2026-08-31.md` | Single-entry handoff with counts, key tables, telemetry inventory, freeze paths, and remaining claim gates. |
| Hover safety checklist | `C:\Research\hover3dof\docs\SAFETY_CHECKLIST.md` | Mandatory before any physical run. |
| Hover LQR frozen plots | `C:\Research\hover3dof\results\plots\final_best` | Six final figures: tracking and neuron activity for hard45/full3/yaw360. |
| Hover PD campaign table | `C:\Research\hover3dof\pd_cmg_focused_final_round_2026-08-28\results\compiled\campaign_pairs.csv` | Contains valid and invalid/aborted pairs with audit flags. |
| Frozen Nengo/MuJoCo archive | `frozen_archives\nengo_nef_gui_viewer_CANONICAL_FROZEN_2026-08-29.zip` | Preserves complete Nengo campaign, GUI, viewer, and the current layout checkpoint. |
| Frozen neuron-family checkpoint | `frozen_archives\nengo_neuron_family_INDEX_CODE_COMPILED_FROZEN_2026-08-31.zip` plus the raw-tree SHA-256 manifest | Preserves code/docs/compiled outputs compactly; 4.07-GB raw telemetry remains frozen in place and individually hashed. |
| Frozen Hover Nengo prehardware checkpoint | `C:\Research\hover3dof\frozen_archives\hover_nengo_disturbance_PREHARDWARE_INDEX_CODE_COMPILED_FROZEN_2026-08-31.zip` plus its raw-tree SHA-256 manifest | Explicitly emulated/prehardware; does not replace the physical campaign archives. |
| Connected Q8 Nengo shadow checkpoint | `C:\Research\hover3dof\frozen_archives\hover_nengo_CONNECTED_Q8_SHADOW_INDEX_FROZEN_2026-08-31.zip` plus qualification/shadow raw-tree SHA-256 manifests | Real Q8/encoder and real-time computation evidence, hard-coded zero output; not a closed-loop performance dataset. |

## 8. Honest claim boundaries

| Claim | Allowed now? | Required wording / reason |
|---|---:|---|
| Online CMG--PES improves nominal X2 and CF2-design simulations | Yes | State missions, 45 s duration, nominal/single-run status, and explicit actuator model. |
| CF2 result applies to stock Crazyflie hardware | No | It is a 1.5x rotor-authority design study, not identified stock hardware. |
| Adaptive conductance is responsible for the 50% gain | No | Online decoder adaptation is the identified mechanism in the present regime. |
| CMG is intrinsically superior to LIF/ALIF/Izhikevich | No | The matched matrix disproves exclusivity: Izhikevich-PES also learns strongly. CMG's supported advantage is consistency at roughly one-third the normalized residual effort, not universal error dominance. |
| Pendulum accuracy improves | No | Transfer is stable, but nominal RMS is equivalent to LQR. |
| Hover hardware validates end-to-end operation | Yes, cautiously | Physical result exists, but each reported cell is n=1 and controller generations must remain separate. |
| QCar neural lane keeping is complete | No | Perception baseline exists; CMG/SNN steering integration remains future work. |
| Hover Nengo GUI may be armed | Not for an adaptive mission yet | The connected zero-output gate now passes. Reconfirm physical encoder signs, E-stop/shields/gain/headroom and run a stable baseline-only Hover/Roll stage before separately authorizing low-beta single-axis CMG. |

## 9. Priority queue

| Priority | Action | Acceptance condition |
|---:|---|---|
| 1 | Reverify connected encoder ordering/signs by deliberate manual axis movement | Live count changes agree with documented yaw/pitch/roll mapping and sign; current stationary data alone are insufficient. |
| 2 | Stage the Nengo HIL baseline before any adaptive authority | Complete safe baseline-only Hover and then Roll qualification under the lab checklist; connected zero-output qualification is already complete. |
| 3 | Reconcile manuscript Hover table | Paper, frozen progress doc, figures, and presentation cite the same selected LQR dataset. |
| 4 | Run repeated UAV robustness/hold-out matrix | Multiple seeds/disturbances summarized with mean and variance. |
| 5 | Repeat Hover hardware pairs | At least three matched trials per selected mission/controller under identical allocator and mission configuration. |
| 6 | Finish yaw360 and shaped Hardstep PD/CMG generation | Baseline completes first; matched CMG follows with identical home, allocator, duration, and shaping. |
| 7 | QCar perception-first integration | Validate lane signal/sign in shadow mode before CMG/SNN can influence steering. |
| 8 | Final paper rebuild and audit | Clean PDF builds; every numeric claim traces to an archived summary/manifest. |
