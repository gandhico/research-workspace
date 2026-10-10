# Runs copied unchanged from the published tree

Their control law has no desired-rate term (fixed PD, or PID with --rate-ff none so omega_d = 0), so the
frame-aligned rate error cannot change them. Everything else in this sandbox was re-run with the patch.

- `experiments/nengo_nef_replication_2026-08-29/results/matched_45s` (68 files)
- `experiments/nengo_nef_replication_2026-08-29/results/pid_baseline_2026-09-10/regress` (40 files)
- `experiments/nengo_nef_replication_2026-08-29/results/pid_baseline_2026-09-10/tune/ki0.05` (20 files)
- `experiments/nengo_nef_replication_2026-08-29/results/izh_fixed_pd_corrected_2026-09-24` (20 files)
- `experiments/nengo_nef_replication_2026-08-29/results/compiled` (3 files)
- `experiments/cmg_mechanism_controls_2026-10-01/results/ladder/pd` (60 files)

Code of `experiments/cmg_mechanism_controls_2026-10-01` copied; its confirm/development arms are re-run in the sandbox.
