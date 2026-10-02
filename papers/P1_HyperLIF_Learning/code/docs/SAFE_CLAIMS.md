# Safe Claims — Phase 0 (foundation)

Supported by the parity gate (`PARITY.md`) and the skeleton smoke (`scripts/skeleton_smoke.py`).

1. **The PyTorch HyperLIF / Adaptive HyperLIF neuron is the validated continuous-reset model.**
   It reproduces the Nengo-equivalent reference to machine precision (max\|Δv\| ≈ 1e-15,
   max\|Δr\| ≈ 1e-14, zero event mismatch) across step / stress / db_drive protocols.

2. **The model is differentiable and trainable in float32.** Autograd flows from a loss back to
   the input through the surrogate event; the logistic gate is numerically stable.

3. **The origin knob (idea 1) is wired and inert-by-default.** `delta_reset=0` collapses to the
   reference exactly; `delta_reset>0` measurably changes the voltage trajectory.

4. **Through-time BPTT is well-conditioned at the tested short horizons** (random init, dt=1e-3,
   T≤16): the gradient grows mildly (≈0.008→0.66), it does not explode. (Stiff/knife-edge
   regimes near a trained solution are a separate, known concern — to be handled with truncation
   + clipping + annealed surrogate, per the Gate-Eligibility study.)

5. **The reproducibility scaffolding runs:** seeding, per-run folders, registry, dynamics
   metrics, and config-driven dispatch.
