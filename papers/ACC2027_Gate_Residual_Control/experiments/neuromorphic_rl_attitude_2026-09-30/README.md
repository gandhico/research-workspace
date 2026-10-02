# Neuromorphic RL attitude pilot (2026-09-30)

This is a **new exploratory study**, separate from the ACC 2027 manuscript's
online PES results. It tests whether the continuous coupled membrane-gate
(CMG) state is a useful feature basis for reward-driven learning. The current
paper PDF is `C:\Users\gandhico\Downloads\Online_PES_Decoder_HyperLIF_Residual_Control___Quaternion_Tracking (29).pdf`.

## Research question

> Under the same MuJoCo attitude missions, PD with desired-rate feedforward,
> torque limits, rotor allocation, observation vector, actor/critic dimensions,
> reward, policy clock, training budget and held-out protocol, does a policy
> driven by CMG activity learn a safer or more effective bounded residual than
> policies driven by LIF, ALIF, LIFRate, Izhikevich, instantaneous paired
> current, or constant activity? Does any benefit persist under held-out
> missions, platform transfer, noise or disturbances?

The causal question is about the **activity basis**, not yet about conductance
modulation. A positive result must survive the non-neural and threshold-aware
controls. A negative result is useful: it identifies where a PES teacher,
reward design, policy memory or training budget matters.

## Exact shared plant and controller interface

The runner imports `AdvancedBaseline` from the archived Nengo/MuJoCo campaign
and uses its final paper settings: `rho=3`, `zeta=0.95`, `left-neg`
desired-rate feedforward, and no model feedforward. At each MuJoCo step
(`dt=0.0005 s`), it reads the passive quaternion and body rate, computes the
shortest-path error, and requests `u0`. The paper's 4x4 inverse rotor
allocation, collective height loop and rotor clipping are retained. X2 uses
its model rotor ceiling; CF2-rotor uses the paper's declared 1.5x ceiling.
The same output saturation-opposition gate acts after the learned residual.

The policy receives the same physical feedback as the PD path plus six basis
activities; it receives no true future state, race gate information or camera.
The feedback is uncorrupted in this first pilot. During training the actor
acts every 20 ms and holds its bounded action; plant and neuron states still
advance every 0.5 ms. Evaluation is deterministic and uses the trained actor.

## Learning rule and distinction from PES

For activity `a_k in [0,1]^6`, normalized torque `n_k=u0/l`, shortest-path
error `e_k`, and rate error `w_k-wd_k`, the 16-dimensional feature is

```text
phi_k = [1, a_k-0.5, clip(e_k/0.1,-2,2),
         clip(w_k-wd_k,-2,2), clip(n_k,-1,1)].
```

The actor samples latent `z_k ~ N(mu_k, sigma^2 I)` with
`mu_k=tanh(A phi_k)`, `sigma=0.08`; the control action is
`b_k=clip(z_k,-1,1)`. Its torque residual is

```text
delta_k = beta l (g(theta_k) b_k),
u_k = sat_l(u0_k + h_k delta_k),
```

where `h_k` is the paper's componentwise saturation-opposition mask. The
first direct pilot uses `g=1`. The separately labeled error-envelope pilot
uses `g(theta)=min(theta/0.03,1)`, a **new RL design change** that reduces
residual authority near a tracking error floor. It is not part of the paper's
reported controller.
In this noise-free pilot, `theta` is computed from the same exact quaternion
available to PD. A later noisy test must compute the envelope from the
corrupted feedback quaternion and retain true state only for scoring;
otherwise it would give the RL arm an oracle signal.

The per-plant-step reward is

```text
r = -min(25,1000 theta^2) - c_a mean(b^2) - 0.05 1{any rotor saturated}.
```

Rewards are averaged over each 20-ms policy interval. A linear critic
`V_c(phi)=c^T phi` gives
`d_k=r_k+gamma V_c(phi_{k+1})-V_c(phi_k)` with `gamma=0.98`.
Actor and critic have eligibility traces with `lambda=0.90`; the Gaussian
score `grad_A log pi(z|phi)` is multiplied by the TD error. Step and weight
clipping are disclosed in `run_rl.py`. This is a small **online TD(lambda)
actor-critic**, not PPO, SAC, PES, or backpropagation through CMG dynamics.
It is an RL *pilot*, not a standard deep-RL benchmark.

For CMG, the runner directly calls the existing Nengo
`CoupledMembraneGate.step` neuron implementation, including membrane and gate
integration. The actor/critic is NumPy code outside a Nengo graph. LIF,
ALIF, LIFRate and Izhikevich likewise use Nengo neuron `step` methods, then
the archived output filter/calibration. The tuned bias/gain/filter choices
are frozen from the **separate PES development split**. They were not tuned
on this RL pilot. The original PES decoder `W` is absent from the RL arms.

## Protocol and interpretation

1. Train on 15-s X2 Full3 and Hard45 episodes in alternating order. For a
   platform-specific policy, do the same on that platform. Choose one
   training budget and seed set before the cross-family comparison.
2. Freeze the actor. Evaluate each of Roll, Full3, Hard45, Hardstep and
   Yaw360 for **45 s**, with the same seed/configuration across all bases.
   Roll, Hardstep and Yaw360 are held out; Full3 and Hard45 are development
   missions. Report these groups separately.
