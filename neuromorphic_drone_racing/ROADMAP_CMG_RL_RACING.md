# CMG reinforcement learning for drone racing — roadmap (2026-09-30)

Goal (Gandhi, 2026-09-30): not to beat model-based controllers, but to show that a **CMG-based RL policy can learn
and complete the race**, trained the way UZH trained its racing policies, then scale to **perception with the
emulated DVS in MuJoCo** (event + IMU fusion), and benchmark model-based, model-free RL and CMG-RL, with the dual
(self-tuning + residual) controller as the hybrid high-level variant.

## 1. What UZH did, and why our pilots failed

**Verified** from Song, Steinweg, Kaufmann, Scaramuzza, *Autonomous Drone Racing with Deep RL*, IROS 2021
(rpg.ifi.uzh.ch/docs/IROS21_Yunlong.pdf):

| Ingredient | UZH 2021 |
|---|---|
| Learner | PPO, policy 2 x 128 tanh, tanh output |
| Observation | velocity, acceleration, rotation matrix, body rates (18-D) + next gates in spherical coordinates and gate-normal angle (2 future gates by default), z-scored |
| Action | four rotor thrusts |
| Reward | progress along gate-centre segments `s(p_t) - s(p_{t-1})`; optional safety term near gate edges; body-rate penalty; crash penalty `-min((d_g/w_g)^2, 20)` |
| Sampling | vectorized Flightmare, up to 100 parallel quadrotors, up to **25,000 environment interactions/s** |
| Key tricks | **distributed initialization** (start in hover around all path segments, later from previous trajectories); random-track curriculum adapted to crash ratio |
| Result | lap times within 5.2% of optimization-based time-optimal planning |

Swift (Kaufmann et al., *Nature* 2023) extended this with onboard perception. Full text was not accessible in this
session (publisher login, PMC CAPTCHA); **the following is from memory and must be checked before citing**:
collective thrust + body-rate action; observation with platform state, relative gate corners and previous action;
reward with progress, a perception-aware term keeping the camera on the next gate, command smoothness and crash
terms; PPO in simulation; perception = VIO fused with a learned gate-corner detector in a Kalman filter; residual
dynamics/perception models identified from real flights.

UZH's own survey (Hanover et al., T-RO 2024) states that event cameras in drone racing "are yet to be explored",
so event-driven racing with a neuromorphic policy is an open, publishable direction.

**Why our pilots failed.** The direct pilot trained each arm on 600 teacher samples + 1,200 PPO decisions (24 s of
flight); UZH-scale training is 10^7-10^8 interactions. Our MuJoCo racing environment with 32 CMG cells runs about
9 decisions/s. A feasibility probe (batched torch rigid body + rate loop + rotor clipping + 32 CMG cells per drone)
reaches **~19,000 decisions/s on the CPU at 1,024 drones** (8,300 at 256; GPU 1,100/s, launch-bound on this laptop
A500). That closes the gap by about 2,000x. The dual pilot failed for a different reason: a reward dominated by
action-insensitive terms (`dual_rl_benchmark_2026_09_30/PILOT_REPORT.md`).

## 2. Architecture

```text
TRAINING (batched torch, CPU, ~1k drones)                VALIDATION (full MuJoCo, our race world)
  rigid body + thrust/body-rate inner loop                  same policy, frozen; sim-to-sim transfer
  rotor limits & allocation identified from the MJCF        X2 -> CF2 -> Y6 (Omnicopter needs 6-D wrench)
  analytic gates: pass / collision, progress reward          gates, collisions, lap time vs geometric baseline
  CMG cells batched (same update as Nengo CMG)
        observation o_t ──► current encoder ──► CMG (v, r, events) ──► [o_t, CMG features] ──► actor/critic (PPO)
                                                                                         └──► thrust + body rates
PERCEPTION (stage 3)
  MuJoCo dvs camera ──► event stream ──► event gate detector (CMG/spiking encoder) ──┐
  IMU (gyro, accel) ─────────────────────────────────────────────────────────────────┴─► EKF ──► policy observation
```

## 3. Stages and acceptance gates

