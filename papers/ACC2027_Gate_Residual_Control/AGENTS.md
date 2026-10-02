# ACC 2027 CMG residual control: agent handoff

Last reviewed: 2026-09-30 (America/Denver). Read this file before changing
code, experiments, figures or paper claims in this project. It is a map and a
claim boundary, not a substitute for checking each cited run's manifest.

## Start here

1. The project root is `C:\Research\papers\ACC2027_Gate_Residual_Control`.
   Use `C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe`
   for the established MuJoCo/Nengo simulations. `README.md` is the original
   setup; `REPRODUCE_ACC2027.md` is the current claim-to-code map.
2. The most recent paper **as supplied by the user** is
   `C:\Users\gandhico\Downloads\Online_PES_Decoder_HyperLIF_Residual_Control___Quaternion_Tracking (29).pdf`
   (eight pages, created 2026-09-30). The local editable version may lag the
   user's Overleaf/Claude work. Check both before editing. Local recent source:
   `paper\v15_2026-09-29_corrected\ACC2027_v15.tex`.
3. `REPRODUCE_ACC2027.md` maps the paper's tables and 59 checked numerical
   claims to source and result files. Run
   `& .\.venv\Scripts\python.exe .\reproduce\verify_acc2027_claims.py`
   before changing a reported number. Its last stated audit was 59/59.
4. The equation-to-code companion is
   `paper\companion_2026-09-30\ACC2027_equation_code_companion.pdf`.
5. The new RL pilot is `experiments\neuromorphic_rl_attitude_2026-09-30`.
   It is exploratory and must not silently enter ACC result claims.

## Research objective and present architecture

The ACC paper studies a **bounded additive attitude-torque residual** on a
quaternion PD controller with desired-rate feedforward. Six continuous
coupled membrane-gate (CMG) units provide signed temporal activity; an
18-weight decoder learns online by prescribed error sensitivity (PES). A
componentwise output gate blocks a residual opposing a baseline torque axis
at its torque limit. Rotor inverse allocation and collective height control
remain common to baseline and augmented arms.

The main signal path is:

```text
qd, measured q,omega -> shortest-path qe,eq -> PD+desired-rate ff u0
u0/l -> paired positive/negative currents -> six CMG (v,r) states -> a
pre-update W, a -> s=clip(Wa,-1,1) -> bounded residual beta*l*s
u0 + gated residual -> torque box -> inverse rotor allocation and rotor clip
-> MuJoCo rigid body -> next measured state
eq,omega -> target y* -> PES error (y*-s) -> W update for next step
```

Canonical equations and parameter values are in the current paper and
`experiments\neuron_basis_decisive_2026-09-24\TECHNICAL_METHOD.md`.
The CMG membrane `v` and gate `r` both evolve; the decoder reads
`a=clip(Gr,0,1)`. The CMG unit is **continuous and non-spiking**. PES changes
the decoder `W`; input-dependent conductance changes internal CMG dynamics.
These are distinct mechanisms. The tested conductance switch `chi` had little
measurable effect in the canonical high-gain regime. Do not attribute the
reported tracking gain specifically to conductance modulation.

The current paper's `rho=3` primary result uses X2 `beta=.5` and CF2-rotor
`beta=.2`. CF2 per-rotor authority is scaled 1.5x as a disclosed *simulation
design*, not a manufacturer or hardware measurement. Both plants are MuJoCo
rigid-body/rotor-force models; motor lag, battery dynamics, full aerodynamics
and real sensor timing are outside the validated scope.

## Approved and limited evidence

