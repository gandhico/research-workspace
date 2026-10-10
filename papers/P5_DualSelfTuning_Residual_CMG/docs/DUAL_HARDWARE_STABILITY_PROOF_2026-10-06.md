# A stability theorem for dual CMG control with a hardware endpoint

Date: 2026-10-06. Scope: P5 self-tuning layer S plus ACC 2027 CMG–PES residual R. This is a **theorem design and evidence audit**, not a claim that the current dual implementation is stable on hardware.

**Hardware-target update (later 2026-10-06):** The user selected QDrone2 and a quadrotor-first route instead of Aero2. Sections below that discuss Aero2 are historical examples. The active application, X2/CF2 twin gates, QDrone2 vendor-interface audit, and full-flight state set are in `QUAD_TWINS_QDRONE2_STABILITY_2026-10-06.md`.

## 1. What the two lines establish, and what they do not

The ACC paper bounds CMG states, projected decoder weights, and the requested residual `|delta_i| <= beta_R ell_i`. P5 additionally boxes the tuner multipliers `m_g` and, for a frozen gain choice, gives a local Hurwitz test. Those are useful interface facts. They do not establish stability under arbitrary gain switching, torque-box saturation, rotor allocation, actuator lag, sampling, sensor delay, or large quaternion errors.

The saved P5 v6 run `results/v6_2026-09-25/lqr/cf2-rotor/hardstep/` is a counterexample to any unconditional tracking/safety interpretation of the present bounds: baseline mean quaternion error 0.30090 rad and minimum height 0.40558 m; residual-only 2.19012 rad and 0.01335 m; dual 2.18234 rad and 0.01764 m. Dual saturation fraction is 0.87296 and maximum attitude error 3.14111 rad. The local shortest-path chart is left in this run. These are simulation observations, not a mechanism proof.

Two corrections to `docs/ARCHITECTURE_MATH.md` §8 are important before publication:

1. Decreasing one positive gain need not decrease *net* torque when terms cancel. For `u=-K_p e-K_d omega`, take `e=1`, `omega=-1`, `K_p=K_d=1`: `u=0`; reducing `K_p` to 0.5 gives `u=+0.5`. Thus the per-gain gate is an envelope rule, not a guarantee of reduced actuator demand.
2. A bounded command can destabilize a plant or violate a state constraint. The §8 statement that a hardware anomaly must come from the sim-to-real gap is false as a logical deduction; the saved simulation already shows a large nominal regression under bounded commands. Bounded command and bounded adaptation are necessary but insufficient for tracking stability or safety.

## 2. Best proof for the present unfiltered dual: regional common-Lyapunov ISS

First certify the **actual active gain box**, including every gated and ungated mode. On a constant-reference, unsaturated, local attitude chart, define `z=[e_q; omega_e]` for PD-type families, or `z=[e_q; omega_e; xi]` for PID with its stated integrator logic. The linearization is `dot z=A(K)z+B_d d`, affine in the gain vector `K` while its mode is fixed. For a rectangular gain box `K`, solve for a **single** `P=P^T>0`, `Q=Q^T>0` satisfying

`A(K_v)^T P + P A(K_v) <= -Q`

at every vertex `K_v` of that box. Affinity makes the same inequality hold throughout the box. A common `P` handles *arbitrarily fast* gain changes and the hard loaded/unloaded gate without a slow-variation or dwell-time assumption. It is sufficient, not necessary; infeasibility means only that this certificate failed. For PID, include integral state and the exact conditional-integration modes, or prove a separate hybrid inequality for each mode using the **same** `P`.

On a certified local set, bound the nonlinear remainder, time-varying-reference feedforward error, disturbances, sampled-data error, and the realized-torque mismatch. Then `V=z^T Pz` yields

`dot V <= -a||z||^2+b||z||D`,

`D >= ||delta_R|| + ||e_alloc|| + ||d_ref|| + ||d_plant|| + ||d_sample||`.

