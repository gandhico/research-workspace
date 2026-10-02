# Paper 5 — Online-Learned HyperLIF Gate Residual: Full Results Dossier

**Date:** 2026-07-05  •  **Line:** Neuromorphic Embodied AI (program Paper 5).
**Thesis:** making the HyperLIF gate decode *learnable* converts the modest fixed
residual into an online-adaptive neuromorphic controller that **beats** the
hand-tuned adaptive STN-PID-PES baseline and **generalizes across platforms**.

Everything here is reproducible from
`neuromorphic-robotics-control/experiments/controller_benchmarks/learned_gate_experiment.py`
(MuJoCo 3.8; venv `.venv\Scripts\python.exe`). Primary write-up mirror:
`neuromorphic-robotics-control/docs/2026_07_05_learned_gate_residual_advances.md`.

---

## 1. The fixed-gate ceiling — diagnosed

The self-contained pipeline reproduces the ground-truth scripts **bit-for-bit**:
classical `0.287391`, fixed gate `0.266117`. But at the validated operating point
the decoded residual torque is only **1.75e-5 N·m**. The pair-coded gate channels
are near-symmetric, the fixed decode `W0 = [I | −I]` cancels them, and
`τ ≈ (1−β)·τ_pd` — the +7.4% is **half-PD detuning**, not the gate. The gate is a
passenger. ⇒ learn the decode.

## 2. Primary benchmark — Bitcraze / hard45, aggressive learning (lr=8e-4, k_err=8)

| method | score J | qerr_mean | vs classical | note |
|---|---|---|---|---|
| classical (PD) | 0.287391 | 0.285448 | — | reference |
| fixed gate | 0.266117 | 0.264470 | +7.4% | residual ~0 (half-PD) |
| STN-PID-PES (teacher) | 0.047864 | 0.045254 | +83.3% | adaptive baseline |
| **online_pes** (idea 1) | **0.038258** | 0.035549 | **+86.7%** | **beats teacher** |
| **eprop_anneal** (idea 3) | **0.038215** | 0.035445 | **+86.7%** | ≈ online_pes |
| imitation / imitation_pes (idea 2) | ~2.6 | — | diverges | covariate shift |
| demand_mod (idea 4) | 0.266547 | — | +7.3% | no effect on fixed decode |
| stn_mod (idea 5) | 0.265530 | — | +7.6% | no effect on fixed decode |

Learned decode raises residual torque ~7× (to 1.3e-4 N·m); gate activity stays
selective (~0.40). e-prop ≈ online PES ⇒ the online delta-rule is the driver.

## 3. Generalization — online_pes across regimes × platforms (score J, lower better)

| config | hard45 (CF2) | hardstep (CF2) | hard45 (Skydio) |
|---|---|---|---|
| classical | 0.287 | 0.690 (flips) | 0.299 |
| fixed gate | 0.266 | 0.108 | 0.282 |
| STN-PID-PES | 0.048 | 0.331 | 0.298 (≈ classical) |
| **learned aggressive** (k_rate 0, leak 0) | **0.038** | 2.18 diverges | **0.129** |
| **learned balanced** (k_rate 0.3, leak 1e-3) | 0.120 | 0.158 stable | 0.150 |
| **learned strong-damp** (k_rate 1.0, leak 2e-3) | 0.153 | **0.095** | 0.214 |

Skydio: STN-PID-PES ≈ classical (platform-scaling weakness); learned gate
self-tunes to +50–57%. **Platform-agnostic vs hand-tuned.**

## 4. Performance–robustness frontier

The knob is the learning **target**, not the step size. Pure proportional target
`−k_err·error` peaks on smooth tracking but learns extra gain → overshoots/flips
on step commands (hardstep diverges 2.18; weight-leak alone does NOT fix). Fix =
PD-style target `−k_err·error − k_rate·omega` (damping). `k_rate`: 0 = performance
champion, 0.3 = robust generalist, 1.0 = maximally damped.

## 5. HyperLIF ≡ Adaptive HyperLIF in gate mode (boundary result)

| online_pes condition | HyperLIF | Adaptive HyperLIF |
|---|---|---|
| hard45 aggressive (CF2) | 0.038258 | 0.038258 |
| hard45 balanced (CF2) | 0.120469 | 0.120469 |
| hardstep balanced (CF2) | 0.157573 | 0.157574 |
| hard45 aggressive (Skydio) | 0.129264 | 0.129264 |
| hard45 balanced (Skydio) | 0.150457 | 0.150457 |
| fixed gate (control) | 0.266117 | 0.266117 |

