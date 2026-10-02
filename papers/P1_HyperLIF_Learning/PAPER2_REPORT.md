# Paper 2 — Full Report & Insights Log (2026-07-04)

*Master narrative for "HyperLIF Learning: a controlled, cross-framework study." Consolidates the
dense-architecture work, the validation journey, the HPC run, and every scientific insight so nothing
is lost. Companion detail docs: [`DENSE_ROSTER_VALIDATION_AND_INSIGHTS.md`](DENSE_ROSTER_VALIDATION_AND_INSIGHTS.md)
(validation matrix + bugs), `paper/paper2_manuscript.md` (draft), `RESEARCH_ROADMAP.md` (status log).*

---

## 1. What Paper 2 is
A controlled study isolating the HyperLIF neuron across **datasets × architectures × neuron-variants ×
readouts × learning frameworks** — arc: *isolate → transfer → innovate*. It owns the learning-benchmark
narrative (PyTorch/snnTorch + Julia/APEX); the Nengo/reference story is Paper 3, the NSA theory is TNNLS.

## 2. The experimental cube (running on NMSU Discovery)
- **Architectures:** `ff` (baseline FF-SNN) · `conv` (shallow conv-SNN) · **`convres`** (deep
  SEW-ResNet-style, 14M ResNet-18-class — the dense/SOTA net) · `rsnn` (recurrent) · `delay` (delay-SNN).
- **Neuron roster (7, all validated):** `lif` · `hyperlif` · `adaptive` · `hyperlif_t0.95` ·
  `adaptive_t0.95` (θ_event=0.95) · `adaptive_origin` (v_reset=−0.6) · `adaptive_dreset` (δ_reset=0.3).
- **6 readouts × 5 seeds × 60 epochs** → **112 bundles / 3360 configs** into `results_roster60`.
- Grounded in the real-data variant spine (`07/results/spine_summary.md`): base HyperLIF best overall;
  **adaptive+θ_event=0.95 = best adaptive variant**; **origin = temporal-task asset** (helps SHD).

## 3. Scientific insights (the keepers)

### 3.1 Deep HyperLIF needs SPIKE propagation — the gate is a readout ★
The headline architectural finding. Propagating HyperLIF's **graded gate `r`** between layers trains in
shallow nets (ff/conv/rsnn/delay all → 1.0) but **stalls at chance through the deep residual stack** —
the steep α=100 gate destroys gradient flow across ~9 layers, while LIF (spike-propagating) trains to
1.0 on the identical net. Fix: propagate the **surrogate spike** (SEW-ResNet design); keep gate `r` as
the head readout. convres HyperLIF then trained (0.25 → 0.64–1.0). **Generalizable law: graded-gate
propagation is a shallow-net convenience; deep spiking residual nets transport spikes and *decode* the
gate at the readout.** (Echoes the `01` gate-eligibility "exact-gradient mirage" and Paper 3's NEF
"gate is a readiness readout" — three substrates, one truth.)

### 3.2 Efficiency dial
HyperLIF matches representation at **~3.5× fewer spikes** (echoed in Paper 3's NEF: 33 vs 120 Hz).
In shallow conv the gap reaches **~200×** (conv HyperLIF fires ~4 events/sample vs LIF ~370) while
still learning to 1.0 — sparse-by-design, not starved.

### 3.3 Variants are real and were never tested at scale before
The 450-run + §6.4 (1170-run) sweeps were **base-3 only**. This cube is the first at-scale test of the
θ_event and origin variants inside real architectures. θ_event=0.95 densifies deep firing; origin is a
temporal asset; both are **parity-preserving operating-point tools**, not new dynamics.

### 3.4 The efficiency ↔ learning-speed trade (cross-paper)
The same sparsity that buys representation efficiency **costs online-learning speed** (Paper 3 PES:
HyperLIF slower, recoverable to a ~40 Hz sweet spot but with a ceiling below LIF). One trade, visible in
both the deep-learning and NEF regimes, and in the `01` gate-eligibility "coverage/events matter" result.

## 4. Validation journey — 4 bugs caught BEFORE the run (why we stopped to validate)
On a full local run of the exact `train_hpc.py` build path (5 arch × 7 neuron × 6 readout = 210
build/fwd/bwd + 35 fire+learn):

| # | Bug | Symptom | Fix |
|---|-----|---------|-----|
| 1 | Variant cfg silently dropped | `hyperlif_t0.95` built plain HyperLIF | resolve `NEURON_VARIANTS`→(base,cfg) in train_hpc |
| 2 | convres head starved | head fired 0 events/gate → gate/hybrid/efficiency readouts dead | head `fc→BN→×DRIVE_SCALE` |
| 3 | Run-dir collision | conv/convres shared `summary.json` | arch-aware `{arch}_{neuron}_{readout}` |
| 4 | **Deep HyperLIF training stall** | convres HyperLIF fired but flat at chance | **surrogate-spike propagation** (§3.1) |

**Final gate: Pass A 210/210, Pass B 35/35 fire+learn, no starvation, none stuck → 100% VALIDATED.**

## 5. HPC run saga (operational lessons)
- **Deployment:** cache-driven; 112 single-index-array bundles submitted by a throttled loop under the
  `p-normal` 20-submit / 10-run QOS caps.
- **Bug in the field #1 — stalled submitter.** The tmux loop died (login-node session ended) at ~bundle
  18; the queue silently drained. **Lesson: run the submitter under `nohup … & disown`, log to a file,
  and it survives disconnect.** Diagnosed via empty `squeue` + `sacct` + registry row count.
- **Bug in the field #2 — CUDA OOM on convres.** The 14M net at `--batch 64` × T=20 BPTT exhausts a
  16 GB GPU (worst on 48×48 DVS ≈ 2.25× the 32×32 footprint). Symptom: convres bundles "COMPLETED" in
  ~2.5 min with `ok=0 fail=30` and zero registry rows, while conv took ~1.5 h. **Fix: arch-aware batch —
  `convres → batch 16`, light archs stay `batch 64` (`grid.py` emits per-arch batch).** Each arch is
  internally batch-consistent; batch size does not materially move final accuracy.
- **Resumability:** the registry + `--skip-existing` make every restart idempotent — completed configs
  skip, missing ones run. No work lost across any restart.

## 6. Current status
- **Validated code deployed**, all 4 fixes byte-verified in the cluster zip.
- **~360 configs done** (conv/rsnn/delay on dvsg32, all `stable=True`); convres now running at batch 16.
- Run in progress (~2–3 days). Feeds §6.4 (architecture transfer) of the manuscript.
- **Success signal:** convres bundle ≈1 h elapsed + canary `grep ',convres,.*,hyperlif,'` shows
  events>0/gate>0 on real data (confirms the head-drive + spike-prop fixes are live).

## 7. Cross-substrate thesis (ties Paper 2 ↔ Paper 3 ↔ 01)
> **HyperLIF's continuous gate `r` is a decodable *readout/state* signal and a principled
> *operating-point* knob — never the transport or exact-gradient channel. Transport is the surrogate
> spike (deep nets) / rate code (NEF); the gate is decoded on top. Usability is a calibration question
> (θ_event, origin, gain), and the one honest cost is sustained integration/memory — while the payoff is
> greatest in learning/plasticity.**

## 8. What remains for Paper 2
- Finish the convres/roster cube → fold §6.4 numbers into `paper/paper2_manuscript.md`.
- §6.6 APEX GPU cross-framework run (PyTorch ≡ Julia parity at scale).
- Optional denser tiers (57M/97M) on full-data caches for the headline SOTA-accuracy line.
