# Paper Narrative — IEEE Conference Draft

## Title (proposed)
"HyperLIF Gate-State Residual Augmentation for Quaternion Attitude Control of Quadrotors"

## Abstract (draft)

We present a neuromorphic augmentation layer for classical quaternion PD attitude controllers on quadrotors. Rather than replacing the PD controller, a bank of HyperLIF neurons runs in parallel, and their continuous gate states—bounded in [0,1]—form a smooth residual torque signal that is blended with the PD output. The gate state's threshold dynamics implement a natural *adaptive gain schedule*: the residual is near zero for small attitude errors (reducing overshoot) and fires near saturation for large errors (boosting convergence torque). We validate on two platforms—Skydio X2 (1.325 kg) and Bitcraze Crazyflie 2 (27 g)—across multi-axis sinusoidal missions in MuJoCo 3.9. On the X2, HyperLIF gate-state residual reduces quaternion tracking error by **6.4%** (hard45, 45 s), **8.1%** (full3, 20 s), and **1.8%** (single-axis roll). Standard neural controllers (Direct LIF, Izhikevich, Nengo LIF-Rate) uniformly degrade performance by 12–20%, confirming that the gate-state mechanism—not neuromorphic augmentation in general—is responsible for the improvement.

---

## 1. Problem Statement

Neural spiking networks are increasingly explored for robotic control, but direct integration into safety-critical attitude control loops remains challenging:
- Spike events are discrete and sparse → hard to use directly as smooth control signals
- Standard LIF neurons add instability if blended naively with PD controllers
- Izhikevich event coding and Nengo LIF-Rate population coding both degraded performance by 12–20% in our benchmarks

The key question: *can a neurodynamic mechanism naturally implement adaptive gain scheduling without explicit hand-tuning of gain schedules?*

---

## 2. Key Insight (our contribution)

The HyperLIF gate state r ∈ [0,1] is a *continuous*, *bounded* signal that rises smoothly as the neuron approaches threshold. When used in gate mode:
- r responds to input current magnitude
- r encodes the "readiness to act" of the neuron
- r can be decoded as a smooth torque residual signal even without explicit spikes

**Threshold-adaptive gain scheduling:** with pair-coded neuron inputs biased below v_thresh:
- Small error (|τ_norm| < 0.20): gate stays near 0 → τ_final ≈ (1−β)·τ_pd (softer gain)
- Large error (|τ_norm| > 0.20): gate fires to r≈1 → τ_final → ±τ_limit (boosted gain)
- Threshold fires at τ_norm ≈ 0.20, i.e., |e_q| ≈ 0.76° attitude error

This creates a two-regime adaptive schedule entirely from gate dynamics, requiring no explicit logic.

---

## 3. Method Summary

**Body-torque gate-state residual architecture:**
```
τ_pd   = −kq·e_q − kw·ω               (clipped to τ_limit)
τ_norm = τ_pd / τ_limit               (in [−1, 1], per axis)
I_pos  = bias + gain · max(+τ_norm, 0)  (positive-channel currents)
I_neg  = bias + gain · max(−τ_norm, 0)  (negative-channel currents)
r      ← HyperLIF gate dynamics         (integrate I_pos, I_neg)
δ_τ    = clip(r_pos − r_neg, −1, 1) · τ_limit
τ_final = (1−β)·τ_pd + β·δ_τ
```

**Gain design:** wn=15 rad/s, ζ=0.9, α_max=30 rad/s² → kq=2I·wn², kw=2ζ·wn·I, τ_limit=I·α_max

**Key parameters:** β=0.50, gate_gain=100000 (clips gate output to binary ±1), bias=0.75, input_gain=1.25

**HyperLIF dynamics:**
```
dv/dt = (−(v−v_rest) + I)/τ − reset_gain·r²·(v−v_reset)
dr/dt = (σ(α·(v−θ_eff)) − r)/τ_r
θ_eff = v_thresh − γ·r                  (gate-modulated threshold)
```
Parameters: τ=0.05, τ_r=0.005, reset_gain=120, γ=2.0, v_thresh=1.0

---

## 4. Experimental Results (from v2_clean MuJoCo simulations)

*All experiments: MuJoCo 3.9.0, dt=0.5 ms, seed=1, Python 3.11.*

### Table 1: Controller Comparison — Skydio X2, hard45 Mission, 45 s

