# HyperLIF across Nengo capabilities — findings (2026-07-04)

Easiest-but-complete example of each Nengo capability block, run with **LIF vs calibrated HyperLIF
(T023: θ_event=0.95, origin v_reset=−0.6, rate_to_current=140) vs Adaptive (T033)**, on NengoCore.
Data: `results/csv/13_hyperlif_nengo_capability_matrix.csv`. Experiment:
`experiments/13_hyperlif_nengo_capability_matrix.py`. Error is task-specific (lower is better);
`rate` is mean population firing rate (Hz).

## The matrix

| capability | app | metric | LIF | HyperLIF T023 | Adaptive T033 | LIF rate | HyperLIF rate |
|---|---|---|---:|---:|---:|---:|---:|
| NEF repr | comm channel | decode rmse | 0.193 | 0.211 | 0.205 | 124 | **33** |
| NEF repr | function x² | function rmse | 0.194 | 0.222 | 0.200 | 122 | **35** |
| NEF repr | 2D transform | transform rmse | 0.197 | 0.211 | 0.209 | 118 | **33** |
| NEF dyn | integrator | hold err (→0.3) | 0.001 | 0.003 | 0.010 | 84 | 38 |
| NEF dyn | oscillator | amp err | 0.147 | **0.100** | 0.164 | 117 | 40 |
| memory | gated memory | hold err (→0.6) | 0.033 | **0.019** | 0.035 | 113 | 45 |
| online learn | PES channel | late rmse | **0.051** | 0.445 | 0.102 | 117 | 34 |
| cognition | binding (cconv) | 1−cos | 0.014 | 0.054 | 0.011 | — | — |
| cognition | action selection | argmax err | 0.000 | 0.000 | 0.000 | — | — |

**Every capability builds and runs with HyperLIF — 9/9 apps, 0 failures.**

## HyperLIF advances (in Nengo)
1. **Universal NengoCore citizen.** Representation, dynamics, memory, online learning, and *cognition*
   (circular-convolution binding + basal-ganglia/thalamus action selection) all run with HyperLIF as a
   drop-in `NeuronType`. Action selection is **perfect** (0.000, correct argmax with margin).
2. **Efficiency.** Comparable representation at **~3.5× fewer spikes** (≈33 Hz vs ≈120 Hz) — same
   NEF story as Paper 2's event-efficiency, now in the NEF.
3. **Dynamics + memory once calibrated.** With T023, HyperLIF **integrates and holds** (0.003),
   **oscillates better than LIF** (0.100 vs 0.147), and **holds working memory better than LIF**
   (0.019 vs 0.033). This overturns the earlier "HyperLIF holds weakly (0.034)" smoke — that was an
   **un-calibrated** result. Direct evidence for the *calibration, not dynamics* thesis.

