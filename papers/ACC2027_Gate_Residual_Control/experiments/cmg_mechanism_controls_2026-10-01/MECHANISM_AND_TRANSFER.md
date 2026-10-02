# How the CMG (HyperLIF) residual learns — and what transfers

Reference note written 2026-10-01 from the preregistered study in this folder
(`PREREGISTRATION.md`, `analysis/RESULTS.md`, report artifact
https://claude.ai/artifact/3ZzbKfmNLLjn7MQKA2dcgC). Every statement carries an evidence label:

- **[software]** shown in this study's MuJoCo runs (X2 + CF2-rotor, five 45 s missions, seed 1, noise-free) or
  derived exactly from the equations and checked against those runs.
- **[derived]** follows analytically from the model equations; not separately simulated.
- **[proposed]** a hypothesis for another project; untested.

---

## 1. What learns, and what does not

The CMG–PES residual has two parts with different roles.

| Part | Learns? | What it does |
|---|---|---|
| Six CMG units (membrane v, gate r, readout a = clip(G r, 0, 1)) | No | Fixed temporal feature generator driven by the paired baseline command I± = 0.75 + 1.25·max(±u₀/ℓ, 0) |
| Decoder W (3×6), initialized [I, −I] | Yes, by PES | s = clip(W a, −1, 1); residual = β ℓ s; W ← W + η (y* − s) aᵀ − leak·W, projected to ±6 |

So "how CMG learns" means **how good a basis the CMG units hand to a normalized-LMS learner**. Performance is
the product of two things: how informative the features are, and how well-conditioned the PES update is.
[software]

Implementation detail [software]: the Nengo CMG path applies PES one step late
(W_k uses y*_{k−1}, s_{k−1}, a_{k−1}). The archived NumPy constant/paired arms update in the same step. The ordering
changes nothing measurable (constant-one 10.34 / 4.29 either way), but exact replication needs it: a NumPy
restatement with Nengo ordering matches the archived Nengo run to 3·10⁻¹³ over 90,000 closed-loop steps.

## 2. The three operating regimes of a CMG unit

With v frozen, the gate equilibria r = σ(α(v − v_th + γ r)) form an S-curve when αγ > 4. Its folds are at
r± = ½(1 ± √(1 − 4/(αγ))), v_fold = v_th − γ r± + (1/α) ln(r±/(1 − r±)). [derived]

For Table I (α = 50, γ = 2, so αγ = 100): onset fold v_on ≈ 0.888, release fold v_off ≈ −0.89. [derived]

| Regime | Condition | Readout a | Learning consequence |
|---|---|---|---|
| **Sub-fold graded** | v below v_on, r ≪ 1 | a ≈ min(1, G e^{α(v − v_th)}) — an exponential tuning curve of the low-passed command | Informative. This is where the gain comes from. [software] |
| **Latched** | v crossed v_on once | r → 1, a = 1 forever, because v ≥ v_reset = 0 > v_off | Feature collapses to a constant. PES can only learn a bias (leaky lagged-P tracker of y*). [software: 0 releases in 10 runs] |
| Relaxation oscillation (spiking) | needs v to fall below v_off | periodic | Never reached in this application. [derived] |

Resting readout: a_rest = G e^{−α(v_th − I_b)} = 10⁵ e^{−12.5} = 0.3728. [derived; simulated 0.372803]

Small-command behaviour of a pair, before any latch [derived]:

    a± ≈ a_rest · exp(α I_g · LPF_τ(n±)),   n± = max(±u₀/ℓ, 0),   α I_g = 62.5
    saturates (a = 1) once LPF(n) > ln(1/a_rest)/62.5 ≈ 0.016

The initial decoder reads s₀ = a₊ − a₋ ≈ 2 a_rest sinh(62.5·LPF(n)): a lag-filtered, high-gain,
saturating function of the baseline command. PES then reshapes it. (The initial and learned parts each exceed the
total output and largely cancel; an η = 0 control is needed to apportion the gain — not yet run.)

## 3. What the controls established [software]

X2 / CF2 geometric-mean tracking-error reduction vs classical PD+ff:

| Basis | X2 | CF2 | Reading |
|---|---|---|---|
| CMG (paper) | 37.30 | 22.42 | reference |
| LPF + static logistic (CMG minus gate state, γ feedback and conductance) | **46.34** | **28.61** | the sub-fold mapping alone does better than CMG |
| CMG χ = 0 | 37.30 | 22.42 | conductance adaptation is irrelevant here |
| CMG G = 10³ / G = 1 | 9.01 / 4.44 | 3.58 / 1.68 | shrinking G removes the graded tail |
| Latch replay (rest → 1 at recorded latch times) | 9.65 | 3.81 | two levels alone carry nothing |
| Constant-rest (0.3728) / constant-one | 6.85 / 10.34 | 2.63 / 4.29 | persistence alone carries nothing |

Mission pattern: LPF + logistic equals CMG on Roll, Yaw360 (CMG never latches) and Hardstep (CMG latches at once),
and beats it on Full3 and Hard45 (X2 +35.2 vs +12.4 and +45.5 vs +13.8). On latched missions CMG performs at the
constant-one level.

## 4. Principles to carry forward

1. **Separate the basis from the learner.** Report the basis's regime (graded / latched / oscillating) alongside the
   learner's result. A good learner on a collapsed basis learns only a bias. [software]
2. **Irreversible latching is feature death.** It is the CMG analogue of a saturated sigmoid or a dead ReLU.
   Monitor the latched fraction during training and deployment. [software]
3. **Report η‖a‖² as well as η.** The PES corner frequency is η‖a‖²/h: about 1.4 rad/s on unlatched missions and
   9.6 rad/s once all six units latch. G changes feature amplitude and effective learning rate together, so
   compare bases at matched η‖a‖² or with a normalized (NLMS) update. [derived; values software]
4. **Graded content beats persistence.** Constant and two-level bases fail even at matched ‖a‖². What the learner
   uses is variation that tracks the error signal. [software]
5. **The useful tail is sensitive to bias.** a_rest = G e^{−α(v_th − I_b)}: a shift δ in I_b multiplies a_rest by
   e^{αδ}. With α = 50, δ = 0.0075 (1% of I_b) gives a 1.45× change. Sensor or current offsets on hardware
   matter. [derived]
6. **Validate harnesses by exact equivalence before interpreting.** Bit-level or 1e-13 agreement with the
   archived run, then preregistered arms, then open-loop replay controls. [method]

## 5. Design levers for a CMG that keeps its features [derived / proposed]

- Make the gate monostable (αγ < 4), or put v_reset below the release fold so a latched unit can release.
  Then the relaxation-oscillation regime becomes reachable as well.
- Keep the graded tail and drop the hysteresis: LPF + logistic is the tested lower bound on what is needed.
- Normalize PES by ‖a‖² (NLMS) so changing G or the regime does not silently change the learning rate.
- If persistence is wanted, make it deliberate: a latch can serve as an event flag ("a disturbance happened")
  routed to a separate decoder, rather than overwriting the tracking features.

## 6. Extrapolation to other projects [proposed unless marked]

| Project | Transfer | Concrete next test |
|---|---|---|
| **ACC 2027 paper** | State plainly that CMG works as a smooth temporal-feature unit in the tested regime; latching limits it; χ has no effect. Rename the readout gain (G clashes with the HyperLIF conductance). | η = 0 frozen-decoder control (20 runs) to split fixed feedforward from PES learning. |
| **Neuromorphic RL attitude pilot** (TD actor-critic on CMG features; 45 s replay slightly negative) | The same latch likely turns actor/critic features into constants on large-error missions. | Rerun the frozen protocol with LPF + logistic features and report the latched fraction per run. |
| **Drone racing** | Racing errors are larger than Hard45, so units latch within seconds; a latching basis is a poor fit. | Use a non-latching basis, or reset the gate per gate/lap, and log the latched fraction. |
| **DVS / event perception** | LPF + logistic maps naturally onto an event-rate encoder; the exponential tail acts as contrast sensitivity near threshold. | Encode event rates with LPF + logistic; compare against latching CMG at matched η‖a‖². |
| **P1 HyperLIF Learning (gradients, TNNLS)** | Near the folds the gate's sensitivity scales like α/τ_r (stiff, ill-conditioned gradients); latched units have zero input gradient (dead units). | Track the latched fraction and gradient norms during training; test τ_r → 0 against exact event-based (EventProp) gradients. |
| **P5 dual self-tuning + residual** | The residual basis and the self-tuning path need separate authority bounds; a latched residual basis degrades to a lagged-P term that overlaps the tuner. | Ablate basis regime (graded vs latched) inside the dual architecture. |
| **Hardware (3DOF Hover, Aero2, QArm)** | Point 5: bias offsets move a_rest exponentially. | Measure the current-encoder bias on hardware; recompute a_rest and the tail range before arming. |
| **Multi-agent systems** | A shared fixed basis with per-agent decoders is cheap; latching would make agents' features diverge by history, not by state. | Compare shared non-latching basis vs per-agent latching CMG on a formation task. |
| **General ML** | Same lesson as saturating activations: keep units in their graded range, normalize the learning rate by feature energy, and audit dead units. | — |

## 7. Files

| File | Purpose |
|---|---|
| `PREREGISTRATION.md` | Hypotheses, arms, decision rules (written before new arms ran) |
| `phase0_latch_diagnostics.py`, `analysis/phase0/` | Latch times, saturation, log-r histograms from archived runs |
| `cmg_control_adapters.py` | NumPy bases with Nengo PES ordering (CMG restatement, LPF + logistic, constant-rest, latch replay) |
| `run_cmg_controls.py`, `run_campaign.py` | Single-case wrapper on the frozen final runner; preregistered matrices |
| `check_gates.py`, `results/gates/GATES.json` | Harness equivalence gates G1–G3 |
| `analyze.py`, `analysis/RESULTS.md` | Aggregates, verdicts, development check |
| `make_report_figures.py`, `make_report_html.py`, `analysis/report/` | All figures, summary tables, report page |