**Numerically identical, learned decode and all.** Mechanism: in gate mode
`r ≈ 3.7e-6`, so the adaptive gain (which lives only in `g = dynamic_gain·r²`)
multiplies `r² ≈ 1.4e-11` → `g ≈ 2e-9`, ~10 orders below `1/τ = 20`. The adaptive
gain scales a ~0 number. ⇒ report ONE neuron (HyperLIF); to make adaptation matter
read the voltage/event pathway or drive `r`→O(1).

## 6. Imitation / behavioral cloning (negative result)

Offline ridge-fit of `W` to the STN-PES residual **diverges** everywhere
(J~2.6). The teacher visits only small-error states → tiny fitted decode → cannot
handle the student's large-error startup transient. Classic covariate shift.
On-policy / DAgger-style collection is the fix if a data route is ever wanted.

## 7. Parameters (control scale, gate mode)

| group | parameter | value |
|---|---|---|
| HyperLIF | τ, τ_r | 0.05 s, 0.005 s |
| | reset_gain g0, γ | 120, 2 |
| | α, v_thresh, event_thresh | 50, 1.0, 0.5 |
| | activity mode, gate_gain G | gate, 1e5 |
| Adaptive | base_gain g_b, gain_scaling κ | 120, 30 |
| Encoding | current_bias b, current_gain η | 0.75, 1.25 |
| | channels | 6 (pair-coded pos/neg) |
| Decode | W init | [I₃ | −I₃] (3×6) |
| Learning | target gains k_err, k_rate | 8, {0, 0.3, 1.0} |
| | rate λ (lr) | 8e-4 (e-prop 2×) |
| | elig decay d (anneal) | 0.98 → 0.50 |
| | leak ℓ, clip | {0, 1e-3, 2e-3}, ±6 |
| | blend β | 0.5 |
| Sim | dt, duration | 5e-4 s, 45 s |
| | z_ref | 1.0 (hardstep 1.5) |
| Metric | J | qerr_mean + 0.02·τ̄ + 0.20·f_sat + 0.05·σ_z |

## 8. Runner commands

From `experiments/controller_benchmarks/` (venv python):
```powershell
# Full 5-idea suite (default Bitcraze / hard45, aggressive learning)
python learned_gate_experiment.py --methods all

# Single methods / knobs
python learned_gate_experiment.py --methods online_pes,eprop_anneal
python learned_gate_experiment.py --methods online_pes --k-rate 0.3 --leak 1e-3   # balanced
python learned_gate_experiment.py --methods online_pes --k-rate 1.0 --leak 2e-3   # strong-damp

# Adaptive HyperLIF (equivalence check)
python learned_gate_experiment.py --neuron adaptive_hyperlif --methods classical,fixed_gate,online_pes,eprop_anneal

# Generalization
python learned_gate_experiment.py --mission hardstep --z-ref 1.5 --methods online_pes,eprop_anneal --k-rate 0.3 --leak 1e-3
python learned_gate_experiment.py --quad skydio_x2 --mission hard45 --methods classical,fixed_gate,online_pes,eprop_anneal
```
Ground-truth baselines (original scripts):
```powershell
python mujoco_classical_vs_neural.py --controller direct_hyperlif --quad bitcraze_crazyflie_2 `
  --mission hard45 --sim-time 45 --dt 0.0005 --z-ref 1.0 --direct-scale control `
  --direct-activity-mode gate --direct-gate-gain 100000 --direct-blend 0.5      # -> 0.26612
python mujoco_classical_vs_neural_stn.py --controller stn_pid_pes --quad bitcraze_crazyflie_2 `
  --mission hard45 --sim-time 45 --dt 0.0005 --z-ref 1.0 --direct-blend 1.0     # -> 0.04786
```
CLI knobs: `--lr --k-err --k-rate --leak --neuron {hyperlif,adaptive_hyperlif} --methods --quad --mission --z-ref`.

## 9. Pending (hardware)
Aero2 HIL + static-quadrotor validation of the learned-gate decode + PES rule,
using the same parameters. Insert as Table V / Section VI of `paper/main.tex`.
