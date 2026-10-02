# DeePC controller research

This directory contains the frozen P-only constrained DeePC runtime, analyses,
guarded X-Plane runner, and tests.

Planned layout:

- `configs/`: frozen DeePC hyperparameters and experiment contracts
- `src/`: controller, Hankel/data utilities, solver interface, and runtime logic
- `analysis/`: offline replay, rank/conditioning, robustness, and timing audits
- `tests/`: deterministic unit and regression tests

Raw X-Plane logs must remain in `../logs/`. Generated numerical results belong
in `../configs/` until a dedicated generated-results registry is introduced.
No script in this directory may send X-Plane controls until the authoritative
development record explicitly authorizes an engaged DeePC stage. Online runners
must default to observe-only and retain permanent latched backstepping fallback.

Backstepping-style API: `DeePC` exposes `SetPoint`, `output`, `clear()`, and
`update()`. Direct guarded R3 test with timestamped CSV and analysis:

```bash
cd /home/ubuntu/GHYN/Xplane_controllers/EHEKATL_BWB_XP12
bash deepc/run_deepc_direct.sh
```

The launcher uses the validated small paired pulse so response is measurable,
and retains the R3 gate, limits, permanent Backstepping fallback, restoration,
and rich logging. Independent superiority confirmation remains underpowered.
