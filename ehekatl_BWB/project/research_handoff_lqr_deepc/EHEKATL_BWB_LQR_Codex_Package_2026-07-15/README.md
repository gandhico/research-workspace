# EHEKATL BWB LQR Research Handoff

Package prepared on 2026-07-15 for transfer to Ubuntu and continuation with Codex.

## Research scope

The current paper should compare:

1. **Model-based LQR**, using the thesis-derived longitudinal and lateral linear models.
2. **A direct data-driven or model-free optimization method**, with regularized Data-Enabled Predictive Control (DeePC) as the primary candidate.

The previously published adaptive Backstepping controller should be cited as prior work, not repeated as a main quantitative baseline.

## Important distinction

The NPZ files in this package are **pre-X-Plane continuous-time LTI validation and reference-tracking datasets**. They are not yet real-time X-Plane 12 flight logs. The next research stage is to implement and validate the LQR in the online X-Plane loop, collect persistently exciting input-output data from the EHEKATL plant, and then build the DeePC comparison.

## Unit and actuator policy

- Internal simulation units: SI units and radians.
- Angular states: radians.
- Angular rates: radians per second.
- Controller commands: radians.
- Degrees: plots, reports, and interpretation only.
- Current validation actuator limit: `+/-25 deg` (`+/-0.436332 rad`).

## Current principal LQR baseline

Longitudinal:

- `Qlon = diag(6, 18, 3, 0.1)`
- `Rlon = 1.0`
- `Klon = [1.58255059, -2.53350077, -1.84584039, -22.06327663]`
- Small-case maximum elevator: `9.450 deg`
- Small-case saturation: `0%`
- Settling time: approximately `6.36 s`

Lateral-directional:

- `Qlat = diag(3, 9, 9, 3)`
- `Rlat = 1.0`
- `Klat = [0.11366923, 2.95176288, -0.16714788, 2.67770629]`
- Small-case maximum aileron: `18.405 deg`
- Small-case saturation: `0%`
- Settling time: approximately `4.176 s`

## Folder contents

- `manuscript/current/`: current LaTeX source and rendered manuscript.
- `manuscript/legacy/`: earlier Word/PDF manuscript versions.
- `references/`: the EHEKATL BWB thesis.
- `data/lti/`: small-perturbation and saturated-stress datasets.
- `data/missions/`: step and sinusoidal pitch/roll tracking datasets.
- `summaries/`: human-readable and JSON validation summaries.
- `CODEX_START_PROMPT.md`: ready-to-paste project handoff prompt.
- `SHA256SUMS`: integrity hashes for every packaged file.

## Suggested Ubuntu location

The existing controller workspace is:

```text
/home/ubuntu/GHYN/Xplane_controllers/EHEKATL_BWB_XP12
```

A clean extraction location is:

```text
/home/ubuntu/GHYN/Xplane_controllers/EHEKATL_BWB_XP12/research_handoff_lqr_deepc
```

Example:

```bash
mkdir -p ~/GHYN/Xplane_controllers/EHEKATL_BWB_XP12/research_handoff_lqr_deepc
unzip EHEKATL_BWB_LQR_Codex_Package_2026-07-15.zip \
  -d ~/GHYN/Xplane_controllers/EHEKATL_BWB_XP12/research_handoff_lqr_deepc
cd ~/GHYN/Xplane_controllers/EHEKATL_BWB_XP12/research_handoff_lqr_deepc/EHEKATL_BWB_LQR_Codex_Package_2026-07-15
```

For the existing XPlaneConnect bridge, preserve the control routing convention:

```text
sendCTRL = [aileron, elevator, rudder, throttle]
```
