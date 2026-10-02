# CMG-PES / HyperLIF Architecture — Complete Technical Audit
### Chronological history, architecture evolution, results ledger, traceability, and full equation/parameter reference

---

## Part 1 — Chronological project timeline

| # | Phase | Dates | What happened |
|---|---|---|---|
| 1 | QDrone2 virtual-twin (Quanser QLabs) | early | Recovered `QDrone2_Workspace.rt-win64`, confirmed the RT model runs and connects to QLabs, but found no scriptable Python command channel. **Closed, redirected to Hover** at user's request. |
| 2 | 3DOF Hover physical hardware, LQR-based | 2026-08-27 | First Python code ever written for this rig. Built `hover3dof_hil_cmg_control.py`. Found and fixed 4 real bugs (channel swap, no encoder tare, bridge baseline-clip misuse, gate-drive starvation from baseline=0). Caught a duration-confound methodology error twice. Froze results in `PROGRESS_2026-08-27.md`. |
| 3 | MuJoCo X2/CF2 Nengo/NEF replication | 2026-08-29 (pre-existing, reviewed not authored this session) | `nengo_cmg.py`/`nengo_neuron_family.py` — Nengo-native CMG replication matched to ~2ppm vs the frozen NumPy controller. Neuron-family ablation (LIF/ALIF/Izhikevich vs CMG) begun. |
| 4 | Status check | 2026-08-31 checkpoint | Reviewed `PROJECT_STATUS_TABLE_2026-08-31.md` — discovered a Hover Nengo GUI/HIL system (software-validated, not yet armed) and a quaternion-PD Hover hardware campaign in progress. |
| 5 | **6-DOF architecture expansion (MuJoCo)** | 2026-08-31, this session | Option B (idealized 6-DOF wrench) built, debugged (force-limit bug), validated. Option A (realistic cascade) built, went unstable, root-caused (quaternion-convention bug), fixed, validated. Extended to CF2, to Nengo-native, to 6-channel neuron-family ablation. |
| 6 | Hover real-hardware campaign, LQR/PD-vs-CMG | 2026-08-31 → 2026-09-01 | Independently, `hover3dof/nengo_gui_hil_2026-08-29/` was armed and run on the real Q8 rig — roll qualification (2026-08-31), full3/hard45/hardstep/yaw360(PD-only, safety-aborted) (2026-09-01 daytime). |
| 7 | **This session's hardware work (evening, 2026-09-01)** | 2026-09-01 evening | Picked up where the prior operator ("ChatGPT") left off. Diagnosed and fixed the GUI-thread-contention timing bug (root cause: GIL contention between the 200Hz worker's Nengo computation and the GUI's own thread — PD never triggered it because PD runs no Nengo computation). Built `run_hover_direct_nengo.py` (bypasses the GUI entirely). Completed the missing hover CMG-PES pair. Resolved a data-integrity question (a remembered "~10%" figure traced to a *different, emulated* disturbance-rejection study, not real hardware). Solved yaw360's repeated safety-abort (root cause: physical/cable constraint near a half-turn, not tunable) with a reduced-range (108°) variant. Compiled neuron-family results (emulated, since neuron families were never safety-qualified for armed hardware). |

---

## Part 2 — Evolution of the architecture

The residual-augmentation idea is constant throughout: **`command = baseline ⊕ neural_residual`**, where the neural residual is bounded, and the baseline is a conventional controller that would work fine alone. What evolved is *how* the residual is computed, *how many channels* it spans, and *what it's attached to*.

