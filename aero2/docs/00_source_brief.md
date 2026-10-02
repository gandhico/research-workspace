# Source Brief (governing spec) — persisted into the repo

> This is the original `AERO2_SNN_CLAUDE_CODE_BRIEF.md`, preserved here because
> the staged Downloads copy was ephemeral and has been removed. It is the
> authoritative intent for this repository. The operational essence is distilled
> in `../CLAUDE.md`; this file keeps the full original for traceability.

---

## 1. Purpose
Migrate and clean up an existing, working Quanser **Aero2** system-identification
and control project into a new research tree, restructured so that:
1. the **full implementation** (identification + control) is preserved and traceable to the math;
2. there is a **first-class separation** between **offline simulation**, **QLabs virtual twin**, and **real-time hardware (HIL/PAL)**;
3. the plant is generalized to **all Aero2 model variants**: 2-DOF helicopter, half-rotor, pitch-only (1-DOF), yaw-only (1-DOF);
4. two **application classes** are supported on every variant: **reference tracking** and **equilibrium regulation under external disturbances**;
5. the codebase is staged for a future research phase applying **Adaptive HyperLIF** (spiking / neuromorphic) to both **identification** and **control**.

Deliverable: a well-organized, documented, math-traceable Python repository with runners, notes, references, insights, and future work — a clean refactor, not a rewrite of the science.

