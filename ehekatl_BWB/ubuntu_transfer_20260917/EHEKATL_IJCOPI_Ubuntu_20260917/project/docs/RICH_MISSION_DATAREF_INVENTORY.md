# Rich LQR mission dataref inventory

Source: X-Plane 12.4.3 `Resources/plugins/DataRefs.txt`, reviewed 2026-07-12.

This is an offline authority check. Read-only availability and timing still
must be confirmed in X-Plane before a regime is accepted.

## Required channels

| Group | Datarefs | Use |
|---|---|---|
| Artificial stability | `sim/cockpit/switches/art_stab_on` | augmentation state |
| Yoke/total controls | `sim/joystick/yoke_*_ratio`, `sim/cockpit2/controls/total_*_ratio` | commanded vs realized input |
| Trim | `sim/cockpit2/controls/elevator_trim`, `aileron_trim`, `rudder_trim` | operating-point bias |
| Primary surfaces | `sim/flightmodel/controls/lail1def`, `lail2def`, `rail1def`, `rail2def`, `ldruddef`, `rdruddef` | realized surface response |
| Surface arrays | `sim/flightmodel/controls/ail1_def`, `ail2_def`, `elv1_def`, `elv2_def`, `rudd_def`, `rudd2_def` | distributed BWB surface activity |
| Moments | `sim/flightmodel/forces/L_total`, `M_total`, `N_total` | dynamic-response explanation |
| Actuator model | `sim/aircraft/controls/acf_elev_def_time`, `acf_ailn_def_time`, `acf_rudd_def_time` | delay/rate interpretation |
| Artificial-stability parameters | `sim/aircraft/artstability/acf_AShiV`, `acf_ASloV`, `acf_ASmaxp_lo`, `acf_ASp_lo_rate`, `acf_ASmaxh_lo`, `acf_ASh_lo_rate`, `acf_ASmaxr_lo`, `acf_ASr_lo_rate` | augmentation/configuration metadata |
| Ownership/failures | `sim/operation/override/override_joystick*`, `override_flightcontrol`, `override_control_surfaces`, relevant `sim/operation/failures/*` | control-path validity |

## Existing rich logger coverage

The canonical rich logger already records P/Q/R, derivatives, AOA/beta,
velocities, accelerations, loads, moments, total controls, trims, throttles,
automation, failures, timing, and ownership requests. The next implementation
should add the artificial-stability switch, primary surface scalars, selected
nonzero surface-array summaries, actuator time constants, and override/failure
state snapshots.

Do not add every 56-element surface array as independent model states without
first checking variance and observability. Log the arrays for audit, then derive
low-dimensional surface summaries for identification.

## Read-only acceptance

Before the first new regime, verify for every required dataref:

- present/nonempty numeric value;
- stable shape and units;
- no blocking acquisition at 10 Hz;
- no missing values or unexplained discontinuities;
- consistent metadata and aircraft configuration;
- no writable action during the diagnostic.

Any channel that fails is marked unavailable and excluded explicitly; it is not
silently replaced by a guessed proxy.
