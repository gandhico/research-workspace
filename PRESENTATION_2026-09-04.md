# Tomorrow's Presentation — Pendulum, Aero2, 3DOF Hover, QCar
Speech + adversarial Q&A prep, built from tonight's hardware sessions (2026-09-03).

---

## How to use this doc

Each platform section has: **(1) the narrative** — what to say, in order, **(2) the technical
spine** — exact numbers/gains/algorithms so you never get caught flat, **(3) "if they push
on X"** — the honest limitation, stated before they find it. The closing section is a
straight Q&A bank organized by question TYPE (implementation / algorithm / gains /
safety / honesty), because a sharp reviewer's questions cut across platforms, not within one.

**One rule that should survive the whole talk:** every result you show tonight came from
either (a) a fresh hardware run tonight, or (b) a dated historical report you can name.
Never blur the two. The strongest thing about this presentation is that you can say, for
almost every number, exactly when and how it was produced — use that.

---

## 1. Pendulum (Qube-Servo 3)

### Narrative
Start here — it's your most complete story: classical baseline → neuromorphic residual →
autonomous swing-up, all on real hardware, with a documented selectivity result.

1. **Equilibrium (LQR baseline).** Classical PD/LQR balance, Simulink-derived control law
   (`kp_theta=-2, kd_theta=-2, kp_alpha=30, kd_alpha=2.5`), manual-swing-to-catch engagement.
2. **Gate-residual balance.** Same classical anchor + a bounded HyperLIF gate-state residual,
   capped at ±0.20V. This is your headline selectivity result (below).
3. **Autonomous swing-up.** Energy-pumping law lifted directly from Quanser's own validated
   Simulink model (not invented), now driving the *same* Python control stack.

### Technical spine
- **Classical balance law** (`simulink_balance_runner.py`): PD on arm angle + PD on pendulum
  angle, `u = kp_theta*e_theta + kd_theta*theta_dot + kp_alpha*(-alpha) + kd_alpha*alpha_dot`,
  motor sign −1, derivative filter `H(s)=w·s/(s+w)`, bandwidth 50 rad/s.
- **Upright convention:** encoder zero = hanging; `alpha_upright = wrap(alpha_raw − π)`.
  Confirmed against Quanser's own hardware example (`balance_control_qube.py`:
  `alpha = mod(raw, 2π) − π`) — mathematically identical, independently verified.
- **Engagement state machine:** wait for manual swing >15° → capture band ±10° → 3
  consecutive confirm samples + velocity gate (≤3 rad/s) → **latch** (no longer disabled by
  high velocity once engaged) → hysteresis release at 12°.
- **Gate residual:** `AdaptiveHyperLIFGate`, 2-unit gate/conductance ODE, current-encoded
  from the baseline voltage demand, residual bounded to `±residual_max_voltage`
  independent of the motor limit, summed with baseline and clipped to `±voltage_limit`.
  Applied **only** during active balance (never during swing-up or waiting).
- **Autonomous swing-up (tonight's addition):** energy law extracted directly from
  `qs3_swingup.slx` (Quanser's own Simulink model, `.slx` is a zip — read the block
  diagram XML to confirm the formula rather than trust the `.m` file alone):
  - `E = ½·Jp_cm·α̇² + mp·g·l·(1−cos α)`, `Jp_cm = mp·Lp²/12`, `Er = 2·mp·g·l`
  - `pump = sign(α̇·cos α)`, `u_accel = ke·(E−Er)·pump`, saturated at `a_max`
  - `ke = 50.0` — **Quanser's own validated default** (their model exposes it as a
    live-tunable slider, range 0–100, default 50).
  - Converted `accel → torque → voltage` via the real motor constants (`mr, r, Rm, kt`),
    not an invented scale factor.
  - Two additions on top of the stock Quanser law, both new tonight: a **Schmitt-trigger
    hysteresis** on the pump-direction sign (0.15 rad/s deadband) — prevents rapid
    direction-flip chatter right at each swing's zero-crossing; and an **arm-range guard**
    — pump authority linearly tapers to zero (and centering triples) between 45° and
    120° of arm rotation, so repeated pump kicks can't walk the arm into its hard limit.