```
Stage 0  HyperLIF fixed gate            (P3_Gate_Residual, earlier project)
         Paired CMG-style neuron population, FIXED decode W0=[I|-I].
         Diagnosed as spurious: residual torque ~0, "improvement" was
         just half-PD detuning from beta blending. Motivated Stage 1.
              |
              v
Stage 1  HyperLIF + learned decode (online-PES)
         Same neuron population, decode W now PES-learned online.
         +86.7% on Bitcraze/hard45, beats a hand-tuned adaptive teacher.
         Generalizes CF2->Skydio (the hand-tuned teacher didn't).
              |
              v
Stage 2  Renamed/formalized as CMG (Coupled Membrane-Gate) in
         ACC2027_Gate_Residual_Control. Same neuron ODE, same PES rule,
         now canonical in gate.py: CMGResidualAugmentor, 3 channels
         (attitude torque only). Validated across X2/CF2/CF2-rotor,
         multiple missions (roll/full3/hard45/hardstep/yaw360).
              |
              v
Stage 3  Nengo/NEF-native replication (nengo_cmg.py)
         Same math, ported to a real Nengo Simulator + PES learning
         rule instead of hand-rolled NumPy. Verified ~2ppm equivalent.
         Neuron-family ablation added: same paired-population pattern,
         neuron type swapped for nengo.LIF/AdaptiveLIF/Izhikevich/LIFRate.
              |
              v
Stage 4  6-channel generalization (this session, MuJoCo)
         CMGResidualAugmentor(channels=6): 3 position + 3 attitude.
         Option B: direct 6-DOF wrench (idealized, bypasses the mixer).
         Option A: realistic cascade (position PD -> thrust/attitude
         decomposition -> quaternion-PD inner loop -> real rotor mixer).
         Option A's first version was unstable; root cause (quaternion-
         convention mismatch) found and fixed. Nengo-native and
         neuron-family versions of the 6-channel cascade built and
         validated the same session.
              |
              v
Stage 5  Real hardware, 6-channel cascade equivalent (Hover, ypr order)
         hover_nengo_hil_gui.py: HoverWorker engine, same CMG-PES
         mechanism (channels=3, yaw/pitch/roll torque), armed against
         a real Quanser Q8 card. Originally GUI-coupled; this session
         found the GUI-thread-contention bug and built a GUI-free
         direct driver (run_hover_direct_nengo.py) that produced every
         final real-hardware number.
```

### Honest distinctions between what changed at each stage (so nothing gets conflated)

| Variable | Stage 0-1 (HyperLIF) | Stage 2 (CMG, MuJoCo attitude) | Stage 4 (6-ch, MuJoCo) | Stage 5 (Hover hardware) |
|---|---|---|---|---|
| Channels | 3 (attitude only) | 3 (attitude only) | 6 (3 pos + 3 att) | 3 (attitude only, ypr order) |
| Plant | MuJoCo CF2/Skydio | MuJoCo X2/CF2/CF2-rotor | MuJoCo X2/CF2-rotor | Real Quanser 3DOF Hover |
| Decode | learned (online-PES) or fixed | fixed or online-PES (both supported) | online-PES (adaptive) | online-PES (armed), fixed/PES (emulated only) |
| `beta` (residual authority) | 0.5 | 0.5 (typical) | 0.5 (X2), down to 0.02 (CF2, retuned) | **0.2** (real hardware, deliberately conservative) |
| `learning_rate` | 8e-4 | 8e-4 | 8e-4 (X2), 2e-4 (CF2) | **2e-4** (real hardware) |
| Motor/torque authority | simulation, no hard cap | `torque_limits` policy | force/torque `limits6` | **motor_residual_cap_volts=0.2V**, real physical bound |
| Timing regime | offline batch sim | offline batch sim | offline batch sim | **real 200Hz hard deadline** |

This table is the single most important "honesty" artifact in this document: **beta and learning_rate are never the same number twice** across stages, because hardware safety staging deliberately detuned them, and CF2's simulated retuning was a separate, independent finding. Comparing raw percentages across stages without this table is exactly the kind of mistake that produced the "~10%" confusion resolved earlier this session.

---

## Part 3 — Complete results ledger, chronological, approved/not-approved

Legend: ✅ approved (trust this) · ⚠️ approved, negative/mixed (real data, not a win) · ❌ not approved (superseded/diverged/unsafe/never completed)

