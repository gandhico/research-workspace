# CMG-PES results, explained: concepts, math, and every mission

Companion to the paper (`paper\acc2027_neuromorphic_gate_residual_draft.tex`,
Sections "Full mission-suite validation" and "Physical Hardware Validation").
This document is the deep dive: what a CMG unit actually computes, why it
behaves like a neuron and not just a filter, why the residual beats a
fixed-gain baseline, and a per-mission walkthrough of every plot generated
during the 2026-08-27/28 session — MuJoCo X2 and CF2 across five missions,
and the first-ever physical hardware run on the Quanser 3DOF Hover.

Source code for everything below: `src\gra_control\gate.py` (the CMG unit,
canonical, shared by every platform), `src\gra_control\platforms\drone.py`
(the MuJoCo controller), `scripts\rerun_with_euler_logging.py` and
`scripts\plot_neuron_activity.py` / `scripts\plot_mujoco_drone_results.py`
(the logging and plotting used for every figure here), and
`C:\Research\hover3dof\runners\hover3dof_hil_cmg_control.py` (the hardware
controller).

---

## Part 1 — What a CMG unit computes

### 1.1 The two coupled ODEs

Forget "neuron" for a moment and look directly at `CoupledMembraneGateBank.step()`:

```
x      = clip(alpha * (v - (v_threshold - gamma * r)), -60, 60)
target = sigmoid(x) = 1 / (1 + exp(-x))
dr/dt  = (target - r) / tau_r
gain         = base_gain + gain_scaling * |current|      (if adaptive_conductance)
conductance  = gain * r^2
lambda       = 1/tau + conductance
drive        = v_rest/tau + current/tau + conductance * v_reset
v(t+dt)      = v*exp(-lambda*dt) + (drive/lambda)*(1 - exp(-lambda*dt))
```

Two state variables per unit: membrane potential `v`, gate state `r in [0,1]`.
`v` is driven toward a sigmoid target that depends on `r`; `r`'s own dynamics
depend on whether `v` has crossed a threshold that `r` itself moves
(`v_threshold - gamma*r`). That mutual dependence is the "coupling" in
coupled membrane-gate — each state feeds the other's equation, not just its
input.

The membrane update is the **exact** solution of the linear ODE
`tau*dv/dt = -(v - v_rest) - tau*conductance*(v - v_reset) + current` over
one timestep, not an Euler approximation. This matters because `lambda`
(and therefore the effective time constant) can change by orders of
magnitude within a single step once the gate opens — conductance grows as
`r^2` and `r` can move from 0 to 1 in a few milliseconds (`tau_r = 0.005 s`).
Euler integration would be unstable there; exponential integration isn't.

### 1.2 Why it looks like a real neuron, not a filter

As `r` grows, it does two things to its *own* system simultaneously:
raises its own activation threshold (`-gamma*r` term) and raises the
membrane's decay rate (`conductance ~ r^2`). Both are negative feedback
onto `v`. This is exactly spike-frequency adaptation in real neurons: a
strong sudden input causes a big initial response, which then triggers
self-inhibition that damps the response back down even though the input
hasn't gone away. Every neuron-activity plot in this document shows this:
`v` shoots up toward ~0.9, crosses threshold, `r` snaps open within
milliseconds, and `v` then collapses back to a ~0.1 resting oscillation
*while `r` stays open*. A pure low-pass filter doesn't overshoot and
self-correct like that; the v-r coupling produces it.

### 1.3 Positive/negative branch encoding

Each physical output axis gets **two** CMG units, not one — the current
driving them is `bias + gain*max(normalized, 0)` and
`bias + gain*max(-normalized, 0)`, i.e. rectified halves of a signed
quantity. This is push-pull / ON-OFF encoding — the same principle behind
ON-center/OFF-center retinal ganglion cells in biological vision, and
behind a push-pull amplifier in analog electronics: a leaky integrator
built this way can't run on negative current, so a signed quantity gets
split into two nonnegative populations and the difference is decoded back
out afterward. For a 3-axis drone that's 6 units; for the 4-channel Hover
it would be 8, though the Hover integration in this session drives the
gate through a 3-axis (yaw/pitch/roll) proxy mixed into 4 motor channels
downstream, not through the bank directly.