### Headline result — the one to lead with
From the June-14 hardware block (12 real trials, repeated tonight's protocol):

| Condition | Mean \|α error\| | Applied active fraction | Applied residual energy |
|---|---:|---:|---:|
| Gate ±0.10V | 0.912±0.349° | **4.60%** | 1.17e-04 |
| Gate ±0.20V | **0.775±0.161°** (best) | 4.44% | 3.82e-04 |
| Always-on ±0.10V | 0.901±0.213° | 70.4% | 1.77e-03 |

**The claim:** the gate residual achieves comparable-or-better tracking than continuous
("always-on") augmentation while using **~93% less residual activity and energy**. It's
nearly silent at low demand (0.04% active) and activates selectively under disturbance
(68% active in high-demand windows). Gating matters, not just having residual capacity.

### If they push on X
- **"Is this the same architecture as the paper's canonical result?"** — No, be precise:
  the June-14 hardware numbers above used the *legacy* current-encoded gate blend
  (`servo_pendulum_snn` / `simulink_balance_runner.py`'s own `ShadowGateResidual`), not
  the canonical ACC2027 `gra_control.gate` implementation. The canonical gate was only
  ever run on the **QLabs twin** (2026-08-27), never on this physical hardware.
- **"What about the 14% improvement I heard about?"** — Retracted, and you should say so
  unprompted. That number came from a *different* dataset (ACC2027 twin, unmatched
  wall-time protocol) where swing-up ate a different fraction of each run per controller.
  Under the matched protocol (fixed 20s of actual balance time, 3 trials/controller), all
  five ACC controllers — classical, fixed-residual, adaptive-residual, online-PES fixed,
  online-PES adaptive — converge to statistically indistinguishable performance (all
  within the QLabs encoder's own quantization limit-cycle, ~1.0–1.1° RMS). **The honest
  claim there is safety/transfer, not performance.**
- **"How do you know the swing-up law is correct and not just copied blindly?"** — Show
  you understand it: explain the energy formula in words (kinetic + potential energy of
  the pendulum about its own center of mass, driven toward the energy needed to just
  reach upright), and be ready to say you found and fixed three real bugs getting it
  working tonight (see below) — that's evidence of understanding, not blind copying.
- **"What broke and how did you find it?"** — Tell this straight, it's a good story:
  1. Hardware balance initially failed silently because the read-state helper used by
     the simpler debug runner (`run_online_qube.py`) was missing the hanging→upright
     shift — traced by comparing against the twin script's own (correct) convention.
  2. Fixing that generically then broke the *other* runner (`simulink_balance_runner.py`,
     which applies its **own** offset on top) — the two shifts stacked to 2π and
     cancelled out. Fixed by making the shift a parameter, defaulting differently per
     caller.
  3. Auto swing-up initially did nothing — the energy pump's `sign()` term is exactly
     zero at rest (no velocity → no defined pump direction). Fixed with a deterministic
     kickstart direction below a small velocity threshold.
  4. Auto swing-up then "worked" but chattered/buzzed — bang-bang sign flipping at
     every zero-crossing noise sample instead of holding a clean push per half-swing.
     Fixed with hysteresis.
  5. Original swing-up gain (an invented `ke=0.35` on a made-up energy scale) was ~140x
     too weak. Fixed by extracting Quanser's real `ke=50` and real physical units
     directly from their `.slx` file.

---

## 2. Aero2

### Narrative
This is your "first flight" story — tonight is the **first time this specific hardware
backend has ever been run against the physical rotors**, staged deliberately like a real
first flight (short low-voltage test, then full run), for five different controllers.

### Technical spine
- **Architecture:** `Backend`/`Controller` contract — the same controller code runs
  unchanged across offline / virtual-twin / hardware; execution mode is a config field,
  never an `if` inside a controller (a golden rule in this repo's own working notes).
  `HardwareBackend` is literally `VirtualTwinBackend` with `hardware=1` — same PAL
  wrapper, same encoder scaling, same measured-`dt` discipline, same LED convention.
- **State/inputs:** `x=[θ,α... ]` — sorry, correct state: `x=[θ,ψ,θ̇,ψ̇]` (pitch, yaw,
  rates), `u=[u_pitch,u_yaw]`, command clip ±24V (HIL/hardware) or ±15V (PAL/twin).
- **Controllers exercised tonight, all via the same `reference_tracking` mission** (2-DOF
  pitch+yaw square wave):
  - **PD** — the reference/safest controller, historically best overall on the old
    codebase's hardware benchmark (Table IV: pitch RMS 0.1544, yaw RMS 0.4215).
  - **LQR, Backstepping, SMC, NMPC** — staged tonight for the *first time* on this
    backend (short low-voltage test → full run each). Historically (old codebase): SMC
    best nonlinear pitch tail (0.0110), NMPC fastest/realtime (~303Hz) but not
    competitive on tracking, **yaw unresolved for every model-based controller** — only
    PD ever handled yaw reasonably. If yaw looks rougher on the other four tomorrow,
    that's consistent history, not a new bug.
- **Yaw-specific missions, also run tonight:**
  - **Yaw-max-hold-pitch** — PD holds pitch level (`cos θ=1`, maximizes yaw authority,
    keeps a safe orientation) while yaw is pushed to its full continuous-rotation range,
    with a permissive plateau/stall detector.
  - **`yaw_large_setpoint`** (your "yaw360"-style mission): setpoint schedule
    0°→+170°→−170°→+270°→0°, deliberately crossing the ±180° wrap boundary. Compares
    **naive PD** (error = `ψ_ref − ψ`, breaks at the wrap — a 170→−170 flip reads as a
    −340° error and drives the long way, or winds up) against **`qpd`**, a **unit-
    quaternion** wrap-aware controller giving the shortest-path error on the circle (for
    a single yaw axis this reduces to SO(2) wrapping; the formulation generalizes to
    full 3-D attitude for future platforms). First-ever hardware attempt tonight — was
    twin-only before.
- **Safety note specific to this platform:** `run_control.py` has **no `--armed` gate** —
  unlike Pendulum/Hover, it commands voltage the instant you run it in hardware mode.
  Say this if asked how you staged it: 3s at 5V, watch behavior, then full duration at
  standard voltage limit.
- **Neuromorphic/Julia:** HyperLIF residual controller exists and is offline-validated
  only — not attempted on hardware (correctly, given tonight's controllers were already
  a first-time set). Julia bridge: Bridge 1 (PythonCall, Julia policy in the loop,
  offline closed-loop validated at 200Hz) and Bridge 2 (`ccall` straight into `hil.dll`,
  zero-overhead, virtual-sensor-only connect validated) — both real, both stopped short
  of live hardware voltage commands deliberately.

### If they push on X
- **"Has this backend ever run on real hardware before tonight?"** — No, and say so
  directly. It was explicitly documented as "scaffolded only" until tonight. The reason
  it was safe to try: it's code-identical to the already-validated twin backend, just
  `hardware=1` — same contract, not a separate unvalidated code path.
- **"Why does yaw always seem to lag pitch?"** — Yaw is a continuous-rotation axis with
  weaker aerodynamic authority than pitch, and historically no model-based controller
  besides PD has resolved it well on hardware. This is a known, documented limitation
  carried forward from the old codebase's own benchmark, not something new.
- **"Is the quaternion controller actually necessary, or is it overkill for one axis?"**
  — Be honest: for a single yaw axis, the quaternion math reduces exactly to SO(2)
  angle-wrapping — you could write the same shortest-path correction directly. The
  quaternion formulation is chosen because it generalizes without modification to full
  3-D attitude control (QDrone, QArm), which is the actual motivation.

---

## 3. 3DOF Hover

### Narrative
Frame this platform carefully — it had the most hardware progress of any platform in the
last week (armed hardware validation only 3 days ago), but also the most mixed results.
Lead with Roll (your one clean win), be upfront about the rest.

### Technical spine
- **Two controllers on hardware, and only two** — enforced by the launcher script itself:
  `pd` and `nengo-pes`. Everything else (`nengo-nef-pes`, `nengo-cmg-fixed`,
  `nengo-lif-*`, `nengo-alif-*`, `nengo-izhikevich-*`, `nengo-lifrate-*`) is
  simulation/GUI-only — a full neuron-family ablation (110 cells) exists, but only in
  sim, not hardware.
- **`nengo-pes`** = the CMG-PES controller: a Nengo-native coupled-membrane-gate neuron
  population with an online PES (Prescribed Error Sensitivity) learning rule adapting
  the readout. Shared neural params across every mission: `beta=0.2` (residual blend),
  `motor-residual-cap-volts=0.2`, `learning-rate=0.0002`, `k-error=2`, `k-rate=0`,
  `residual-slew-v-per-s=1`.
- **Six missions, each with its own tuned safety envelope** (duration, max pitch/roll,
  allocation policy):

  | Mission | Duration | Max pitch/roll | Result status |
  |---|---:|---|---|
  | **Roll** | 8s | 15°/25° | ✅ **n=3, CMG-PES beat PD by +2.16%** — your clean result |
  | Hover | 5s | 20°/20° | Recorded, n=1 |
  | Full3 | 12s (0.5 scale) | 25°/25° | Recorded — **negative, −3.21%** |
  | Hard45 | 12s (0.4 scale) | 25°/30° | Recorded, n=1 |
  | Hardstep | 12s (0.35 scale) | 30°/30° | Recorded, n=1 |
  | Yaw360 | 45s (longest) | 20°/20°, stability-priority allocator | Recorded, history of runtime safety-aborts |

- **Safety guardrails baked into every hardware run:** `--max-abs-pitch-deg`,
  `--max-abs-roll-deg`, `--max-encoder-step-deg 5`, `--motor-floor-volts 2` — the
  launcher aborts safely if any of these trip. Software torque disturbances are
  explicitly **refused** in physical hardware mode (simulation-only).
- **No LED indicator** on this platform (unlike Pendulum) — only the amplifier's own
  fixed power light. Say so if asked, rather than let it look like an oversight.

### If they push on X
- **"So does the neuromorphic controller actually beat the classical one?"** — The
  honest answer: **on Roll, yes, modestly and repeatably (n=3, +2.16%). On Full3, no —
  it was worse (−3.21%).** Present it exactly that way: mission-dependent, not a
  universal win. Do not show only the positive missions without this context — there is
  a "positive-only" figure generator in the repo, and using it without the negative
  numbers alongside would overstate the result.
- **"Why does yaw360 take so much longer than the others?"** — It's the largest attitude
  excursion (full continuous rotation) and uses a more conservative "stability-priority"
  allocation policy rather than the fixed-bias policy the shorter missions use — trading
  speed for margin given its abort history.
- **"How many trials support these numbers?"** — Be exact per mission: Roll is n=3
  (repeatable), everything else is n=1 (single observation, preliminary). Don't let n=1
  results get presented with the same confidence as Roll's n=3.
- **"What's actually in the isolated `.venv` — is this really running on the hardware
  card or just simulated?"** — Real `nengo`, `nengo_gui`, and Quanser's own
  `quanser_hardware`/`quanser_api` wheels (2026.5.13) in an isolated environment
  separate from the shared research Python env — `--io q8` in hardware mode talks to
  the physical Q8-class DAQ card, confirmed by the armed runs and the safety-abort
  history (a simulator wouldn't trip real encoder-step limits).

---

## 4. QCar

### Narrative
Close with QCar — most controllers of any platform (7, tuned individually), running on
an entirely different execution environment (the car's own onboard Jetson, not this
laptop), plus a manual-drive fallback.

### Technical spine
- **Execution environment:** unlike the other three platforms, QCar controllers run
  **on the car's own Jetson** via SSH (`ssh nvidia@192.168.1.129`), not on this laptop.
  Say this explicitly if asked "what's this connected to" — it's a genuinely different
  architecture, not a detail to gloss over.
- **Safety discipline:** perception-only mode first (camera, lane-sign, steering-sign,
  logging all confirmed working with zero motor output) — only add `--armed` after
  that's clean.
- **Seven controllers, each with hand-tuned gains** (from tonight's/recent tuning pass):
  - **PID** — baseline and a "stronger" variant (`kp=1.8, kd=0.08, slope_gain=0.90`)
  - **SMC** — sliding-mode with boundary-layer saturation
    (`error_gain=1.30, slope_gain=0.70, switch_gain=0.12, λ=1.60, boundary=0.35`)
  - **NMPC (image-state)** — lightweight receding-horizon grid search directly on image
    features (`horizon=10, candidates=11, beam=20, q_error=18.0`)
  - **Adaptive HyperLIF gate** — standalone neuromorphic controller
    (`family_kp=5.0, family_kd=0.055, gate_gain=0.85, output_limit=0.35`)
  - **Three gated-residual hybrids** — PID/SMC/NMPC each with a gated adaptive-HyperLIF
    residual added on top (`residual_gain=0.35, residual_limit=0.080,
    residual_gate_min=0.40`) — the NMPC+residual combo is documented as the
    "strongest experimental run."
- **A real bug found and fixed on this platform tonight, worth mentioning as a process
  point:** the physical joystick steering direction was inverted (`turn right → car goes
  left`) on manual-drive testing. Traced and corrected via `--steering-sign -1.0` in the
  hardware runner's own convention — the same sign-convention discipline as the
  Pendulum's alpha-shift bug, just surfaced through direct driving rather than sensor logs.
- **Manual drive fallback** (Logitech F710 gamepad, switch in "X" position): LB = arm/
  deadman, left stick = steering, RT = throttle, A = reverse. Two independent scripts
  exist (stock Quanser + a version customized in your own working folder) — useful as a
  live safety fallback if an autonomous controller misbehaves.
- **Not present on this platform:** no Julia, no MATLAB/Simulink — Python only, plus the
  onboard ROS2 stack as a separate, unused-tonight lineage.

### If they push on X
- **"Why run controllers on the car's own computer instead of this laptop?"** — The
  QCar's Jetson has the camera/lidar/encoder I/O and needs the control loop local for
  latency; this laptop is used for Pendulum/Aero2/Hover because those use a USB/network
  HIL link back to a desktop-class machine instead.
- **"How was the steering-sign bug actually found?"** — Direct manual-drive testing
  (physically turning the wheel and observing the car go the opposite way) — a hardware
  ground-truth check the same as the Pendulum sensor logs, just executed by hand instead
  of instrumented.
- **"Which controller is 'best'?"** — Don't overclaim; you have tuned gains for seven
  controllers but the presentation is about demonstrating range and the residual-gating
  architecture pattern (same demand-triggered idea as Pendulum/Hover), not a settled
  ranking. If pressed, the residual-augmented combos are the ones built to show the
  cross-platform generality of the gating idea.

---

## 5. Cross-cutting Q&A bank

Group by question TYPE — a sharp reviewer's questions often cut across all four platforms.

### Implementation
- **"Is this the same code running on every platform, or four different things?"** —
  Same *idea* (classical anchor + bounded, demand-gated neuromorphic residual), four
  platform-specific implementations, at different levels of maturity: Pendulum
  (legacy blend, hardware-proven selectivity) → Hover (canonical CMG-PES,
  mission-dependent) → Aero2 (offline-validated, not yet hardware-tested) → QCar (own
  standalone gate architecture, hardware-tuned).
- **"What's the software stack — is any of this Simulink, or all Python?"** — Mostly
  Python. Pendulum has a genuine MATLAB/Simulink reference implementation (Quanser's own
  `qs3_swingup.slx`, verified tonight on the twin) alongside the Python port. Aero2 has
  a Julia bridge (two variants) plus a MATLAB PD twin bridge. QCar and Hover are Python-only.

### Algorithms
- **"What exactly is a 'gate-state residual' — walk me through the math."** — A small
  neuron population (1–2 units typically) receives a current encoding of control
  demand (how hard the classical controller is working), evolves a gate/conductance
  state, and its output is blended with — never replaces — the classical command,
  hard-clipped to a small voltage budget. Near equilibrium, demand is low, the gate
  stays near zero, residual ≈ 0. Under disturbance, demand spikes, the gate opens,
  residual assists briefly, then decays back.
- **"Why 'adaptive' HyperLIF vs plain HyperLIF?"** — Adds an adaptation variable on the
  gate gain (spike-frequency-adaptation-like). Numerically shown (offline, Nengo/NEF
  parity work) to be equivalent to the fixed-gate version under the tested regimes so
  far — an open question requiring harder/noisier regimes to actually differentiate.
  Don't claim adaptive is proven better; it isn't, yet.

### Gains / weights — have these ready verbatim if asked
- Pendulum LQR: `K=[-1.000, 26.72, -0.8269, 2.214]` (Quanser twin-tuned) vs.
  `[-1.2247, 24.9044, -0.6877, 3.1321]` (this repo's independently-derived gains) —
  both exist, documented as two valid gain sets.
- Pendulum swing-up: `ke=50` (Quanser's own), arm-centering `k_theta=2.5,
  k_theta_dot=0.5` (this project's own addition, not in the stock model).
- Residual caps: Pendulum ±0.10V/±0.20V; Hover 0.2V; QCar 0.080V (residual_limit)
  with a 0.40 gate-min threshold.
- Every gain above came from either Quanser's own shipped model (extracted, not
  guessed) or a documented tuning pass — none were invented on the spot tonight except
  where explicitly marked as "this project's own addition."

### Safety / process
- **"What's your safety protocol for a totally new hardware combination?"** — Consistent
  across all four platforms tonight: sensor/perception-only check first (zero actuation)
  → short low-voltage/short-duration test → full run, with a human hand near power/e-stop
  for every first attempt. Aero2 and Hover both have hard-coded safety envelopes
  (voltage/angle limits) that abort automatically; Pendulum and QCar rely on the staged
  human-supervised protocol plus (for Pendulum) an explicit arm-range software guard.
- **"How many of tonight's 'first-time' hardware attempts actually worked cleanly on
  the first try?"** — Be honest, this is a credibility strength not a weakness: several
  didn't — the Pendulum swing-up needed four real fixes before it worked (see above),
  and the Aero2 hardware backend, while it worked, had never been exercised before
  tonight for four of its five controllers. The fixes were diagnosed from first
  principles (reading actual encoder conventions, actual vendor source, actual physics)
  each time, not trial-and-error guessing.

### Honesty checkpoints — say these before being asked
1. Pendulum: the 14% number is retracted; the real hardware claim is selectivity, not
   raw performance.
2. Aero2: today is the hardware backend's first real flight for four of five
   controllers; yaw is historically unresolved for anything but PD.
3. Hover: only Roll has a repeatable positive result; Full3 was negative; don't cite the
   "positive-only" figure set without the audit's full context.
4. QCar: seven controllers are tuned and armed-tested, but there's no single
   "winner" claim — the point is demonstrating the architecture pattern across all seven.

---

## Suggested closing line

*"Every platform here uses the same underlying idea — keep the classical controller as
the stability anchor, add a small, bounded, demand-triggered neuromorphic correction on
top — at a different stage of maturity: proven and selective on the pendulum, real but
mission-dependent on the hover, freshly validated tonight on Aero2, and tuned across
seven controller variants on the QCar. The story isn't that neuromorphic control wins
everywhere yet — it's that the same architecture transfers, stays safe, and is honest
about where it does and doesn't help."*
