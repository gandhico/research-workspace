# From CMG residual RL to dual control and event-camera racing

Status: design proposal only. No dual-control or event-driven closed-loop
racing result is validated by the attitude RL pilot.

## Why CMG could be useful in RL

In the ACC controller, CMG converts recent signed torque demand into six
bounded, stateful activities. PES uses an externally prescribed teacher to
update a linear decoder. In RL there is no such teacher: the learner must
assign credit from task reward, possibly after a gate crossing or recovery.
CMG could help by retaining a compact history of command direction and
duration in `(v,r)`, which a memoryless actor cannot reconstruct from a
single observation. This is a *hypothesis*, not a result. It may fail if the
gate saturates, if the policy already sees enough history, or if a tuned
LIFRate or simple filter provides the same memory more cheaply.

There is a specific gradient obstacle if RL is meant to tune **internal CMG
parameters**. The paper reads `a=clip(G r,0,1)` with `G=10^5`. Its derivative
is `G` only for `0<r<1/G` and zero after saturation. Many opened gates are
latched above `1/G`, so ordinary backpropagation or local eligibility
through the readout has no informative derivative there. The present pilot
therefore freezes the CMG cell and learns only the actor/critic readouts.
Learning `gamma`, `g1`, thresholds or time constants would require a
predeclared graded-activity regime, a justified surrogate derivative, or
another estimator. It would change the studied neuron and must be reported.

The minimum fair RL controls are: identical actor-critic with CMG, tuned
LIFRate, static paired-current, constant activity and a recurrent non-neural
filter. Include LIF, ALIF and Izhikevich after this mechanism screen. Match
activity scale, policy size, reward, training steps, action limits and seeds.
For spiking units report spikes and active fraction; for all arms report
latency, per-step compute, action variation and saturation. CPU runtime is
not a neuromorphic energy measurement.

## Dual actor: self-tuning and residual

Let `a_k` denote six CMG features from the signed demand. Let `Kq0,Kw0` be
the frozen PD gains, `l` the torque box and `h_k` the saturation-opposition
mask. A candidate dual interface is

```text
gq,k = clip(gq,min, gq,max, 1 + alpha_q tanh(Vq a_k))
gw,k = clip(gw,min, gw,max, 1 + alpha_w tanh(Vw a_k))
u0,k(g) = sat_l[-(gq,k Kq0)(2 e_q,k) - (gw,k Kw0)(w_k-wd_k)]
s_k = tanh(Wr a_k)
delta_k = beta l (h_k s_k)
u_k = sat_l[u0,k(g) + delta_k].
```

`Vq,Vw` and `Wr` are separate outputs/parameters. The gain factors must have
declared numerical bounds and slew limits; gains should update more slowly
(for example 10 Hz) than the residual (50 Hz), while plant/CMG states run at
2 kHz. An RL critic can use tracking error, rate error, saturation and CMG
activity to estimate future return. Policy-gradient/TD learning signals are
reward prediction errors, not PES target errors. If an auxiliary PES teacher
is retained, name it a hybrid and ablate it separately.

The interface has exact baseline recovery when `alpha_q=alpha_w=beta=0`.
The bounded-residual proof from the ACC paper alone does not certify the
time-varying gain loop. Its gain/slew limits and closed-loop analysis require
a new proposition, tested with and without rotor saturation and delayed
sensing.

Required ablations, all with the same episode and seed set:

| Arm | Gain adaptation | Residual actor | Purpose |
|---|---|---|---|
| PD+ff | off | off | anchor |
| self-tuning only | on | off | value of gain adaptation |
| residual only | off | on | value of additive correction |
| dual | on | on | interaction, not just sum of gains |
| dual with frozen CMG | on | on | value of neuron state learning/parameters |
| dual with alternative basis | on | on | CMG specificity |

Use development missions Full3/Hard45 and held-out Roll/Hardstep/Yaw360.
Report mission means, peaks, slew/settled Hardstep error, rotor limits,
command variation and episode-return distribution. The dual should not be
declared successful because of an aggregate dominated by Roll/Yaw floors.

## Transfer ladder to the racing project

The current race code is `C:\Research\neuromorphic_drone_racing`. It has
four vehicle models, geometric control and an offline DVS emulator. Before
coupling everything, use this sequence:

1. **Attitude gate:** 45-s X2/CF2 missions with paired seeds. Decide whether
   residual RL or dual RL adds benefit under noise/disturbance and how much
   actuator demand it costs.
2. **Perfect-state race:** adapt the same bounded action to the race
   controller's body-rate/torque interface, one vehicle first. Measure gate
   completion, collisions, lap time, path error, action limits and compute.
   Preserve the original race controller as the baseline.
3. **Observation study:** replay exactly the same race trajectories through
   RGB and emulated DVS. Train an event estimator for gate-relative pose or
   a compact state, quantify timestamp rate, dropped events, brightness
   changes and estimator latency. The current renderer uses 500-Hz frames
   with interpolated sub-millisecond event times, so it is not a physical
   event camera.
4. **Closed-loop event control:** replace only the gate/state observation
   source, retaining the trained control policy first. Then jointly train
   perception and control only if the modular interface is stable. Compare
   against identical policy capacity using RGB/state observations.
5. **Heterogeneous fleet:** after X2/CF2, extend to Y6 and Omnicopter with
   geometry-specific allocation and common normalized policy inputs.

The existing seven-gate track approximates the *format* of UZH Swift racing;
its geometry and 101-m lap are not Swift's 75-m track. Any performance
comparison with [Swift](https://www.nature.com/articles/s41586-023-06419-4)
requires matching course, sensing, vehicle limits and metric definitions.

## Decision after the present pilot

The six-episode X2 pilot and the frozen-policy 45-s X2/CF2 replays are
negative; they verify the software interface, not the CMG-in-RL hypothesis.
Do not enlarge the ACC paper with them. Before a
full family matrix, lock one improved RL algorithm and training budget on
development missions, then test held-out missions and platform transfer.
PPO with a recurrent state encoder would be a standard deep-RL reference;
the local TD actor-critic here is the interpretable neuromorphic candidate.
Those are different algorithms and should be compared at equal simulator
steps and observation/action budgets.

The nominal `rho=3` baseline is already near the tracking floor on Roll and
Yaw360. Random residual exploration therefore creates a strong downside and
little immediate upside. The next development run should train on a declared
model mismatch or repeated torque-burst distribution while retaining a
nominal held-out test. Two defensible learning routes are (a) a stronger
standard RL policy such as PPO with the same bounded residual interface, and
(b) PES imitation pretraining followed by RL fine-tuning. Route (b) is a
**PES-bootstrapped hybrid**, not a pure reward-only RL result. The fair
comparison includes the PES-only teacher policy and the same simulation
sample budget after pretraining.