3. Evaluate a matched zero-residual PD+ff arm. Report mean and maximum
   true-state quaternion-angle error, normalized realized residual RMS,
   rotor saturation fraction and gate-blocked fraction. Use paired seeds and
   dispersion before any inferential statement.
4. Add noise and matched torque bursts in a preregistered second stage;
   then train on one model and evaluate the other with the same policy.
5. Only after an attitude policy has credible held-out improvement, attach it
   to `C:\Research\neuromorphic_drone_racing`. Start with perfect-state racing
   so control transfer is isolated. Then make the emulated DVS event stream
   drive an explicit perception network, log latency and event rates, and
   compare RGB/state/event observation budgets fairly.

The racing project currently has four airframes, a seven-gate approximate
track and offline emulated DVS. Its camera is **not in the control loop**.
Swift/UZH is inspiration for the racing test design, not a performance
benchmark for this pilot: [Kaufmann et al., Nature 2023](https://www.nature.com/articles/s41586-023-06419-4).
For spiking continuous-control and local eligibility-learning context see
[Tang et al., CoRL/PMLR](https://proceedings.mlr.press/v155/tang21a.html) and
[Bellec et al., Nature Communications 2020](https://www.nature.com/articles/s41467-020-17236-y).

## Reproduction

Use the existing project environment:

```powershell
$root = 'C:\Research\papers\ACC2027_Gate_Residual_Control'
$py = "$root\.venv\Scripts\python.exe"
$rl = "$root\experiments\neuromorphic_rl_attitude_2026-09-30"

& $py "$rl\run_rl.py" --platform x2 --family cmg --mode baseline `
  --eval-duration 45 --output "$rl\results\full_x2_baseline"

& $py "$rl\run_rl.py" --platform x2 --family cmg --mode train-eval `
  --train-episodes 12 --train-duration 15 --eval-duration 45 `
  --output "$rl\results\full_x2_cmg_direct"

# The new error-envelope variant must have its own label and baseline match.
& $py "$rl\run_rl.py" --platform x2 --family cmg --mode train-eval `
  --train-episodes 12 --train-duration 15 --eval-duration 45 `
  --error-envelope-rad 0.03 --action-penalty 0.3 `
  --output "$rl\results\full_x2_cmg_envelope"
```

Repeat with `--platform cf2-rotor`; the runner selects `beta=.2` and the
paper's 1.5x rotor ceiling automatically. Replace `cmg` by any name in
`--family {cmg,lif,alif,lifrate,izhikevich,paired-current,constant}` for a
matched basis run. Run at least three training seeds and paired evaluation
seeds before comparing families. `--mode eval --checkpoint PATH` replays a
frozen policy and rejects a platform/family mismatch.

To replay an already trained policy on the exact 45-s paper missions:

```powershell
& $py "$rl\run_rl.py" --platform x2 --family cmg --mode eval `
  --checkpoint "$rl\results\pilot_x2_cmg_envelope\policy.npz" `
  --eval-duration 45 --error-envelope-rad 0.03 --action-penalty 0.3 `
  --output "$rl\results\full45_x2_cmg_envelope"
& $py "$rl\summarize_full45.py"
```

The full-45 summary script uses the archived `pdff_rho3` rows in
`experiments\final_robustness_gating_2026-09-20\results\final_nominal.csv`.

Every evaluation folder contains `summary.json`, a 50-Hz `policy_trace.csv`
and a `full_rate_trace.npz` with activity, neuron states, true quaternion
error, baseline and applied torque, rotor saturation and gate masks at the
2-kHz plant clock. `training.json`, `policy.npz` and `manifest.json` capture
learning history, weights, configuration, versions and source hashes.

## First smoke/pilot status

- A 2-s X2 Full3 baseline from this runner matched the frozen paper runner:
  mean error differed by `4.2e-17 rad` after matching its time loop.
- The initial X2 6-episode, 10-s-training / 15-s-evaluation **direct RL**
  pilot was worse than PD+ff on all five short evaluations. This is not a
  paper result and must not be extrapolated to the 45-s mission table.
- The separately labeled error-envelope pilot reduced the Roll error floor
  but did not beat the matched PD+ff baseline on any X2 short evaluation
  (five-mission geometric change `-2.19%`). The corresponding CF2 short
  pilot was close to baseline but negative on all five (`-0.43%`).
- The 15-s yaw360 reference is three times faster than the paper's 45-s
  yaw360 reference. Do not compare any short-pilot value with Table II.
- Replaying the frozen six-episode CMG envelope policy on the actual 45-s
  missions gave a five-mission geometric change of `-1.50%` (X2) and
  `-0.33%` (CF2) versus the archived tuned PD+ff baseline. Every individual
  mission was slightly negative. See `PILOT_REPORT.md` and
  `analysis/full45/comparison.md`.

The pilot establishes that CMG activity can feed a reward-driven actor and
that the existing plant/controller interface is reusable. It does **not**
yet establish that CMG improves RL, beats conventional bases, or transfers
to racing. Keep it outside the imminent ACC manuscript until those tests
are complete.