| # | Date | Result | Platform | Controller | Status | Number |
|---|---|---|---|---|---|---|
| 1 | 2026-07-05 | Fixed-gate HyperLIF, hard45 | MuJoCo CF2 | fixed HyperLIF | ❌ | J=0.266117 (+7.4%) — self-diagnosed spurious (half-PD detuning) |
| 2 | 2026-07-05 | STN-PID-PES teacher | MuJoCo CF2 | hand-tuned adaptive | ✅ | J=0.047864 (+83.3%) |
| 3 | 2026-07-05 | Learned HyperLIF, online-PES | MuJoCo CF2 | HyperLIF+PES | ✅ | J=0.038258 (+86.7%), beats teacher |
| 4 | 2026-07-05 | Learned HyperLIF, e-prop anneal | MuJoCo CF2 | HyperLIF+eprop | ✅ | J=0.038215 (+86.7%) |
| 5 | 2026-07-05 | Imitation/behavioral cloning | MuJoCo | HyperLIF | ❌ | diverges, J≈2.6 |
| 6 | 2026-07-05 | Learned aggressive, hardstep | MuJoCo CF2 | HyperLIF+PES | ❌ | diverges, J=2.18 |
| 7 | 2026-07-05 | Learned balanced/strong-damp, cross-platform | MuJoCo CF2+Skydio | HyperLIF+PES | ✅ | stable, +45-67% |
| 8 | 2026-07-05 | Aero2 HIL hardware validation | real hardware | HyperLIF | ❌ | never run ("pending") |
| 9 | 2026-08-27 | 4 hardware bugs found/fixed | Hover hardware | LQR/CMG | ✅ | qualitative — root causes fixed |
| 10 | 2026-08-29 | Nengo/NEF 3-channel equivalence | MuJoCo | CMG (Nengo) | ✅ | ~2 ppm vs NumPy |
| 11 | 2026-08-31 | Option B 6-DOF wrench, first attempt | MuJoCo X2 | CMG-PES | ❌ | force-limit bug, hover3d 0.90m error |
| 12 | 2026-08-31 | Option B 6-DOF wrench, fixed | MuJoCo X2 | CMG-PES | ✅ | full6_stress +3.96%/+49.17% |
| 13 | 2026-08-31 | Option A cascade, first attempt | MuJoCo X2 | CMG-PES | ❌ | unstable, diverges every mission |
| 14 | 2026-08-31 | Option A cascade, fixed | MuJoCo X2 | CMG-PES | ✅ | full6_stress +76.1%/+65.8% |
| 15 | 2026-08-31 | Option A cascade | MuJoCo CF2-rotor | CMG-PES | ⚠️ | -18.7% to -26% (real negative) |
| 16 | 2026-08-31 | "More powerful rotors" test | MuJoCo X2/CF2 | CMG-PES | ⚠️ | no benefit confirmed (tested to 3x) |
| 17 | 2026-08-31 | 6-channel Nengo equivalence | MuJoCo X2 | CMG-PES (Nengo) | ✅ | 1.05e-7 relative error |
| 18 | 2026-08-31 | 6-channel neuron-family, full6_stress | MuJoCo X2 | LIF/ALIF/Izhikevich/LIFRate | ✅ | CMG +76%/+66%; spiking families destabilize at 1/50th authority; LIFRate neutral |
| 19 | 2026-08-31 | Roll qualification, armed (3 pairs) | Hover hardware | pd/nengo-pes | ✅ | +2.65% ± 1.08% |
| 20 | 2026-09-01 (day) | full3/hard45/hardstep matched pairs | Hover hardware | pd/nengo-pes | ✅ | -0.87% to +0.21% |
| 21 | 2026-09-01 (day) | yaw360, full scale | Hover hardware | pd | ❌ | safety-aborted, roll -20.083° |
| 22 | 2026-09-01 (eve) | Hover GUI-path, hover mission | Hover hardware | nengo-pes | ❌ | 6+ consecutive timing-abort failures |
| 23 | 2026-09-01 (eve) | Direct-Nengo (no-GUI) engine built | Hover hardware | nengo-pes | ✅ | 10/10 clean completions |
| 24 | 2026-09-01 (eve) | Final hardware campaign (hover/roll/full3/hard45/hardstep) | Hover hardware | pd/nengo-pes | ✅ | see table below |
| 25 | 2026-09-01 (eve) | yaw360, full scale, retested (2 durations) | Hover hardware | pd | ❌ | reproduced safety abort, speed-independent → physical constraint |
| 26 | 2026-09-01 (eve) | yaw360, reduced-range (108°) | Hover hardware | pd/nengo-pes | ✅ | -8.38%, per-axis cause verified in trace |
| 27 | 2026-09-01 (eve) | "~10%" figure traced | MuJoCo (emulated) vs Hover hardware | -- | ⚠️ | real emulated data (10.6%), was mistakenly conflated with hardware — corrected |
| 28 | 2026-09-01 (eve) | Neuron families, all missions | Hover plant (emulated) | LIF/ALIF/Izhikevich/LIFRate | ⚠️ | mixed: roll +10.65% (CMG-fixed), hardstep -11% all families, hard45 Izhikevich-PES -19.53% |
| 29 | 2026-09-01 (eve) | Neuron families, real hardware | Hover hardware | LIF/ALIF/Izhikevich/LIFRate | ❌ | never attempted — not safety-qualified |

