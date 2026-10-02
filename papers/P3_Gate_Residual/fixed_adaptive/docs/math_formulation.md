# Mathematical Formulation

## 1. Quaternion Attitude Representation

Unit quaternion: **q** = [q₀, q₁, q₂, q₃] = [w, x, y, z], ‖q‖ = 1

Convention: q₀ is scalar (real) part; [q₁, q₂, q₃] is vector (imaginary) part.

### Quaternion product
```
p ⊗ q = [p₀q₀ − pᵥ·qᵥ,  p₀qᵥ + q₀pᵥ + pᵥ×qᵥ]
```

### Conjugate / inverse
```
q* = [q₀, −q₁, −q₂, −q₃]
```

### Euler ZYX → quaternion
```
q = f(φ, θ, ψ)   where φ=roll, θ=pitch, ψ=yaw
```

---

## 2. Rigid-Body Attitude Dynamics

State: **x** = [**q**(4), **ω**(3)]  — 7 states

**Quaternion kinematics** (paper sign convention):
```
q̇ = −0.5 · Ω(ω) ⊗ q
```
where Ω(ω) = [0, ωₓ, ωᵧ, ω_z] is a pure quaternion.

**Angular rate dynamics** (Newton-Euler):
```
ω̇ = I⁻¹ (τ − ω × Iω)
```

where I = diag(Iₓₓ, Iᵧᵧ, I_zz) is the body inertia tensor.

---

## 3. Classical Quaternion P2 Controller

**Attitude error:**
```
q_err = q_ref ⊗ q_meas*
```

Shortest-path correction: if q_err[0] < 0, use −q_err.

**Vector error:** e_q = vec(q_err) = q_err[1:4]

**Control law:**
```
τ = −Kq · e_q − Kw · ω
```

**Gain design (bandwidth-based):**
```
Kq = 2 · I · ωₙ²
Kw = 2 · ζ · ωₙ · I

where ωₙ = desired natural frequency, ζ = damping ratio
```

Default: ωₙ = [4, 4, 3.5] rad/s, ζ = 0.95

**Torque saturation:** τ = clip(τ, −τ_max, τ_max)

---

## 4. HyperLIF Neuron Dynamics

Standard LIF baseline:
```
dv/dt = (−(v − v_rest) + I) / τ_m
fire when v ≥ v_thresh, reset to v_reset
```

HyperLIF extends LIF with a gate/reset state r:
```
dv/dt = (−(v − v_rest) + I) / τ_m  −  g_reset · r² · (v − v_reset)

dr/dt = (σ(α·(v − eff_thresh)) − r) / τ_r

eff_thresh = v_thresh − γ·r
```

where σ(x) = 1/(1 + e^{−x}) is the sigmoid function.

**Key property of the gate state r:**
- r ∈ [0, 1] is a continuous, differentiable signal
- r rises as v approaches threshold
- r acts as a "readiness-to-fire" indicator
- r is smooth even without explicit spike events
- **r can be used directly as a residual control signal**

---

## 5. Adaptive HyperLIF

Replaces fixed reset_gain with input-dependent conductance:
```
g_dynamic = g_base + g_scale · |I|
```

This means: larger input current → stronger gate activation → more responsive
residual signal. Useful for maneuvers with varying intensity.

---

## 6. Gate-State Residual Controller (Body-Torque)

**Pair-coded current encoding:**
```
I_pos[k] = bias + gain · max(τ_norm[k], 0)     k = 0,1,2
I_neg[k] = bias + gain · max(−τ_norm[k], 0)    k = 0,1,2
```
where τ_norm = τ_pd / τ_limit.

**Neural update:** advance 6 HyperLIF neurons by one dt step.

**Decoding:**
```
signed_activity[k] = clip(r_pos[k] − r_neg[k], −1, 1)
τ_neural = signed_activity · τ_limit
```

**Final torque:**
```
τ = (1−β) · τ_pd + β · τ_neural
τ = clip(τ, −τ_limit, τ_limit)
```

where β = `blend` ∈ [0, 1].

---

## 7. Rotor Mixer (Skydio X2)

**Actuator model:** 4 motors at positions r_i = [x_i, y_i, z_i].
Each motor produces force F_i = u_i · ẑ_body and yaw reaction torque κ_i · u_i.

**Mixer equation:**
```
[T, τₓ, τᵧ, τ_z]ᵀ = B · [u₁, u₂, u₃, u₄]ᵀ
```

where:
```
B = | 1     1     1     1   |   (collective thrust)
    | y₁    y₂    y₃    y₄  |   (roll torque)
    | −x₁  −x₂  −x₃  −x₄  |   (pitch torque)
    | κ₁    κ₂    κ₃    κ₄  |   (yaw torque)
```

For Skydio X2 (from scene.xml):
- Positions: (±0.14, ±0.18, ~0.065) m
- Yaw coefficients κ = [−0.0201, +0.0201, −0.0201, +0.0201]
- Hover: u_i ≈ 3.25 N each (total mass ≈ 1.325 kg)
- Range: [0, 13] N per motor

**Motor commands from desired wrench:**
```
[u₁, u₂, u₃, u₄]ᵀ = B⁻¹ · [T, τₓ, τᵧ, τ_z]ᵀ
u_i = clip(u_i, 0, 13)
```

---

## 8. Rotor-Level Gate-State Residual

**8-neuron pair encoding (one per motor, + and − channels):**
```
I_pos[i] = bias + gain · (u_nom[i] − u_min) / u_range    i = 0..3
I_neg[i] = bias + gain · (u_max − u_nom[i]) / u_range    i = 0..3
```

**Decoding:**
```
Δu[i] = clip(r_pos[i] − r_neg[i], −1, 1) · u_scale
u_final = clip(u_nominal + β_r · Δu, u_min, u_max)
```

where β_r = `residual_blend`, u_scale = scalar amplitude of residual.

---

## 9. Crazyflie 2 — Virtual Wrench Interface

CF2 actuators (from cf2.xml):
```
ctrl[0] = body_thrust     ∈ [0, 0.35] N      gear = [0,0,1,0,0,0]
ctrl[1] = x_moment        ∈ [−1, 1]           gear = [0,0,0,−1e-5,0,0]
ctrl[2] = y_moment        ∈ [−1, 1]           gear = [0,0,0,0,−1e-5,0]
ctrl[3] = z_moment        ∈ [−1, 1]           gear = [0,0,0,0,0,−1e-5]
```

Torque mapping:
```
ctrl[1] = −τₓ / gear_mx
ctrl[2] = −τᵧ / gear_my
ctrl[3] = −τ_z / gear_mz
```

Note: CF2 maximum torque ≈ 1e-5 Nm. Since I_CF2 ≈ 2.4e-5 kg·m², this
limits α_max ≈ 0.4 rad/s² via the virtual interface. The xfrc_applied
path is needed for larger torques during experiments. The CF2 virtual
interface suffices for hover + gentle maneuvers.
