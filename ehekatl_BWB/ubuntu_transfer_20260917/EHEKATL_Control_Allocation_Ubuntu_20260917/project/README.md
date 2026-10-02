# EHEKATL BWB X-Plane 12 Controllers

This is the single controller workspace for the EHEKATL BWB aircraft in
X-Plane 12.

## Layout

- `backstepping/` — preserved dissertation backstepping controller and runners.
- `pid/` — preserved PID controller and its runner.
- `lqr/` — current, unvalidated LQR code retained for work after identification.
- `configs/` — controller notes and configuration references.
- `logs/` — shared controller logs and plots.
- `scripts/` — shared analysis and XPlaneConnect health-check utilities.
- `docs/` — project history and the stage-gated development record.
- `tests/` — offline tests.
- `archive/` — obsolete, duplicate, rejected, and backup material; nothing was
  intentionally deleted during the 2026-07-10 reorganization.

X-Plane 12 is installed at `/home/ubuntu/Xplane12` and is outside this project.
Do not modify it as part of controller development. Third-party XPlaneConnect
support is retained unchanged at `../shared/third_party/XPlaneConnect-master`.

See `../RUNNERS_EHEKATL_BWB_XP12.md` for launch commands and current status.
