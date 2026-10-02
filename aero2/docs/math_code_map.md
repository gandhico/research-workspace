# Math ↔ Code Map

Single table: *equation / quantity → code symbol*. Two layers:
**(A)** what is live in this repo now (config), and **(B)** the recovered
traceability from the original implementation, which each migration phase
re-points to the new-repo symbol. Acceptance: every paper equation ends up here
with a concrete code symbol.

## A. Constants → `aero2/config/` (live now, Phase 1)

| Quantity | Paper | Symbol |
|---|---|---|
| Plant params `DT_ARM, KSP, DP, KPP, KPY, DY, KYY, KYP` | Ref 3 drift `b`, input `M(θ)` | `config.params.*` |
| Inertias `J_P, J_Y` | Ref 3 | `config.params.J_PITCH/J_YAW` |
| `cosθ` clip `|cθ|≥0.25` | Ref 3 (impl. detail) | `config.params.MIN_COS_THETA` |
| Encoder counts 2880 / 4096 | Ref 3 setup | `config.params.PITCH/YAW_COUNTS_PER_REV` |
| Gyro bias / noise, accel mean / noise | Ref 1 Eqs. 10–21 | `config.sensors.*` |
| Sampling 100/200/500 Hz, measured ≈380/303 | Ref 1, Ref 3 | `config.timing.*` |
| Square refs `Aθ=20°,Aψ=45°,fθ=0.05,fψ=0.04` | Ref 3 Eqs. 3–4 | `config.references.*` |
| PD/LQR/LQG/MPC/BS/SMC/NMPC gains | Ref 3 §Control | `config.gains.*` |

## B. Equation families → original code (migration reference)

Recovered from `aero2_paper_results/16_code_to_equation_traceability/`. The
"new-repo symbol" column is filled as each phase migrates the code.

| Paper section | Equation | Original code file → symbol | New-repo symbol (phase) |
|---|---|---|---|
| Setup | encoder/rate state `θ,ψ,θ̇,ψ̇` | `M7_aero2_simulink_2dof_pd_replicate.py → DirectHilAero2IO.read` | ✅ `io.encoders` (counts↔angles); hardware read P6 |
| Setup | gyro bias corr `ω−b` | `M8_aero2_hardware_2dof_nonlinear.py → main (gyro_y_corr, gyro_z_corr)` | ✅ `io.imu_calibration` |
| State est | pitch rate: gyro vs encoder Δθ/Ts (Eqs. 23-24, 49) | M1 state-est script | ✅ `io.state_estimation.Aero2StateEstimator` / `PitchStateEstimator` |
| Sampling | ZOH u_c(t)=u_d(k) (Eq. 25) | — | ✅ `io.sampling.ZeroOrderHold` |
| Input mapping | `[v0,v1]=M_u[u_p,u_y]` (direct/mixed) | `... → output_mapping` | `models/`/`io/` mixer (P3/P6) |
| Preprocess | filtered derivative (Eqs. 28–30) | `... → SimulinkSecondOrderDerivative.update` | ✅ `control.filters.SecondOrderDerivative` |
| Nonlinear model | drift + `M(θ)` (Eqs. 5–7) | `M8.../src/nonlinear_aero2_model.py → drift, input_matrix, dynamics` | ✅ `helicopter_2dof.drift/.input_matrix/.f` |
| Nonlinear model | RK4 | `nonlinear_aero2_model.py → rk4_step` | `models/base.Model.step` ✅ |
| Inverse dynamics | LS `Mu=v−b` (Eqs. 9–10) | `... → inverse_dynamics` | ✅ `helicopter_2dof.inverse_dynamics` |
| ID | SISO ARX `Y=Φβ` (Eqs. 31–33) | `M3_aero2_ls_arx_common.py → build_arx_matrices, estimate_ls` | `identification/arx.py` (P5) |
| ID | MIMO ARX | `M3_aero2_ls_arx_common.py → build_mimo_arx_matrices` | `identification/arx.py` (P5) |
| ID | DARX export | `M3_aero2_10_export_nominal_darx_models.py` | `identification/arx.py` + `data/identified_models/` (P5) |
| State-space | DARX→SS | `aero2_common/aero2_utils.py → darx_siso_to_ss`; `M6_aero2_state_space_models.py` | `identification/ss_realize.py` (P5) |
| PD | 2DOF PD (Eqs. 39–41) | `M7_aero2_simulink_2dof_pd_replicate.py → main` | ✅ `control.linear.pd.PD2DOF` |
| Linear plant | `A,B,C` | `M7.../controllers/linear_2dof.py → plant_matrices` | ✅ `linear_2dof.linear_plant_matrices` |
| LQR | CARE (Eqs. 43–44) | `linear_2dof.py → LQR2DOFController` | `control/linear/lqr.py` (P7) |
| LQG | observer (Eq. 45) | `linear_2dof.py → LQG2DOFController` | `control/linear/lqg.py` (P7) |
| Linear MPC | first-gain (Eqs. 46–47) | `linear_2dof.py → MPC2DOFController._finite_horizon_first_gain` | `control/linear/mpc_linear.py` (P7) |
| Backstepping | computed torque (Eqs. 48–50) | `controllers/backstepping.py → Backstepping2DOFController.step` | `control/nonlinear/backstepping.py` (P7) |
| SMC | surface + robust (Eqs. 51–53) | `controllers/sliding_modes.py → SlidingMode2DOFController.step` | `control/nonlinear/smc.py` (P7) |
| NMPC | grid MPC (Eqs. 54–55) | `controllers/nmpc.py → NMPC2DOFController.step` | `control/nonlinear/nmpc.py` (P7) |
| Eval | benchmark metrics | `M8_aero2_combined_controller_benchmark.py → metrics_for_file` | ✅ `benchmarking.metrics.tracking_metrics` (core) |
| Uncertainty | `Δm`, `W_m(s)`, `|TW_m|<1` (Eqs. 35–36) | M4 robust-stability scripts | `identification/validation.py` (P5) |

✅ = already implemented in the new repo.
