# DILISIC Paper Replication Report

Date: 2026-04-25

Project: `neuromorphic-mujoco-robotics-control`

Paper: *Limbic System-Inspired Performance-Guaranteed Control for Nonlinear Multi-Agent Systems With Uncertainties*

## Summary

We implemented a Python replication scaffold for the DILISIC controller described in the paper. The current implementation is stable for an 80-second simulation with seven flexible single-link arm agents, sinusoidal center-of-mass tracking, and an external disturbance from `t = 70 s` to `t = 75 s`.

The implementation is not yet a one-to-one reproduction of every paper equation. The flexible-arm plant, LISIC estimator structure, robust integral term, DILISIC reference model, seven-agent setup, and disturbance timing are represented. The outer multi-agent obstacle/formation controller is currently a simplified 1-D formation controller, not the exact Appendix `u_alpha + u_beta + u_gamma` flocking law.

## What Was Implemented

| Area | Paper Status | Added Beyond Paper? | Notes |
|---|---:|---:|---|
| Fourth-order flexible single-link arm plant | Replicated | No | Uses the paper model parameters `c = 2276.3`, `g = 9.81`, `m = 2.27`, `l = 0.96`, `alpha = -36.52`. |
| Seven-agent initial condition | Replicated | No | Agents start equally distributed from `-0.64 rad` to `0.64 rad`. |
| Disturbance timing | Replicated | No | Uses `d = 6000` from `70 s` to `75 s`, otherwise `0`. |
| RBF count and centers | Replicated | No | Uses `p = 45`, centers from `-45` to `45`, and `sigma = 45`. |
| LISIC estimates `f_hat` and `h_hat` | Mostly replicated | Yes | Same amygdala/OFC RBF structure. We initialize `h_hat` near the known flexible-arm inverse gain to avoid numerical collapse during reproduction. |
| Projection-bounded adaptive weights | Mostly replicated | No | Implements projection-style norm bounding for `V_f`, `W_f`, `V_h`, and `W_h`. |
| Robust Riccati term `u_r` | Replicated | Yes | Uses the paper CARE expression. A NumPy Hamiltonian fallback was added in case SciPy is unavailable. |
| DILISIC double-integrator reference model | Mostly replicated | Yes | Uses `q_ddot_ref = u_DI`. We added a first-order filter before finite-differencing `u_DI` to prevent artificial derivative spikes. |
| Outer MAS controller | Not exact | Yes | Current version is a simplified 1-D formation/obstacle controller. The exact Appendix `u_alpha + u_beta + u_gamma` flocking law is still future work. |
| Obstacle behavior | Approximate | Yes | Current obstacle activation is smoothed to avoid saturation chatter. The exact beta-agent obstacle equations are not yet implemented. |
| Plotting and summaries | Not in paper | Yes | Added reusable CSV analysis and plot generation for positions, velocities, controls, and agent-0 LISIC estimates. |
| MuJoCo/Quanser integration | Not implemented yet | No | Current work is simulation-only and does not connect to MuJoCo or hardware. |

## Result History

| Run | Command Intent | Duration / Step | Outcome | Key Metrics | Interpretation |
|---|---|---:|---|---|---|
| `results/dilisic_quick` | Smoke test | `0.05 s`, `dt = 0.001` | Passed execution but not physically meaningful | `max_abs_control = 50000.75`, `h_hat_final = 1e-6` | Verified plumbing only. Too short to evaluate the paper mission; estimator collapsed in the initial scaffold. |
| `results/dilisic_medium` | First 80-second attempt | `80 s`, `dt = 0.001` | Diverged | `final_com_error = -2167.21`, `max_weight_norm = 100000`, `max_abs_s_agent0 = 12053963.40` | Revealed serious numerical issues: `h_hat` collapse, weight saturation, and reference finite-difference spikes. |
| `results/dilisic_80s_stability` | Stabilized controller | `80 s`, `dt = 0.001` | Stable but control had saturation stripes | `final_com_error = -9.22e-06`, `max_weight_norm = 299.86`, `max_abs_control = 50006.96` | Dynamics were bounded and tracking recovered, but the control plot showed non-paper-like saturation chatter after obstacle activation. |
| `results/dilisic_80s_smoothed` | Smoothed controller/reference | `80 s`, `dt = 0.001` | Best current result | `final_com_error approx 1.29e-4`, `max_weight_norm = 2.48`, `max_abs_control = 8271.73` | Stable and much cleaner. Remaining sharp event around `70 s` is consistent with disturbance rejection. |

## Analysis of Current Best Result

Current best result folder:

`results/dilisic_80s_smoothed`

Generated plots:

- `positions.png`
- `velocities.png`
- `controls.png`
- `agent0_lisic_estimates.png`
- `summary.json`

The position plot shows seven agents preserving a roughly fixed spacing while following the sinusoidal motion. This qualitatively matches the paper's goal of maintaining a formation while tracking a center-of-mass reference. The final center-of-mass error is approximately `1.29e-4`, which indicates good tracking at the end of the simulation.

The velocity plot shows the agents moving together after the initial transient. The disturbance interval around `70 s` creates a visible correction, which is expected because the paper explicitly injects a disturbance from `70 s` to `75 s`.

The control plot improved substantially after smoothing. The earlier vertical saturation bands were not paper-like; they came from abrupt obstacle activation and numerical differentiation of a sharp `u_DI` signal. After adding obstacle ramping and a first-order filter before finite differencing, `max_abs_control` dropped from about `50006.96` to `8271.73`. The remaining large transient near `70 s` is aligned with disturbance rejection rather than obstacle chatter.

The LISIC estimate plot shows bounded `s` after startup and disturbance transients. The estimate `h_hat` increases over the run, especially after the disturbance. This should not yet be interpreted as a validated exact estimate of `1/g(x)` because we added an initialization aid and still use a simplified outer controller. It is useful as an internal adaptive signal showing that the estimator remains bounded in the current simulation.

## Important Deviations From the Paper

The largest deviation is the outer MAS controller. The paper uses the Appendix flocking law:

- `u_i = u_alpha_i + u_beta_i + u_gamma_i`
- sigma norm
- bump function `rho_h`
- pairwise potential `psi_alpha`
- obstacle beta-agent terms
- center-of-mass reference terms

The current code uses a simpler 1-D formation controller with smoothed obstacle repulsion. This makes the current results a strong numerical scaffold, but not yet a complete paper reproduction.

The second important deviation is numerical conditioning. We added:

- initial `h_hat` near the known flexible-arm inverse gain,
- RBF input clipping to the center range,
- lower adaptation rates,
- filtered `u_DI` before finite differencing,
- smoothed obstacle activation.

These additions make the reproduction stable and practical, but they should be documented as engineering scaffolding rather than paper equations.

## Safety and Project Impact

This implementation is safe to run inside the project because it is simulation-only. It does not start MuJoCo, does not connect to Quanser hardware, and does not actuate any physical device. It writes CSV and plot outputs only when the experiment commands are run.

The current computational warning is runtime cost. The paper setting `dt = 1e-4` for `80 s` requires about `800,000` integration steps and will be substantially slower than the current `dt = 0.001` runs.

## Recommended Next Steps

1. Implement the exact Appendix flocking controller equations `(39)-(43)`.
2. Add obstacle/reference overlays to the position plot so paper-event timing is visible.
3. Add separate plots for center-of-mass versus reference and tracking error.
4. Run `dt = 0.001` until the exact outer controller is stable.
5. Only then run the paper-scale `dt = 1e-4`.
6. After numerical validation, create MuJoCo and Quanser adapters around the DILISIC inner loop.
