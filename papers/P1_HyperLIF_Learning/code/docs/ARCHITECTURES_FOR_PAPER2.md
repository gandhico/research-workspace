# Paper 2 — Architectures in the HPC benchmark cube (exact spec)

Source of truth: `08_HyperLIF_Architectures/src/arch/*.py` (built via `arch/registry.py`),
neuron from `07_AdHyperLIF_Triage/.../snntorch_hyperlif.py`. Grid: `07_.../hpc/grid.py`.
Every network returns `(logits, aux)`; `aux` carries `events_per_sample`, `gate_mean`.

---

## 0. The benchmark cube

**architectures × neurons × readouts × seeds × datasets**, one SLURM task per config.

| axis | values |
|---|---|
| topologies | **conv, rsnn, delay, convres** (roster60 cube) — `ff` is the project-07 base-sweep baseline |
| neurons (7) | lif, hyperlif, hyperlif_t0.95, adaptive, adaptive_t0.95, adaptive_origin, adaptive_dreset |
| readouts (6) | membrane, spike_count, gate, hybrid_gr, hybrid_vr, hybrid_vr_conductance |
| seeds | 0,1,2,3,4 |
| datasets | N-MNIST, DVS-Gesture-32, DVS-Gesture-48, CIFAR10-DVS (vision); SHD, SSC (audio) |
| total | ≈112 bundles × 30 (6 readouts × 5 seeds) = **3360 configs** |

**Shared training recipe (all archs):** Adam, lr 1e-3, 60 epochs, hidden H=256, batch 64
(**convres: batch 16**, OOM), T=20 timesteps, grad-clip 1.0, CrossEntropy, input from a
uniform `{Xtr,ytr,Xte,yte}.pt` cache `[B,T,F]`. `conv`/`convres` are vision-only (need a
2-D sensor); audio (SHD/SSC) uses `rsnn`/`delay` only.

**Sensor map** `F → (P,H,W)`: 2312→(2,34,34) N-MNIST · 2048→(2,32,32) DVSG32 ·
4608→(2,48,48) DVSG48 · 128→(2,8,8).

**Shared forward pattern:** project input → run the spiking hidden stack for T steps,
accumulating per-neuron means `v̄, r̄, ḡ` and `spk_sum` → assemble the readout feature →
`BatchNorm → Linear head → logits`. Conductance `G = reset_gain·r²` (HyperLIF) or
`(base_gain+gain_scaling·|I|)·r²` (Adaptive), squashed `tanh(G/20)`.

---

## 1. `ff` — feed-forward baseline (project-07 `SNNTorchNet`, parity-validated)

```
X[B,T,F] → Linear(F→256)  (init std=16/√F)
         → spiking neuron (1 state LIF / 2 state HyperLIF), T-step loop
         → readout feature → BatchNorm1d → Linear(→C)
```
Single hidden layer. This is the base-sweep reference (byte-identical to the 450-run
baseline); the roster60 cube focuses on the four topologies below.

## 2. `conv` — convolutional SNN (`ConvSNNNet`, vision)

```
per timestep t:
  Conv2d(P→16, 3×3, pad1) → neuron n1 → AvgPool2d(2)
  Conv2d(16→32, 3×3, pad1) → neuron n2 → AvgPool2d(2)
  flatten(32·(H/4)·(W/4)) → Linear(→128) → head neuron nh
accumulate v̄,r̄,ḡ,spk_sum over T → readout → BN → Linear(→C)
```
`c1=16, c2=32, n_hidden=128, input_scale=8`. Conv layers propagate the neuron's **natural
output** (spike for LIF, **gate r for HyperLIF**). Firing-init on conv/fc weights.

## 3. `rsnn` — recurrent SNN (`RSNNNet`, audio + general)

```
per timestep t:
  cur = Linear_in(F→256)·X[t] + Linear_rec(256→256, orthogonal gain 0.2)·spk[t-1]
      → spiking neuron (recurrent hidden)
accumulate v̄,r̄,ḡ,spk_sum → readout → BN → Linear(→C)
```
`H=256`. Standard RSNN (hidden spikes fed back through `W_rec`); the SHD/SSC workhorse.

## 4. `delay` — delay SNN / DCLS-style (`DelaySNNNet`, audio)

