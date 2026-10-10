# One-step rotor reachability and the first L1 controller screen

Date: 2026-10-06. This is a mathematical result for the **declared reduced-order motor model** plus a deterministic MuJoCo sensitivity screen. The 30 and 100 ms time constants are synthetic. They are not estimates of X2, CF2 or QDrone2 motors.

## Exact force reachability in the L1 model

Let each normalized rotor speed be `s in [0,1]`, commanded force `c in [0,fmax]`, realized force `f=fmax s^2`, sample time `h>0`, and first-order speed constant `tau>0`. For a held command,

`s_next = a s + (1-a) sqrt(c/fmax)`, with `a=exp(-h/tau)`.

As `c` varies over its physical command box, the **exact** reachable realized-force interval at the next sample is

`f_next in [fmax (a s)^2, fmax (a s + 1-a)^2]`.

For any target force in that interval, the inverse held command is

`c = fmax [(sqrt(f_next/fmax)-a s)/(1-a)]^2`.

The result follows because `sqrt(c/fmax)` and squaring on nonnegative speeds are monotone. It is implemented in `hifi/rotor_response.py`; `experiments/hifi_quad_2026_10_06/check_reachability.py` checked feasible inversion and rejected an infeasible force. With hover-initialized rotors, `h=0.5 ms`, synthetic `tau=30 ms`, the one-step force intervals are `[3.1430,3.3579] N` per X2 rotor and `[0.064047,0.067113] N` per CF2 rotor under P5's 1.5x force-authority variant. The widths are 6.61% and 4.63% of respective hover thrust, despite much wider static command boxes. Values and model variants are saved in `TWIN_L1_REACHABILITY_2026-10-06.json`.

If a physical time constant is bounded by an interval, for a **fixed** command the next speed is affine in `a`; its extrema over that time-constant interval occur at the endpoint values of `a`. Applying the nonnegative quadratic force map gives an exact interval for this motor law. This is a useful uncertainty component for a future robust sampled-data filter. It does not bound aerodynamic, estimator, battery or contact errors, and it does not establish filter feasibility.

There is a useful **necessary** altitude-authority check. At a stationary hover with body-z tilt `theta`, the maximum end-of-next-sample vertical thrust is `4 f_next,max cos(theta)` if all four rotors take their maximum command. Nonnegative vertical acceleration at that instant requires `cos(theta) >= f_hover/f_next,max`. For the same synthetic 30 ms lag and 0.5 ms step, the maximum permissible tilt under that one-step test is 14.59° for X2 and 9.37° for the P5 CF2 variant. Their static-force limits would suggest 75.52° and 59.70° respectively. These are *instantaneous necessary limits from a hover motor state*, not flight envelopes: velocity/height can buffer transient descent, and demanding a body torque consumes some of the all-rotors-max authority. They show why a static torque box cannot represent immediate altitude authority.

## Controlled 8-second Hardstep screen

`experiments/hifi_quad_2026_10_06/run_l1_v5.py` is a separate opt-in copy of the existing P5 LQR family runner. The initial vehicle state is a hover at 1 m, so its motor state is initialized at hover force. The `tau=0` path assigns the original allocated motor force directly. An unchanged original 2-second CF2/base run and this copied runner's `tau=0` run matched in all 201 decimated rows and 20 common trace columns, with identical reported tracking and height metrics. The first, interrupted screen initialized rotor speed at zero despite a hovering body; it is excluded from conclusions. Its partial files are under `results/l1_sensitivity_2026-10-06/cf2-rotor` and should not be cited.

The corrected screen ran sequentially in one Python process, with no video and 20 Hz stored traces. Each cell used the same 8-second Hardstep reference, LQR/APA controller family, P5 v6 saturation gate, and the v5 platform-specific `e_ref` for S/dual. `results/l1_sensitivity_hover_init_2026-10-06/screen.json` contains all 18 cells, including separate X2 and CF2 authority variants. All 18 summaries record the same source hashes. Selected results:

