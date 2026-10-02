# 10 — Adaptive HyperLIF: implementation survey + Aero2 integration map

> **Deep-research deliverable (2026-06-09).** What Adaptive HyperLIF is, which
> implementations exist across **modelling**, **control**, and **identification/
> learning**, how mature/portable each is, and exactly how each maps onto the
> Aero2 pipeline. Nothing here is yet run on the Aero2 — this is the survey that
> precedes the Phase-10 scaffold. No HyperLIF-on-Aero2 results exist yet.

## 0. What Adaptive HyperLIF is
Paper: **"Robust Biophysical Spiking Neural Networks: The Adaptive HyperLIF Model"**
(TNNLS submission, April 2026; `01_Adaptive_HyperLIF/AdaptiveHyperLIF/MATH_AND_CODE.md`).

Core idea: lift the non-differentiable LIF reset jump into the hyperreals
(Robinson NSA *transfer principle*) → a continuous, **differentiable** two-time-scale
ODE. State `(v, r)`: slow membrane voltage `v`, fast continuous **gate** `r`.

```
θ_eff   = v_thresh − γ·r                         (hysteresis threshold)
r*(v)   = σ(α (v − θ_eff)),   σ = logistic
r_{t+1} = r* + (r − r*)·e^(−dt/τ_r)              (exact gate relaxation)
G(r,I)  = (G_base + β|I|)·r²                      (adaptive conductance; r² → ∂G/∂r=0 at r=0)
λ = 1/τ + G ;  drive = v_rest/τ + I/τ + G·v_reset
v_{t+1} = v·e^(−λdt) + (drive/λ)(1 − e^(−λdt))   (exact linearized voltage)
```
Three properties that matter for us:
1. **Differentiable** → gradient-based and *local* learning are possible (no surrogate).
2. **Gate `r ∈ [0,1]`** is a smooth, bounded "readiness-to-fire" signal → a natural
   **residual control feature** (no spike-event detection needed).
3. **Adaptive `β|I|`** feedforward conductance prevents depolarization block for *all*
   drive strengths (stability rule Eq. 14: `β > T/(τ_eff·(v_thresh−v_reset))`; default `β=100`).

Stiffness ratio `τ_r/τ = 0.02` (fast–slow). Paper defaults: `τ=10, τ_r=0.2, α=50,
γ=3, G_base=800, β=100`. **Control-scale** preset (fast loops): `τ=0.05, τ_r=0.005,
G_base/base_gain=120, gain_scaling=30, γ=2, event_threshold=0.5`.

## 1. Repos surveyed
| Repo | Process | Language | Maturity | Key artifacts |
|---|---|---|---|---|
| `…\Neural_Networks_and_Learning\04_Adaptive_HyperLIF_Nengo` | **modelling** (neuron core) | Python + Nengo | clean, validated | `src/neurons/{lif,hyperlif,adaptive_hyperlif,nengo_hyperlif}.py`, `MATH_NOTES.md` |
| `…\Neuromorphic_Embodied_AI\01_HyperLIF_Gate_Residual` | **control** | Python (+MuJoCo, Nengo) | working, has results | `v2_clean/src/controllers/{neuron_dynamics,neural_controllers,classical,factory}.py` |
| `…\Neural_Networks_and_Learning\01_Adaptive_HyperLIF` | **identification/learning** | mostly Julia (+CUDA) | research-grade | `AdaptiveHyperLIF/` (paper), `04_…_Gate_Eligibility/`, `03_…_Apex_Engine/` (APEX V11) |

## 2. MODELLING — neuron-core implementations (mature; portable now)
Three consistent implementations of the same equations:
- **Python/Nengo** (`04_…_Nengo`): `LIF`, `HyperLIF`, `AdaptiveHyperLIF` + Nengo
  `NeuronType` ports (probeable `voltage/reset_gate/previous_voltage/dynamic_gain`).
  Two stepping modes: `"julia"` (Euler) and `"stable"` (exact linearized). Python↔Nengo parity-checked.
- **Julia canonical** (`AdaptiveHyperLIF/src/{HyperLIF.jl,HyperLIFadapt.jl}`): the paper
  reference, with NSA derivation, depolarization-block + flux-balance proofs.
- **Python control-ready** (`Gate_Residual/.../neuron_dynamics.py`): `StandardLIFDirect`,
  `HyperLIFDirect`, `AdaptiveHyperLIFDirect`, `IzhikevichDirect`, all `BaseDirectNeuron`
  returning `NeuronStepResult(activity, events, voltage, gate)`; `make_direct_neuron(name,
  n, activity_mode∈{voltage,gate,events}, scale∈{paper,control})`. **Pure numpy.**