### Final approved hardware numbers (run #24 + #26, the numbers to cite)

| Mission | PD (deg) | CMG-PES (deg) | Δ | Source directory |
|---|---:|---:|---:|---|
| hover | 0.116 | 0.046 | +60.4%* | `.../results/DIRECT_NENGO_FINAL_2026-09-01/{pd,nengo-pes}_hover_none_armed_20260901_1926{13,26}` |
| roll | 5.498 | 5.192 | +5.57% | `.../{pd,nengo-pes}_roll_none_armed_20260901_1926{41,54}` |
| full3 | 11.282 | 11.644 | -3.21% | `.../{pd,nengo-pes}_full3_none_armed_20260901_1927{15,33}` |
| hard45 | 9.743 | 9.689 | +0.55% | `.../{pd,nengo-pes}_hard45_none_armed_20260901_1928{12,44}` |
| hardstep | 13.626 | 13.497 | +0.95% | `.../{pd,nengo-pes}_hardstep_none_armed_20260901_1929{04,22}` |
| yaw360 (108°) | 2.731 | 2.960 | -8.38% | `.../{pd,nengo-pes}_yaw360_none_armed_20260901_1938{49}/1939{29}` |

\*near-zero baseline, not a robust effect.

---

## Part 4 — Best-results traceability: file dependency chains

### 4a. Best MuJoCo result: Option A cascade, X2, full6_stress, +76.1%/+65.8%

```
run_6dof_cascade.py  (--platform x2 --controller online-pes-adaptive --mission full6_stress)
  |
  +-- imports thrust_vector_to_attitude, rotmat_to_quat  [defined in this file]
  +-- imports position_reference, MASS_FORCE_LIMIT_SCALE  <- run_6dof_wrench.py
  +-- imports CMGResidualAugmentor                        <- src/gra_control/gate.py       [canonical]
  +-- imports quat_angle, quat_conj, quat_error            <- src/gra_control/math3d.py    [canonical]
  +-- imports SPECS, _free_joint, _mixer, torque_limits    <- src/gra_control/platforms/drone.py [canonical]
  |
  +-- plant: third_party/mujoco_menagerie/skydio_x2/x2.xml (via SPECS["x2"])
  |
  +-- writes results/optionA/{mission}_{classical,pes}/{trace.csv,summary.json}
  +-- plot_optionA.py reads those -> results/plots/*.png
```

### 4b. Best real-hardware result: Hover, hover mission, +60.4% (and every 2026-09-01-evening number)

