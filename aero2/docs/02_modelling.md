# 02 — Modelling

Status: **Phase 3 complete.** Code: `aero2/models/`. Constants: `config.params`.

## Convention
`x = [θ, θ̇, ψ, ψ̇]`, `u = [u_p, u_y]`, `y = [θ, ψ]`. Motor mapping
`u_c=(v_f+v_r)/2`, `u_d=(v_f−v_r)/2` (the IO layer, Phase 4).

## Primary nonlinear plant — `helicopter_2dof.py` (Ref 3, Eqs. 5-10)
```
[θ̈, ψ̈]ᵀ = b(θ,θ̇,ψ,ψ̇) + M(θ) u
b = [(−KSP·sinθ − DP·θ̇)/J_P,  (−DY·ψ̇)/J_Y]ᵀ
M(θ) = [[ d_t·KPP/J_P,  d_t·KPY/J_P ],
        [ cθ·KYP/J_Y,   cθ·KYY/J_Y  ]],   cθ = cos θ clipped to |cθ| ≥ 0.25
```
Params (all in `config.params`): `d_t=0.16743`, `KSP=0.00744`, `DP=0.00199`,
`KPP=0.00321`, `KPY=0.00137`, `DY=0.00192`, `KYY=0.00610`, `KYP=−0.00319`,
`J_P=23188500.45/1000·0.001²`, `J_Y=23810415.95/1000·0.001²`. Symbols:
`models.helicopter_2dof.drift`, `.input_matrix`, `Helicopter2DOF.f`.

**cos(θ) clip** (`MIN_COS_THETA=0.25`) bounds yaw authority at large pitch — kept
per brief §17; verified by `test_cos_theta_clip_active`.

### Inverse dynamics (Ref 3, Eqs. 9-10)
Least squares, not symbolic: `u_raw = argmin‖M(θ)u − (v − b)‖₂`, then clip to
`±24 V`. Symbol: `helicopter_2dof.inverse_dynamics` (used by nonlinear controllers, P7).

## Linear realization — `linear_2dof.py` (Ref 3, Eqs. 13-25)
`ẋ = A x + B u`, `y = C x`, defined once in `linear_plant_matrices()` and reused by
`Helicopter2DOF.linearize()`. The yaw input row uses `KYP, KYY` **without** the
`cos θ` factor (small-pitch linearization, cos 0 = 1). Backbone for LQR/LQG/MPC (P7).

## 1-DOF variants
- **`pitch_only.py`** — pitch with yaw inert; near-integrating (small `KSP` → slow
  pole), which is *why* pitch free-run drifts while one-step stays strong. Only `u_p`
  acts. 4-state-frozen layout (ψ≡ψ̇≡0) so it stays drop-in with the generic backend.
- **`yaw_only.py`** — yaw with pitch inert; driven by the differential `u_y`
  (IO: `u_L=−v_ψ, u_R=+v_ψ`). **Breakaway/stiction**: at rest, `|u_y|` below
  `YAW_BREAKAWAY_V` produces no motion. Thresholds (`YAW_BREAKAWAY_V=2.0 V`,
  `YAW_STICTION_RATE=0.02 rad/s`) are **offline modelling approximations**, grounded
  in the observed first-yaw-motion ~2.0 V — *not* identified constants.

## `half_rotor.py` — FUTURE WORK, hardware `NotValidated`
No validated half-rotor model exists (Ref 3 future work). This is a **plausible
placeholder**: a single rotor arm (elevation + roll), structure mirrored from the
2-DOF helicopter, parameters borrowed as placeholders. Flags `validated=False`,
`hardware_status="NotValidated"`. Treat all half-rotor results as preliminary.

