# Nengo/CMG checkpoint frozen 2026-08-31

The lossless telemetry is frozen **in place** rather than duplicated because
the matched neuron-family tree is 4.07 GB and the Hover prehardware disturbance
tree is 0.61 GB. Each tree contains a per-file SHA-256 manifest:

- `C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\nengo_nef_replication_2026-08-29\results\neuron_family_matched_45s\FROZEN_SHA256_MANIFEST.json`
- `C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\disturbance_campaign_profiled_2026-08-31\FROZEN_SHA256_MANIFEST.json`

The matched matrix contains 110 summaries and 100 non-baseline 2-kHz neural
archives. The Hover set contains 10 paired summaries and five CMG/PES 2-kHz
archives. A frozen manifest verifies every raw, schema, summary, figure, and
diagnostic file by relative path, byte size, and SHA-256 digest.

The companion compact ZIP contains source code, calibration, documentation,
compiled tables/figures, the successful manuscript build, the deep experiment
catalog, campaign manifest, and integrity manifests. It intentionally does not
duplicate the raw NPZ/CSV traces. Therefore the compact ZIP plus the two
in-place telemetry roots are the complete checkpoint.

The later connected-Q8, hard-coded-zero-output qualification and five-mission
shadow set are frozen separately at
`C:\Research\hover3dof\frozen_archives\hover_nengo_CONNECTED_Q8_SHADOW_INDEX_FROZEN_2026-08-31.zip`.
Its raw qualification, mission, and compiled folders each contain a SHA-256
manifest. This connected dataset validates I/O, real-time computation, Nengo
state evolution, logging, and safe shutdown; it is not tracking-performance
evidence because the DAC outputs were exactly zero.

Evidence labels must remain explicit:

- X2 and CF2 1.5x rotor-design neuron-family runs are nominal MuJoCo results.
- The CF2 result is an actuator-design study, not stock Crazyflie hardware.
- The Hover hard-pulse set is emulated/prehardware and not an identified twin.
- Hover Hard45 and Yaw360 disturbance pairs are partial safety-boundary runs.
- Physical LQR and physical quaternion-PD Hover results are separate campaigns.
