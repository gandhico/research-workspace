# Paper 4 — Results, Parameters, Runners (update 2026-07-05)

Consolidated MuJoCo evidence for the gate-state residual **mechanism** paper,
plus the required correction to the Adaptive-HyperLIF claim. Drop-in LaTeX:
`paper/sec_mujoco_gate_mechanism.tex` (`\input` after `\section{Results}`).

---

## ⚠️ REQUIRED CORRECTION — Contribution (3) is disproven

`main2.tex` currently states (Contribution 3, and Section headings):
> "an Adaptive HyperLIF variant ... outperforms fixed HyperLIF and a direct LIF
> baseline across all Hard45 metrics."

**This is false.** In gate mode Adaptive HyperLIF is **numerically identical** to
HyperLIF (bit-for-bit, fixed and learned decode). Mechanism: the operating point
sits at `r ≈ 3.7e-6`, and the adaptive gain enters only via `g = (g_b+κ|I|)·r²`;
with `r² ≈ 1.4e-11`, `g ≈ 2e-9` — ~10 orders below `1/τ = 20`. The adaptive gain
multiplies a ~0 number. **Action:** replace Contribution 3 with the *equivalence*
finding (see `sec_mujoco_gate_mechanism.tex`, §"Adaptive HyperLIF equals HyperLIF
in gate mode"). This turns a would-be reviewer objection into a clean, cited
boundary result and de-scopes the paper to a single neuron model.

---

## 1. Fixed gate-residual — cross-platform (Hard45, 45 s, control scale, gate, G=1e5, β=0.5)

| platform | classical | fixed gate | improvement | decoded residual |
|---|---|---|---|---|
| Bitcraze Crazyflie 2 | 0.287391 | 0.266117 | 7.4% | ~1.75e-5 N·m |
| Skydio X2 | 0.299286 | 0.282060 | 5.8% | (larger; still small) |

**Honest framing:** the improvement is real but is *selective half-PD detuning*
with a near-silent gate (residual ~1e-5 N·m, ~0.04% duty). This supports the
paper's selectivity / timing-causality / actuation-economy story; the gate's
*performance* potential is unlocked by learning the decode → **Paper 5**.

## 2. Adaptive ≡ HyperLIF (gate mode) — identical scores

| condition | HyperLIF | Adaptive HyperLIF |
|---|---|---|
| Bitcraze fixed gate | 0.266117 | 0.266117 |
| Bitcraze learned aggressive | 0.038258 | 0.038258 |
| Bitcraze learned balanced | 0.120469 | 0.120469 |
| Skydio learned aggressive | 0.129264 | 0.129264 |

## 3. Parameters (control scale, gate mode)

| group | parameter | value |
|---|---|---|
| HyperLIF | τ, τ_r | 0.05 s, 0.005 s |
| | reset_gain g0, γ | 120, 2 |
| | α, v_thresh, event_thresh | 50, 1.0, 0.5 |
| | activity, gate_gain G | gate, 1e5 |
| Adaptive | base_gain, gain_scaling | 120, 30 (inert) |
| Encoding | bias, gain, channels | 0.75, 1.25, 6 (pair-coded) |
| Blend / sim | β, dt, T | 0.5, 5e-4 s, 45 s |
| Metric | J | qerr_mean + 0.02·τ̄ + 0.20·f_sat + 0.05·σ_z |

## 4. Runner commands (this validation)

Ground-truth scripts (`experiments/controller_benchmarks/`, venv python):
```powershell
# Fixed HyperLIF gate residual -> 0.26612 (Bitcraze), 0.28206 (Skydio)
python mujoco_classical_vs_neural.py --controller direct_hyperlif --quad bitcraze_crazyflie_2 `
  --mission hard45 --sim-time 45 --dt 0.0005 --z-ref 1.0 --direct-scale control `
  --direct-activity-mode gate --direct-gate-gain 100000 --direct-blend 0.5

# Adaptive HyperLIF (identical result)
python mujoco_classical_vs_neural.py --controller direct_adaptive_hyperlif --quad bitcraze_crazyflie_2 `
  --mission hard45 --sim-time 45 --dt 0.0005 --z-ref 1.0 --direct-scale control `
  --direct-activity-mode gate --direct-gate-gain 100000 --direct-blend 0.5

# Classical reference
python mujoco_classical_vs_neural.py --controller classical --quad bitcraze_crazyflie_2 `
  --mission hard45 --sim-time 45 --dt 0.0005 --z-ref 1.0
```
Equivalence + mechanism sweep (self-contained pipeline):
```powershell
python learned_gate_experiment.py --neuron adaptive_hyperlif --methods classical,fixed_gate,online_pes,eprop_anneal
```
Paper's own rotor-level runners: see `docs/runner_commands.md` (unchanged).

## 5. Cross-reference
- Full learned-gate performance story (Paper 5): `10_Paper5_Learned_Gate_Control/`.
- Mechanism mirror: `neuromorphic-robotics-control/docs/2026_07_05_learned_gate_residual_advances.md`.
- Pending Paper 4 hardware: Qube Servo 3 pendulum HW rows (Table + Section).
