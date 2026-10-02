# Qube Servo/Pendulum Future Work

- Port the Quanser `read_write_qube3.py` pattern into a read-only hardware check.
- Implement a hardware-safe baseline upright-balance runner with `--armed`.
- Add a residual blend sweep for `beta in {0.05, 0.10, 0.20, 0.35}`.
- Add a swing-up/capture experiment only after upright residual tests are stable.
- Compare fixed gate residuals against trained residual weights from logged
  recovery trajectories.

