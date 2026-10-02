# HyperLIF Architectures — living roadmap (Paper 2)

*Purpose:* make the architectures behind **Paper 2 (HyperLIF Learning, PyTorch + Julia)** robust, so the
result is not "a shallow feedforward net." Three tiers form a narrative arc that answers three
reviewer objections in order. **This doc is updated after every phase.**

## The arc
| Tier | Answers the objection | Establishes |
|---|---|---|
| **T1 baselines** | "is the effect just tuning?" | controlled, isolated |
| **T2 SOTA archs + HyperLIF** | "does it matter at scale?" | the gain transfers into high-capacity nets |
| **T3 out-of-the-box** | "what's genuinely new?" | architectures only the gate/conductance enables |

## Architecture matrix
Every architecture is swept `{LIF, PLIF, ALIF/LSNN, HyperLIF, Adaptive (+θ-event, +origin)} × {6 readouts} × 5 seeds`.

| Tier | Vision (N-MNIST, DVS-Gesture, CIFAR10-DVS) | Audio (SHD, SSC) |
|---|---|---|
| **T1** | frame-CNN, ANN→SNN (atemporal) · **LIF/PLIF/ALIF-FF ✅** · LIF-RSNN · ALIF/LSNN | frame-MLP · **LIF/PLIF/ALIF-FF ✅** · LIF-RSNN · ALIF/LSNN |
| **T2** | **conv-SNN** (SEW/VGG-style) · delayed-conv · PLIF/GLIF-vs-HyperLIF | **RSNN** · learnable-delay SNN (DCLS) · PLIF/GLIF-vs-HyperLIF |
| **T3** | 2-compartment (dendritic gate) · **heterogeneous learnable gate** (γ, τ_r, reset_gain) · neuromodulatory gain · gated WTA · predictive gating | same |
| *stretch* | Spikformer | Spikformer |

## Local vs HPC
> **Local = "runs, stable, has signal?"** (tiny subset, ≤5 epochs). **HPC = the real sweep** (full data, all readouts, 5 seeds).
Nothing goes to HPC until it passes **parity** (new neurons) or a **tiny-mode smoke** (new architectures).

## Phases → paper
- **A — Scaffolding (local):** model registry `ff | conv | rsnn`, parity, smoke → *Methods §4–5*.
- **B — Transfer (HPC):** complete T1 + run T2 conv-SNN (vision) & RSNN (audio), full data → *Results §6.5*.
- **C — Innovate (local→HPC):** delays + T3 gate-enabled nets → *Results §6.6 + Discussion §7*.
- **D — Julia (parallel):** caches→HDF5, parity ≤1e-16, reproduce headline → *Results §6.4*.
- **E — Consolidate:** fold each tier in; update roadmap + paper together.

## Priorities (honest)
- **Must-do:** conv-SNN (vision) + RSNN (audio) with HyperLIF — the Tier-2 paper result.
- **Strong stretch:** learnable-delay SNN (SHD/SSC SOTA route) + PLIF/GLIF-vs-HyperLIF head-to-head.
- **Exploratory:** T3 — start with the heterogeneous learnable gate + dendritic 2-compartment.
- **Defer:** Spikformer (high effort/compute; the mechanism story doesn't need it).

## Status — Phase A (started 2026-07-03)
- ✅ **Model registry + conv-SNN + RSNN built** (`src/arch/`), reusing project-07's parity-validated neuron.
- ✅ **Baseline harness extended:** PLIF and ALIF/LSNN are now available in the same snnTorch/HPC
  path as LIF, HyperLIF, and Adaptive HyperLIF. This directly addresses the reviewer concern about
  contemporary neuron baselines.
- ✅ **Smoke gate:** `scripts/smoke.py` passed **150/150** finite forward/backward checks on
  2026-07-19: `(5 archs × 5 neurons × 6 readouts)`.
- ✅ **Train/log smoke:** one-epoch FF membrane runs on `nmnist_tiny_T20` are stable for PLIF
  and ALIF/LSNN. These are launcher checks, not paper results.
- 🔎 **Finding — deep-HyperLIF fires once the cascade has time to build.** On a too-short T=5 proxy it
  looked starved (~0 spikes); at **T=20 + training** conv+HyperLIF fires and learns (ev/samp ~72). The
  **validated variants behave as expected and are now sweepable** (`NEURON_VARIANTS`, threaded through
  conv + rsnn): **θ_event=0.95 → denser firing** (hyperlif 72→82, adaptive 42→49); **origin
  (v_reset<0 static AHP / δ_reset>0 gate-coupled, min_voltage=-2.0) → sparser, reshaped dynamics**
  (ev/samp 7–15) — the temporal-task levers. conv propagates each neuron's natural output (spike for
  LIF, gate `r` for HyperLIF). **These θ_event + origin variants are part of the Tier-2/3 sweep** — the
  activity/accuracy trade they open (dense vs sparse) is itself an interesting result, not a problem to fix.

## Next
- **Phase B prep:** run the expanded PLIF/ALIF/HyperLIF architecture matrix, regenerate `--mode full`
  caches for the SOTA runs, then push conv-SNN + RSNN to HPC.
- **Phase D (weekend, parallel):** cache→HDF5 exporter + Julia parity scaffold.
