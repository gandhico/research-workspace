# Putting the CMG–PES residual on other controllers — design considerations

2026-09-10. Written before the five-family results arrive; numbers are added
in the companion report. Controllers: LQR, backstepping, SMC, MPC, NMPC,
carried from Gandhi's Aero 2 implementations (`C:\Research\aero2\aero2\control\`)
to a 3-axis torque-input rigid body.

## Short answer

**Yes, the architecture transfers to all five without structural change.**
The residual attaches at the torque interface, `u = sat_ℓ(u₀ + βℓ⊙s)`, and
every one of these controllers produces a torque `u₀` inside the same box.
The boundedness and exact-baseline-recovery properties (Props. 1–3) never
assumed anything about how `u₀` was computed, so they hold for every family.

What does *not* transfer automatically is **performance** and the **tuning of
the residual itself**. Six things need attention.

## 1. Every family needs reference-rate feedforward first

All five aero2 laws damp absolute rate: LQR's `x_ref` has zero rates,
backstepping uses `−k₂θ̇`, SMC's surface is `θ̇ + λe`. That is the gap found in
the attitude PD, where adding `ω_d` alone removed 76–99% of error on moving
references. A residual on top of a baseline without feedforward will largely
learn the missing feedforward, which inflates its apparent benefit.
**Here every family runs with `ω − ω_d` and `J ω̇_d + ω×Jω`.** This also
applies to the Aero 2 paper's own comparisons.

## 2. What the CMG encodes changes with the baseline

The CMG currents encode the normalised baseline command `ū = u₀/ℓ`. For PD,
`u₀` is almost pure feedback, so the gates see the error. For a model-based
law, `u₀` also carries a large feedforward term (`J ω̇_d + ω×Jω`) that says
nothing about error, so the gates are driven partly by the reference, not the
mistake. Two options, not yet tested:
- encode only the feedback part of `u₀` (the architecture's intent);
- keep encoding `u₀` and accept a reference-driven basis.

## 3. The teaching signal assumes a PD-like correction

`y* = −k_e e_q` prescribes what the decoder should output. It is independent
of the baseline, but it presumes the residual should push like extra
proportional action. When a strong baseline already drives `e_q` near zero,
`y*` shrinks and so does learning. **Expect diminishing returns as the
baseline improves** — the 6-DOF CF2 runs already show it (0–5% over a
feedforward cascade).

## 4. Residual authority β must be re-tuned per baseline

A faster, tighter baseline has less gain margin left for an additive
perturbation. The 6-DOF CF2 cascade tolerated β = 0.008 (vs 0.5 on the
canonical X2); the tuned X2 cascade needed ≈ 0.02. The small-gain remark
makes this precise: the residual is a bounded perturbation of size `β‖ℓ‖`,
and the admissible β is set by the *baseline's* ISS gain. **β is a property
of the baseline–residual pair, not of the residual.**

## 5. MPC and NMPC want the residual inside the model, not after it

Added after the optimiser, as here, the residual is an unmodelled
disturbance the MPC does not know about; the two can fight. The principled
integration is **learning-based MPC**: feed the learned residual into the
prediction model as a known correction, so the optimiser plans with it.
Two more points:
- **Rates.** MPC/NMPC update at 100 Hz here; the residual runs at 2 kHz and
  can correct between updates — a genuine multi-rate advantage worth
  measuring separately.
- **The aero2 MPC is unconstrained** (first-move gain + clip). Without active
  constraints, finite-horizon unconstrained MPC converges to LQR, so it will
  behave like LQR. MPC's real advantage — constraint handling — needs an
  online QP solver, which this environment does not have.

## 6. SMC and the boundary layer

Inside its boundary layer SMC is a linear law (here critically damped at the
PD's ωₙ); outside it is a bounded reaching law. A residual large enough to
push `s` out of the layer turns a smooth correction into switching, i.e.
chattering. **Keep `β‖ℓ‖` below the reaching margin η**, or the residual
reintroduces what the boundary layer removed. SMC's robustness to matched
disturbances also overlaps with what the residual learns, so gains may be
small here by design.

## Family by family — where the residual should help

| family | what the residual can add | expectation |
|---|---|---|
| LQR | nonlinearity beyond the linearisation (large angles, gyroscopic coupling) | modest; LQR ≈ PD + ff with ζ = 1/√2 |
| backstepping | model mismatch in `J`, gyroscopic term, allocation | the natural "model + learned residual" pairing |
| SMC | little — overlaps with SMC's own robustness | smallest |
| MPC (unconstrained) | same as LQR | ≈ LQR |
| NMPC | model mismatch, and correction between 100 Hz updates | depends on fixing the cost (below) |

## Fairness protocol used

- same missions, torque box, allocation, rotors, timestep, feedforward;
- bandwidth tied to the PD's ωₙ, then a common `bw-scale` sweep per family,
  best single setting per platform, tuned **on the evaluation missions**
  (favours the baselines — conservative for the CMG claim);
- **PD+ff gets the same bandwidth sweep**, so structure is compared with
  structure, not with a better-tuned competitor;
- CMG on top of each family at that family's tuned setting.

## Known limitations of this study

- **NMPC** in the aero2 form (grid of constant offsets, RK4 shooting) performs
  *worse* than its own nominal law, even with closed-loop prediction. Its
  one-period prediction is accurate (0.002°), so the model is not at fault;
  the likely causes are the cost weighting (rate error weighted while the
  metric scores angle) and the ±10%-only grid. A real NMPC needs an NLP solver
  (CasADi/acados). Installing one must go in a **separate venv**: if pip moves
  numpy, every Table V number stops reproducing bit-for-bit.
- The families are the aero2 formulations, not state-of-the-art variants
  (e.g. geometric SO(3) controllers, tube MPC).
- Simulation only; one run per cell (missions are deterministic).
