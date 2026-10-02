# Connected Q8 Nengo shadow qualification — 2026-08-31

## Evidence class

These runs used the physically connected Quanser Q8-USB and real encoder
channels, but were deliberately **unarmed**. The headless runner hard-coded
`armed=False`; all four analog outputs were written as zero at every 200-Hz
step and once more in `finally` before closing the card.

This is connected-hardware signal-path, real-time computation, telemetry, and
Nengo shadow-mode evidence. It is **not** closed-loop hardware tracking or a
baseline-versus-CMG performance experiment because the propellers never moved.

## Five-second qualification

| Controller | Control rows | Neural samples | Deadline misses | Maximum DAC | Result |
|---|---:|---:|---:|---:|---|
| PD | 1,000 | not applicable | 0 | 0.0 V | complete, no abort |
| Nengo CMG--PES | 1,000 | 10,000 | 0 | 0.0 V | complete, 23 finite signal groups |

The universal neural analyzer passed and generated full CSV, statistics, and
equation/mechanism PNG/PDF files for the Nengo qualification.

## Mission shadow set

| Mission | Control rows | Neural samples | Deadline misses | Max computed motor voltage | Max physical DAC | Mean gate | Decoder drift |
|---|---:|---:|---:|---:|---:|---:|---:|
| Roll | 5,000 | 50,000 | 0.240% | 7.010 V | **0.0 V** | 0.296 | 0.650 |
| Full3 | 5,000 | 50,000 | 0.340% | 24.000 V | **0.0 V** | 0.940 | 0.592 |
| Hard45 | 5,000 | 50,000 | 0.120% | 24.000 V | **0.0 V** | 0.916 | 0.619 |
| Hardstep | 5,000 | 50,000 | 0.340% | 24.000 V | **0.0 V** | 0.919 | 0.592 |
| Yaw360 | 6,000 | 60,000 | 0.333% | 24.000 V | **0.0 V** | 0.238 | 0.127 |

All five runs completed. The isolated deadline misses never reached the
consecutive-miss abort threshold. The matrix contains 26,000 real-time control
rows and 260,000 full-rate neural samples. All neural analyzers passed.

Full3, Hard45, Hardstep, and Yaw360 reach the modeled 24-V computed-command
limit because a stationary unarmed plant cannot follow their reference. Those
values are computations only; the saved `*_dac_written` channels remain
exactly zero. They must not be interpreted as voltages applied to motors.

The encoder streams were stationary at zero during Roll, Full3, Hard45, and
Hardstep. Yaw360 showed a one-count Roll span (approximately 0.0439 degrees),
which demonstrates a live encoder stream but does not establish the complete
axis-sign audit. Before arming, the operator must deliberately move each axis
while watching the sign and confirm the physical rig checklist again.

## Data retained

Every mission folder contains:

- `trace.csv`: 200-Hz encoders, references, quaternion error, rates, PD torque,
  requested/realized residual, computed/written voltages, allocator state,
  all six synchronized neuron channels, all 18 decoder values/updates,
  quaternions, raw counts, deadline flags, and DAC writes;
- `neural_trace_2khz.npz`: membrane, gate, activity, currents, every CMG
  equation term, PES target/error, raw/clipped decoder, every weight/update,
  residual torque, and exact hardware/substep alignment;
- `neural_trace_schema.json`, `summary.json`, and `manifest.json`; and
- `analysis`: flattened neural CSV, statistics JSON, and two PNG/PDF diagnostic
  figure sets.

## Paths

- Five-second qualification:
  `C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\hardware_q8_qualification_2026-08-31`
- Five mission raw shadow data:
  `C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\hardware_q8_shadow_missions_2026-08-31`
- Compiled CSV/JSON and figure:
  `C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\hardware_q8_shadow_compiled_2026-08-31`
- Zero-output headless runner:
  `C:\Research\hover3dof\nengo_gui_hil_2026-08-29\run_hover_headless.py`

## Gate before armed operation

The connected software/data gate now passes. Armed operation still requires
an in-person reconfirmation of shields, E-stop, amplifier gain, centered frame,
encoder ordering/signs, baseline stability, mission choice, voltage headroom,
and residual authority. The next stage should be baseline-only Hover/Roll,
followed by shadow residual and then a deliberately low-authority single-axis
CMG trial—not an immediate all-mission adaptive sweep.
