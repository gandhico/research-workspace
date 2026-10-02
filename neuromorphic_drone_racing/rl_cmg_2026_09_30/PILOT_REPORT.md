# Honest checkpoint: graded and event-driven CMG RL for racing

Date: 2026-09-30. Status: **exploratory negative pilot**, not an ACC 2027
result and not a comparison with Swift race times.

## What was validated

The plant is the existing X2 MuJoCo rigid body with rotor allocation and
limits. The policy observes perfect state, next-two-gate vectors and a planned
trajectory reference; it issues collective thrust and body-rate requests.
The race is one vehicle on our own seven-gate, 101-m Swift-*format* track.
The original geometric controller and its action projected through the new
thrust/rate interface both passed **4 gates in the 12-s window**, with no
contact. Thus the interface can reproduce the existing controller under
closed-loop oracle commands. The CMG numerical core passed parity against
the Nengo `CoupledMembraneGate.step` for 1,200 steps at two parameter sets.

All learned arms received 600 teacher samples, 20 behavior-cloning epochs,
two PPO rollouts of exactly 600 decisions each, 4 PPO epochs per rollout,
the same observation/action/reward definitions and seed 1. Each arm therefore
received exactly **12,000 MuJoCo steps** of reward-driven training, plus the
teacher initialization trajectory. Episodes that terminated early were
reset within the rollout. Evaluation used deterministic actor output.

| Actor feature | 12-s teacher gates | Learned gates | Survival (s) | End reason | Event rate, all units (Hz) |
|---|---:|---:|---:|---|---:|
| MLP, no neuron | 4 | 0 | 6.62 | ground | 0 |
| Continuous CMG gate | 4 | 0 | 4.34 | outside | 0.20 diagnostic crossings; not policy input |
| Continuous CMG upward crossings | 4 | 0 | 3.50 | gate collision | 0.16 |
| Reset-enabled CMG gate | 4 | 0 | 5.46 | ground | 17.14 internally; policy reads gate |
| Reset-enabled CMG filtered spikes | 4 | 0 | 3.36 | ground | 17.25 |

The event rate is the mean across 32 units over each *different* evaluation
trajectory. It is not an energy measure. In constant-current calibration,
the unreset crossing arm produced **zero sustained crossings** at J=0.4–2.8,
whereas the reset-enabled cell produced 38, 56, 72 and 105 Hz at J=1.2,
1.6, 2.0 and 2.8, respectively. The gate remained active during this
spiking regime (mean r≈0.09–0.12 at those currents). This validates distinct
spiking/non-spiking operating modes at the *cell* level, but not useful RL
control. The reset variant changes the continuous dynamics and must not be
presented as simply a different readout of the ACC neuron.

The `results/final_pilot_analysis/pilot_tracking.png` figure shows all
learned controllers losing the teacher trajectory before G1. Its position
error curves terminate at different times; their means cannot be ranked as
equal-horizon tracking metrics. `cmg_activity_events.png` shows the graded
gate, the almost-silent historical crossings, and the sustained reset-cell
events. These figures are diagnostic, not publication evidence.

## What this does and does not imply

This failure is **not evidence that CMG cannot learn by RL**. It shows that
the present behavior-cloned direct 4D policy plus only 24 s of PPO simulator
experience per arm is insufficient for this racing task. Even the MLP arm
fails. A 100-epoch BC check followed by three DAgger rounds for the MLP also
failed to pass a gate (`results/dagger3_mlp`), indicating closed-loop
distribution shift and/or insufficient observation/training despite a low
supervised action loss. No architecture ranking is justified from one seed
when every arm has zero task success. The current reward includes a small
planned-reference anchor, so this is **trajectory-conditioned RL**, not
end-to-end gate-only navigation. DVS is not in feedback.

The pilot does establish a useful mechanistic result: retaining the original
continuous dynamics and merely reading upward crossings does **not** yield
a high-rate spiking policy in the tested operating range. Sustained spikes
required an explicit voltage reset in this implementation. `reset_gate` is
the matched control for the changed dynamics, while `graded` is the
non-spiking CMG comparator. The source and per-run manifests distinguish all
four conditions.

## Next pre-registered development protocol

1. Retain the exact oracle gate as a regression test for X2, CF2 and Y6.
2. Improve direct-policy learning on a designated **development** course:
   more PPO experience, teacher-mixture curriculum, explicit time-limit
   bootstrap, action smoothness, and properly held-out seeds. Do not change
   neuron modes based on the held-out race outcome. A recurrent GRU policy is
   the next fair temporal-memory comparator.
3. Require successful gate passage in at least several seeds before any
   CMG-vs-MLP/SNN ranking. Report completion, crashes, lap time conditional
   on completion, actuator saturation, normalized event rates, action
   variation and wall-clock compute. Do not infer chip energy from CPU time.
4. Freeze reference-conditioned results before switching to the harder
   `--observation gate_only` study. Then test held-out track geometry and
   vehicle parameters. Preserve the distinction between the racing CF2
   1.7× authority design and the ACC paper's CF2 1.5× design.
5. Only after a successful state-based policy, integrate RGB/event-gate
   estimation and IMU fusion into the observation loop. The present 500-Hz
   frame-derived DVS emulator is offline and is not a physical event camera.

## Files

- `cmg_cells.py`: exact continuous CMG core and explicitly new reset variant.
- `test_cmg_cells.py`, `calibrate_cmg.py`: Nengo parity and operating-point data.
- `racing_env.py`: full-vehicle MuJoCo action/observation/reward interface.
- `policy_basis.py`, `rollout_worker.py`, `train_split.py`: fixed encoder,
  isolated simulator and PyTorch BC+PPO learner.
- `results/final_x2_*_seed1/`: every source/model manifest, weights, teacher,
  training and evaluation trace.
- `results/final_pilot_analysis/`: checked CSV, JSON, PNG and PDF figures.
  `audit_pilot.py` verifies all five run/manifests (5/5 passed).

The earlier `pilot_x2_*` and `matched_x2_*` directories are developmental
attempts. Use **`final_x2_*`** for the current source-aligned comparison.