This proves regional ultimate boundedness, with a radius proportional to `D`, if the resulting invariant sublevel set stays inside the chart and actuator-feasible region. It gives no guaranteed improvement relative to residual-only, and it cannot cover the recorded CF2 Hardstep trajectory. For P5's attitude-priority allocator, `e_alloc=(alpha-1)tau_req` when collective thrust itself is feasible; even if `alpha=1`, the preceding torque-box saturation and limited authority must still be included.

For the PD-type families, the common-P vertex check is the most useful immediate replacement for the existing frozen-time and unquantified slow-variation claims. LQR, backstepping, MPC, and NMPC need their *implemented* linearizations and reference/offset terms. A certificate for one family is not inherited by another merely because their gains are positive.

**A constructive ideal-axis certificate.** For one decoupled axis with `dot e=omega/2` and `j dot omega=-k_p e-k_d omega`, P5's nominal rule gives `k_p/j=2 omega_n^2`, `k_d/j=2 zeta omega_n`. With the v2/v6 box `m_p in [0.5,1.5]`, `m_d in [1,1.5]`, `zeta=0.95`, take `P_roll=P_pitch=[[102,2],[2,1]]` for `omega_n=4`, and `P_yaw=[[82,2],[2,1]]` for `omega_n=3.5`. Direct evaluation of all four box vertices gives minimum eigenvalues of `-(A^T P+P A)` of `6.3944` and `5.7774`, respectively; `P` is positive definite (minimum eigenvalues `0.9604` and `0.9506`). Since the matrix inequality is affine in `k_p,k_d`, this certifies arbitrary switching of the *ideal, decoupled, unsaturated PD axes* in those boxes. It is a useful mathematical answer to the slow-variation question in that narrow model. It does **not** cover rotated 3-D inertia, PID integral modes, actuator saturation, moving references, or hardware. A family/vehicle certificate must use its actual `J` and implemented law.
The four-vertex arithmetic is reproducible with `python tools/check_ideal_pd_common_p.py`.

## 3. Recommended final hardware theorem: a robust sampled-data Lyapunov filter

Treat S and R as **proposal generators**. Let `u_dual,k` be their combined proposed command and let `u_k` be the physically applied rotor command or Aero2 motor voltage. Include motor lag, filters, integrator, sample/hold and any estimator state in the augmented state `x_k`. Let the measured hardware uncertainty set `W(x,u)` include model residual, sensor error, timing jitter, and disturbance. Let `F_h(x,u,w)` be a validated one-step model for the actual sampling interval.

Choose a compact local region `Omega={x: V(x)<=rho}` away from quaternion switching (for a flying vehicle) and away from unmodeled mechanical limits. At every step, choose the feasible command closest to the dual proposal:

`u_k = argmin_{u in U_hw(x_k)} ||u-u_dual,k||_H^2`, subject to

`sup_{w in W(x_k,u)} V(F_h(x_k,u,w)) <= (1-lambda h_k)V(x_k)+h_k sigma`, and

`F_h(x_k,u,w) in X_safe` for every `w in W(x_k,u)`.

`U_hw` contains voltage/rotor limits and slew limits, using the **applied** control rather than a requested torque box. On Aero2 it must use the measured sample period, whose existing project notes report a loop mean around 380 Hz against a commanded 500 Hz. If the uncertainty bound is too large or no input meets the constraints, a proof is unavailable for that state/reference; the supervisor must use a separately certified fallback or a reference governor and declare the test outside its certified region. An optimization solver returning an infeasible or late result is not silently treated as a valid command.

**Conditional theorem.** Assume (i) the one-step reachable set of the real hardware lies inside `F_h(x,u,W)` for every state/input in `Omega`; (ii) the filter is feasible and solved to a certified tolerance at every step; (iii) the robust state constraint holds between samples as well as at samples, using a reachability/tube bound; (iv) `0<lambda h_k<1`, `sigma/lambda<rho`, and `x_0 in Omega`; (v) the actual input follows the modeled actuator dynamics. Then, for *any* bounded and finite CMG/PES/tuner proposal sequence,