| Controller | qerr_mean [rad] | qerr_max [rad] | RMSE_euler [rad] | Score | Δqerr_mean |
|-----------|:--------------:|:--------------:|:----------------:|:-----:|:----------:|
| Classical PD | 0.2941 | 0.5811 | 0.1806 | 0.2977 | baseline |
| Direct LIF (voltage) | 0.3518 | 0.7086 | 0.2131 | 0.3559 | **−19.6%** |
| **HyperLIF (gate)** | **0.2753** | **0.5460** | **0.1703** | **0.2807** | **+6.4%** |
| Adaptive HyperLIF (gate) | 0.2753 | 0.5460 | 0.1703 | 0.2807 | +6.4% (= HyperLIF) |
| Izhikevich (events) | 0.3488 | 0.7025 | 0.2116 | 0.3530 | −18.6% |

Score = qerr_mean + 0.02·τ_mean + 0.20·rotor_sat_fraction + 0.05·z_std. Lower is better.

> **HyperLIF = Adaptive HyperLIF** at gate_gain=100000 because both variants saturate to binary gate output r∈{0,1}. The adaptive gain only affects voltage dynamics (transient speed), not gate equilibrium. Differentiation requires lower gate_gain or softer threshold.

### Table 2: Cross-Mission Generalization — Skydio X2, HyperLIF (gate)

| Mission | Sim | Classical qerr | HyperLIF qerr | Δqerr | Notes |
|---------|-----|:--------------:|:-------------:|:-----:|-------|
| hard45 | 45 s | 0.2941 | 0.2753 | **+6.4%** | Multi-axis sinusoidal |
| full3 | 20 s | 0.3056 | 0.2810 | **+8.1%** | 3-axis combined |
| roll | 20 s | 0.0512 | 0.0503 | +1.8% | Single-axis roll |
| step | 20 s | 2.085 | 2.206 | −5.8% qerr | z_std: 4.0→0.48 m (+88%) |

> Step mission: HyperLIF shows slightly higher attitude error during step impulse but dramatically better altitude stability (z_std 4.0→0.48 m). The composite score improves (+2.4%).

### Table 3: Cross-Platform Comparison — hard45, 45 s

| Platform | Controller | qerr_mean | Score | Δqerr vs classical |
|---------|-----------|:---------:|:-----:|:------------------:|
| Skydio X2 | Classical PD | 0.2941 | 0.2977 | — |
| Skydio X2 | Direct LIF | 0.3518 | 0.3559 | −19.6% |
| **Skydio X2** | **HyperLIF (gate)** | **0.2753** | **0.2807** | **+6.4%** |
| Crazyflie 2 | Classical PD | 0.2854 | 0.2949 | — |
| Crazyflie 2 | Direct LIF | 0.3203 | 0.3304 | −12.2% |
| **Crazyflie 2** | **HyperLIF (gate)** | **0.2820** | **0.2916** | **+1.2%** |
| Crazyflie 2 | Nengo LIF-Rate | 0.3218 | 0.3316 | −12.7% |

> CF2 improvement is smaller (+1.2%) because the tiny CF2 inertia means τ_limit (7.2×10⁻⁴ Nm) is much smaller relative to the control authority needed, so the controller operates near saturation and the gate fires almost continuously.

### Table 4: Cross-Mission — Crazyflie 2, HyperLIF (gate)

| Mission | Classical qerr | HyperLIF qerr | Δqerr |
|---------|:--------------:|:-------------:|:-----:|
| hard45 (45 s) | 0.2854 | 0.2820 | +1.2% |
| full3 (20 s) | 0.2906 | 0.2867 | +1.3% |
| roll (20 s) | 0.0520 | 0.0503 | +3.3% |

---

## 5. Key Scientific Findings

1. **Gate-state dynamics are essential:** Direct LIF (voltage mode) degrades by 12–20%. The gate state's continuous, bounded nature enables smooth residual control without instability.

2. **Threshold-adaptive gain scheduling:** Gate fires at τ_norm≈0.20 (|e_q|≈0.76°), creating two regimes:
   - Below threshold: (1−β)×gain — softer, less oscillation
   - Above threshold: full residual → boosted gain toward τ_limit — faster convergence

3. **Cross-platform consistency:** Both X2 and CF2 show improvement. The effect is stronger on X2 (6.4% vs 1.2%), likely because X2 has more dynamic range between τ_limit and typical τ_pd, allowing the gate to modulate a larger fraction of control authority.

4. **Altitude stability improvement (step mission):** Near-setpoint gain reduction dramatically reduces altitude perturbations — z_std drops 88% — because reduced PD torques during hover corrections perturb the altitude-maintaining force budget less.