| Design model | Arm | Synthetic tau | Mean quaternion error (rad) | Minimum height (m) | Requested motor saturation fraction |
|---|---|---:|---:|---:|---:|
| CF2, P5 1.5x | baseline | 0 ms | 0.263 | 0.677 | 0.048 |
| CF2, P5 1.5x | baseline | 30 ms | 0.352 | 0.489 | 0.273 |
| CF2, P5 1.5x | residual | 30 ms | 1.364 | 0.016 | 0.781 |
| CF2, P5 1.5x | self-tuning | 30 ms | 0.359 | 0.441 | 0.288 |
| CF2, P5 1.5x | dual | 0 ms | 0.367 | 0.183 | 0.292 |
| CF2, P5 1.5x | dual | 30 ms | 1.422 | 0.014 | 0.784 |
| CF2, P5 1.5x | baseline | 100 ms | 2.109 | 0.018 | 0.812 |
| X2 | baseline | 30 ms | 0.335 | 0.212 | 0.125 |
| X2 | residual | 30 ms | 1.463 | 0.080 | 0.162 |
| X2 | dual | 0 ms | 0.348 | 0.213 | 0.077 |
| X2 | dual | 30 ms | 0.750 | 0.010 | 0.251 |

These are deterministic design-model outcomes, not statistical performance estimates or hardware predictions. The large instantaneous reference jumps cause a quaternion-error peak around 3 s even in the baseline, so a first-crossing threshold of 1.2 rad is **not** an instability diagnostic here. The sustained post-jump error, saturation and height trajectory are more informative. The 30 ms lag amplifies the already negative residual/dual behavior; a 100 ms lag also causes CF2 baseline failure in this design model. Height near the ground means the controller has left any defensible free-flight certificate region. The plot `results/l1_sensitivity_hover_init_2026-10-06/hardstep_lag_screen.png` shows baseline and dual trajectories for both models.

The saturation metric tests **requested** motor commands against their static limits. The current tuner headroom signal also uses those requests, not realized motor speed. In every stored 30 ms trace sample, APA's torque scaling `alpha` remained 1, yet the applied force differed from the request (motor-force mismatch RMS 0.0033–0.0040 N per CF2 rotor, 0.67–0.73 N per X2 rotor). Thus a statically feasible allocator output does not establish immediate dynamic feasibility. These values are diagnostic for the synthetic model and should not be interpreted as measured motor error.

## Stability-proof implication

The future QDrone2 sampled-data filter must constrain **reachable applied motor forces**, not merely the static force box or requested body torque. A torque proposal that is statically allocatable may be dynamically unreachable in one control interval. Let `B f` denote collective plus body torque from actual rotor forces. At a given augmented state, the feasible next wrench belongs to `B` times the product of four intervals above; the collective/torque coupling persists. A robust CLF/CBF test must propagate this reachable set through the coupled vehicle model and preserve its state constraints between samples. One-step rotor reachability supplies an exact actuator subproblem, but the full QDrone2 theorem still requires identified uncertainty bounds, a feasible filtered baseline and a certified fallback.

There is also a structural obstruction to a *full position* stability theorem for the current P5 runner. It feeds altitude/vertical velocity and attitude/body rates to its control law, but never horizontal position. On a flat, translation-invariant free-flight model at hover, shifting an equilibrium by any small horizontal displacement leaves all sensed control inputs and commands unchanged. Thus there is a continuum of horizontal-position equilibria. A fixed horizontal waypoint cannot be locally asymptotically stable under this controller alone: a nearby shifted equilibrium never converges to it. An outer position loop (or a position-aware CLF filter that supplies that action) is a required controller addition before proving QDrone2 waypoint/geofence stabilization. An attitude or altitude certificate cannot be promoted to a full-flight certificate by relabeling the state.

## Next evidence gates

- Obtain motor command and response traces for each relevant platform; keep their propeller, battery and firmware conditions attached. Fit time-constant *intervals* on training steps and test them on held-out steps before calling L1 calibrated.
- Extend the screen to actuator-identified intervals and a multi-mission holdout. Keep the X2, CF2 P5, CF2 racing and QDrone2 parameter sets separate.
- Build a filter using the exact reachable force box and a coupled position/attitude CLF candidate; test numerical feasibility on the saved CF2 Hardstep trajectory first.
- In QDrone2's native virtual session, log `motorCmd`, state, timing and battery from the installed 47-field telemetry stream; identify its units and the inner-loop injection path before connecting the dual controller.