`V(x_k) <= [prod_{j<k}(1-lambda h_j)]V(x_0) + sigma/lambda`,

and the declared safe set is invariant. If `sigma=0`, the tracked equilibrium is exponentially stable in the certified local region. If `sigma>0`, the theorem gives practical stability with ultimate level `sigma/lambda`. The proof is induction on the robust one-step inequality; learner dynamics do not enter except through finiteness and deadline handling. A hard safety constraint and a relaxed tracking CLF can coexist, but a *relaxed* CLF alone gives only a stated practical bound, and feasibility remains an assumption to verify.

This theorem is the best long-term hardware claim because it covers both adaptive channels and their abrupt gates without asserting that PES follows a plant Lyapunov gradient. It requires a validated model set and a certified filter; adding those is a controller change, not a reinterpretation of existing P5 runs.

## 4. Hardware application choice and measurement obligations

The Quanser Aero2 is the cleaner first hardware endpoint: two controlled axes, voltage `+-24 V`, established PD/LQR/backstepping/SMC/NMPC logs, and no free-flying altitude or quaternion antipodal boundary. The current Aero2 notes also say one-step identification fit is good while free-run yaw prediction is poor. Therefore the existing model fits alone cannot justify a narrow robust uncertainty set or a claimed hardware certificate. Reidentify and validate closed-loop one-step reachable error, voltage-to-motion lag, rate limits, sensor timing, and the operating region. Preserve the classical backend unchanged and put the filter between the dual proposal and the hardware actuator interface.

For a later free-flying CF2/X2 claim, add rotor-force allocation, collective/altitude constraints, motor dynamics, battery sag, and reference feasibility. A local quaternion chart is appropriate for practical tracking; a global attitude claim would require a separate hybrid quaternion design and enough actuator authority.

## 5. Concrete sequence

1. **Audit:** reproduce the CF2 Hardstep baseline/R/S/dual summaries and log torque-box clip, APA `alpha`, gate switches, reference jumps, and Lyapunov candidate increments. The residual-only failure means S tuning alone cannot fix the architecture.
2. **Existing-controller certificate:** build `A(K)` from the implemented PD/PID and family-specific laws; attempt common-P vertex LMIs, with separate PID integrator modes. Report solver residuals, eigenvalue margins, and the certified local region; do not infer success from frozen eigenvalues.
3. **Authority design:** bound the residual in the *actuator feasible set* and attenuate or reject proposals that worsen the robust CLF. A rotor-headroom gate should replace the torque-box-only gate for free flight. Keep the PES weights projected and freeze/decay learning when actuation is infeasible.
4. **Aero2 model set:** derive a conservative one-step uncertainty envelope from held-out hardware logs, including missed deadlines and measured `dt`; certify a region with voltage and slew constraints.
5. **Filter validation:** replay saved logs/offline counterfactuals, run virtual twin and HIL with injected delay/mismatch, then supervised hardware from small setpoints. Compare baseline, S, R, dual, and filtered dual; log filter intervention and infeasibility, not just tracking error.

## Primary control sources consulted

- Ames, Xu, Grizzle, Tabuada, *Control Barrier Function Based Quadratic Programs for Safety Critical Systems*, IEEE TAC 2017, https://authors.library.caltech.edu/records/jnhr0-1ww05 — CLF/CBF constraints and actuator bounds.
- Nguyen and Sreenath, *Robust Safety-Critical Control for Dynamic Robotics*, https://arxiv.org/abs/2005.07284 — robust CLF/CBF constraints under uncertainty and feasibility limits.
- Mayhew, Sanfelice, Teel, *Quaternion-Based Hybrid Control for Robust Global Attitude Tracking*, IEEE TAC 2011, https://ieeexplore.ieee.org/document/5701762/ — hybrid/hysteretic route if global attitude tracking is later required.

These sources motivate the design; none certifies the P5 implementation automatically.
