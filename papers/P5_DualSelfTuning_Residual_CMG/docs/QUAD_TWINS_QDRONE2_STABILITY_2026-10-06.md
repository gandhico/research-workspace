# Quadrotor route: X2/CF2 MuJoCo twins, racing, and QDrone2 hardware

Decision dated 2026-10-06: QDrone2 replaces Quanser Aero2 as the intended hardware endpoint of P5. Keep the research question on a free-flying quadrotor: compare classical baseline, self-tuning S, residual R, and dual S+R, then certify the **applied** command and state envelope before hardware flight. The earlier Aero2 proposal remains historical context, not the active target.

## Current assets and claim boundaries

| Layer | Present asset | What it establishes | Missing before the next claim |
|---|---|---|---|
| X2 MuJoCo | ACC 2027 Menagerie Skydio X2 MJCF and P5/racing runners | Ideal rigid-body/instantaneous actuator comparisons | Measured motor map, lag, battery, aero, sensor timing and held-out flight validation |
| CF2 MuJoCo | ACC 2027 four-rotor design MJCF | Explicit rotor allocation study | Physical rotor parameters; the current authority multipliers are design assumptions: 1.5x in P5 and 1.7x in racing, so those studies cannot be compared as one calibrated airframe |
| Racing | `C:/Research/neuromorphic_drone_racing` four-airframe MuJoCo world, geometric baseline and emulated DVS | Stress tests for trajectory, allocation and sensor processing | Its camera is not yet in control feedback; DVS is frame-derived, with no validated end-to-end latency; no real Swift benchmark equivalence |
| QDrone2 local | `C:/Research/qdrone` telemetry-only hardware runner and kinematic QLabs mirror | Read-only telemetry path and a visual demonstration | No verified CMG injection into the real inner attitude/ESC loop; current QLabs mirror uses X2 parameters and is not QDrone2 dynamics |
| QDrone2 vendor | Local Quanser thrust parametrization and `QDrone2_Workspace.rt-win64` file now present | A vendor motor polynomial, mixer convention and a candidate native virtual model | Verify the compiled model loads/runs and determine the actual command/logging channel. Presence of the binary is not a tested native twin |

Quanser's 2023 local parametrization gives `m_takeoff=1.504 kg`, roll/pitch spans `0.254/0.2032 m`, thrust polynomial `T=0.03616 V^2+0.117 V-0.01215 N` (the accompanying `Motor_Mapping_7_Inch.m` is the source of these rounded coefficients), and an inverse motor mapping. These are vendor bench/source parameters, not measurements of this particular vehicle. At 9.81 m/s² the implied hover force is 3.6886 N per rotor and the polynomial root is 8.627 V; treat that as a sanity check, not an ESC command or identified hover setting. Record propeller, battery and firmware configuration before using it.

The QDrone2 project handoff still says `QDrone2_Workspace` is absent. A file now exists at `C:/Users/gandhico/Documents/Quanser/0_libraries/resources/rt_models/QDrone2/QDrone2_Workspace.rt-win64`; this changes the **availability audit**, not the execution/physics validation status. The project README has only telemetry-read-only hardware code. Official Quanser documentation states that the QDrone2 board exposes four ESC command channels through QUARC/HIL; the repository's existing Mission Server Python route is waypoint-level. Therefore low-level integration is possible in principle but must be verified in the actual installed vendor stack. A waypoint residual would answer a different scientific question from the ACC attitude-torque residual.

## Twin completion: keep L0 and build controlled variants