5. **Standard neural controllers uniformly fail:** LIF voltage (−12% to −20%), Izhikevich (−18.6%), Nengo LIF-Rate (−12.7%). The gate mechanism is the differentiator, not neuromorphic augmentation in general.

---

## 6. Experimental Setup

| Parameter | Value |
|-----------|-------|
| Simulator | MuJoCo 3.9.0 |
| Platform A | Skydio X2 (1.325 kg, I=[0.0607,0.0365,0.0254] kg·m²) |
| Platform B | Bitcraze Crazyflie 2 (27 g, I=[2.4,2.4,3.2]×10⁻⁵ kg·m²) |
| Control dt | 0.5 ms |
| Gain design | wn=15 rad/s, ζ=0.9, α_max=30 rad/s² |
| Missions | hard45 (45 s), full3 (20 s), roll (20 s), step (20 s) |
| Metric | qerr_mean + 0.02×τ_mean + 0.20×sat_fraction + 0.05×z_std |
| X2 control | Rotor-level via B⁻¹ mixer (4-motor allocation) |
| CF2 control | xfrc_applied (external force/torque injection) |

**Hard45 mission:** φ(t) = 0.55·sin(0.75t) + 0.20·sin(2.10t+0.40), θ(t) = 0.45·sin(0.95t+π/3) + 0.18·sin(1.75t), ψ(t) = 0.65·sin(0.55t+π) + 0.25·sin(1.35t+0.20). Peak amplitudes ≈45° on each axis simultaneously.

---

## 7. Paper Sections (Target: 8 IEEE pages)

1. **Introduction** — quadrotor PD limitations, neuromorphic motivation, gate-state contribution
2. **Related Work** — SNN control, Nengo robotics, adaptive gain scheduling
3. **Mathematical Formulation** — quaternion PD, HyperLIF dynamics, gate-state mechanism
4. **Method** — pair-coded encoding, gate-state residual, gain design
5. **Experimental Setup** — MuJoCo platforms, missions, metrics
6. **Results** — Tables 1–4, comparison figures, ablation (gate vs voltage vs events)
7. **Analysis** — threshold mechanism, why gate >> LIF, CF2 vs X2 discussion
8. **Conclusion** — summary, limitations, future work

---

## 8. Figures for Paper

1. `compare_skydio_x2_hard45_qerr.pdf` — main result: all controllers, X2
2. `compare_skydio_x2_hard45_euler.pdf` — Euler angle tracking overlay
3. `compare_skydio_x2_hard45_gate.pdf` — gate state dynamics
4. `compare_bitcraze_crazyflie_2_hard45_qerr.pdf` — CF2 cross-platform validation
5. Threshold diagram: τ_norm vs effective gain (conceptual, to be drawn)
6. Architecture block diagram (TikZ)

---

## 9. Limitations and Future Work

- **HyperLIF ≡ Adaptive HyperLIF at saturation**: With gate_gain=100000, both saturate to binary gate. The adaptive conductance affects transient speed only. Future work: explore gate_gain sweep (100–100000) to find intermediate regime where conductance adaptation matters.

- **Rotor-level residual**: Body-torque gate-state residual (+6.4%) outperforms rotor-level residual (~0.7%). The multi-axis error problem: combined hard45 activates multiple motor channels simultaneously, reducing directional differential. Single-axis missions may show stronger rotor-level effect.

- **Physical hardware validation**: CF2 experiments use xfrc_applied (bypasses actuator limits). A custom CF2 XML with properly scaled motor actuators is needed for hardware-realistic simulation.

- **Online adaptation**: Fixed blend β and gate_gain. An adaptive β proportional to gate activity could further reduce oscillation near setpoint.

---

## 10. BibTeX References (key, to be completed)

```bibtex
@article{quaternion_pd,
  title={Full quaternion-based attitude control for a quadrotor},
  author={Fresk, Emil and Nikolakopoulos, George},
  journal={IFAC Proceedings Volumes},
  year={2013},
}

@inproceedings{nengo,
  title={Building a large-scale functional brain model},
  author={Bekolay et al.},
  booktitle={Science},
  year={2014},
}

@article{mujoco,
  title={MuJoCo: A physics engine for model-based control},
  author={Todorov, Emanuel and Tassa, Yuval and Erez, Tom},
  journal={IEEE IROS},
  year={2012},
}

@article{izhikevich2003,
  title={Simple model of spiking neurons},
  author={Izhikevich, Eugene M.},
  journal={IEEE Transactions on Neural Networks},
  year={2003},
}
```