```
run_hover_direct_nengo.py  (--io q8 --armed --confirm-hardware-review --controller nengo-pes --mission hover)
  |
  +-- sets HOVER_NENGO_* environment variables (armed/confirmed/controller/mission/beta/...)
  +-- imports hover_nengo_hil_gui as engine
        |
        +-- RunConfig (CFG)             reads the env vars set above, validates safety flags
        +-- HoverWorker (WORKER)        the 200Hz real-time loop; NO nengo_gui involved
        |     |
        |     +-- build_augmentor("nengo-pes") -> NengoCMGPESAugmentor(channels=3, ...)
        |     |     <- nengo_nef_replication_2026-08-29/nengo_cmg.py
        |     |          <- nengo.Simulator (external dependency, PES learning rule)
        |     |
        |     +-- from pd_baseline import mujoco_quaternion_pd_torque_ypr, mujoco_pes_target_ypr,
        |     |     torque_to_motor_differential, allocate_stability_priority_torque, ...
        |     |     <- pd_cmg_focused_final_round_2026-08-28/src/pd_baseline.py [VendorPlant physical constants]
        |     |
        |     +-- from gra_control.math3d import quat_error, euler_to_quat, reference_euler
        |     |     <- src/gra_control/math3d.py [canonical, same file as MuJoCo work]
        |     |
        |     +-- self._read_q8_angles() / self._write_q8()
        |           <- quanser.hardware.HIL  (real Q8-USB card, board "0")
        |
        +-- WORKER._save() writes results/DIRECT_NENGO_FINAL_2026-09-01/{controller}_{mission}_..._{ts}/
                {trace.csv, neural_trace_2khz.npz, neural_trace_schema.json, summary.json}
  |
  +-- compile_final_hardware_report.py reads PAIRS of those dirs -> results/.../plots/*.png
```

**Key fact this chain makes explicit**: the MuJoCo work and the Hover hardware work share exactly two files — `gra_control/gate.py` (indirectly, via the Nengo port `nengo_cmg.py`) and `gra_control/math3d.py` (directly) — everything else is platform-specific. This is *why* it's meaningful to call them "the same architecture": the neuron ODE and the quaternion math are byte-identical between simulation and real hardware; only the plant, the mixer, and the safety layer differ.

---

## Part 5 — Complete technical specification

### 5.1 Core equations

**CMG unit dynamics** (`gate.py: CoupledMembraneGateBank.step`, `nengo_cmg.py: CoupledMembraneGate.step` — identical math, two implementations):

```
x              = clip(alpha * (v - (v_threshold - gamma * r)), -60, 60)
r_target       = sigmoid(x) = 1 / (1 + exp(-x))
r             += dt * (r_target - r) / tau_r ;  r = clip(r, 0, 1)
gain           = base_gain [+ gain_scaling * |J|   if adaptive_conductance]
conductance    = gain * r^2
lambda         = 1/tau + conductance
drive          = v_rest/tau + J/tau + conductance * v_reset
v              = v * exp(-lambda*dt) + (drive/lambda) * (1 - exp(-lambda*dt))
output (activity) = clip(gate_gain * r, 0, 1)
```
Non-spiking, continuous. `J` = external drive current (per unit).

**Residual augmentor** (`gate.py: CMGResidualAugmentor.step`):
```
u0          = clip(baseline, -limits, limits)
normalized  = u0 / limits
current     = concat( current_bias + current_gain*max(normalized,0),
                       current_bias + current_gain*max(-normalized,0) )   # paired +/- channels
r           = CMG_units.step(current, dt)          # 2*channels units
a           = clip(gate_gain * r, 0, 1)             # "activity"
y_signed    = clip(W @ a, -1, 1)
if online_pes and target is not None:
    W += learning_rate * outer(target - y_signed, a) - leak * W
    W = clip(W, -6, 6)
residual    = beta * y_signed * limits              # ("residual" mode; "blend" mode differs)
command     = clip(u0 + residual, -limits, limits)
```
`W0 = [I_channels | -I_channels]` at init (identity-minus-identity decode).