## Model fidelity vs. SOTA literature (validation, 2026-06-09)
Cross-checked against three independent papers, all using the **canonical Quanser
2-DOF helicopter model** (identical structure, two different research groups):
- Kim & Ahn, *Performance-Boosting Attitude Control for 2-DOF Helicopter…*, IEEE TIE 69(7), 2022.
- Kim, Kim & Ahn, *Order Reduction… PD-Type Attitude Stabilizer…*, IEEE TII 18(10), 2022.
- Zhao, Zhang, Liu, Mu & Hong, *Adaptive NN Control of an Uncertain 2-DOF Helicopter…*, IEEE TNNLS, 2022.

Canonical model (their Eqs. 1-2):
```
(J_p + M·l²)·θ̈      = K_pp·V_p + K_py·V_y − M·g·l·cosθ − D_p·θ̇ − M·l²·ψ̇²·sinθ·cosθ
(J_y + M·l²·cos²θ)·ψ̈ = K_yp·V_p + K_yy·V_y − D_y·ψ̇ + 2·M·l²·ψ̇·θ̇·sinθ·cosθ
```

Structural differences from the project's implemented model:
| Aspect | Project (code = truth) | SOTA canonical |
|---|---|---|
| Pitch restoring | `−KSP·sinθ` (weak, KSP=0.0074) | `−M·g·l·cosθ` (gravity, ≈0.075·cosθ) |
| Centrifugal (pitch) | omitted | `−M·l²·ψ̇²·sinθcosθ` |
| Coriolis (yaw) | omitted | `+2·M·l²·ψ̇θ̇·sinθcosθ` |
| Yaw inertia | constant `J_Y` | `(J_y + M·l²·cos²θ)` |
| yaw-input θ-dependence | `cosθ` on input row (clip ≥0.25) | none (it lives in inertia/coupling) |
| Pitch inertia | constant `J_P` | `(J_p + M·l²)` constant ✓ |

Parameter cross-check (project vs. Zhao et al. Table I — Quanser values):
| | J_p | J_y | K_yp (sign) | D_p | D_y |
|---|---|---|---|---|---|
| Project | 0.0232 | 0.0238 | −0.0032 | 0.0020 | 0.0019 |
| SOTA (Quanser) | 0.0215 | 0.0237 | −0.0027 | 0.0071 | 0.0220 |

**Inertias and the negative `K_yp` cross-sign match → confirms the plant is the
Quanser Aero2.** Damping/gain magnitudes differ because the project re-parameterizes
input gains through `DT_ARM` as a moment arm (`torque = DT_ARM·K`, physically
consistent: K is a force gain [N/V], DT_ARM a length [m]).

**Verdict.** The implementation is *faithful to the project code* (no bug). The
project uses a deliberately **simplified, control-oriented** model: it drops the
Coriolis/centrifugal coupling, uses a weak `sinθ` restoring instead of the gravity
`cosθ` term (consistent with the project's own "near-integrating pitch" finding),
and folds the yaw θ-dependence into a `cosθ` input multiplier. Per the brief
(code = truth, preserve results/tunings), the project model stays canonical and is
**not** silently changed.

**Open items for the user (research decisions, not bugs):**
1. The `sinθ`-vs-`cosθ` restoring is the most significant divergence. If it was an
   oversight rather than an intentional θ-reference / identified choice, revisiting
   it would change pitch behavior and all downstream controller tunings.
2. A high-fidelity `helicopter_2dof_hifi` variant implementing the full canonical
   model (Quanser params above) would give a physics-grounded reference plant for the
   SNN-surrogate comparison (Phase 10/14) and a model-fidelity study — added as a
   *new* variant, without altering the project model. (Recommended, optional.)

## What works / what doesn't
Nonlinear + linear 2-DOF and the two 1-DOF reductions are faithful to the code and
run offline. Free-run pitch drift (near-integrating) and yaw breakaway are modelled,
not hidden. Half-rotor is unvalidated by design. The model is a control-oriented
simplification of the full Quanser dynamics (see above).

## How to run
```python
from aero2.models import make_model
from aero2.execution.offline import OfflineBackend
backend = OfflineBackend(make_model("helicopter_2dof"), dt=0.01)
```