1. **Freeze L0:** hash the current X2 and CF2 MJCFs, run the ACC/P5/racing regression missions unchanged, and retain the two CF2 authority settings as explicitly different variants.
2. **L1 propulsion:** implement a shared four-rotor lag and static command-to-thrust/reaction-torque map, with measured or sourced parameter intervals. The ideal path must be recovered exactly when lag/effects are disabled. Start with MuJoCo activation/filter or an equivalent explicit state; do not copy QDrone2 motor coefficients onto X2/CF2.
3. **L2 electrical:** battery voltage and current-dependent thrust ceiling from measured discharge/ESC data. Keep unknown X2 parameters null rather than inventing values.
4. **L3 flight effects:** identify rotor-plane drag, body drag and near-ground correction from held-out motion data; compare prediction intervals, not only visual realism.
5. **L4 sensing/computation:** IMU, estimator, state/command delay, missed control periods, DVS generation and processing latency. Repeat the baseline/R/S/dual ablation with the same observations and actuator limits.
6. **Validation:** per-rotor step, hover trim, attitude chirp/doublet, free decay, aggressive trajectory and battery-level holdouts. A variant is called a *validated digital twin* only when uncertainty intervals cover held-out physical traces at predeclared coverage/tolerance. Without X2/CF2 hardware or equivalent logs, label those variants high-fidelity **design models**; QDrone2 data validate only QDrone2.

Prefer the fast motor-state variant for broad campaigns and use a physical rotor/ESC variant only if its extra states change the measured response enough to justify its cost. Avoid saving dense video or long uncompressed traces during the current storage-limited phase; keep summaries, downsampled traces and hashes, and preserve raw calibration logs at their source.

**L0 inventory now executed:** `tools/audit_quad_l0_models.py` compiled both existing scene XMLs with MuJoCo 3.12.0 and wrote `docs/TWIN_L0_AUDIT_2026-10-06.json` with source hashes, mass, inertia, rotor sites/gears and control limits. The XML's static thrust-to-weight ratios are 4.001 (X2) and 1.321 (CF2 stock design); these are model properties, not flight validation. ACC/P5/racing mission regressions and all L1–L4 validation remain open.

**First L1 code now executed:** `hifi/rotor_response.py` implements exact frozen-command first-order response in normalized rotor speed, followed by quadratic thrust. The zero-lag switch is bit-exact at the force interface. `experiments/hifi_quad_2026_10_06/smoke_rotor_response.py` loaded both existing MuJoCo scenes at a 0.5 ms study clock and passed 200-step bit-exact L0 `ctrl/qpos/qvel` parity on each. With a *synthetic* 30 ms lag, the 100 ms hover rollout differed in altitude by 0.029245 m (X2) and 0.029127 m (CF2); this verifies that the variant affects the plant, not that 30 ms is physical. No X2/CF2 time constant is yet identified, and broad controller campaigns have not been rerun.

**L1 controller screen added later 2026-10-06:** The opt-in copied P5 runner now uses a hover-initialized motor state, records requested versus realized per-rotor forces, and has an exact one-step reachable-force box/inverse. An unchanged L0 runner and the new zero-lag runner matched all 201 rows and 20 common columns in a two-second CF2/base comparison. A sequential 18-cell, eight-second Hardstep screen across X2/CF2 and baseline/R/S/dual shows strong sensitivity to a *synthetic* 30 ms lag, especially for R and dual. The exact math, selected metrics, plot and limits are in `ROTOR_REACHABILITY_AND_L1_SCREEN_2026-10-06.md`. This closes a **small sensitivity screen**, not motor identification, a broad L1 regression, or twin validation. The earlier 100 ms smoke test started the motor state at zero and was only a component-level response check; its altitude difference is not a hover-equilibrium comparison.

## Stability proof for the quadrotor, with dual as a proposal

The ideal-axis common-P certificate in `DUAL_HARDWARE_STABILITY_PROOF_2026-10-06.md` is a useful local bridge, but it cannot cover free flight. For the final theorem, define the augmented state

`x=(p,v,Q,omega, rotor states, estimator/filter states, PID integrator, reference-governor state)`.

The dual controller proposes collective and torque. A **single safety/stability filter after S+R** chooses the physically realizable four-ESC command (or inner-loop equivalent) closest to that proposal. Certify a compact local operating set `Omega` containing position, altitude, velocity, attitude-chart, rate, rotor, battery and delay limits. From an uncertainty-bounded sampled model `x_(k+1) in F_h(x_k,u_k,W_k)`, require robust constraints at and between samples and