**PES learning rule** (embedded above): `ΔW = η(y* - y)aᵀ - λW`, standard delta-rule with weight leak, clipped to ±6.

**Quaternion utilities** (`gra_control/math3d.py`, canonical, shared by every platform):
```
quat_conj(q)               = [q0, -q1, -q2, -q3]
quat_mul(p, q)              = Hamilton product
euler_to_quat(phi,theta,psi)= half-angle roll-pitch-yaw composition (ZYX)
quat_error(q_ref, q_meas):
    qe = normalize( q_ref (x) conj(q_meas) )
    eq = qe[1:];  if qe[0] < 0: eq *= -1              # shortest-path sign fix
    return qe, eq
quat_angle(qe) = 2 * atan2(|qe[1:]|, |qe[0]|)
```

**Quaternion-PD control law** (canonical, `drone.py: run_drone`, MuJoCo xyz convention):
```
qe, eq = quat_error(q_ref, q_meas)
tau0   = clip(-kq*eq - kw*omega, -limits, limits)
kq     = 2 * J * wn^2          (elementwise, wn = [4.0, 4.0, 3.5] rad/s default)
kw     = 2 * 0.95 * wn * J
limits = J * [12, 12, 10]       (policy="model": min(that, gear*ctrl) for cf2)
```

**Same law, real-hardware (Hover) form** (`pd_baseline.py: mujoco_quaternion_pd_torque_ypr` — note the **sign flip**, explicitly documented as a coordinate-convention transform, not a different law):
```
torque = +kq*eq_ypr - kw*omega_ypr        # MuJoCo's -kq*eq becomes +kq*eq in Hover's ypr/physical coordinate
kq, kw = same formula as above, reordered xyz<->ypr, using VendorPlant.inertia (real physical inertia,
         not a MuJoCo-model inertia)
PES target (Hover form) = clip(+k_error*eq_ypr - k_rate*omega_ypr, -1, 1)
```

**Position PD, 6-DOF cascade** (`run_6dof_cascade.py`):
```
F0 = clip( mass*g*z_hat - kp_pos*(p - p_ref) - kd_pos*v,  -force_limits, force_limits )
kp_pos = mass * wn_pos^2          (wn_pos = [1.0, 1.0, 1.2] rad/s, validated stability ceiling)
kd_pos = mass * 2 * 0.75 * wn_pos
```

**Thrust-to-attitude decomposition** (Mellinger-Kumar style, `run_6dof_cascade.py: thrust_vector_to_attitude`):
```
zb = F / |F|
xc = [cos(yaw_des), sin(yaw_des), 0]
yb = (zb x xc) / |zb x xc|
xb = yb x zb
R_des = [xb | yb | zb]
q_des = rotmat_to_quat(R_des);  q_des = quat_conj(q_des)   # <- the convention fix, see Part 3 #13/#14
```
Angular-rate feedforward: `omega_des = 2 * vec(quat_error(q_des, q_des_prev)) / dt`.

**Vendor Hover physical model** (`pd_baseline.py: VendorPlant`):
```
K_t (torque_thrust)     = 0.0036  N.m/V
K_f (force_thrust)      = 0.1188  N/V
L (arm_length)           = 7.75 * 0.0254 = 0.19685 m
m (moving_mass)          = 2.85 kg
J_motor (rotor inertia)  = 1.91e-6 kg.m^2 (per motor)
bias_voltage              = 2.0 V
voltage range              = [0.0, 24.0] V  (Eq. 2.5's positive-voltage-only law,
                                              enforced as np.clip(v, 0, 24) in code)

inertia(yaw,pitch,roll) = [4,2,2] * (J_motor + (m/4)*L^2)   [physical formula, not identified]
motor_to_torque (F/B/L/R -> yaw/pitch/roll):
   tau_yaw   = -K_t*V_f - K_t*V_b + K_t*V_l + K_t*V_r
   tau_pitch =  K_f*L*V_f - K_f*L*V_b
   tau_roll  = -K_f*L*V_l + K_f*L*V_r
```

