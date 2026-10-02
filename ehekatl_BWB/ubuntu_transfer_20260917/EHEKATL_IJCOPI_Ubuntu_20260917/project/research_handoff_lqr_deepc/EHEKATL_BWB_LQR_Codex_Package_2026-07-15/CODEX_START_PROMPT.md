# Codex project handoff prompt

We are continuing the EHEKATL blended-wing-body aircraft control research in Ubuntu.

Project root:

```text
/home/ubuntu/GHYN/Xplane_controllers/EHEKATL_BWB_XP12
```

This extracted package contains the current manuscript, thesis, pre-X-Plane LTI validation datasets, mission-tracking datasets, and summaries. First audit the package and report exactly what is available. Do not modify or overwrite the source datasets.

Research objective:

- Implement the validated longitudinal and lateral LQR controllers in the real-time EHEKATL X-Plane 12 plant.
- Compare LQR against a direct input-output predictive optimization method, preferably regularized DeePC.
- The adaptive Backstepping controller is already published. Cite it as prior work only; do not make it the main baseline of this new paper.

Hard technical conventions:

- Use SI units and radians internally.
- Use degrees only for plots and reported metrics.
- Current actuator limit is +/-25 degrees unless the X-Plane aircraft model proves a different physical limit.
- XPlaneConnect `sendCTRL` ordering is `[aileron, elevator, rudder, throttle]`.
- Keep logs in `/home/ubuntu/GHYN/Xplane_controllers/EHEKATL_BWB_XP12/logs`.
- Keep controller-specific implementation under the existing `lqr/` structure, and create a separate, clearly named `deepc/` folder for the data-driven controller.
- Do not rename or delete the existing Backstepping implementation.

Begin with these steps:

1. Read `README.md`, the current manuscript, the mission summary, and the LTI summaries.
2. Inspect all NPZ keys, dimensions, gains, matrices, time vectors, and units; create a concise dataset inventory.
3. Verify that the current LQR matrices/gains in the manuscript and NPZ files agree.
4. Audit the existing X-Plane controller code and dataref/sign/routing conventions before writing new code.
5. Propose a staged implementation plan:
   - online X-Plane LQR regulation,
   - LQR reference tracking,
   - safe excitation and input-output data collection,
   - offline DeePC replay validation,
   - online regularized DeePC,
   - common benchmark scenarios and metrics.
6. Do not claim the supplied NPZ files are X-Plane logs; they are pre-X-Plane LTI results.

At the end of the audit, give the exact files you propose to create or modify and wait for approval before major restructuring.