| Stage | Content | Accept when |
|---|---|---|
| **S0 Simulator** | Batched trainer environment with parameters extracted from the MuJoCo X2/CF2 models; analytic gates and progress reward (UZH); batched CMG cells | (a) open-loop command replay matches MuJoCo trajectories within a declared tolerance; (b) CMG batch matches `cmg_cells.py` to machine precision; (c) >= 10,000 decisions/s |
| **S1 Learn to race (state-based)** | UZH 2021 recipe: progress reward, distributed initialization, PPO; arms MLP, CMG-graded features, GRU (memory control), CMG-spiking (reset variant) | policy completes full laps in >= 3 of 3 seeds in the batched sim, then completes laps in **full MuJoCo** (sim-to-sim) |
| **S2 Benchmark** | Model-based (geometric baseline; optional MPC), model-free RL (MLP, GRU), CMG-RL, dual hybrid (fixed reward: tracking relative to the teacher) | Table: completion, crash rate, lap time, robustness (gust, mass/inertia randomization), action smoothness, compute; >= 3 seeds |
| **S3 Perception** | DVS in the loop: fast geometric event generator for training (gate edges projected into the `dvs` camera), validated against the rendered `event_camera.py`; event gate detector + IMU EKF; perfect-state vs estimated-state policy | estimated-state policy completes laps; error budget of the estimator reported; event rate and latency logged |
| **S4 Fleet / tracks** | CF2, Y6; random-track curriculum; held-out tracks | completion on held-out tracks |

## 3b. Progress log

**2026-09-30, S0 passed (X2)** — `uzh_style_rl_2026_09_30/` (`extract_x2.py`, `vec_race.py`, `validate_sim.py`,
`results/s0_validation.json`):

| Test against the MuJoCo race world | Result |
|---|---|
| One 20-ms decision from recorded states (600 decisions) | position 0.003 mm mean / 0.07 mm max; attitude 0.007 / 0.16 deg; rate 0.005 / 0.08 rad/s |
| Open-loop replay of the 12-s command sequence (no feedback) | 0.31 m drift after 12 s |
| Gate passes along the reference flight | 4 = 4 |
| Batched CMG cells vs `cmg_cells.py` (graded, reset_spike) | 1e-15 |
| Throughput, 1,024 drones x 32 CMG cells | 15,229 decisions/s |

Not yet validated: crash detection (vehicle approximated by a 0.32-m sphere vs MuJoCo's real geoms); checked on
crashing flights once trained policies exist. S1 training started: `train_ppo.py` (arms mlp / cmg / cmg_spike),
transfer test `export_policy.py` + `mujoco_eval.py`.

**2026-09-30 night, S1 attempt 1 failed: reward hacking (all arms, MLP included).** After 6-9M steps every episode
ended in failure (ep_gates 0.02). `diagnose_crashes.py`: the analytic crash check gives 0 false crashes on the
teacher's MuJoCo flight; trained policies dash at ~40 m/s and leave the 30-m arena in ~1.5 s (1,764 / 2,048 episodes
"outside", 26 m from the gate). Cause: v1 progress = projection on the gate-to-gate line keeps paying past the gate
(~23 m gained > 10 crash penalty). Fix (v2, default): progress = decrease of the distance to the next gate centre
(Swift-style; from memory, verify before citing), bounded at the gate. v1 runs archived in
`results/archive_v1_reward/`. Added the exact-ACC CMG arm `cmg_acc` (parity with ACC `gate.py` 1e-14,
`results/cmg_acc_parity.json`; ACC paired currents, readout clip(1e5 r): ~90% of features saturated under drive —
a property of the ACC latch regime to report, not a bug).

**Reward v2 -> hover trap; v3 adopted.** 5M-step pilots on v2 (mlp, cmg_acc): both learned to survive and then
collapsed to hovering (eval: 0 gates, no crash; MLP train gates/episode 0.05). Reward breakdown
(`reward_breakdown.py`): smoothness + rate penalties make hovering cheaper than risking the -10 crash. 5M-step MLP
sweep: A = v2 + gate-pass bonus 10 -> 0.40 gates/episode, eval passes gate 1 (at 3.3M, 4.6M, 5M); B = A + crash 5 +
w_smooth 0.001 -> 0.35-0.46 gates/episode, eval 0 gates. **v3 = A** (single change from v2). Neither had plateaued at
5M. 20M-step runs on v3: `v3_{mlp,cmg_acc,hyperlif_spike}_s1`.

**2026-10-01: first full lap, MLP control, v3, seed 1.** Batched-sim evals: 4 gates from 8.5M (stalled at the
split-S: gates 3 (6,6,5.4, yaw 180) and 4 directly below (6,6,1.8, yaw 0); `where_stuck.py` showed the policy
hovering 1.74 m from gate 4 on the exit side - a local optimum of distance progress), 6 gates at 14.4M, first lap
15.7M (18.16 s), laps on every eval from 17.0M, 2 laps / 14 gates / no crash at 19.7M and 20M (first lap 15.1 s).
**MuJoCo transfer (`mujoco_eval.py`, frozen numpy policy, real contacts): lap completed, 7/7 gates in order,
0 collisions, 14.98 s** (gate times 1.60, 3.24, 4.38, 5.98, 11.70, 13.12, 14.98 s; split-S 3->4 takes 5.7 s; mean
rotor saturation 0.29). Batched-sim gate times agree within 0.1 s. Seed 1 only; S1 needs 3 seeds and the CMG/HyperLIF
arms. v4 (v3 + 5-s stall termination) queued as the split-S comparison.