### 5.2 I/O interfaces

| Interface | Where | Direction | Notes |
|---|---|---|---|
| MuJoCo `data.ctrl[act_ids]` | `drone.py`, `run_6dof_cascade.py` | write | rotor4 platforms (X2, CF2-rotor): 4 motor thrust commands via `B_inv @ [thrust,tau]` |
| MuJoCo `data.xfrc_applied` | `run_6dof_wrench.py` (Option B) | write | direct 6-DOF world-frame wrench, bypasses the mixer entirely |
| MuJoCo `data.qpos`/`data.qvel`/`data.xmat` | all MuJoCo runners | read | ground-truth state (no sensor noise unless explicitly injected) |
| Nengo `nengo.Node` (paired currents) | `nengo_cmg.py` | write→sim | `drive` node feeds `population.neurons` directly, `synapse=None` |
| Nengo `nengo.Connection` (PES) | `nengo_cmg.py` | learning | decoder connection carries `learning_rule_type=nengo.PES(...)`, error computed via a `nengo.Node` |
| `quanser.hardware.HIL` | `hover_nengo_hil_gui.py` | read (`read_encoder`), write (`write_analog`) | real Q8-USB card, board "0"; 3 encoder channels (pitch/roll/yaw), 4 analog outputs (F/B/L/R) |
| `nengo_gui.GUI` websocket | `hover_nengo_hil_gui.py` (GUI path only) | bidirectional | dashboard telemetry + browser heartbeat; **removed entirely** in `run_hover_direct_nengo.py` |

### 5.3 Models

| Model | File | Platform | Interface type |
|---|---|---|---|
| Skydio X2 | `third_party/mujoco_menagerie/skydio_x2/x2.xml` (via `SPECS["x2"]`) | MuJoCo | `rotor4` (real 4-actuator mixer) |
| Bitcraze Crazyflie 2 (stock) | `third_party/mujoco_menagerie/bitcraze_crazyflie_2/scene.xml` (`SPECS["cf2"]`) | MuJoCo | `virtual_wrench` (idealized, not used for Option A) |
| Custom CF2-rotor | `models/cf2_rotor_design/scene.xml` (`SPECS["cf2-rotor"]`) | MuJoCo | `rotor4` (real mixer, used for CF2 Option A) |
| Quanser 3DOF Hover | physical rig, no MuJoCo file | real hardware | Q8-USB DAQ, 3 rotational DOF (yaw/pitch/roll), fixed base |
| Hover "emulated" plant | `hover_nengo_hil_gui.py: _step_emulated` (2nd-order model, `WCF`/`ZETAF`-filtered rates) | MuJoCo-free numeric sim | used for `--io emulated` runs (disturbance campaigns, neuron-family emulated data) |

### 5.4 Parameters — complete reference table

| Parameter | CMG unit default | Hover armed value | X2 6-DOF (Option A) | Source |
|---|---|---|---|---|
| tau (membrane) | 0.05 s | (same, canonical) | (same) | `CMGConfig` |
| tau_r (gate) | 0.005 s | (same) | (same) | `CMGConfig` |
| alpha | 50 | (same) | (same) | `CMGConfig` |
| gamma | 2.0 | (same) | (same) | `CMGConfig` |
| v_threshold | 1.0 | (same) | (same) | `CMGConfig` |
| base_gain | 120.0 | (same) | (same) | `CMGConfig` |
| gain_scaling | 30.0 | (same) | (same) | `CMGConfig` |
| gate_gain | 1.0e5 | (same) | (same) | `CMGConfig` |
| current_bias | 0.75 | (same) | (same) | augmentor ctor default |
| current_gain | 1.25 | (same) | (same) | augmentor ctor default |
| beta (residual authority) | 0.5 | **0.2** | 0.5 (X2), 0.02 (CF2) | mission-specific override |
| learning_rate | 8e-4 | **2e-4** | 8e-4 (X2), 2e-4 (CF2) | mission-specific override |
| k_error | 8.0 | **2.0** | 8.0 | mission-specific override |
| k_rate | 0.0 | 0.0 | 0.0 | default everywhere |
| residual_slew_v_per_s | n/a | 1.0 V/s | n/a | Hover-only slew limiter |
| motor_residual_cap_volts | n/a | 0.2 V | n/a | Hover-only hard cap |
| wn (attitude) | 4.0, 4.0, 3.5 rad/s | same formula, VendorPlant inertia | 4.0, 4.0, 3.5 | canonical |
| wn_pos (position, Option A) | n/a | n/a | 1.0, 1.0, 1.2 rad/s | validated stability ceiling |
| amplifier gain K_AMP | n/a | 3.0 | n/a | Hover hardware constant |

