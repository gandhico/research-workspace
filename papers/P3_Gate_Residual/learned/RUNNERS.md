# P3 (learned) — Runners / Launchers, mapped to the paper

**RESOLVED tonight.** The generating code — confirmed missing from this machine and the main
D: backup (`D:\NMSU_backups\Backup\00_Research_\`) — was located by the user in a *different*
top-level D: folder, `D:\NMSU_backups\Backup\02_Research\00_Code_Ecosystem\
neuromorphic-robotics-control\experiments\controller_benchmarks\`. Verified as the genuine
file (not a guess): its CLI args (`--methods`, `--k-rate`, `--leak`, `--neuron
{hyperlif,adaptive_hyperlif}`) match the dossier's documented interface exactly, and its file
date (2026-07-05) matches the dossier's stated date.

Full dependency chain traced and copied to `code\experiments\`, preserving the original
relative folder structure (`controller_benchmarks\` and a sibling `mujoco_stn_hyperlif_benchmark\`)
because `mujoco_classical_vs_neural_stn.py` locates the STN controller via
`Path(__file__).parents[1] / "mujoco_stn_hyperlif_benchmark"` — moving the files out of this
relative shape would break the import.

| File | Role |
|---|---|
| `controller_benchmarks\learned_gate_experiment.py` | Entry point — everything in the table below |
| `controller_benchmarks\mujoco_classical_vs_neural_stn.py` | Base classical/neural benchmark harness (imported as `B`) |
| `controller_benchmarks\neuron_dynamics.py` | `make_direct_neuron` — HyperLIF/Adaptive HyperLIF neuron construction |
| `controller_benchmarks\neural_torque_controllers.py` | `make_controller` — controller factory |
| `controller_benchmarks\benchmark_metrics.py` | `summarize_controller_run` — the `J` score computation |
| `mujoco_stn_hyperlif_benchmark\stn_pid_attitude_controller.py` | `STNPIDAttitudeController` — the adaptive baseline being beaten |
| `controller_benchmarks\learned_gate_*.json` | Saved result snapshots (hardstep, imitfix, results, skydio) |

## External dependency (not included, not proprietary)

Same as `fixed_adaptive`: this code loads drone models from
`third_party/mujoco_menagerie/{skydio_x2,bitcraze_crazyflie_2}/scene.xml` — Google DeepMind's
**public, open-source** asset repository (`github.com/google-deepmind/mujoco_menagerie`), not
part of this research. To actually run: `git clone
https://github.com/google-deepmind/mujoco_menagerie third_party/mujoco_menagerie` from the
`code\` root before invoking any command below.

## Table ↔ command ↔ result — now independently re-runnable

| Paper item | Command | Evidence |
|---|---|---|
| Primary benchmark table, **+86.7%** headline | `python learned_gate_experiment.py --methods all` | `learned_gate_results.json`; matches `main.tex` Table exactly |
| Generalization table (hard45/hardstep × CF2/Skydio) | `python learned_gate_experiment.py --methods online_pes --k-rate {0,0.3,1.0} --leak {0,1e-3,2e-3}` | `learned_gate_hardstep.json`, `learned_gate_skydio.json` |
| Performance–robustness frontier (§`sec:frontier`) | Same `--k-rate`/`--leak` sweep | Same files |
| Equivalence result (Adaptive ≡ HyperLIF, learned decode) | `python learned_gate_experiment.py --neuron adaptive_hyperlif --methods online_pes,eprop_anneal` | Cross-checked bit-for-bit against `..\fixed_adaptive`'s independent numbers |
| Imitation/behavioral-cloning negative result | `--methods imitation,imitation_pes` | `learned_gate_imitfix.json` |

Run from `code\experiments\controller_benchmarks\` after cloning `mujoco_menagerie` as above.
