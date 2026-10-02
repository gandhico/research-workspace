# LQR controller

This folder contains historical and frozen R3 delay-aware/discrete controllers.
The R3 roll controller executed safely, but failed its matched performance gate.

The existing gains lack a fully documented and independently validated plant
model. Identification must follow the stage-gated process in
`../docs/CONTROL_DEVELOPMENT_PROCESS.md`; do not run identification or flight
validation merely as part of project cleanup.

Backstepping-style API: `LQRController` exposes `SetPoint`, `output`, `clear()`,
and `update()`. Direct guarded R3 test with timestamped CSV and analysis:

```bash
cd /home/ubuntu/GHYN/Xplane_controllers/EHEKATL_BWB_XP12
bash lqr/run_lqr_direct.sh
```

A failed start gate sends no controls. The runner retains limits, latched
Backstepping fallback, ownership restoration, and rich logging.