### 5.5 Timers / rates — every layer

| Layer | Value | Where |
|---|---|---|
| MuJoCo physics timestep | 0.0005 s (2 kHz) | `model.opt.timestep`, all MuJoCo runners |
| Hover hardware loop | HARDWARE_DT = 0.005 s (**200 Hz, hard real-time**) | `hover_nengo_hil_gui.py` |
| Hover inner Nengo loop | NEURAL_DT = 0.0005 s (2 kHz), NEURAL_SUBSTEPS = 10 per hardware tick | `hover_nengo_hil_gui.py` |
| Hover GUI dashboard | GUI_DT = 0.02 s (50 Hz) | `hover_nengo_hil_gui.py` (GUI path only — absent in the direct runner) |
| GUI heartbeat timeout | 0.5 s default (set to 999999 s in the direct runner, replaced by a dedicated heartbeat thread) | `RunConfig.gui_heartbeat_timeout_s` |
| Max consecutive deadline misses (abort threshold) | 20 | `RunConfig.max_consecutive_deadline_misses` |
| Windows timer resolution fix | `timeBeginPeriod(1)` — 1 ms requested resolution (was ~15.6 ms default) | added this session, `hover_nengo_hil_gui.py` top of file |
| Encoder resolution | 8192 counts/rev quadrature → K_EC = 2π/(8×1024) rad/count | `hover_nengo_hil_gui.py` (note: yaw's constant carries a negative sign — verified sign convention) |

### 5.6 Simulation / hardware run setups

| Setting | MuJoCo (all experiments) | Hover armed (real hardware) | Hover emulated |
|---|---|---|---|
| Ground truth source | `data.qpos`/`data.qvel` (exact) | real Q8 encoders, tared at run start | 2nd-order numeric plant model |
| Sensor noise | none unless explicitly injected | real (quantized, ~0.044°/count) | none (idealized) |
| Actuator saturation | `model.actuator_ctrlrange`, optionally scaled (`--actuator-scale`) | `[0, 24] V` per `VendorPlant`, floor via `allocate_stability_priority_torque` | same voltage law, no physical floor needed |
| Safety limits | none (batch simulation) | `max_abs_pitch/roll_deg`, `max_encoder_step_deg`, deadline-miss abort — all hard-coded checks that raise and zero output | same checks, non-fatal in practice (no physical risk) |
| Real-time constraint | none — runs as fast as Python allows | **hard**, 5 ms per step or abort | paced to real time only if `emulation_realtime=True` |

---

## Notes on completeness and honesty

- Every equation above was read directly from the source file in this session (not reconstructed from memory) except the QDrone2/Hover-LQR-bugs items in Part 1, which are carried forward from earlier in this same conversation and are already frozen/closed work.
- The sign flip between MuJoCo's `-kq*eq-kw*omega` and Hover's `+kq*eq-kw*omega` is real and intentional (documented in `pd_baseline.py`'s own docstring) — it is a coordinate-convention transform between MuJoCo's xyz torque convention and the Hover rig's verified physical yaw/pitch/roll convention, not an inconsistency.
- Table 5.4's beta/learning_rate/k_error columns are the clearest evidence that hardware and simulation results are **not** directly comparable percentage-for-percentage — this is why Part 2's evolution table exists.
