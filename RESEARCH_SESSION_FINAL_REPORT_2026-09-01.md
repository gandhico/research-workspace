# CMG-PES Residual Architecture — Final Session Report, 2026-09-01

Covers two projects sharing one architecture: `ACC2027_Gate_Residual_Control`
(MuJoCo simulation, X2/CF2, 3- and 6-channel) and `hover3dof` (real Quanser
3DOF Hover hardware). Written for later independent verification — every
number below is traceable to a specific script, config, and output
directory listed in Section 3.

## 1. Conclusion

The CMG-PES architecture (a paired continuous membrane/gate neuron
population, online-PES-learned decoder, additive bounded residual on top
of a classical baseline) delivers **large, consistent benefit specifically
on demanding, tightly-coupled 6-DOF simulation tasks on a heavier platform
(X2)** — up to +76% position, +68% attitude on the hardest MuJoCo mission.
That benefit **does not transfer uniformly** to either a lighter simulated
platform (CF2) or the real physical 3DOF Hover rig: real hardware shows a
small, mission-dependent effect (roughly -8% to +6%, one mission near
+60% but on a near-zero baseline), and CF2 shows the same muted-to-negative
pattern in simulation. The common thread, checked and confirmed
independently on both platforms: **the architecture's benefit tracks how
much genuine structural error the classical baseline leaves uncorrected**
— not a fixed multiplier. Where the baseline is already good (CF2's low
inertia, Hover's conservative safety-limited residual authority), there is
little room left for a learned residual to help, and it can add a small
net cost (exploration noise, or — confirmed by direct trace inspection
tonight — coupling a stronger correction on one axis into a small but real
disturbance on another, e.g. yaw360's roll/pitch excursion).

Two real engineering problems were found and fixed this session, not
just measured around:
1. **Option A cascade instability (MuJoCo)** — root cause was a
   quaternion-convention mismatch between `q_des` (built from a geometric
   rotation matrix) and `q_meas` (built via `quat_conj(raw MuJoCo qpos)`);
   fixed with one line (`q_des = quat_conj(q_des)`), verified by exact
   ground-truth MuJoCo testing, not more hand-derivation.
2. **Hover hardware CMG-PES timing aborts** — root cause was GIL
   contention between the 200Hz hardware worker thread's Nengo computation
   and the `nengo_gui` dashboard's own concurrent thread/websocket
   activity (PD never triggered it because PD runs no Nengo computation at
   all — the user's own direct observation of that asymmetry was the key
   clue). Fixed by driving the same engine directly, with no GUI:
   `run_hover_direct_nengo.py`, 10/10 clean armed completions on first
   full attempt versus near-total failure through the GUI that same
   evening.

One data-integrity question was raised and resolved: a remembered "~10%"
improvement figure was traced to a *different, emulated* MuJoCo
disturbance-rejection experiment (`disturbance_campaign_profiled_2026-08-31`,
10.6% on roll), not the real hardware numbers — confirmed the physical
hardware data itself is genuine (real quantized encoder steps, not
simulated) before concluding this.

## 2. Results, tracked per mission

### 2a. MuJoCo — Option B, fully-actuated 6-DOF wrench, X2 (idealized)

| Mission | pos improvement | att improvement |
|---|---:|---:|
| hover3d | N/A (baseline exact) | N/A |
| waypoint_step | -40% | N/A |
| circle_xy | -0.3% | N/A |
| full6_stress | +3.96% | +49.17% |

### 2b. MuJoCo — Option A, realistic cascade (real rotor mixer)

X2:

| Mission | pos improvement | att improvement |
|---|---:|---:|
| hover3d | N/A (exact) | N/A |
| waypoint_step | +11.5% | +13.2% |
| circle_xy | +65.1% | +68.1% |
| full6_stress | +76.1% | +65.8% |

CF2-rotor:

| Mission | pos improvement | att improvement |
|---|---:|---:|
| hover3d | N/A (exact) | N/A |
| waypoint_step | -18.7% | -11.2% |
| circle_xy | -21.6% | -19.0% |
| full6_stress | -26.0% | -25.9% |

More-powerful-rotor test (actuator_scale/authority_scale up to 3x, X2/CF2):
no change at well-tuned gains; partial rescue of badly-tuned gains only;
never exceeded a well-chosen tuning at 1x power. CF2's limitation is
control-theoretic (cascade bandwidth), not actuator power.

### 2c. MuJoCo — Nengo/NEF validation (X2, 6-channel)

Isolated augmentor vs frozen NumPy, 2000 steps: relative command error
1.05e-7. Full closed-loop mission match: exact (hover3d, waypoint_step) to
3-4 significant figures (circle_xy, full6_stress).

### 2d. MuJoCo — neuron-family validation (X2, full6_stress)

| Engine | tuning | pos err (m) | att err (deg) |
|---|---|---:|---:|
| CMG-PES | natural (beta=0.5) | 0.237 | 5.01 |
| classical | -- | 0.989 | 14.65 |
| LIFRate-PES | beta=0.01 | 0.889 | 14.12 |
| ALIF-PES | beta=0.01 | 1.825 | 21.04 |
| LIF-PES | beta=0.01 | 2.175 | 22.28 |
| Izhikevich-PES | beta=0.01 | 2.196 | 25.00 |

Spiking families destabilize the demanding mission even at 1/50th CMG's
authority; LIFRate (same tuning curve, no spike discretization) stays
roughly neutral — isolates spiking noise as the failure mode.

### 2e. Real hardware — 3DOF Hover, PD vs CMG-PES (final, validated, direct-Nengo no-GUI path)

| Mission | PD (deg) | CMG-PES (deg) | Improvement |
|---|---:|---:|---:|
| hover | 0.116 | 0.046 | +60.4%* |
| roll | 5.498 | 5.192 | +5.57% |
| full3 | 11.282 | 11.644 | -3.21% |
| hard45 | 9.743 | 9.689 | +0.55% |
| hardstep | 13.626 | 13.497 | +0.95% |
| yaw360 (reduced-range, 108 deg sweep — see 2f) | 2.731 | 2.960 | -8.38% |

\* near-zero baseline, not a robust effect.

Cross-check: roll's earlier 3-replicate statistical compilation (partly
GUI-collected) gave +2.65% +/- 1.08%; tonight's single fresh pair (+5.57%)
is within a plausible range of that distribution.

### 2f. yaw360 — full 0-360 deg sweep vs reduced-range

Full-scale (reference_scale=1.0) safety-aborted on the roll limit twice
independently, at nearly identical magnitude (+/-20.127 deg) regardless of
whether the rotation took 30s or 50s — pointing to a physical constraint
tied to vehicle orientation (most plausibly cable wind-up near a half-turn
on this cable-tethered rig), not a tunable control/rate parameter.
Reduced-range variant (scale=0.3, ~108 deg sweep, same "hold pitch/roll at
zero" reference) completed cleanly for both controllers. Per-axis
breakdown (checked directly in the trace, not assumed): the dominant error
for BOTH controllers is yaw-tracking lag at peak angular velocity
(mid-sweep); CMG-PES additionally shows a real, ~3x-larger roll/pitch
excursion than PD at that same moment (mean roll error 0.67 deg vs 0.20 deg)
— consistent with cable/asymmetry coupling into the rotation, a real
secondary effect riding on top of the (larger, common-to-both) yaw-lag
effect.

### 2g. Real hardware — neuron families: not armed (deliberate safety boundary)

Only `pd` and `nengo-pes` were ever staged through the Hover
safety-qualification process. LIF/ALIF/Izhikevich/LIFRate were not armed
on the physical rig this session — that gap was not bypassed under time
pressure. Reported instead from the existing **emulated** (same Hover
plant model) matched campaign:

| Mission | best family | vs PD | worst/flat note |
|---|---|---:|---|
| roll | nengo-cmg-fixed | +10.65% | several spiking variants show exactly 0.00% (near-zero residual this calibration) |
| full3 | nengo-izhikevich-pes | +0.37% | all families within +/-0.4% |
| hard45 | nengo-izhikevich-fixed | +3.86% | nengo-izhikevich-pes worst: -19.53% |
| hardstep | -- | all families -11 to -11.5% | residual mechanism hurts here for every family, CMG included |
| yaw360 | nengo-nef-pes | +1.77% | all families within +/-2% |
| hover | not run in this campaign | -- | -- |

## 3. Code, math, and data map — for independent verification

### 3a. Canonical architecture (never modified this session; verify math here)

| File | Contents |
|---|---|
| `C:\Research\papers\ACC2027_Gate_Residual_Control\src\gra_control\gate.py` | `CMGResidualAugmentor`, `CoupledMembraneGateBank` — the CMG ODE and PES update law (`ΔW = η(y*-y)aᵀ - λW`) |
| `C:\Research\papers\ACC2027_Gate_Residual_Control\src\gra_control\math3d.py` | `quat_error`, `quat_mul`, `quat_conj`, `euler_to_quat`, `reference_euler` (mission reference trajectories) |
| `C:\Research\papers\ACC2027_Gate_Residual_Control\src\gra_control\platforms\drone.py` | `SPECS` (x2/cf2/cf2-rotor), `_mixer`, `torque_limits`, `run_drone` (the original validated 3-channel attitude-only MuJoCo controller) |
| `C:\Research\hover3dof\nengo_gui_hil_2026-08-29\hover_nengo_hil_gui.py` | `HoverWorker` (200Hz real-hardware loop), `RunConfig`, `LiveSnapshot` — canonical Hover hardware engine. One change made this session: `timeBeginPeriod(1)` added near the top (Windows scheduler-granularity mitigation), documented inline with the full investigation trail. |

### 3b. MuJoCo 6-DOF expansion (built this session)

Directory: `C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\six_dof_expansion_2026-08-31\`

| File | Purpose | Key output dirs |
|---|---|---|
| `run_6dof_wrench.py` | Option B (idealized 6-DOF wrench) | `results\optionB\` |
| `run_6dof_cascade.py` | Option A (realistic cascade, NumPy); contains `thrust_vector_to_attitude`, `rotmat_to_quat`, the q_des-convention fix, `--platform`/`--actuator-scale`/`--authority-scale` flags | `results\optionA\` (X2), `results\optionA_cf2\` (CF2) |
| `run_6dof_cascade_nengo.py` | Option A, Nengo-native augmentor | `results\nengo_x2\` |
| `nengo_neuron_family_6dof.py` | Channel-general neuron-family augmentor (generalizes the frozen 3-channel one below) | `results\nengo_families\` |
| `linearize_cascade.py` | Eigenvalue analysis (superseded once the real bug was found empirically) | -- |
| `verify_6dof_nengo_equivalence.py` | NumPy vs Nengo equivalence check (1.05e-7) | -- |
| `plot_optionA.py`, `plot_6dof.py`, `plot_neuron_family_6dof.py` | All plots | `results\plots\` |
| `PROGRESS_2026-08-31.md` | Full narrative including the instability debugging journey | -- |

### 3c. Nengo/NEF replication, 3-channel (pre-existing, frozen; backs the published benchmark doc)

Directory: `C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\nengo_nef_replication_2026-08-29\`

| File | Purpose |
|---|---|
| `nengo_cmg.py` | `CoupledMembraneGate` (Nengo NeuronType), `NengoCMGPESAugmentor` — channel-general, reused directly by the 6-DOF work above |
| `nengo_neuron_family.py` | 3-channel `NengoNeuronFamilyAugmentor`, `FAMILIES`, `neuron_type()` — not modified; `nengo_neuron_family_6dof.py` above generalizes it without touching this file |
| `feature_calibration.json` | Per-family `feature_scale`/`native_current_scale` calibration, reused by the 6-DOF neuron-family work |
| `run_mujoco_nef.py`, `run_campaign.py`, `run_neuron_family_campaign.py` | Campaign runners |

Companion docs: `C:\Research\papers\ACC2027_Gate_Residual_Control\docs\NENGO_NEURON_FAMILY_BENCHMARK_2026-08-31.md`, `PROJECT_STATUS_TABLE_2026-08-31.md`.

### 3d. Hover hardware (real Quanser rig)

Directory: `C:\Research\hover3dof\nengo_gui_hil_2026-08-29\`

| File | Purpose |
|---|---|
| `hover_nengo_hil_gui.py` | Canonical engine (see 3a) |
| `launch_hover_nengo_gui.py` | GUI launcher: env-var setter + `nengo_gui.main()` invocation; owns the safety-flag validation (`--armed` requires `--io q8` + `--confirm-hardware-review`, only `pd`/`nengo-pes` may be armed) |
| `launch_hover_experiment.ps1` | Per-mission validated parameter profiles (hardware and simulation) |
| **`run_hover_direct_nengo.py`** | **Built this session.** Same engine, same safety gates, **no `nengo_gui`** — the fix for the GUI-thread-contention timing failures. This is the script that produced every hardware number in Section 2e/2f. |
| `run_hover_headless.py` | Hard-coded `armed=False` — sensor/dry-run only, cannot drive real motors (checked and deliberately not used for real data collection) |
| `compile_final_hardware_report.py` | Generates the tracking+mechanism plots and summary table from any `PAIRS`/`ROOT` directory |
| `scratch_q8_io_benchmark.py` | Isolated Q8 hardware I/O timing benchmark (diagnostic; confirmed I/O is not the bottleneck, ~0.004ms/call) |
| `docs/`, `LAB_RUNBOOK.md`, `C:\Research\hover3dof\docs\SAFETY_CHECKLIST.md` | Safety staging process and history |

Result directories (chronological, all real Q8 hardware unless noted):

| Directory | Contents |
|---|---|
| `results\hardware\` | Every individual GUI-path armed/dry-run from 2026-08-31 and 2026-09-01 |
| `results\hardware_armed_roll_validation_2026-08-31\`, `results\hardware_armed_roll_n3_2026-09-01\` | Statistically compiled roll validation (3 paired trials, mean/sample_sd) |
| `results\hardware_q8_shadow_missions_2026-08-31\`, `results\q8_gui_shadow\`, `results\q8_neuron_family_shadow_2026-09-01\` | Zero-output dry-runs (unarmed, real sensors, no motor engagement) |
| `results\final_hardware_campaign_2026-09-01\` | Today's earlier GUI-path matched campaign (full3/hard45/hardstep/yaw360-PD-only) |
| **`results\DIRECT_NENGO_FINAL_2026-09-01\`** | **The final, validated dataset** — every number in Section 2e/2f, all via `run_hover_direct_nengo.py` |
| `results\FINAL_ANALYSIS_2026-09-01.md` | Prior write-up this session, superseded/extended by this document |
| `results\disturbance_campaign_2026-08-31\`, `..._mission_scaled_2026-08-31\`, `..._profiled_2026-08-31\`, `results\disturbance_compiled_profiled_2026-08-31\` | **Emulated** (MuJoCo, not hardware) disturbance-rejection study — this is where the earlier "~10%" figure actually comes from (roll, hard-pulses, profiled: 10.6%) |
| `results\hover_neuron_family_matched_25s_2026-09-01\` | **Emulated** neuron-family campaign, all missions except hover — source of Section 2g |

## 4. Open items for next session (not urgent, noted honestly)

- Hover mission was not included in the emulated neuron-family campaign (2g) — gap, not a result.
- Neuron-family controllers remain unqualified for armed real hardware — would need the full staged process (shadow → dry-run → baseline-only → single-axis low-authority → matched multi-axis) before that changes.
- yaw360's cable-wind-up hypothesis (2f) is a strong inference from reproducible, speed-independent trip behavior, not a physically confirmed diagnosis — worth a visual check of the cable routing next time the rig is open.
- CF2's "more powerful rotors" result (2b) is now well-tested; worth writing up explicitly as a negative result in the paper rather than omitting it.