## 2. Source material
- Original implementation (authoritative code): `C:\02_Research\01_Robotics_Quanser\01_Aero2`
- Ref 1: *Sample-data real-time hardware tests on the Quanser Aero2 platform for digital control* (Module 1 / HM04).
- Ref 2: *Hardware-Oriented Identification of the Quanser AERO 2-DOF Platform and Preliminary Control Results* (mid-project).
- Ref 3: *Modelling, Identification, and Control of the Quanser Aero2 System* (final).
- **Rule:** when code and paper disagree, treat the *code* as truth, the *paper* as intent; record resolution in `docs/math_code_map.md`.
- Target: `C:\00_Research_\Neuromorphic_Embodied_AI\04_Aero2_SNNs` (built at root per the user's decision).

## 3. Guiding principles
One source of truth for every constant (`aero2/config/`). Math↔code traceability. Backend-agnostic controllers (mode is a config flag, not a branch). Honest results preserved (strong one-step / weak free-run; yaw unresolved — don't silently fix). Half-rotor modelled but hardware `NotValidated`.

## 4. Target repository structure
The brief's tree: `README.md`, `CLAUDE.md`, `pyproject.toml`, `docs/` (papers + numbered topic docs + math_code_map + references + insights), `aero2/` (`config models io identification control{linear,nonlinear,neuromorphic} execution applications benchmarking utils`), `runners/`, `configs/`, `data/{raw_logs,identified_models}`, `results/{figures,tables}`, `tests/`.

## 5. Core architecture (the offline / virtual-twin / hardware contract)
Four small interfaces so any `model × backend × controller × application` composes without conditionals:
- **`Model`** (`models/base.py`): `state_dim/input_dim/output_dim`, `f(x,u,t)->xdot`, `step(x,u,dt)->x_next`, `linearize(x0,u0)->(A,B,C,D)`, `output(x)->y`.
- **`Backend`** (`execution/backend.py`): `reset(x0)->Measurement`, `apply(u)`, `read()->Measurement`, `dt_actual()->float`, `close()`. Implementations: `OfflineBackend(model)`, `VirtualTwinBackend` (QLabs), `HardwareBackend` (Direct HIL `DirectHilAero2IO.read`).
- **`Controller`** (`control/base.py`): `reset()`, `compute(x_est, ref, dt) -> u` (dt is `dt_actual`).
- **`Application`** (`applications/`): owns reference generator and/or disturbance schedule; one shared closed-loop runner. Capability matrix documented in `docs/07_execution_modes.md`.

## 6. Model variants (`aero2/models/`)
State `x=[θ,θ̇,ψ,ψ̇]`, `u=[u_p,u_y]`, `y=[θ,ψ]`. Motor mapping `u_c=(v_f+v_r)/2`, `u_d=(v_f−v_r)/2` (Ref 2 Eq. 2).
1. `helicopter_2dof.py` — primary coupled plant. Nonlinear drift `b` + input `M(θ)` with `cθ=cosθ` clipped `|cθ|≥0.25`. Linear A,B,C. Inverse dynamics by least squares.
2. `pitch_only.py` — 1-DOF pitch about trim `U0≈1.4 V`; near-integrating.
3. `yaw_only.py` — 1-DOF yaw via pure differential `u_L=−v_ψ, u_R=+v_ψ`; encode breakaway/stiction.
4. `half_rotor.py` — half-quadrotor; offline/virtual only; hardware `NotValidated`.

## 7. Sensing / IO / state estimation (`aero2/io/`, Ref 1)
Encoders `θ=2π·n_θ/2880`, `ψ=2π·n_ψ/4096`. IMU bias/noise defaults (gyro bias `[+0.00985550,−0.01797350,−0.00718040]`, etc.). Pitch state `x_θ=[θ,θ̇]` with `θ̇` from bias-corrected y-gyro vs quantized encoder finite-difference (provide both + switch). Sampling/ZOH `u_c(t)=u_d(k)`. Rates: 100 Hz (sampling/IMU), 200 Hz (state est), controllers nominal 500 Hz but measured ≈380 Hz (≈303 Hz realtime NMPC). Loops use measured Δt.

## 8. Identification (`aero2/identification/`, Refs 2 & 3)
Excitation: trim search → `U0≈1.4 V`; pitch doublet; PRBS common-mode (`v_pitch≈0.075 V`); yaw chirp pure differential (≤6 V, `|u_L−u_R|≤12 V`); coupled. Drop `t<3 s` + demean. Nonparametric: step/impulse, linearity, correlation FRF, FFT; pitch band ≈0.6–0.8 Hz; primary yaw FRF `ω_z,c/v_yaw`. ARX/DARX: `Y=Φβ`, `φ(k)=[1,y(k−1)…y(k−na),u(k−1)…u(k−nb)]`, `lstsq`. Reproduce Table II. Validation: one-step AND free-run separately (Table I). Multiplicative uncertainty + weight + robust check. ss-realize with ctrb/obsv ranks.

## 9. Control (`aero2/control/`, Ref 3)
**Critical:** derivative filters/discrete updates use the **actual measured Δt**, not nominal 0.002 s. Shared 2nd-order derivative filter `ω_n=100, ζ=1`, Euler with measured Δt, clip `±24 V`.
- PD (baseline): `Kp_θ=116.2420, Kd_θ=99.6990, Kp_ψ=35.8626, Kd_ψ=38.0289`; no integral.
- LQR: `Q=diag(180,4,60,2), R=diag(0.30,0.30)`; `u_ff` by least squares.
- LQG: LQR gain + Luenberger, Euler with actual Δt.
- Linear MPC: unconstrained finite-horizon first-move + clip (not full QP).
- Backstepping: `k1θ=2.0,k2θ=3.0,k1ψ=1.2,k2ψ=2.2`; yawboost `k1ψ=4.0,k2ψ=3.5`.
- SMC: boundary-layer sat; `λθ=2.5,ηθ=0.7,φθ=0.10,λψ=2.0,ηψ=0.8,φψ=0.15`; yawboost `λψ=4.0,ηψ=3.0,φψ=0.25`.
- NMPC: grid search around inverse-dynamics nominal, RK4; realtime `N=5,Δt_p=0.06,Q=diag(80,2.5,50,1.5),R=diag(0.10,0.10)`, terminal 1.5, grid `(−2.5,0,2.5)`.
References: square waves `Aθ=20°, Aψ=45°, fθ=0.05, fψ=0.04`.

## 10. Applications
`reference_tracking.py` (square-wave) and `regulation_disturbance.py` (hold setpoint under injected disturbances; report peak deviation, recovery time, steady-state error). One shared closed-loop runner; differ only in references + disturbances. Keep yaw weakness visible.

## 11. Benchmarking
Reproduce Ref 3 §XI–XII Table IV (sample count, duration, loop freq, pitch/yaw RMS, tail MAE, saturation fraction, ranges, dominant error freqs). `compare.py` regenerates figures + table. Conclusions: PD strongest overall, SMC best nonlinear pitch-tail, NMPC benchmarkable but not competitive, yaw unresolved.

## 12. Runners
Thin CLIs driven by YAML configs selecting `model_variant, execution_mode, controller, application, sampling`: `run_identification.py`, `run_control.py`, `run_benchmark.py`, `run_state_estimation.py`. Each writes a standard record and prints realized loop rate.

## 13. Documentation requirements
Each `docs/*.md`: math (with eq numbers), code symbols, parameters, how to run, honest "what works / what doesn't / why". `math_code_map.md` = equation → file → symbol. `references.md` includes Refs 1–3 + cross-repo HyperLIF. `insights_and_future_work.md` consolidates the lessons + neuromorphic plan.

## 14. Future research phase — Adaptive HyperLIF (scaffold now, implement later)
Apply Adaptive HyperLIF to (a) identification (SNN surrogate/one-step predictor vs ARX/DARX on identical splits) and (b) control (neuromorphic controller benchmarked on the same tracking/regulation + Table-IV metrics). Cross-repo sources to READ before integrating:
`...\Neural_Networks_and_Learning\01_Adaptive_HyperLIF`, `...\04_Adaptive_HyperLIF_Nengo`, `...\Neuromorphic_Embodied_AI\01_HyperLIF_Gate_Residual`.
Scaffold now (interfaces + stubs + `docs/10_neuromorphic_hyperlif.md`): `NeuromorphicIdentifier` (same fit/validate API as `arx.py`); `HyperLIFController` (the `Controller` interface); reuse the gate/residual idea as a residual augmentation on a model-based baseline (PD + neuromorphic residual). Keep partitioned + experimental; classical pipeline must remain runnable alone.

## 15. Phased plan
1. Scaffold + config + 4 interfaces + CLAUDE.md + param tests.
2. Migrate original code; move CSVs to `data/raw_logs/`; reconcile into `math_code_map.md`.
3. Models (4 variants).
4. IO / state estimation.
5. Identification (reproduce Table II + one-step/free-run).
6. Execution backends (offline → virtual-twin → hardware).
7. Control (linear → nonlinear, measured Δt; reproduce benchmark).
8. Applications (tracking + regulation on every variant/backend).
9. Docs pass.
10. Neuromorphic scaffold (interfaces + stubs + doc only).

## 16. Acceptance criteria
Fresh user runs reference tracking on 2-DOF helicopter offline with one command, switches to virtual-twin/hardware by changing only `execution_mode`. Identification reproduces Table II + one-step/free-run split. PD reproduces Table IV ranking; yaw visibly weakest. Every paper equation appears in `math_code_map.md`. All four variants instantiate offline; half-rotor hardware `NotValidated`. Neuromorphic stubs satisfy interfaces and are picked up by runners unmodified. Nothing fabricated.

## 17. Constraints / cautions
Don't invent hardware results or improve reported metrics. Don't collapse offline/virtual/hardware into in-controller `if`. Don't drop the `cθ` clip, the actual-Δt rule, the `t<3 s` trim discard, or the pure-differential yaw drive. Treat the cross-repo HyperLIF paths as inputs to read, not assumptions to encode blindly.