| Evidence | Current interpretation | Main location |
|---|---|---|
| X2 and CF2, five missions, `rho=3` PD+ff plus gated CMG-PES | Primary MuJoCo result: 37.3% / 22.4% reduction in geometric-mean quaternion-angle error, noise-free. X2/CF2 Hardstep remain slightly negative (-2.0%/-0.2%). | `experiments\final_robustness_gating_2026-09-20\results\final_nominal.csv` |
| Noise and repeated torque bursts | Gains persist on larger-error Full3/Hard45 and during selected burst phases; near the Roll/Yaw error floor, noise can erase them. CF2 rotor saturation can defeat a torque-box-only gate. | `experiments\final_robustness_gating_2026-09-20` |
| Corrected neuron-family/no-neuron study | All tested families can benefit after appropriate operating-point tuning; CMG is strongest in the tested common interface. Static paired and constant bases help but do not match CMG. | `experiments\neuron_basis_decisive_2026-09-24\analysis\final\FINAL_NEURON_BASIS_REPORT.md` |
| Controller-family attachment | Latest user manuscript reports positive attachment to optimal/nonlinear baselines; inspect amendment A5 and its manifests before repeating a number. Earlier campaigns used different gates/settings and must not be conflated. | `experiments\final_robustness_gating_2026-09-20\results\a5_numbers.json`, `REPRODUCE_ACC2027.md` |
| 3DOF Hover physical results | Preliminary n=1 mission demonstrations, useful context rather than multi-run proof. Hardware requires an on-site operator. | `C:\Research\hover3dof\docs\NENGO_ARMED_HARDWARE_VALIDATION_2026-08-31.md` |
| QCar and pendulum | Integration/virtual-twin work; check each twin's provenance before citing. QCar neuromorphic camera control is planned. | `C:\Research\qcar`, `C:\Research\pendulum` |
| Neuromorphic RL pilot | Newly implemented online TD actor-critic using CMG and comparator activities. Frozen-policy 45-s CMG replay is slightly negative on all five missions: geometric change -1.50% X2, -0.33% CF2. No RL benefit or racing transfer is established. | `experiments\neuromorphic_rl_attitude_2026-09-30\PILOT_REPORT.md` |

The RL replay audit (`experiments\neuromorphic_rl_attitude_2026-09-30\analysis\full45\audit.json`)
passed 10/10 runs at 90,000 plant samples each. It checks bounds and saved
trace/summary consistency, not learning optimality.

The corrected conventional-neuron PES conversion is essential. For native
filtered feature `p=S*a` and connection `Theta=W/S`, use
`eta_N=eta*N/(dt*S^2)` to get normalized direct update
`Delta W=eta(y*-s)a^T`. The archived family code used one fewer factor of
`S`, so its older claims of intrinsic family failure were not a fair
equal-rate comparison. Never reuse the archived Izhikevich loss/effort or
LIF inactivity wording without checking the corrected experiment.

The local stability work establishes bounded internal/interface signals and
conditional local statements. It is not a global tracking stability proof
for moving references, persistent online learning and rotor clipping. Do not
claim global stability or neuromorphic energy savings from these simulations.

## Directory map and ownership

| Location | Purpose |
|---|---|
| `src\gra_control\math3d.py` | Quaternion conventions and mission references. |
| `src\gra_control\platforms\drone.py` | X2/CF2 model paths, mixer, force limits. |
| `src\gra_control\gate.py` | Original direct CMG residual implementation. |
| `models\cf2_rotor_design` | CF2 rotor-level design model. |
| `third_party\mujoco_menagerie` | Imported model assets and licenses. |
| `experiments\nengo_nef_replication_2026-08-29\nengo_cmg.py` | Nengo CMG neuron and online PES decoder. |
| `experiments\nengo_nef_replication_2026-08-29\nengo_neuron_family.py` | Historical family model; old PES scale, keep for provenance. |
| `experiments\nengo_nef_replication_2026-08-29\run_mujoco_nef_baselines.py` | Shared baseline/controller laws including LQR, backstepping, SMC, MPC/NMPC. |
| `experiments\final_robustness_gating_2026-09-20` | Final PD+ff, noise, disturbance, gating and controller-family campaigns. |
| `experiments\neuron_basis_decisive_2026-09-24` | Exact-normalization benchmark and held-out family tuning. |
| `experiments\neuromorphic_rl_attitude_2026-09-30` | New reward-driven attitude pilot; no paper claims yet. |
| `paper\v15_2026-09-29_corrected` | Recent editable manuscript snapshot. |
| `paper\companion_2026-09-30` | Equation-to-code audit. |
| `reproduce` | Numerical claim verifier and claim outputs. |
| `share` | Older advisor archives; rebuild after manuscript changes. |
| `docs` | Historical audits and handoffs; use dates to resolve conflicts. |