### 1.4 Decoding: population coding, not per-neuron grading

```
activity = clip(1e5 * r, 0, 1)          # nearly a hard step of r
signed   = clip(W @ activity, -1, 1)    # W: channels x 2*channels, init [I, -I]
neural   = signed * limits
residual = beta * neural                 # "residual" mode
command  = clip(baseline + residual, -limits, limits)
```

`gate_gain = 1e5` means an *individual* unit's `activity` is nearly a hard
binary step of `r` — barely graded at all once the gate opens even
slightly. But `signed` is a **weighted combination across all units**, and
`W` (learned online, bounded to +/-6) can take fractional and negative
values. The graded correction that actually reaches the motors isn't from
any one neuron being graded — it emerges from the population, the same way
a population of near-binary neurons can jointly encode a continuous
quantity in real cortex. This is population coding.

### 1.5 Online-PES: the learning rule

```
target ~ independently-computed error signal (NOT derived from `baseline`)
W += learning_rate * outer(target - signed, activity) - leak * W
```

The delta rule / LMS — the same update behind the original Widrow-Hoff
adaptive filter — applied **online, during the mission itself**, not as
offline training. The critical design point, confirmed the hard way during
tonight's Hover bring-up: `target` must be computed **independently** of
`baseline`. Feed the same signal into both the gate's driving current and
its own supervision target, and the decoder can only learn to rescale a
direction the baseline already picked — mechanically active, zero benefit.
That was bug #4 in the Hover bring-up (Section 5a of `PROGRESS_2026-08-27.md`);
fixing it — mirroring `tau0` (gate drive) vs. `k_error*eq` (learning
target) in the MuJoCo controller — was what made the Hover's residual
functionally useful.

---

## Part 2 — Why residual-on-top beats a fixed gain

