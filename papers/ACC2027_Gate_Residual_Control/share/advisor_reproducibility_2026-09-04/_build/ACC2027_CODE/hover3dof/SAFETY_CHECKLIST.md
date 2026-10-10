# 3DOF Hover — pre-arming safety checklist

**Status: no physical hardware has been touched or armed as of this checklist's
creation (2026-08-27). Nothing in this repository sends a motor command.**
Do not check any item below from a PDF or from memory — every item must be
independently verified at the physical rig before the corresponding phase of
`docs\AGENT_HANDOFF_2026-08-27.md`'s staged sequence proceeds.

## Why this exists

`C:\Research\hover3dof` had zero Python code before 2026-08-27 — only vendor
Simulink/MATLAB courseware. The ACC2027 repo's `hover3dof_bridge()`
(`gra_control.hardware_bridges`) is disarmed by default (`armed=False` →
zero output) and is designed to sit inside an *existing* QUARC/PAL hover
control loop, never to talk to hardware directly. This checklist is the gate
between "the bridge compiles" and "the bridge is allowed to see the real
rig."

## Reference values from the vendor documentation (READ, not verified)

Sources, both read in full 2026-08-27:
- `3DOF_Hover\...\Documentation\3 DOF Hover - Laboratory Guide.pdf` (Quanser, 2013)
- `3DOF_Hover\...\Technical Resources\3 DOF Hover - User Manual.pdf` (Quanser, 2013)

These are the vendor's own generic/worked-example values, not measurements
from *this specific* unit — treat every number as a starting point to
re-verify, not a fact to trust blindly.

### Identified physical constants (User Manual Table 2.2/2.3)

| Symbol | Description | Value |
|---|---|---|
| `K_t` | Torque-thrust constant of motor/propeller | 0.0036 N·m/V |
| `K_f` | Force-thrust constant of motor/propeller | 0.1188 N/V |
| `L` | Pivot-to-motor distance | 0.197 m |
| `m_hover` | Total moving mass | 2.85 kg |
| `J_y` | Yaw-axis inertia | 0.110 kg·m² |
| `J_p` | Pitch-axis inertia | 0.0552 kg·m² |
| `J_r` | Roll-axis inertia | 0.0552 kg·m² |
| `R_m` | Motor armature resistance | 0.83 Ω |
| Encoder resolution | quadrature counts/rev | 8192 (0.0439°/count) |
| Pitch motor input rating | | ±24V, 5A peak, 3A continuous |

Motors are Pittman Model 9234.

### CRITICAL — amplifier gain is unknown and must be checked physically

The User Manual states: *"If your amplifier has a Gain setting switch, make
sure you set the Gain to 3 when using the Quanser 3 DOF Hover experiment."*
**Actual motor voltage = DAQ analog-output voltage × amplifier gain.** I
have no way to know this rig's amplifier model or gain-switch position from
software. Do not compute or assume a safe DAQ output voltage for any test
until this is physically confirmed. The manual's example amplifier is a
Quanser VoltPAQ-X4 (green LED = powered/armed).

### CRITICAL — the vendor's own channel map is internally inconsistent

User Manual Figure 3.1 (the wiring *picture*) and Table 3.1 (the wiring
*text*) disagree with each other on which amplifier/cable drives the Left
vs. Right motor:

- **Table 3.1 (text)**: AO0→Amp0→**Front** (D/A0); AO1→Amp1→**Back** (D/A1);
  AO2→Amp2→**Left** (D/A2); AO3→Amp3→**Right** (D/A3).
- **Figure 3.1 (picture)**: cable 5→Front, 6→**Right**, 7→**Back**, 8→**Left**
  — i.e. AO1 and AO3 swapped relative to the text.

The manual itself flags this is only a *typical* configuration ("your
configuration may be different"). **Do not trust either reading — use the
vendor's own Section 4.1.1 test to establish ground truth on this specific
unit**: apply ~4V to one Analog Output channel at a time and visually
confirm which physical propeller spins, before assuming any channel-to-motor
mapping in software. Encoder channels are consistent between figure and
table and not in question: Encoder Input 0 = Pitch (ENC0), 1 = Roll (ENC1),
2 = Yaw (ENC2).

### RESOLVED — verified channel map (2026-08-27, physical test on this unit)

Confirmed by running `runners\single_channel_motor_test.py` on each channel
and visually reading the vendor's own physical labels on the rig (Front /
Back / Left / Right propeller shields, Roll / Pitch encoder labels):

- **Analog Output 0 → Front motor**
- **Analog Output 1 → Back motor**
- **Analog Output 2 → Left motor**
- **Analog Output 3 → Right motor**
- Encoder 0 → Pitch, Encoder 1 → Roll, Encoder 2 → Yaw (per Table 3.1,
  uncontested, not separately re-verified by pulse test)

This matches User Manual **Table 3.1's text**, not Figure 3.1's picture
(which had Back/Left/Right permuted) — the figure was the wrong one for
this unit.

**Observation from the operator during this test** (informational, not a
rule): at the vendor's suggested ~4V DAQ-output / ~12V motor-equivalent
*open-loop, momentary* test pulse, the left/right (roll-axis) motors swung
the frame to its mechanical roll limit, lightly contacting the arm
support, while front/back stayed in normal range. That single open-loop
data point doesn't by itself imply the closed-loop regulator (which only
ever produces small corrections around a level hold, not a sustained
one-sided pulse) needs derating -- noted here for context, not enforced in
code.

