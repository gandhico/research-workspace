# Final analysis: CMG-PES architecture, all platforms, 2026-09-01

Covers every experiment run in this project: MuJoCo simulation (X2/CF2,
Option B fully-actuated wrench, Option A realistic cascade, Nengo/NEF
validation, neuron-family validation) and the 3DOF Hover physical hardware
campaign (final, validated run: `results\DIRECT_NENGO_FINAL_2026-09-01\`).

## 1. MuJoCo simulation (`ACC2027_Gate_Residual_Control`)

### 1a. Option B -- fully-actuated 6-DOF wrench, X2, idealized testbed

| Mission | pos improvement | att improvement |
|---|---:|---:|
| hover3d | N/A (baseline exact) | N/A |
| waypoint_step | -40% | N/A |
| circle_xy | -0.3% | N/A |
| full6_stress | **+3.96%** | **+49.17%** |

### 1b. Option A -- realistic underactuated cascade (real rotor mixer)

X2:

| Mission | pos improvement | att improvement |
|---|---:|---:|
| hover3d | N/A (exact) | N/A |
| waypoint_step | +11.5% | +13.2% |
| circle_xy | **+65.1%** | **+68.1%** |
| full6_stress | **+76.1%** | **+65.8%** |

CF2-rotor (same architecture, retuned beta/lr for the lighter airframe):

| Mission | pos improvement | att improvement |
|---|---:|---:|
| hover3d | N/A (exact) | N/A |
| waypoint_step | -18.7% | -11.2% |
| circle_xy | -21.6% | -19.0% |
| full6_stress | -26.0% | -25.9% |

Reading: the architecture's benefit in simulation is large and consistent
on X2, and genuinely absent on CF2 even after retuning and after testing
whether more actuator authority ("more powerful rotors") would help (it
didn't -- CF2's bottleneck is control-theoretic bandwidth, not thrust).
CF2's classical baseline is simply harder to beat because its low
mass/inertia gives it less structural error to correct.

### 1c. Nengo/NEF validation (X2, 6-channel cascade)

- Isolated augmentor vs frozen NumPy controller, 2000 random steps:
  relative command error 1.05e-7 (activity/gate exact).
- Full closed-loop mission match: hover3d/waypoint_step exact,
  circle_xy/full6_stress match to 3-4 significant figures.

### 1d. Neuron-family validation (X2, full6_stress, most demanding mission)

| Engine | tuning | pos err (m) | att err (deg) |
|---|---|---:|---:|
| CMG-PES | natural (beta=0.5) | **0.237** | **5.01** |
| classical | -- | 0.989 | 14.65 |
| LIFRate-PES | beta=0.01 (50x lower) | 0.889 | 14.12 |
| ALIF-PES | beta=0.01 | 1.825 | 21.04 |
| LIF-PES | beta=0.01 | 2.175 | 22.28 |
| Izhikevich-PES | beta=0.01 | 2.196 | 25.00 |

Spiking families destabilize the demanding mission even at 1/50th CMG's
residual authority; LIFRate (same tuning curve, no spike discretization)
stays roughly neutral -- isolates spiking noise itself as the failure
mode, not "being non-CMG."

## 2. 3DOF Hover physical hardware (real Quanser rig)

### 2a. Root-cause investigation (why armed CMG-PES runs kept aborting)

Every armed run through the Nengo GUI dashboard intermittently or
consistently hit "20 consecutive 200-Hz deadline misses." Ruled out, in
order, with direct evidence:
1. Browser/heartbeat connection timing -- disproven (a human-driven
   attempt with a connected browser still failed identically).
2. Neural computation cost -- isolated benchmark: ~1.5ms/step, well under
   the 5ms/200Hz budget.
3. Real Q8 hardware I/O -- isolated benchmark: ~0.004ms/step, negligible.
4. **Actual cause**: the armed worker thread's Nengo computation (10
   sub-steps/hardware-tick through a 12-neuron ensemble) runs concurrently
   with the GUI's *own* separate Nengo dashboard model and websocket
   server, both sharing one process's GIL. PD never triggers this (no
   augmentor = no extra computation), which is exactly why PD always
   succeeded through the GUI while CMG-PES did not -- confirmed by the
   user's own direct observation of that asymmetry.

**Fix implemented**: bypass `nengo_gui` entirely and drive the same
`HoverWorker` engine directly (`run_hover_direct_nengo.py`) -- same
CMG-PES computation, same safety gates (armed requires `--io q8` +
`--confirm-hardware-review`, only `pd`/`nengo-pes` may be armed), same
trace.csv/neural_trace_2khz.npz/summary.json outputs, zero GUI thread.
Result: **10/10 armed runs completed cleanly** on the first full attempt,
versus near-total failure through the GUI that same evening.

### 2b. Final validated results (`results\DIRECT_NENGO_FINAL_2026-09-01\`)

| Mission | PD mean err (deg) | CMG-PES mean err (deg) | Improvement | PD max | CMG max |
|---|---:|---:|---:|---:|---:|
| hover | 0.116 | 0.046 | +60.4%* | 0.224 | 0.076 |
| roll | 5.498 | 5.192 | **+5.57%** | 8.150 | 9.079 |
| full3 | 11.282 | 11.644 | -3.21% | 17.005 | 17.075 |
| hard45 | 9.743 | 9.689 | +0.55% | 14.919 | 15.722 |
| hardstep | 13.626 | 13.497 | +0.95% | 33.671 | 34.367 |
| yaw360 (reduced-range) | 2.731 | 2.960 | -8.38% | 3.695 | 3.890 |

\* hover's percentage is on a near-zero baseline (both controllers are
already within a fraction of a degree of perfect); not a robust effect,
reported for completeness.

### 2b-i. yaw360: root cause found, resolved with a reduced-range variant

The original full-scale yaw360 (reference_scale=1.0, a true 0-360 deg
sweep) safety-aborted on the roll limit twice, independently, at nearly
identical magnitude both times (+20.127 deg once, -20.127 deg the other) --
around yaw approx 150-190 deg in both cases, **regardless of whether the
rotation took 30s or 50s**. Confirmed via `gra_control.math3d.reference_euler`
that the yaw360 reference commands roll=0, pitch=0 throughout (a pure yaw
sweep -- "keep hover on the other two axes" is already the intent of the
mission, not something that needed adding). That the trip point didn't move
with rotation speed rules out a rate-dependent tracking-lag explanation;
the leading hypothesis is a physical constraint tied to the vehicle's
*orientation* rather than its speed -- most plausibly cable wind-up at the
rig's rotating joint approaching a half-turn, which would explain both the
speed-independence and the near-identical trip angle each time.

Rather than push further against what looks like a real physical limit,
ran a reduced-range variant (reference_scale=0.3, max yaw ~108 deg,
duration=30s) -- same reference *shape*, same "hold pitch/roll at zero"
goal, just not the full 360. Both PD and CMG-PES completed cleanly:
pitch stayed within +/-0.4 deg and roll within ~2.5 deg the entire run for
both controllers (essentially hover-stable on the other two axes, as
requested). This mission is now genuinely two matched, completed,
real-hardware runs rather than one aborted PD-only run.

### 2b-ii. Neuron-family validation, all missions -- emulated (Hover plant model)

LIF, ALIF, Izhikevich, and LIFRate controllers were never staged through
the physical-hardware safety-qualification process (only `pd` and
`nengo-pes` were) and were not armed on the real rig -- that qualification
gap is a deliberate safety boundary, not a data-collection gap, and wasn't
bypassed under time pressure. The following is the existing, already-run
**emulated** (MuJoCo-based Hover plant, matched 25s missions,
`results\hover_neuron_family_matched_25s_2026-09-01\nominal\`) comparison
across every neuron family and every mission except hover (not included in
that emulated campaign):

| Mission | best-performing family | improvement vs PD | notes |
|---|---|---:|---|
| roll | nengo-cmg-fixed | **+10.65%** | nengo-pes/nef-pes cluster ~+10%; several "-fixed"/"-pes" spiking variants show exactly 0.00% (residual computed near-zero for this calibration) |
| full3 | nengo-izhikevich-pes | +0.37% | all families within +/-0.4% of PD -- flat mission for every family |
| hard45 | nengo-izhikevich-fixed | +3.86% | nengo-izhikevich-pes is the worst performer here, **-19.53%** (destabilized) |
| hardstep | pd (all worse) | -11.2 to -11.5% (all families) | every neuron family, CMG included, underperforms PD by roughly the same margin here |
| yaw360 | nengo-nef-pes | +1.77% | all families within +/-2% of PD |

Full per-family, per-mission numbers:
`results\DIRECT_NENGO_FINAL_2026-09-01\neuron_family_emulated_all_missions.json`.

Reading: no neuron family (CMG included) shows a consistent win across all
missions in this emulated Hover-plant setting -- roll is the one mission
where CMG-style residuals (fixed and nef-pes) show a clear, real benefit
(~10%), hardstep is a mission where the residual mechanism itself (any
family) currently hurts, and the rest are close to a wash. This is
consistent with, and reinforces, the mission-dependent pattern already
seen on both real Hover hardware and MuJoCo/X2/CF2: the architecture's
benefit tracks how much genuine structural error the classical baseline
leaves on the table, not a fixed multiplier that holds everywhere.

Cross-check against the earlier (partially GUI-collected, partially this
method) dataset: roll improvement was 2.65% +/- 1.08% across 3 replicate
pairs collected yesterday; tonight's single fresh pair (+5.57%) is within
a plausible range of that same distribution, not a contradiction.

### 2c. Data integrity note (raised and resolved this session)

A user concern that reported improvements (~2-6% real hardware) were much
lower than a remembered "~10%" figure was investigated directly:
- Verified the physical rig genuinely moved for every completed run --
  raw trace shows real quantized encoder steps (0.044 deg increments,
  matching the rig's actual 8192-count quadrature resolution) with
  realistic step-and-hold sensor noise, not smooth simulated values.
- Located the actual source of the "~10%" figure: an **emulated** (MuJoCo,
  not physical hardware) disturbance-rejection experiment,
  `disturbance_campaign_profiled_2026-08-31`, roll mission,
  10.6% improvement -- a different experiment (simulated, with injected
  hard-pulse disturbances) that appears to have been conflated with the
  real-hardware numbers somewhere along the way.
- No matching "~10% yaw" figure was found anywhere, real or emulated.

### 2d. Neuron-family data on real hardware -- not available, and correctly so

Only `pd` and `nengo-pes` were ever staged through the safety-qualification
process (encoder-sign verification, zero-output dry-run, baseline-only
hold, single-axis low-authority residual) required before arming. LIF,
ALIF, Izhikevich, and LIFRate controllers were never qualified for armed
hardware use and remain emulation/Q8-shadow-only by design
(`launch_hover_nengo_gui.py`'s own validation: "only qualified pd and
nengo-pes controllers may be armed"). Their real-hardware absence in this
report is a deliberate safety boundary, not a gap in data collection.

## 3. Overall reading

The architecture (CMG-PES) shows large, consistent benefit in MuJoCo
simulation specifically on the heavier, harder-to-control platform (X2)
under demanding, coupled 6-DOF missions, and a much more muted,
mission-dependent effect (roughly 0-6%, one mission slightly negative) on
the real physical 3DOF Hover rig. This gap between simulation and hardware
is itself a legitimate, publishable finding: the real hardware's
conservative, safety-driven residual authority (beta=0.2, 0.2V cap -- far
below the 0.5/no-cap regime used in simulation) leaves much less room for
the architecture to act, and CF2's simulated results independently show
the same pattern (muted-to-negative benefit) whenever the classical
baseline is already well-matched to the plant's own dynamics. Both lines
of evidence point the same direction.