**cmg_acc v3 seed 1 (20M):** stuck at the split-S like the MLP was at 8.5-14M - evals 3 gates, no crash, from 17M on;
train 1.46 gates/episode at 20M (MLP reached that at ~9.8M); features ~90% saturated throughout. MuJoCo transfer: 3
gates, 0 collisions, time limit; gate times 1.18/2.52/7.04 s vs batched 1.20/2.54/7.06 s (closed-loop check of the
ACC `gate.py` neuron path). Learns the same skills as the MLP but ~8M steps slower on this budget. v4 run started.

**Reward v4 = v3 + 5-s stall termination (adopted for all arms).** MLP seed 1: first lap 9.8M (v3: 15.7M), 2 clean
laps from 13.1M (v3: 19.7M), final eval 2 laps, first lap 9.5 s (v3: 15.1 s); split-S 4->5 now 1.36 s (v3: 5.7 s).
**MuJoCo transfer: lap, 7/7 gates, 0 collisions, 9.42 s** (gate times 1.22, 2.70, 3.92, 5.10, 6.40, 7.42, 9.42 s;
batched within 0.08 s; rotor saturation 0.38). Running on v4: cmg_acc, hyperlif_spike (seed 1).

**FROZEN 2026-10-01** — see `uzh_style_rl_2026_09_30/FROZEN_2026-10-01.md` (seed-1 results, conclusions, flags, hashes).
Summary: MLP laps in MuJoCo (9.42 s, v4); from random starts HyperLIF spiking 2.5–3.0 gates > exact-ACC CMG 0.8; CMG latches
(81–90% saturated). Stopped here pending Gandhi.

## 3c. Two CMG research lines (Gandhi, 2026-09-30): spiking and non-spiking

Every RL stage carries both lines, to learn how well each learns and under what conditions. The 2x2 design
separates the two things that change when the cell "spikes":

| CMG dynamics | Gate readout | Event readout |
|---|---|---|
| Original continuous (ACC neuron) | `cmg` — **non-spiking line** | `cmg_crossing` (upward crossings, no reset) |
| NEW reset variant (CMG-LIF hybrid) | `cmg_reset_gate` | `cmg_spike` — **spiking line** |

All four batched modes match `cmg_cells.py` to 1e-15 (`results/cmg_modes_check.json`). Conditions logged every PPO
update: event rate per unit, fraction of active units, mean feature, fraction of features saturated (> 0.99) or
silent (< 0.01). First observations: under fast-varying random currents the original cell's crossing readout fires
~65 Hz (Codex's constant-current calibration gave zero sustained crossings, so this readout depends on input
variability); the non-spiking gate averages 0.95 (near saturation); under real flight input the spiking cell fires
~18 Hz with 69% of units active and ~55% of features near silent. Candidate conditions to study: encoder current
operating point, neural step vs 20-ms policy step, event filter time constant, unit count, input variability.

### Coherence of the spiking line with the established Nengo HyperLIF (2026-09-30)

The established HyperLIF (`papers/P2_HyperLIF_Nengo/src/neurons/nengo_hyperlif.py`) spikes through its own gate
conductance, not a hard reset. Codex's `cmg_spike` (subtractive reset, ad-hoc preset) is therefore **not** HyperLIF;
its run was stopped and is archived as a non-coherent variant. The spiking line is now `hyperlif_spike`
(`vec_race.HyperLIFBatch`), checked in `check_hyperlif_spiking.py` / `results/hyperlif_coherence.json`:
step-by-step parity with P2's neuron (voltage 8e-14, gate 6e-13, identical spike counts); firing-rate curve equal to
P2's recorded sweep at 13 of 14 currents J = 1.3-2.6 (the one-spike difference at J = 1.5 is P2's Julia-Euler sweep vs
its Nengo exact step). At the RL step 5e-4 the spiking window shifts (onset 1.4, block 2.2), so the line runs at
P2's dt = 1e-4. Readout: P2's 20-ms exponential synapse. Controls: `hyperlif_gate` (same dynamics, gate readout).
Open: the non-spiking `cmg` arm uses Codex's retuned preset (gate gain 1, alpha 12, ...), not the ACC CMG parameters.

## 4. Claim boundary

Exploratory research line, **not** in the ACC 2027 manuscript. "CMG learns to race" requires S1 in full MuJoCo
with several seeds. No Swift lap-time comparison (different track, vehicles, sensing). CPU time is not
neuromorphic energy. The reset/spiking CMG is a new hybrid model and must be labelled as such.