`sup_{w in W_k} V(F_h(x_k,u_k,w)) <= (1-lambda h_k)V(x_k)+h_k sigma`.

If the filter is feasible at each sample, the real one-step dynamics lie in its uncertainty set, the between-sample tube stays safe, and `sigma/lambda` lies inside the certified region, induction gives practical stability and set invariance for **any bounded S/PES/R updates**, including abrupt gates. This is conditional on a verified fallback/reference governor. On a quadrotor, rotor headroom and collective thrust are coupled; a torque-box gate alone is inadequate. The CF2 Hardstep failure in P5 v6 shows why the theorem must be regional and why the training/validation mission set must include saturation and near-180-degree attitude errors. A global attitude claim requires an additional hybrid quaternion mechanism, and a pure attitude theorem does not prove altitude/geofence safety.

The safest implementation sequence is: certify a classical QDrone2 position/attitude baseline; compare S/R/dual as **shadow-mode proposals** on recorded physical flight; run the robust filter in the validated QDrone2 native virtual model; only then test filtered R and filtered dual with an on-site operator. The applied command, rejected residual fraction, filter feasibility, solver deadline, motor saturation, and fallback events are primary metrics. A DVS racing experiment is a stress test of perception latency and aggressive reference feasibility, not a substitute for the QDrone2 hardware certificate.

**Full-position proof prerequisite:** the current P5 runner closes only altitude and attitude loops; horizontal position is absent from its control inputs. On the translation-invariant hover model, every small horizontal shift of a hover equilibrium is another equilibrium, so that controller cannot asymptotically stabilize a specified horizontal point. A QDrone2 waypoint/geofence theorem therefore needs a position-aware outer loop or filter action before the robust full-state CLF can be certified. The one-step rotor-force reachability and this structural argument are detailed in `ROTOR_REACHABILITY_AND_L1_SCREEN_2026-10-06.md`.

## Immediate evidence gates

- [x] Identify the QDrone2 hardware endpoint and locate the present native-model binary and motor parametrization.
- [x] Record the X2/CF2 variant and CF2 authority mismatch across P5/racing.
- [x] Add an opt-in four-rotor L1 response component and verify exact-off L0 MuJoCo parity with small synthetic-lag smoke runs.
- [x] Run a small hover-initialized L1 Hardstep screen and derive the exact one-step reachable rotor-force interval. Document the synthetic-parameter boundary.
- [x] Audit QDrone2 native file and installed Python interface without hardware commands; see `C:/Research/qdrone/docs/NATIVE_VIRTUAL_INTERFACE_AUDIT_2026-10-06.md`.
- [ ] Confirm QDrone2 native virtual model launches and logs state/ESC commands; map its actual control injection point.
- [ ] Identify X2/CF2 motor time constants and complete L1 controller-campaign regressions against unchanged L0 results.
- [ ] Obtain platform-specific propulsion and flight logs; predeclare uncertainty/twin validation criteria.
- [ ] Solve a coupled-vehicle common-P/local ISS certificate, then the robust sampled-data filter feasibility problem.
- [ ] Verify filter and baseline on QDrone2 virtual/HIL, followed by supervised hardware with physical failsafe.

## Relevant primary sources

- Quanser QDrone2 board and ESC interface: https://docs.quanser.com/quarc/documentation/qdrone2.html
- Quanser QDrone2 product and onboard sensing: https://www.quanser.com/products/qdrone-2/
- Quanser QLabs virtual QDrone2 description: https://www.quanser.com/products/qlabs-virtual-qdrone-2/
- Local vendor thrust document: `C:/Users/gandhico/Documents/Quanser/Research_Resources/src/user_manuals/qdrone2/qdrone2_parametrization/qdrone2_thrust_parametrization.pdf`

These establish available interfaces and vendor parameters, not a tested hardware controller or a validated custom MuJoCo twin.
