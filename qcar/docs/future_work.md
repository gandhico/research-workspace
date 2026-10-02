# QCar/QCar2 Future Work

- Re-run the fixed-perception PID/SMC/NMPC comparison on hardware with identical
  lane ROI and thresholds.
- Compare `pid_gated_adaptive_hyperlif_residual` and
  `smc_gated_adaptive_hyperlif_residual` against their baselines.
- Add a post-run analyzer for the hardware runner's CSV schema.
- Use residual-gate confidence to suppress corrections during lane loss and
  recovery.
- Train residual weights offline from logged lane-error data instead of using a
  fixed gate-only correction.
- Use `CAPABILITY_AUDIT_AND_GRAFTON_PLAN_2026-09-08.md` as the staged route from
  the existing image-state search controller to synchronized fusion,
  bicycle-model MPC, safety-filtered ANN/SNN/RL residuals, and measured-energy
  benchmarking.