→ **For Aero2:** port `neuron_dynamics.py` verbatim as `aero2/control/neuromorphic/neuron.py`
(zero new dependencies). It's the foundation for both control and identification below.

## 3. CONTROL — the most actionable; a working PD+residual already exists
`01_HyperLIF_Gate_Residual/v2_clean` is a **complete gate-state residual augmentation
on a classical PD** — exactly the brief's "PD + neuromorphic residual."

Architecture (`neural_controllers.DirectNeuronTorqueController`):
```
1. classical PD  -> τ_pd            (safe baseline; clip ±τ_limit)
2. encode        τ_norm = τ_pd/τ_limit ∈ [−1,1]
                 I_pos = bias + gain·max(τ_norm,0);  I_neg = bias + gain·max(−τ_norm,0)
3. neurons       advance HyperLIF/Adaptive gate r (n = 2·dim, pos+neg channels)
4. decode        signed = clip(r_pos − r_neg, −1, 1);   τ_neural = signed·τ_limit
5. blend         τ = (1−β)·τ_pd + β·τ_neural,  clip ±τ_limit
```
Variants: `classical`, `direct_lif`, `direct_hyperlif`, `direct_adaptive_hyperlif`,
`rotor_residual_*` (residual at motor-command level), `nengo_*` (Nengo ensemble decode).
**Published best** (Crazyflie-2, hard45, 45 s): `direct_adaptive_hyperlif`, `activity_mode=gate`,
`scale=control`, `gate_gain=1e5`, `blend=0.50` → **qerr_mean +7.35%, qerr_max +10.06%,
z_std +15.19%** vs classical PD. (MuJoCo Skydio-X2 / CF2; quaternion 3-axis attitude.)

→ **For Aero2 (`HyperLIFResidualController`):** wrap our `PD2DOF`. The 2-axis virtual
command `u_pd = [u_p, u_y]` replaces the 3-axis torque:
```
u_pd  = PD2DOF.compute(x_est, ref, dt)                 # existing baseline
u_norm = u_pd / V_MAX ∈ [−1,1]                          # 2 signals
4 pair-coded currents (u_p±, u_y±) -> HyperLIF(n=4, gate mode) -> signed residual r_pos−r_neg
u_neural = signed · V_MAX
u = clip((1−β)·u_pd + β·u_neural, ±V_MAX)
```
This satisfies the `Controller` interface, so it drops into `run_control`/`run_benchmark`
unchanged and is scored on the same tracking + Table-IV metrics against PD/LQR/…/NMPC.
Knobs to sweep: `blend β`, `gate_gain`, neuron `scale`, `activity_mode`, adaptive vs base.
Also available to port: a Nengo ensemble torque decoder and an **STN-PID-PES** Nengo
adaptive controller (`code/stn_pid_pes_optional/`).

## 4. IDENTIFICATION / LEARNING — research-grade, mostly Julia
The learning machinery (for an SNN surrogate / one-step predictor of the plant) lives in
`01_Adaptive_HyperLIF`:
- **Gate-eligibility local learning** (`04_…_Gate_Eligibility`, `METHODS.md`): the gate's
  *exact* Jacobian `∂r_{t+1}/∂v = (1−κ)·α·r*(1−r*)` is a **parameter-free e-prop
  post-synaptic factor** (`:gate_exact`), superior to heuristic surrogate gradients;
  plus `:gate_temp` (temperature-annealed bridge). Credit routings Exact/SS/RFA/DFA.
  Validated vs exact BPTT (Zygote). Results in `results/exp1_fidelity.md`, `exp2_convergence.md`.
- **Hebbian online plasticity** (`AdaptiveHyperLIF/src/HebbianLearning.jl`): bipolar LTP/LTD
  with multiplicative bounds.
- **APEX V11 engine** (`03_…_Apex_Engine`, Julia/CUDA): full deep-SNN stack — `CSNNLayer`,
  `EPropHyperLIFLayer`, `V11ReadoutLayer`, learnable **fractional-memory bank** (power-law
  long context), FOH matrix-exponential integration, e-prop with DFA default.

→ **For Aero2 (`NeuromorphicIdentifier`):** train an Adaptive-HyperLIF network as a
**one-step predictor** of `θ/ψ` (or `ω_z,c`) from the *same* M3 PRBS data, evaluated on the
*identical* one-step/free-run splits as ARX/DARX (`docs/09_benchmarking.md` Table II).
Same `fit/validate` API as `identification/arx.py`. **Caveat:** the learning code is Julia;
a Python port (e-prop with the gate-exact factor on the numpy neuron) or a Julia/APEX bridge
is required — this is the larger lift of the three processes.

