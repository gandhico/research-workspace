# HyperLIF Portfolio — Validated Results, Code, and Runners

PDFs in this package are drafts showing the current results — the real paper drafts live in Overleaf
and will be updated there directly from these .tex files (fast, since it's a diff). 
This note's job is to hand off what's been validated, where it comes from, and how to reproduce it
— not to judge submission readiness. Because the full pipeline — code, environment, and runners —
is included and independently verified, any new experiments you propose can be launched directly
from this foundation, whether on this local machine or on the HPC cluster, rather than
rebuilding from scratch.


## P1 — HyperLIF Learning

**Core equations** (continuous-reset neuron, replaces the LIF hard reset):
```
τ_v v̇ = -(v - v_rest) + I - G(r,I)(v - v_reset),   τ_r ṙ = σ(α(v - θ_eff)) - r,   θ_eff = θ - γr
```
Plain HyperLIF: `G(r,I) = g_reset·r²`. Adaptive: `G(r,I) = (g_base + β|I|)·r²`.

**Validated results, with code path**:
- PLIF/ALIF baseline table (N-MNIST tiny, SHD-wide × 3 architectures) —
  `code/scripts/run_p1_baseline_preflight.py`, `run_p1_shd_wide_arch_shortlist.py` →
  `code/results/p1_*_20260719/`. Verified to 3-4 decimals against paper values.
- Architecture-transfer table (conv/rsnn/delay × 5 datasets) — `code/hpc/train_hpc.py` via
  `run_array.slurm` → `code/results/roster60/` (2759 runs).
- Feedforward temporal-gain + gate-readout tables — same HPC pipeline, job 559182 →
  `code/results/hpc_559182/_registry_ff_559182.csv`. Verified by direct aggregation of raw
  per-seed data, not read off a summary.
- Julia/APEX cross-framework check — `code/apex_julia/src/HyperLIF.jl`, `HyperLIFadapt.jl`
  (environment: Flux, CUDA, Zygote, DifferentialEquations via `code/apex_julia/Project.toml`).

Full command-by-command map: `P1_HyperLIF_Learning_code.zip → RUNNERS.md`.

## P2 — HyperLIF in Nengo/NEF

**Core validated relations**:
- Depolarization-block onset: `J_DB = (v_thresh - γ)(1 + τG_b) = 2.4` — matches simulated
  collapse at `J≈2.3–2.4`.
- Fixed-gain latched voltage: `v* = J/(1+τG_b)` — predicted `1.3333` vs. simulated `1.3333` at
  `J=4` (exact).
- Exact Python↔Nengo parity (RMSE = 0) on step/stress protocols.

**Code path**: every claim maps to one of 16 numbered scripts in `code/experiments/`, each
writing a named CSV in `code/results/csv/`. Full table (script → CSV → figure/table it feeds)
is in `P2_CLAIM_ARTIFACT_AUDIT.md` (this folder) and `P2_HyperLIF_Nengo_code.zip → RUNNERS.md`.
Nothing here needs re-deriving — pull the equations/values straight from the CSVs into Overleaf.

## P3 (fixed_adaptive) — Gate-Residual Mechanism

**Core result** (Hard45, Crazyflie 2, 45s): `qerr_mean` 0.2820 vs. classical 0.2854 (+1.2%);
Skydio X2: 0.2753 vs. 0.2941 (+6.4%). Adaptive HyperLIF reproduces HyperLIF bit-for-bit in gate
mode (`g_gate=10^5` saturates `r` to `{0,1}`; the adaptive term only touches transient voltage
speed, not gate equilibrium — proof and full derivation in `main2.tex` §"Adaptive HyperLIF
equals HyperLIF in gate mode").

**Code path**: `code/runners/run_rotor_level.py --quad {bitcraze_crazyflie_2,skydio_x2}
--controller {classical,direct_lif,direct_hyperlif,direct_adaptive_hyperlif} --mission hard45
--gate-gain 100000 --blend 0.50` → `code/results/logs/*_summary.json`. `qerr_mean=0.28203`
verified exact against the paper's `0.2820`.

**Dependency**: `mujoco_menagerie` (Google DeepMind's public asset repo, not proprietary —
`git clone https://github.com/google-deepmind/mujoco_menagerie models`).

## P3 (learned) — Online-Learned Gate Residual

**Core result**: `J=0.0383` (+86.7%) on Bitcraze/Hard45, beats hand-tuned STN-PID-PES
(+83.3%); generalizes to Skydio X2 (+57%) where the hand-tuned baseline doesn't transfer.
Learning rule: `Δt* = clip(-k_e·e - k_r·ω, -1, 1)`, `ΔW = λ(t*-s)ρᵀ - ℓW` (PES delta-rule on
the decode matrix `W ∈ ℝ^{3×6}`, initialized at the fixed decode `W₀=[I₃|-I₃]`).

**Code path**: `code/experiments/controller_benchmarks/learned_gate_experiment.py --methods
all` → `learned_gate_results.json`. Full parameter table (τ, g₀, γ, learning rates, leak) is
in `main.tex` Table I — copy straight across, it's already been cross-checked against the code.

**Dependency**: same `mujoco_menagerie` clone as `fixed_adaptive`.

---
**Zips contain full code + `RUNNERS.md` per paper** (exact commands, file-by-file dependency
notes). `CODE_REPRODUCIBILITY_TABLE.md` in this folder is the condensed cross-paper version.