```
cur = Linear_in(F→256)(X)                         # [B,T,256]
cur = DepthwiseConv1d(256, kernel=7, groups=256)  # learnable per-channel temporal delays,
                                                   #   init = passthrough (centre tap = 1)
per timestep t: cur[t] → spiking neuron
accumulate v̄,r̄,ḡ,spk_sum → readout → BN → Linear(→C)
```
`H=256, kernel=7`. Minimal learnable-synaptic-delay prototype (the SHD/SSC SOTA route).

## 5. `convres` — deep spiking conv-residual, SEW-ResNet style (`ConvResSNN`, vision, ~14M)

The at-scale / SOTA-class net. `base_ch=128, stage_blocks=(2,2,2)` ⇒ ResNet-18-class **≈14M params**.

```
SNNConv = Conv2d(3×3) → BatchNorm2d → ×DRIVE_SCALE(5.0) → spiking neuron (state across T)
ResBlock = SNNConv → SNNConv, then SEW-ADD:  out = c2(c1(x)) + x

stem:  SNNConv(P → 128)
stage0 (128 ch):  2× ResBlock
stage1 (→256 ch): SNNConv stride-2 downsample, then 2× ResBlock
stage2 (→512 ch): SNNConv stride-2 downsample, then 2× ResBlock
head:  global-avg-pool(H,W) → Linear(512→256) → BatchNorm1d → ×DRIVE_SCALE(5.0)
       → head spiking neuron → readout → BN → Linear(→C)
```
**Key design decisions (report these):**
- **Inter-layer signal = surrogate SPIKE for every layer** (LIF and HyperLIF alike), as SEW-ResNet
  is designed for. Propagating HyperLIF's *graded gate r* trains in the shallow nets
  (ff/conv/rsnn/delay) but **stalls at chance across this ~9-layer stack** (steep α=100 gate kills
  gradient flow); the spike carries the same `fast_sigmoid` surrogate gradient as LIF and trains
  through depth. The continuous gate **r is retained as the HEAD readout feature** (gate/hybrid /
  gate-state decoding) — a decodable readout, **not** the deep transport signal.
- **`DRIVE_SCALE=5.0`** after BN restores firing-level drive (BN normalizes below `v_thresh=1`,
  which would starve the gate/spikes where all readouts are taken).
- **batch 16** for convres only (14M net OOMs a 16 GB GPU at batch 64 × T20 BPTT).

---

## 6. Neurons — the 7-variant roster (`NEURON_VARIANTS`)

| name | base | cfg override | intent |
|---|---|---|---|
| lif | snntorch.Leaky | β=0.95, fast_sigmoid slope 25 | 1-state honest baseline (no gate) |
| hyperlif | HyperLIF | — | 2-state (v, r) |
| hyperlif_t0.95 | HyperLIF | event_threshold=0.95 | denser firing (deep-starvation fix) |
| adaptive | Adaptive HyperLIF | — | conductance `(base+scale·|I|)·r²` |
| adaptive_t0.95 | Adaptive | event_threshold=0.95 | denser firing |
| adaptive_origin | Adaptive | v_reset=−0.6, min_voltage=−2.0 | static hyperpolarizing AHP (temporal asset) |
| adaptive_dreset | Adaptive | delta_reset=0.3, min_voltage=−2.0 | gate-coupled AHP |

`ff` uses only the base 3 (lif/hyperlif/adaptive); the θ_event/origin variants apply to
conv/rsnn/delay/convres.

## 7. Readouts — the 6 heads (`assemble`)

| readout | feature (dim × H) | reads |
|---|---|---|
| membrane | v̄ (1) | mean membrane |
| spike_count | Σ spk (1) | true spikes (also the events metric) |
| gate | r̄ (1) | mean gate — **0 for LIF (structurally blind)** |
| hybrid_gr | [r̄, ḡ] (2) | gate + conductance — 0 for LIF |
| hybrid_vr | [v̄, r̄] (2) | membrane + gate |
| hybrid_vr_conductance | [v̄, r̄, ḡ] (3) | full state |

For LIF the gate/conductance channels are identically zero — this is the honest baseline that
yields the **structural-blindness** contrast (LIF `gate`/`hybrid_gr` → chance 0.143; HyperLIF
`gate` → 0.84 on DVSG32).
