# Research Roadmap — Two Lines toward HPC + Publication

**Framing.** Local machine = CPU, no GPU, and long jobs die in idle gaps → local work is for
**stability checks + preliminary de-risking** (make sure the model and the test pipeline actually
work). **HPC = the full-scale runs.** Everything below keeps that split: we only upload to HPC
what has been shown locally to be stable and correct.

Two research lines run in parallel:
- **Line A — Spiking Control:** the differentiated test of whether the rich / adaptive dynamics
  matter (the perception benchmarks say they don't; control is where the theory predicts they do).
- **Line B — Event-Vision at scale (other libraries):** port HyperLIF into an established SNN
  library, validate locally, then run the heavy event-vision benchmark on HPC.

---

## 0. Shared foundation — what we have PASSED

- **Parity-gated PyTorch HyperLIF** == validated Nengo reference to machine precision
  (`docs/PARITY.md`). Reproducible harness: neurons (LIF/ALIF/HyperLIF/Adaptive/+origin),
  readouts, task + dynamics metrics, resumable runs.
- **Perception triage** (N-MNIST + SHD, feedforward): **HyperLIF wins**; hybrid gate/conductance
  readout best; **θ_event=0.95** best adaptive variant; **origin helps on temporal only**;
  **β (adaptation) inert**; LIF/ALIF last. (`results/spine_summary.md`, `results/phase1b_shd/`)
- **Reservoir / LSM** (Phase 2): HyperLIF > LIF, but the margin is **mixed** (widens on vision,
  narrows on temporal; hyperparameter-sensitive).
- **Control probe v1** (PD-imitation tracking): **null** — all controllers imitate PD equally;
  HyperLIF has the best control-torque fidelity but no closed-loop edge (the task is too easy).
- **Through-line insight:** the **continuous reset (HyperLIF) is the robust, real win** and its
  gate/conductance state is a genuinely useful decodable feature; the **adaptive elaborations
  (β, origin) have not yet shown a clear task advantage anywhere** — this *refines* the original
  thesis and is the gap both lines aim to close.

---

## Line A — Spiking Control

> "The harder the control / the more the mission demands it, the more a good spiking controller
> should pay off." Goal: find the regime where the rich/adaptive dynamics demonstrably help.

**Passed:** pendulum plant + PD demonstrator (validated; `drive` knob spans easy→69% torque
saturation), control probe v1 (null on PD-imitation).

**Now:** the null was a *design* limitation — PD-imitation is forgiving and never forces the
controller to a regime where adaptation matters. Need harder, mission-demanding tasks + training
that goes beyond copying PD.

**Next (in order):**
- **A1 — Harder tasks (local, stability + preliminary):**
  1. *Swing-up* — drive the pendulum from hanging to upright; PD can't solve it, so the controller
     must learn a genuine nonlinear policy (sustained high torque → the regime β targets).
  2. *Disturbance rejection* — random impulses; tests stability recovery under sudden high drive.
  3. *Energy-constrained tracking* — penalize control energy; rewards efficient spiking control
     (where sparse, stable dynamics should help).
- **A2 — Training beyond imitation:** move from PD-imitation to **closed-loop policy learning** —
  BPTT through the plant (HyperLIF is exactly differentiable, *no surrogate needed* through its
  continuous state — a structural advantage over LIF here) and/or **FORCE/RLS** online learning.
- **A3 — Comparison:** LIF / ALIF / HyperLIF / Adaptive / +origin × tasks × drive levels. Metrics:
  task success (swing-up time, recovery time), tracking error, **control energy**, stability,
  spikes-per-decision.
- **A4 — Decision gate:** *does adaptation/origin win in the high-drive / mission-demanding band?*
  - **Yes →** the strong "Adaptive HyperLIF earns its keep in control" paper.
  - **No →** the honest reframe (continuous reset + decodable gate state is the contribution).
- **A5 — Replicate + scale:** confirm the winning control setup in **Nengo** (NEF, the
  quaternion-attitude bridge from the Nengo paper) and the **Julia** reference; then HPC-scale to
  harder plants (cartpole, quadrotor attitude).

---

## Line B — Event-Vision at HPC scale (other libraries)

> Local = make sure the model + tests are correct and stable; HPC = the full benchmark.

**Passed:** custom PyTorch harness on N-MNIST + SHD (parity-gated). Findings as above. Constraint
found: figshare-hosted sets (CIFAR10-DVS, DVS Gesture) won't download locally (HTTP 202);
zenkelab (SHD/SSC) + AWS (N-MNIST) work.

**Now:** the custom harness is correct but CPU-bound and not HPC-optimized. For HPC-scale
event-vision we validate HyperLIF inside an **established SNN library** — for (i) an independent
cross-check of our neuron, (ii) optimized GPU training + dataset pipelines, (iii) standard LIF
baselines in that framework.

**Next (in order):**
- **B1 — Port HyperLIF into one library + parity-validate.** Candidates:
  - **snnTorch** — cleanest custom-neuron API; easiest to port + parity-check. *(recommended first)*
  - **SpikingJelly** — fastest CUDA + best DVS/event pipelines → the strongest HPC target.
  - **Norse** — functional PyTorch; clean but more rewiring.
  Gate: the ported neuron must reproduce our parity reference (same machine-precision check).
- **B2 — Stability + preliminary local benchmark (de-risk HPC):** run the ported HyperLIF in the
  library on a *small* N-MNIST/SHD subset locally — confirm it (a) trains stably, (b) reproduces
  our finding (HyperLIF ≥ LIF), and (c) the *full pipeline* (data → train loop → logging) runs
  end-to-end. **This is the "make sure it works before HPC" step.**
- **B3 — Package HPC job scripts:** SLURM arrays, full datasets (N-MNIST, DVS Gesture & CIFAR10-DVS
  via HPC-accessible mirrors / manual transfer), all classes, multi-seed, GPU, the dynamics-metric
  logging carried over.
- **B4 — Run on HPC:** the full-scale event-vision benchmark (what local CPU can't do).
- **B5 — Cross-validate:** confirm the library, at scale, reproduces the custom-harness ranking
  (HyperLIF wins, hybrid readout best, β scope). Discrepancies → investigate before any claim.

---

## How the two lines converge (publications)

- **Nengo reference + validation paper** (drafted) — ready-ish → neuromorphic venue / software track.
- **Control paper (Line A)** — needs the A4 win; otherwise folds into the honest reframe.
- **Event-vision benchmark (Line B)** — HPC-scale, library-validated; the perception backbone.
- **Methodology/rigor** — parity gates + claim discipline + the audit that caught the surrogate-LIF
  mislabeling — a timely cross-cutting contribution.
- Venues: journals (*Neuromorphic Comp. & Eng.*, *Frontiers Neuromorphic Eng.*, *TNNLS* theory in
  review); conferences (**IJCNN/WCCI, ICONS, NICE, tinyML**); **NeurIPS/ICML SNN workshops** for
  the rigorous nuanced findings.

---

## Immediate next steps (this order)

1. **A1+A2 — harder control:** build swing-up (+ disturbance) and closed-loop policy learning;
   rerun the LIF/HyperLIF/Adaptive/+origin comparison. *Local, foreground, stable, preliminary.*
2. **B1+B2 — library port:** port HyperLIF to snnTorch, parity-check it, and run a small local
   stability benchmark to confirm the HPC-bound pipeline works.
3. **Decide (A4):** does adaptation win in hard control? → pick the publication framing.
4. **Package for HPC (A5 / B3):** SLURM scripts for the winning control setup and the
   library event-vision benchmark; upload + run.

*Discipline carried throughout: parity-gate every new implementation; keep local runs lean
(de-risk, not final); separate safe vs unsafe claims; never upload to HPC what isn't locally
shown stable + correct.*