Other working roots:

- `C:\Research\hover3dof` — 3DOF Hover HIL, hardware logs, PD/CMG and Nengo GUI.
- `C:\Research\neuromorphic_drone_racing` — seven-gate, four-airframe MuJoCo
  race, classical geometric controller and offline emulated DVS streams.
  `README.md` documents its present limits. The camera is not yet in feedback.
- `C:\Research\pendulum` — QLabs virtual twin.
- `C:\Research\qcar` — virtual twin and planned neuromorphic lane perception.
- `C:\Research\papers\P3_Gate_Residual` — historical source; preserve.
- `D:\NMSU_backups\Backup\00_Research_\Neuromorphic_Embodied_AI\02_Coaxial_TriRotor_Nengo`
  — earlier Nengo inspiration, not current ACC implementation.

## Current RL and racing plan

The relevant research question is recorded precisely in
`experiments\neuromorphic_rl_attitude_2026-09-30\README.md`.
The runner uses the frozen PD+ff plant/actuator path and a new Gaussian
TD(lambda) actor-critic; it compares CMG, LIF, ALIF, LIFRate, Izhikevich,
static paired current and constant activity under the same actor dimensions.
The RL update is driven by a reward-prediction error, **not** the paper's PES
tracking teacher. CMG is a neuron feature generator here, while the current
actor/critic is NumPy outside Nengo. A Nengo graph realization is future work.

Before racing, obtain matched 45-s attitude evaluations, several training
seeds, held-out mission statistics and non-neural controls. Separate a
pure residual interface from the new error-envelope variant. Then test
control transfer in racing with perfect state first. Only afterward connect
the emulated DVS stream to perception and compare latency, observability,
event rates, crashes, gates passed and lap time. The existing racing track
is an original Swift-format approximation; do not claim UZH/Swift track or
performance equivalence.

The proposed dual controller (online gain/self-tuning plus residual) is a
future experiment. Its two learning paths need separate authority bounds,
parameter time scales, an anti-windup rule and ablations (`baseline`,
`self-tuning only`, `residual only`, `dual`). There are no approved dual racing
results as of this handoff.

## Working rules for future agents

- Preserve frozen experiment directories and original outputs. Put new
  protocols in a dated sibling folder. Do not overwrite an advisor package.
- This checkout has substantial pre-existing tracked and untracked changes.
  Inspect `git status` before edits and preserve changes unrelated to the
  current task.
- Record source/model hashes, exact configuration, train/development/held-out
  split, seed, simulation clocks, metrics and exclusions for every new study.
- Run matched baselines with the same plant/mission timing and actuator
  limits. A 15-s Yaw360 is faster than a 45-s Yaw360 and cannot be compared
  directly with the paper table.
- Do not select each mission's RL hyperparameters after seeing its test
  result. Report negative missions and failures.
- Hardware outputs remain zero until a physically present operator confirms
  the safety checklist, tare and kill path. Do not remotely arm the Hover.
- Before sharing a new paper/archive, rerun `reproduce\verify_acc2027_claims.py`
  and audit the current manuscript PDF. Older `share\advisor_2026-09-21_v14`
  predates the corrected neuron-family study.

## Immediate next tasks

1. Decide the next RL training/reward protocol on development missions before
   a 45-s cross-family study. The 2026-09-30 short pilot and frozen-policy
   X2/CF2 45-s replay are complete and negative; preserve those results.
2. Confirm the user's latest Overleaf/Claude source against the supplied
   2026-09-30 PDF; avoid editing the paper based solely on older v15 files.
3. Freeze advisor-facing ACC work independently of RL. The user is preparing
   the October 2 submission; do not insert exploratory RL/racing results into
   this manuscript without a reproducible study.
4. Continue racing and the dual architecture as the next research stage.