The classical baseline (`-kq*eq - kw*omega` for the drones, `K*err` for the
Hover's LQR) is a fixed linear map computed once, offline, around a
nominal model. It cannot notice, during flight, unmodeled coupling,
actuator nonlinearity, or — critically for a *moving* reference — that it
has no feedforward term for the reference's own velocity. A fixed-gain
regulator chasing a moving target carries structural phase lag; that's
linear control theory, not something better tuning removes.

The CMG-PES residual doesn't need a better model. It needs a cheap
supervisory signal and a little authority, and it learns — empirically,
online, within the mission itself — a correction that fills the gap the
fixed gain leaves. This is the same idea as residual learning in ML
(ResNets, boosting): don't relearn the whole controller, learn the
*difference* between what the fixed baseline achieves and what's needed.
That's a much smaller problem, which is why a simple delta rule running for
one 45-second flight sees the improvements below.

---

## Part 3 — Full results

### 3.1 MuJoCo simulation, all five missions, both airframes

Matched configuration: `dt=0.0005s, beta=0.5, learning_rate=8e-4, k_error=8,
k_rate=0, duration=45s`. Mean quaternion error in radians (paper convention).

| Platform | Mission | Classical | CMG-PES | Improvement |
|---|---|---:|---:|---:|
| X2 | yaw360 | 0.075863 | 0.029902 | **+60.6%** |
| X2 | full3 | 0.303275 | 0.131748 | **+56.6%** |
| X2 | hard45 | 0.294082 | 0.138007 | **+53.1%** |
| X2 | hardstep | 0.454528 | 0.359355 | +20.9% |
| X2 | roll | 0.050565 | 0.041785 | +17.4% |
| CF2 | yaw360 | 0.075812 | 0.029870 | **+60.6%** |
| CF2 | full3 | 0.288383 | 0.126476 | **+56.1%** |
| CF2 | hard45 | 0.285449 | 0.132319 | **+53.7%** |
| CF2 | hardstep | 0.426182 | 0.347886 | +18.4% |
| CF2 | roll | 0.051337 | 0.042439 | +17.3% |

`hover` (hold at reference) omitted: both controllers hit exactly 0.000 rad
in noiseless simulation — trivial, no comparative signal.

### 3.2 Physical hardware, Quanser 3DOF Hover

Configuration: `beta=0.4, max_residual_volts=3.0 (of 24V, ~13% authority),
learning_rate=3e-4, k_error=4, k_rate=0, duration=25s, n=1 per cell`. Mean
combined yaw/pitch/roll tracking error in degrees.

| Mission | Classical | CMG-PES | Improvement |
|---|---:|---:|---:|
| yaw360 | 9.696 | 9.013 | **+7.05%** |
| full3 | 12.367 | 12.061 | +2.47% |
| hard45 | 12.954 | 12.795 | +1.23% |

`roll` and `hardstep` not yet attempted on hardware. This configuration was
not the first one tried — a higher-authority, faster-adapting setting
matching the MuJoCo recipe exactly (`beta=0.5, max_residual_volts=4,
learning_rate=8e-4, k_error=8`) caused a genuine hard45 regression (mean
+29% *worse*, peak error 31.8deg -> 49.7deg). See
`PROGRESS_2026-08-27.md` Section 5d for the full six-configuration sweep
that found the setting above.

---

## Part 4 — Per-mission plots

Every plot below is `outputs / error / inputs` (tracking plots) or
`membrane potential / gate state, full mission + zoomed transient` (neuron
plots), generated by `scripts\plot_mujoco_drone_results.py` and
`scripts\plot_neuron_activity.py` from real logged traces — nothing here is
illustrative or synthetic. Paths are relative to `results\plots\`.

### yaw360 — the largest simulated gain (+60.6%)

A smooth 0-360deg ramp. The continuously-moving reference is exactly the
case where the fixed-gain baseline's missing feedforward term shows up as
chronic lag; the residual closes most of it.

- `x2_yaw360_classical_vs_cmg.png`, `cf2_yaw360_classical_vs_cmg.png`
- `x2_yaw360_neuron_activity.png`, `cf2_yaw360_neuron_activity.png`

### full3 — three-axis continuous sinusoid (+56.1-56.6%)

Same mechanism as yaw360 but on all three axes simultaneously. The error
panel shows the CMG-PES curve running visibly below classical through the
full 45s, not just at one point.

- `x2_full3_classical_vs_cmg.png`, `cf2_full3_classical_vs_cmg.png`
- `x2_full3_neuron_activity.png`, `cf2_full3_neuron_activity.png`

### hard45 — the paper's headline case (+53.1-53.7%)

Multi-frequency, multi-axis, moderate-large amplitude — aggressive enough
to expose the fixed gain without being a literal discontinuity. This is
the case reproduced in the paper's original Table (Table~\ref{tab:hard45}).

- `x2_hard45_classical_vs_cmg.png`, `cf2_hard45_classical_vs_cmg.png`
- `x2_hard45_neuron_activity.png`, `cf2_hard45_neuron_activity.png`

### hardstep — mean improves, peak doesn't (+18-21% mean, ~0% peak)

A genuine instantaneous step. The neuron-activity plot for this mission
shows something the others don't: a **second** activation wave right at
the step onset (t=1.0s), on top of the initial mission-start transient —
visible clearly in the zoomed panel. Mean error improves because the
residual helps the settling tail; peak error barely moves because it's set
by actuator rate limits at the step edge itself, common to both
controllers, not by which controller is "smarter."

- `x2_hardstep_classical_vs_cmg.png`, `cf2_hardstep_classical_vs_cmg.png`
- `x2_hardstep_neuron_activity.png`, `cf2_hardstep_neuron_activity.png`

### roll — smallest gain, and why that's expected (+17.3-17.4%)

The gentlest mission (single axis, low amplitude). Classical baseline is
already under 0.05 rad — close to the floor either controller can reach —
so there's little gap left to close. Smallest gain here is a *consistency*
check on the theory above, not a weak result.

- `x2_roll_classical_vs_cmg.png`, `cf2_roll_classical_vs_cmg.png`
- `x2_roll_neuron_activity.png`, `cf2_roll_neuron_activity.png`

### 3DOF Hover hardware — hard45 / full3 / yaw360

Real motor voltages, real encoders, real noise. `outputs` panels show true
per-axis yaw/pitch/roll tracking (the hardware runner logs the actual
state, unlike the drone controller which only logs a scalar quaternion
error — see the note in Part 5). `inputs` panels show all four motor
voltages ([Vf, Vb, Vl, Vr], the verified physical channel order).

- `C:\Research\hover3dof\results\plots\set_e_final\hard45_classical_vs_cmg.png`
- `C:\Research\hover3dof\results\plots\set_e_final\full3_classical_vs_cmg.png`
- `C:\Research\hover3dof\results\plots\set_e_final\yaw360_classical_vs_cmg.png`

---

## Part 5 — Why the gains differ so much, mission to mission

| Mission | Delta | Why |
|---|---|---|
| yaw360 | +60.6% | Continuous ramp, zero baseline feedforward -- chronic lag the residual fills almost entirely |
| full3 | +56.3% | Same mechanism, three axes at once |
| hard45 | +53.4% | Multi-frequency, multi-axis, deliberately "hard" but not discontinuous |
| hardstep | +19.7% mean, ~0% peak | Instantaneous step -- peak is actuator-rate-limited for *any* controller |
| roll | +17.3% | Gentlest mission -- baseline already near its achievable floor |

## Part 6 — Why the Hover hardware shows +1-7%, not +17-61%

Not a failure of the same mechanism -- a materially different authority
regime, by design:

- **Authority**: residual capped at 3V of 24V (~13%) *outside* the safety
  bridge, deliberately, so a first physical-hardware test couldn't send an
  untested full-scale command. MuJoCo's `beta` acts on the *full* torque
  range.
- **Positive-voltage-only**: the Hover cannot apply negative motor
  voltage at all (Eq. 2.5 in the vendor Laboratory Guide) -- an asymmetric
  constraint the drones' torque commands don't have. ~30-38% of
  channel-time already sits at the 0V floor from the baseline alone.
- **Real noise**: quantization, friction, timing jitter -- none of which
  exist in MuJoCo's idealized physics -- dilute the clean error signal the
  delta rule learns from.
- **A stronger baseline**: the vendor's LQR is a genuinely well-tuned,
  near-optimal-for-the-linearization controller -- closer to its own
  achievable floor than the drones' simpler PD-like law, leaving less
  structural gap to exploit.

Given that, +1-7% on constrained real hardware alongside +17-61% on
unconstrained simulation is not a contradiction -- it's the same
architecture in two very different regimes, and it's exactly the
comparison recorded as a limitation/future-work item in the paper
(Section "Physical Hardware Validation," future work: QDrone's full 6-DOF
freedom, then physical CF2/X2, removes this constraint).

## Part 7 — A note on what "outputs" means for each platform

The MuJoCo drone controller (`drone.py`) logs only a scalar quaternion
error (`qerr`), not the raw attitude or reference trajectory, because the
drone state is a full `SO(3)` rotation -- there is no single "the" Euler
angle without picking a convention, and the controller itself never needs
one. `scripts\rerun_with_euler_logging.py` converts both the measured and
reference quaternion to Euler degrees (`quat_to_euler_zyx`, the inverse of
`gra_control.math3d.euler_to_quat`) purely for plotting -- this conversion
is not part of the control loop and does not affect any number in Part 3.
The Hover, by contrast, is a genuine fixed-base gimbal with three physical
joint angles, so its controller already works directly in yaw/pitch/roll --
no conversion needed for its plots.