## HyperLIF weaknesses (in Nengo) — honest
1. **Online learning (PES) is slower — the real weakness.** HyperLIF 0.445 vs LIF 0.051 (Adaptive
   0.102, in between). Cause: **sparse firing → fewer learning events per unit time → slower PES
   convergence** in a matched-time window. The very sparsity that buys efficiency costs online-learning
   speed; the higher-rate Adaptive variant recovers most of it. *(Correction: an earlier per-app sweep
   showed a near-tie/slight PES win; that was setup-dependent. In a clean matched-time channel-learning
   task, HyperLIF is clearly slower to converge — firing rate is the hidden variable, echoing the
   gate-eligibility "coverage/events matter" result in `01`.)*
   **Rate-matched sweep** (`experiments/15_pes_rate_matched.py`): PES error tracks firing rate, with a
   sweet spot at `rate_to_current≈250` (~40 Hz) where late error falls **0.85→0.12 (7×)** — the weakness
   is largely an operating point. But there is an **honest ceiling**: HyperLIF's firing peaks ~40 Hz, so
   even optimally tuned it stays above LIF (0.12 vs 0.05 at 116 Hz). The *same sparsity* that gives 3.5×
   representation efficiency caps online-learning speed — one trade, both directions. The best operating
   point is **task-dependent** (T023's r2c=140 is good for representation, not optimal for learning).
2. **Representation ~10% noisier** (0.21 vs 0.19 rmse) — the efficiency/accuracy trade at low rate.
3. **Calibration-sensitive.** Everything hinges on `rate_to_current`; un-calibrated HyperLIF is weak
   (this is a usability limitation, not a dynamics flaw).

## Limitations of Nengo (for a custom continuous-gate neuron) — EMPIRICAL
Backend portability probe (`experiments/14_backend_portability_probe.py`): the *same* minimal ensemble,
LIF vs HyperLIF, on each backend.

| backend | LIF | HyperLIF |
|---|---|---|
| NengoCore | RUNS | **RUNS** |
| NengoOCL (real GPU; 2 OpenCL devices present) | RUNS | **REJECTED — `ValueError: Unsupported neuron type 'HyperLIFNengo'`** |
| NengoLoihi (pure-Python emulator) | (numpy-2 lib bug) | **REJECTED — `BuildError: neuron type 'HyperLIFNengo' cannot be simulated on Loihi`** |
| NengoDL (TensorFlow) | (untestable) | **BLOCKED — won't import on a modern stack** |

**The hard wall, proven.** This machine has working OpenCL (LIF runs on the GPU), so HyperLIF's NengoOCL
rejection is *not* "no GPU" — it is specifically *"no kernel exists for this custom neuron."* Loihi
rejects it at build validation because a continuous 2-state gate is not in the fixed hardware neuron set.
So a custom continuous-gate `NeuronType` is **locked to the reference Python/NumPy simulator** unless
someone writes a per-backend kernel (OCL), a TF builder (DL), or a hardware mapping (Loihi/FPGA — not
possible for continuous dynamics). *(The LIF-on-Loihi failure here is a separate nengo_loihi 1.1.0 ×
numpy-2 incompatibility, not a neuron issue; HyperLIF fails earlier, at the neuron-type check.)*

**NengoDL adds a second, different wall — ecosystem version-lag.** nengo-dl 3.5.0 (the release compatible
with nengo 4.1) will not even import on a current stack: it requires `keras.engine` (removed in Keras 3,
which ships with TF ≥ 2.16) and `protobuf<4.21` (vs the installed 7.x). The `tf-keras` legacy shim did
not resolve it (nengo-dl imports standalone `keras`, not `tf.keras`). Running the DL backend at all would
require a pinned legacy venv (TF ~2.14 / Keras 2 / protobuf 3.20); *training* HyperLIF would then still
need a hand-written TF `NeuronBuilder`. So the DL/training backend is doubly blocked here — version-lag
first, custom-neuron support second — and unlike Loihi/OCL, the block is not fundamental to HyperLIF but
to the maintenance state of NengoDL.

Secondary: NengoCore is CPU/NumPy; the extra 2-state step makes HyperLIF ensembles slower than LIF.

## The reconciliation (why this matters for Paper 3)
The clean matrix **confirms the "operating-point calibration" thesis empirically**: the previously
reported NEF weaknesses (integrator, memory) were calibration artifacts, not the neuron — T023 fixes
them and even beats LIF on oscillator/memory. The one durable weakness (online-learning speed) is a
**firing-rate** effect, which is itself a *tunable operating point* (θ_event / rate raise it; Adaptive
recovers PES). So across the whole NEF, HyperLIF's story is: **calibrated efficiency with a
rate-vs-learning-speed trade — usable everywhere in Core, blocked only by hardware-backend genericity.**

## Next
- ~~Empirically demonstrate the backend rejection~~ **DONE** (§ Limitations, exp 14): HyperLIF rejected
  by NengoOCL and NengoLoihi with explicit errors; runs only in Core.
- ~~Rate-matched PES curve~~ **DONE** (exp 15): 7× improvement to a ~40 Hz sweet spot, honest ceiling
  vs LIF, task-dependent operating point.
- NengoDL: prototype a TF `NeuronBuilder` to test whether HyperLIF can be *trained* in the DL backend
  (the direct bridge to Paper 2's learning story) — the one backend where a custom neuron is *possible*
  without hardware, and the highest-value remaining probe.
- Fold this matrix into the manuscript as the "operating-point calibration + capability coverage"
  results section (answers "useful across Nengo apps" with the calibration reframe + the honest
  rate↔learning trade + the portability limitation).
