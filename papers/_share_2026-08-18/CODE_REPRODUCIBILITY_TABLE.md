# Code → Runner → Result Map — P1, P2, P3

Every result reported in the three papers, traced to the exact code and command that produced
it. All entries below were verified against raw data (registries, JSON summaries, or
cross-source agreement), not just read off the paper. Full detail and exact CLI flags are in
each paper's own `RUNNERS.md`, included in its code `.zip`.

## P1 — HyperLIF Learning

| Result in paper | Code | Runner command | Evidence |
|---|---|---|---|
| Table: PLIF/ALIF reviewer baselines | `scripts/run_p1_baseline_preflight.py`, `run_p1_shd_wide_arch_shortlist.py` | `python scripts/run_p1_baseline_preflight.py` | `results/p1_plif_alif_ff_nmnist_tiny_20260719/`, `p1_baseline_arch_shortlist_shd_wide_20260719/` — matches paper to 3-4 decimals |
| Table + Fig. 4: architecture-transfer (conv/rsnn/delay × 5 datasets) | `hpc/train_hpc.py` via `hpc/run_array.slurm` (SLURM cluster) | `sbatch --array=... hpc/run_array.slurm` | `results/roster60/` (2759 runs) |
| Table: feedforward temporal gain (5 datasets) | Same HPC pipeline, job **559182** | (cluster-only; local scripts don't reproduce this specific run) | `results/hpc_559182/_registry_ff_559182.csv` — verified by direct aggregation, matches paper exactly |
| Table: gate-readout structural blindness (DVS-32) | Same, job 559182 | — | Same registry — all 12 readout×neuron values matched to 3-4 decimals |
| Julia/APEX cross-framework validation | `apex_julia/src/HyperLIF.jl`, `HyperLIFadapt.jl`, `HyperSNN.jl` | `julia --project=apex_julia -e "import Pkg; Pkg.instantiate()"` then run scripts | Environment: Flux, CUDA, Zygote, DifferentialEquations |

## P2 — HyperLIF in Nengo/NEF

All 16 numbered experiments in `experiments/`, run via `scripts/run_experiments.ps1` →
`experiments/run_all.py`, or individually. Every claim in the paper is tied to one of these by
`RESULTS_AUDIT.md` (included). Highlights:

| Result in paper | Code | Evidence |
|---|---|---|
| Exact Python↔Nengo parity | `experiments/07_python_vs_nengo.py` | `07_python_vs_nengo.csv`, `07_parity_metrics.csv` |
| DB-onset prediction (`J_DB=2.4`) | `experiments/03_current_sweep.py` | `03_db_analysis.csv` |
| Integration-scheme stability | `experiments/06_numerical_integration.py` | `06_integration_accuracy.csv`, `06_stability.csv` |
| Backend portability limitation | `experiments/14_backend_portability_probe.py` | Summarized in `NENGO_CAPABILITY_FINDINGS.md` |
| 5-seed NEF decoder ablation | `experiments/18_nef_decoder_state_ablation.py` | `18_nef_decoder_state_ablation.csv` + summary |

Full 16-row table with every experiment → output file is in P2's own `RUNNERS.md`.

## P3 (fixed_adaptive) — Gate-Residual Mechanism

| Result in paper | Code | Runner command | Evidence |
|---|---|---|---|
| Table: Hard45 Controller Comparison (CF2) — classical/LIF/**HyperLIF (fixed)**/**Adaptive HyperLIF**/Nengo | `runners/run_rotor_level.py` | `--quad bitcraze_crazyflie_2 --controller {classical,direct_lif,direct_hyperlif,direct_adaptive_hyperlif,nengo_lifrate} --mission hard45 --sim-time 45 --blend 0.50 --gate-gain 100000` | `results/logs/*_summary.json` — `direct_hyperlif` verified exact (`qerr_mean=0.28203`→0.2820) |
| Table: Gate-Gain Sweep | `results/gate_gain_sweep_20260703/gate_gain_sweep.py` | (pre-run, see script) | `sweep_cf2_hard45.json`, `sweep_x2_hard45.json` |
| Table: Cross-Quad (CF2 vs. Skydio X2) | Same `run_rotor_level.py`, both `--quad` values | Same pattern, `--quad skydio_x2` | `results/logs/skydio_x2_hard45_*` |
| Adaptive HyperLIF ≡ HyperLIF equivalence (both fixed and learned decode) | Analytic result + `learned_gate_experiment.py --neuron adaptive_hyperlif` | See P3 (learned) row below | Cross-checked bit-for-bit between both P3 papers independently |

**Note**: "Adaptive HyperLIF" gains in this paper's Table 1 are numerically identical to plain
HyperLIF by design (the paper's own proven result, §"Adaptive HyperLIF equals HyperLIF in gate
mode") — both rows are still fully reproducible from the same command above with
`--controller direct_adaptive_hyperlif`.

## P3 (learned) — Online-Learned Gate Residual

**Code recovered tonight** from `D:\...\02_Research\00_Code_Ecosystem\neuromorphic-robotics-control\`
(previously thought missing) and verified genuine against the results dossier's documented interface.

| Result in paper | Code | Runner command | Evidence |
|---|---|---|---|
| Primary benchmark, **+86.7%** headline (beats hand-tuned STN-PID-PES) | `experiments/controller_benchmarks/learned_gate_experiment.py` | `python learned_gate_experiment.py --methods all` | `learned_gate_results.json` |
| Cross-platform generalization (CF2/Skydio × hard45/hardstep) | Same, `--k-rate {0,0.3,1.0} --leak {0,1e-3,2e-3}` | Same | `learned_gate_hardstep.json`, `learned_gate_skydio.json` |
| Performance–robustness frontier | Same `k-rate`/`leak` sweep | Same | Same files |
| Adaptive ≡ HyperLIF equivalence (learned decode) | `--neuron adaptive_hyperlif --methods online_pes,eprop_anneal` | Same | Matches `fixed_adaptive`'s independent numbers bit-for-bit |
| Behavioral-cloning negative result (covariate shift) | `--methods imitation,imitation_pes` | Same | `learned_gate_imitfix.json` |

Dependencies: `neuron_dynamics.py`, `neural_torque_controllers.py`, `benchmark_metrics.py`,
`mujoco_classical_vs_neural_stn.py` (all included), plus `stn_pid_attitude_controller.py` from
a sibling folder (included, structure preserved).

## Shared external dependency — both P3 papers

Both `fixed_adaptive` and `learned` load quadrotor models from `mujoco_menagerie` — **Google
DeepMind's public, open-source asset repository**, not part of this research:
```
git clone https://github.com/google-deepmind/mujoco_menagerie models
```
Run once from each project's root before any simulation command above.

---
*Every code package (`P1_HyperLIF_Learning_code.zip`, `P2_HyperLIF_Nengo_code.zip`,
`P3_FixedAdaptive_code.zip`, `P3_Learned_code.zip`) contains its own detailed `RUNNERS.md` with
exact commands, file-by-file dependency notes, and verification confidence per result.*