Amplifier gain: user-confirmed = 3, matching what `q_hover`'s vendor
Simulink source (`setup_lab_hover.m`: `K_AMP = 3`) assumes.
Pre-flight state at time of test (user-confirmed): propeller shields
installed, E-Stop connected and released, frame balanced/assembled.

### DAQ hardware on this machine

Windows sees two Quanser Q8-USB boards ("Q8-USB A", "Q8-USB B"), both
Status OK (checked 2026-08-27, `Get-PnpDevice`). Board identity has only
been probed via a read-only serial-number query
(`HIL.get_string_property(StringProperty.SERIAL_NUMBER)`, zero channel
I/O) — see `runners\hil_identify.py`. Which physical board (if only one) is
actually wired to the Hover, and which `board_identifier` ("0"/"1") that
corresponds to, is not yet established.

- **State vector**: `x = [θ_yaw, θ_pitch, θ_roll, θ_yaw_dot, θ_pitch_dot, θ_roll_dot]`
- **Output vector**: `y = [θ_yaw, θ_pitch, θ_roll]`
- **Control vector**: `u = [V_f, V_b, V_r, V_l]` — **front, back, right, left**
  motor voltage, in that order. Confirm this order against the physical
  wiring/DAQ channel map before assuming it — do not assume the Simulink
  model's channel order matches whatever DAQ card ordering this specific
  rig uses.
- **Sign conventions**: yaw positive = CCW; pitch positive when
  `V_f > V_b` (front voltage exceeds back); roll positive when `V_r > V_l`.
- **Control law**: `u = K(x_d − x) + u_bias` **if `u ≥ 0`, else `u = 0`**
  (Eq. 2.5) — every channel is clamped to nonnegative voltage,
  element-wise, always.
- **Explicit vendor caution** (verbatim): *"Due to the low resistance of the
  motor, switching between positive and negative voltage can cause
  permanent damage to the power amplifier. The controller given in
  Equation 2.5 only applies positive voltage to the motors."* This is not
  optional tuning guidance — it is a hardware damage warning.
- **Worked example values** (this specific numeric example, not necessarily
  this unit's calibration): bias voltage `V_bias = 2V` per motor; saturation
  limit example `24V` (called "VMAX_HOVER" in the model, configurable).
- Numeric physical constants (`K_f` thrust constant, `K_t` torque constant,
  `L` arm length, `J_yaw`/`J_pitch`/`J_roll` inertias) are **not** given in
  the Laboratory Guide — it defers to a separate "Quanser 3 DOF Hover User
  Manual" not yet located on this machine. Do not proceed to any
  identified-model claim without that document or independent measurement.

## Checklist (independently sign-check every item, in person, before use)

Per `docs\AGENT_HANDOFF_2026-08-27.md`:

- [ ] **Amplifier gain-switch setting** — physically read it off the
      amplifier (VoltPAQ-X4 or equivalent). Every voltage computed by any
      runner must account for this multiplier.
- [ ] **Motor channel order and polarity** — the vendor PDF's own figure and
      table disagree (see above). Resolve using the vendor's Section 4.1.1
      procedure (apply ~4V to one Analog Output channel at a time, confirm
      by eye which propeller spins) before trusting any channel map in code.
- [ ] **Hover bias voltage** for every motor — measure, don't assume `2V`.
- [ ] **Allowed voltage range and residual headroom** — confirm the real
      saturation limit for this unit (vendor example used `24V`) and how
      much headroom is left for a CMG residual on top of the baseline.
- [ ] **Nonnegative-voltage enforcement** — confirm whatever runner is used
      clamps every channel to `≥ 0` at the final output stage, matching
      Eq. 2.5, and that the CMG residual cannot push a channel negative.
- [ ] **Encoder ordering, units, frame convention, and sample rate.**
- [ ] **Watchdog, stale-data behavior, kill switch, and emergency stop** —
      confirm these exist and work *before* anything spins.
- [ ] **Baseline-only stable hover** — confirm the existing vendor
      LQR/state-feedback baseline (no CMG residual at all) holds a stable
      hover on this unit first.
- [ ] **Zero-output / sensor-only logging run** — confirm a full run with
      the CMG bridge computing residuals but `armed=False` (matching
      `SafeGateBridge.step(..., armed=False)`'s guaranteed zero output)
      produces sane, bounded logs before any armed run.

## Staged sequence after the checklist passes

Per the handoff: shadow residual (compute, don't apply) → recorded-log
replay → low-beta, single-axis armed residual → one axis at a time → only
then a matched multi-axis experiment. Never let the CMG bridge bypass the
existing vendor safety layer (QUARC watchdog, PAL arming, hardware E-stop).

## What exists in this repo today (2026-08-27)

- `runners\offline_acc2027_cmg_residual.py` — **pure Python simulation**,
  no hardware, no QUARC. Uses the vendor's exact state/control vector shape
  and Eq. 2.5's positive-voltage-only law, but with placeholder physical
  constants (clearly flagged in that file) since the real `K_f`, `K_t`,
  `L`, and inertias aren't in the Laboratory Guide. Do not cite its results
  as hardware-identified.
- No QUARC/PAL hardware entrypoint exists yet. `gra_control.hardware_bridges.hover3dof_bridge()`
  is ready to be wired in once one does.
