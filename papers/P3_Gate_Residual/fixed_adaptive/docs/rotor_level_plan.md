# Rotor-Level Control Plan

## Overview

The current implementation uses two distinct control paths:

| Path         | Actuator         | Drone     | Notes                                   |
|--------------|------------------|-----------|-----------------------------------------|
| body_torque  | xfrc_applied     | both      | Legacy. External force/torque injection |
| wrench4      | CF2 virtual acts | CF2       | Body thrust + 3 moment actuators        |
| rotor4       | 4 real motors    | X2 only   | Physically accurate, rotor-level        |

## Skydio X2 — Rotor-Level Pipeline

```
q_ref ─────────────────────────────────────────────────────┐
                                                            ▼
q_meas ──► ClassicalPD ──► tau_pd ──► B_inv ──► u_nominal  │
                                                    │        │
          HyperLIF neurons ◄── encode(u_nominal)   │        │
                │                                   │        │
           gate state r ──► decode ──► Δu           │        │
                                        │            │        │
                                 u_final = clip(u_nominal + β·Δu)
                                        │
                                  MuJoCo actuators (data.ctrl)
```

### Mixer Matrix B (Skydio X2)

```
Motor positions (from scene.xml):
  thrust1: (-0.14, -0.18, 0.05)  yaw_k = -0.0201
  thrust2: (-0.14, +0.18, 0.05)  yaw_k = +0.0201
  thrust3: (+0.14, +0.18, 0.08)  yaw_k = -0.0201
  thrust4: (+0.14, -0.18, 0.08)  yaw_k = +0.0201

Mixer B:
  Row 0: [1, 1, 1, 1]                         collective thrust
  Row 1: [-0.18, 0.18, 0.18, -0.18]           roll torque (y positions)
  Row 2: [0.14, 0.14, -0.14, -0.14]           pitch torque (-x positions)
  Row 3: [-0.0201, 0.0201, -0.0201, 0.0201]   yaw torque (gear coefficients)
```

### Hover Equilibrium
```
Total mass = 1.325 kg (0.25 × 4 rotors + 0.325 ellipsoid)
Hover thrust per motor = 1.325 × 9.81 / 4 ≈ 3.25 N
Motor range: [0, 13] N
```

## CF2 — Virtual Wrench Pipeline

```
q_ref ──► ClassicalPD / DirectNeuron ──► tau_body
                                              │
                                    CF2 moment actuators (ctrl[1:4])
                                    + external hover force (xfrc_applied)
```

CF2 inertia: Ixx = Iyy = 2.3951e-5, Izz = 3.2347e-5 kg·m²
CF2 mass: 0.027 kg
CF2 hover thrust: 0.027 × 9.81 ≈ 0.265 N (within [0, 0.35] range)

## Architectural Alternatives Evaluated

### A) Classical → Rotor Mixer [IMPLEMENTED]
- Most stable, clean separation of attitude and thrust
- Baseline for all comparisons

### B) Classical + Body-Torque Residual → Rotor Mixer [IMPLEMENTED]
- HyperLIF residual on tau before mixing
- Works on both X2 and CF2

### C) Classical → Rotor Mixer + Rotor Residual [IMPLEMENTED]
- HyperLIF residual directly on motor commands
- X2 only, most physically meaningful

### D) Pure Nengo Neural [IMPLEMENTED]
- Ensemble decodes same PD law
- Good benchmark comparison point

### E) Adaptive HyperLIF + Safety Bounds [IMPLEMENTED]
- Input-adaptive gate gain
- All commands clipped

## Known Limitations

1. **CF2 torque range**: The CF2 virtual moment actuators provide only ±1e-5 Nm.
   Inertia-scaled tau_limit ≈ 2.87e-4 Nm requires xfrc_applied as fallback.
   See `quad/bridge.py: apply_cf2_wrench()` — for aggressive maneuvers the CF2
   path will saturate. The xfrc_applied path bypasses this.

2. **CF2 no true 4-motor interface**: CF2 menagerie model uses abstract body torques.
   True 4-motor CF2 simulation would require a custom XML with 4 motor sites.

3. **Rotor residual tuning**: `u_scale` and `residual_blend` interact. Start with:
   - u_scale = 0.05 × (ctrl_max - ctrl_min) = 0.5 N (conservative)
   - residual_blend = 0.05 to 0.15

4. **Roll360 limitation**: Full roll flips cause thrust to point downward.
   External hover force support is absent during inversion. This is a known
   research frontier documented in the experimental notes.

## Next Steps

1. Tune `gate_gain` sweep for rotor_residual controllers on X2
2. Run Hard45 × 45s comparison: classical vs rotor_residual_adaptive_hyperlif
3. Investigate CF2 custom XML with 4 motor sites for true rotor parity
4. Add video logging to dashboard
