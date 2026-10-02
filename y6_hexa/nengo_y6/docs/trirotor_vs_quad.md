# Coaxial Y6 Trirotor vs. Quadrotor — the explicit mathematical diff (Phase 5)

What actually changes when the airframe evolves from Victor's quad (Phases 2–4) to the coaxial
Y6 trirotor (Phase 5). **The controller recipe is unchanged** (cascaded PD, virtual commands,
NEF realization); the *plant* and the *allocation* are what differ. Y6 model from `01_Code`
(Mehndiratta & Kayacan 2018 [M]; Czyba 2015 [C]).

## 1. Airframe & actuation
| | Quadrotor (Phases 2–4) | Coaxial Y6 trirotor (Phase 5) |
|---|---|---|
| rotors | 4, single plane | **6**, in **3 coaxial pairs** on a triangular frame |
| thrust map | virtual `u` (no per-rotor) | `F_i = K_F Ω_i²` per rotor, `i=1..6` |
| geometry | one arm length | **3 levers** `l1`(front), `l2`(lateral), `l3`(longitudinal) |
| yaw torque | virtual `τ_ψ` | **coaxial top-vs-bottom drag split** `τ_z = Στ_top − Στ_bot` |
| extra physics | — | gyroscopic moments from coaxial pairs; full `I_xz`-coupled moments |

## 2. State vector
- **Quad:** `[x,ẋ,y,ẏ,z,ż, ψ,ψ̇, θ,θ̇, φ,φ̇]` — reduced model, position/velocity interleaved.
- **Y6:** `[X,Y,Z, u,v,w, φ,θ,ψ, p,q,r]` — full rigid body in **body-frame velocities** `(u,v,w)`
  and body rates `(p,q,r)`, with `R_EB`, `T_EB` kinematic transforms (the complete Newton–Euler
  form, more faithful than the quad's reduced model).

## 3. Moments (the Y6-specific structure)
```
τ_x (roll)  = ((F5+F6) − (F1+F2))·l2                 + gyroscopic
τ_y (pitch) = (F3+F4)·l1 − (F1+F2+F5+F6)·l3          + gyroscopic
τ_z (yaw)   = (τ1+τ3+τ5) − (τ2+τ4+τ6)        [top − bottom coaxial drag]
```
vs. the quad, where `τ_φ, τ_θ, τ_ψ` were the (virtual) control inputs directly.

## 4. THE divergence — control allocation
- **Quad:** controller emits `[u, τ_φ, τ_θ, τ_ψ]` → fed **straight to the plant**. No allocation.
- **Y6:** the 4 virtual commands must be distributed to **6** rotors — an over-actuated,
  under-determined map requiring an explicit **6×4 mixer**:
  ```
  [F1..F6]ᵀ = A(6×4) · [T, τ_x, τ_y, τ_z]ᵀ ,   then  Ω_i = √(F_i/K_F)  (clipped)
  ```
  `A` encodes the triangular geometry (`l1,l2,l3`) and the coaxial yaw split
  (`k_ψ = K_F/(6 K_τ)`). This is implemented classically (`src/allocation/y6_allocation.py`)
  and **neuromorphically** (a 4-D NEF ensemble decoding the six rows of `A` —
  `src/controllers_nengo/trirotor_nef.py`), the new neural component of Phase 5.

## 5. What stays identical
The **cascade controller** — outer position PD → tilt set-points `(θ*,φ*)` via `atan`/rotation,
inner attitude PD → body moments, gravity feed-forward thrust — is the *same recipe* as the quad
(`trirotor_pd.py` mirrors `quadrotor_pd.py`). The **NEF mapping** is identical: PD laws in neuron
populations, nonlinear inversions in nodes. Only the plant and the allocation layer are new.

## 6. Parameters used (Y6 inertias, per your direction) — Mehndiratta Table I
`m=1.412 kg`, `l1=0.28, l2=0.243, l3=0.14 m`, `Ixx=0.014965, Iyy=0.021915, Izz=0.034433 kg·m²`
(`Ixz=0` for a positive-definite tensor), `K_F=6.85e-6, K_τ=3.35e-7`, `Ω_max=900 rad/s`.
