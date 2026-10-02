# CMG reinforcement learning for full-vehicle MuJoCo racing — exploratory stage

Started 2026-09-30. This is a **separate research line**, not part of the
frozen ACC 2027 CMG-PES results. The initial X2 runs are a software/method
pilot and are **negative** as racing results. Read `PILOT_REPORT.md` before
using a number or figure.

## Exact architecture and claim boundary

```text
MuJoCo full 6-DOF X2/CF2/Y6 plant, 2-ms rigid-body step, bounded rotors
  -> perfect state + next two gate vectors + (stage-1 only) planned reference
  -> normalized observation o (26 channels, policy every 20 ms)
  -> fixed random current encoder J = clip(0.85+b+0.95 tanh(Eo), 0.05, 2.2)
  -> 32 CMG cells, each advanced at 0.5 ms [v, r, genuine event count]
  -> selected readout (gate or filtered event rate) concatenated with o
  -> 2x64 actor/critic, Gaussian actor trained by PPO, tanh action
  -> [collective thrust, desired body rates] -> common rate loop
  -> vehicle-specific allocation/rotor limits -> MuJoCo next state
```

The MLP comparator receives the same observation, action interface, reward,
teacher samples and PPO budget, with 32 zero feature slots. The four CMG
arms form a 2-by-2 mechanism experiment:

| Dynamics | Gate readout | Filtered event readout |
|---|---|---|
| Original continuous CMG dynamics | `graded` | `crossing` |
| **New** event-reset CMG dynamics | `reset_gate` | `reset_spike` |

The historical `crossing` event is an **upward crossing** of membrane
voltage through a declared threshold. Threshold occupancy at every timestep
is not counted as repeated spikes. `reset_spike`/`reset_gate` subtract the
event threshold from the voltage after each event, permitting sustained
spiking; **that is a new hybrid CMG-LIF model**, not the ACC controller.
`reset_gate` is the essential control that separates the impact of reset
dynamics from using event activity as a readout. All variants save voltage,
gate, filtered rate, event counts, activity, actions, rotors, rewards and
plant state every 20 ms. `calibrate_cmg.py` saves 2-ms cell traces and the
operating-point table.

The continuous core uses the same Nengo `CoupledMembraneGate.step` update as
the ACC code. `test_cmg_cells.py` verifies its voltage, gate and activity
traces against that Nengo cell at both default and retuned parameter sets.
The retuning is explicit: gate gain 1 instead of 1e5, sigmoid alpha 12
instead of 50, threshold 0.55 instead of 1, gamma 0.35 instead of 2,
base/input conductance 20/10 instead of 120/30. These choices were fixed
for the pilot before comparing racing outcomes. They are **not** a claim of
optimal tuning. `adaptive=True` means input-dependent conductance; it does
not mean PES or online RL adaptation of intrinsic neuron parameters.

The actor/critic is PyTorch and lives **outside the Nengo graph**. The CMG
cell's intrinsic parameters and random input encoder are frozen; the PPO
actor/critic weights learn. No PES teacher acts during PPO; behavior cloning
from the common geometric controller initializes every arm equally. This is
not yet a neuromorphic-hardware or energy-efficiency demonstration.

## Reproduce the current pilot

Use the existing environment, which has MuJoCo 3.11, Nengo 4.1, PyTorch 2.5
and SciPy. MuJoCo/SciPy and PyTorch run in separate processes because loading
both numerical runtimes into one Windows process caused duplicate Intel
OpenMP initialization. Do not set `KMP_DUPLICATE_LIB_OK` as a workaround.

```powershell
$py = 'C:\Users\gandhico\AppData\Local\miniconda3\envs\hyperlif\python.exe'
$root = 'C:\Research\neuromorphic_drone_racing\rl_cmg_2026_09_30'

& $py "$root\test_cmg_cells.py"
& $py "$root\calibrate_cmg.py"

foreach ($mode in @('mlp','graded','crossing','reset_gate','reset_spike')) {
    & $py "$root\train_split.py" --vehicle x2 --observation reference `
        --mode $mode --seed 1 --episode-s 12 --bc-epochs 20 `
        --ppo-rollouts 2 --ppo-epochs 4 --ppo-samples 600 `
        --out "$root\results\final_x2_${mode}_seed1"
}
& $py "$root\summarize_pilot.py"
```

`train_split.py` calls `rollout_worker.py` in a separate process for each
teacher, PPO and evaluation rollout. For every run it saves policy weights,
PPO traces, deterministic evaluation traces, JSON summaries and source/model
hashes. With `--observation gate_only`, the planned reference channels are
zeroed; that is the next, harder experiment and **has not been validated**.
The reward still includes a small planned-reference shaping term, so even
that option is not a strict gate-only *reward* design.
The four-command interface currently supports underactuated X2/CF2/Y6.
Omnicopter requires a separately specified 6D wrench policy to exercise its
full actuation; it is deliberately rejected here instead of being silently
treated as a quadrotor.

## Current result and next gate

The matched single-seed pilot uses 600 common BC teacher samples and two
fixed 600-step PPO rollouts (12,000 MuJoCo training steps at 2 ms) per arm.
The geometric teacher and a direct teacher-action oracle through the new
rate/allocation interface each pass four gates in 12 s. None of the five
learned arms passes a gate under this very small budget. See
`PILOT_REPORT.md`, `results/final_pilot_analysis/pilot_comparison.csv` and
the figures there. No claim about intrinsic CMG-versus-MLP RL superiority
is justified.

Before any broader comparison, improve control learning on development
tracks and verify *successful gate passage* in several seeds. Then freeze
one common algorithm/budget; compare reference-conditioned and gate-only
observations, held-out tracks, X2/CF2/Y6 and the Omnicopter 6D variant.
Only afterward place the emulated DVS estimator in the feedback loop. The
present DVS code remains an **offline renderer**, not a policy observation.