## 5. Practical readiness matrix
| Process | Best existing impl | Language | Portable to Aero2-Python now? | Effort |
|---|---|---|---|---|
| Modelling (neuron) | `neuron_dynamics.py` | Python/numpy | **Yes, verbatim** | low |
| Control (PD+residual) | `v2_clean` gate-residual | Python | **Yes** (rewrite encode/decode for 2-axis) | low–med |
| Identification (SNN ID) | gate-eligibility / APEX | Julia (+CUDA) | No — needs Python port or Julia bridge | med–high |

## 6. Phase-10 build — DONE (2026-06-09) + honest first results
Built into the baseline, registered so existing runners pick it up; classical pipeline
unaffected; **72 tests pass**. Constants in `config/hyperlif.py` (experimental).
- **Modelling** — `aero2/control/neuromorphic/neuron.py`: pure-numpy `StandardLIFDirect/
  HyperLIFDirect/AdaptiveHyperLIFDirect` + `make_direct_neuron` (gate/voltage/events, paper/control scale).
- **Control** — `aero2/control/neuromorphic/hyperlif_residual.py`:
  `HyperLIFResidualController(base=PD2DOF)`, registered as `hyperlif` (drops into
  `run_control`/`run_benchmark`). `blend=0` ≡ PD exactly.
- **Identification** — `aero2/identification/neuromorphic_identifier.py`:
  `NeuromorphicIdentifier` (HyperLIF reservoir + ridge readout), same `fit/validate`
  surface as `arx`, scored on identical splits.

**Honest first results (no fabrication):**
| Process | offline / pitch-PRBS | reading |
|---|---|---|
| Control | PD pitchRMS 0.182; HyperLIF blend=0.5 → 0.199 | fixed-weight residual slightly *degrades* on the ideal plant (PD already near-optimal; the +7.35% source result was on a noisy MuJoCo quadrotor, harder regime) |
| Identification | ARX 98.23%; HyperLIF-hybrid 96.95%; HyperLIF-reservoir −11.6% | the linear lags carry the hybrid; gate features add ~nothing yet |

**Conclusion (empirically confirms §4–5 on Aero2 data):** the HyperLIF gate features do
not yet add value without *real learning*.

**Now built — Python e-prop (`control/neuromorphic/eprop.py`).** A pure-numpy replica of
the Julia gate-eligibility learning: `EpropSNN` (Adaptive-HyperLIF hidden stack + linear
readout), ψ ∈ {`gate_exact`, `gate_temp`, `surrogate`}, credit ∈ {`exact`, `ss`, `dfa`},
per-synapse **membrane eligibility**. **Validated vs finite differences:** gate_exact ψ =
exact gate Jacobian `∂r/∂v` (rel err 2e-10), readout gradient exact (cos 1.0), hidden
e-prop gradient ≈ BPTT (cos 0.97), and it trains (loss ↓ below mean-predictor). So the
gates can now be **trained, not fixed** — the prerequisite for showing HyperLIF's advantage
on the digital twin / hardware in harder regimes (sensor noise, the **yaw axis**). Heavy
offline training can still use Julia/APEX (CUDA) and export weights. Julia↔Quanser
deployment options: **`docs/11`**.

## 7. Honest gaps / cautions
- The **control** residual uses *fixed-weight* neurons (the "adaptive" is input-dependent
  conductance `β|I|`, **not** synaptic plasticity). Online weight learning is Julia-side.
- The **identification** path is the least Python-ready; budget a port or a Julia bridge.
- Source models are **3-axis quaternion attitude** (quadrotor); Aero2 is **2-axis (θ,ψ)** with
  strong pitch→yaw coupling and the yaw-breakaway problem — the residual could specifically
  target the **unresolved yaw axis** (a concrete research hypothesis).
- No fabricated results: HyperLIF-on-Aero2 numbers do not exist until run.

## 8. References
- Adaptive HyperLIF paper: TNNLS submission (Apr 2026) — `01_Adaptive_HyperLIF/AdaptiveHyperLIF/MATH_AND_CODE.md`, `docs/equations.md`.
- Gate-residual control + result: `01_HyperLIF_Gate_Residual/v2_clean/{README.md,docs/math_formulation.md}`.
- Gate-eligibility learning: `01_Adaptive_HyperLIF/04_…_Gate_Eligibility/docs/METHODS.md`.
- Nengo neuron baseline + paper bridge: `04_Adaptive_HyperLIF_Nengo/{README.md,MATH_NOTES.md,PAPER_BRIDGE.md}`.
- e-prop (Bellec et al. 2020); surrogate gradients (Neftci et al. 2019); feedback alignment (Lillicrap 2016, Nøkland 2016).
