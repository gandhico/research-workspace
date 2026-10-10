# ACC HyperLIF: an absorbing silent latch and its learning consequence

**6 October 2026.** This continues the local-fold and two-cell studies in
`PES_CONTINUATION_FOLDS_AND_TINY_NETWORK_2026-10-06.md`. It analyzes the
specific CMG/HyperLIF parameters audited from the supplied ACC manuscript,
not all HyperLIF variants. Julia scripts use only standard libraries and
scalar states; a Python script draws one scientific figure.

**Further readout study:**
`MULTISIGNAL_READOUTS_GATE_MEMBRANE_CONDUCTANCE_2026-10-06.md` tests
raw gate, voltage, full/gate-only conductance, derivatives, and mixed
readouts with normalized PES on same-time and delayed targets.

## 1. A forward-invariant, saturated region

Write the continuous ACC cell, with `v_rest=v_reset=0`, as

\[
 \dot v=\frac{I-v}{0.05}-(120+30|I|)r^2v,\qquad
 \dot r=\frac{\sigma[50(v-1+2r)]-r}{0.005},\quad 0\le r\le1. \tag{1}
\]

The audited decoder activity is `a=clip(10^5 r,0,1)`; an upward event is
`v` crossing 1 from below. Set

\[
 r_0=0.999,\qquad B=\frac{1}{0.05(30)r_0^2}
       =0.668002003\ldots <1,\qquad
 \mathcal R=\{(v,r): |v|\le B,\ r_0\le r\le1\}. \tag{2}
\]

**Invariant-region theorem.** For every bounded, piecewise-continuous
current waveform `I(t)`, a solution of (1) starting in `R` remains in `R`.
It has no upward events and its readiness activity is identically one.
The frozen-target gate/frozen-conductance voltage step used in the small
Julia audits also preserves `R` for every positive step size.

Proof: at fixed `I,r`, voltage relaxes toward

\[
 V(I,r)=\frac{I}{1+0.05(120+30|I|)r^2}.
\]

For `r>=r0`, `|V(I,r)| <= 1/[0.05(30)r^2] <= B`. Hence the voltage
field points inward at `v=+B` and `v=-B`, regardless of the sign or
magnitude of `I`. At the lower gate boundary, its smallest sigmoid
argument in the rectangle is

\[
 50(-B-1+2r_0)=16.4998998\ldots,
 \qquad \sigma(16.4998998\ldots)=0.999999931737\ldots>r_0.
\]

The gate field points inward at `r=r0`; it points inward at `r=1`
because the sigmoid is less than one for finite voltage. This proves
forward invariance. Within `R`, `v<=B<1`, so upward events are impossible,
and `10^5r >=99900`, so clipping gives `a=1`. The numerical substeps
are convex combinations of the previous state and an in-rectangle
frozen target/steady voltage, proving the discrete claim. The practical
interpretation is stronger than a long transient: **once this particular
cell enters the rectangle, input current cannot make it recover**.
This does not exclude recovery if model parameters, gate state, or
reset mechanism are changed.

The same bounds imply a high-readiness equilibrium for every constant
finite current. The scalar equilibrium gate equation has opposite signs
at `r=r0` and `r=1`. It has exactly one root in `(r0,1)`: throughout that
interval the sigmoid argument is at least `16.4998`, and
`|V_r|<4/(3r^3)`, so its scalar derivative is strictly negative.
At this root, `r(1-r)<0.001`, the Jacobian trace is negative, and

\[
 H_r=50r(1-r)[V_r+2]-1
     <0.05\left(2+\frac{4}{3r_0^3}\right)-1 < -0.83.
\]

Since `det J=-(1/0.05+(120+30|I|)r^2)H_r/0.005>0`, this high
equilibrium is locally asymptotically stable for every finite `I`.
This is a mathematical property of the chosen strong positive gate
feedback and input-scaled conductance, not evidence of useful memory.

## 2. Fold, basins, and hysteresis

The previous directed-interval certificate located a low-branch
saddle-node at `I_f≈0.8888130904381024`. A new 256-bit logit-root audit
at `I=0.87` finds three equilibria. The logit parameter is essential:
on the high branch `1-r≈1.02×10^-24`, so a Float64 gate rounds to exactly
one and an ordinary root scan misses that branch.

| Branch at `I=0.87` | `v` | `r` | Jacobian classification |
|---|---:|---:|---|
| Low gate | 0.869979552 | 0.00179375895 | stable |
| Intermediate | 0.861651896 | 0.0364181504 | saddle |
| High gate | 0.104756171 | `1-1.02×10^-24` | stable |

The stability classifications come from the computed trace and
determinant; the previous interval result certifies the nearby *local*
fold. The logit grid locates roots but is not a global, interval-certified
enumeration of every possible equilibrium. A `11×11` initial-state grid,
integrated for 2 s at `I=0.87`, ended near the low sink in 26 cases and
the high sink in 95. No grid point was unsettled by the stated rule.
These frequencies describe this chosen grid, not a basin-volume measure.

A 1 s per-current sweep from `I=0.82` to `1.02` followed the low branch
through `0.88`, then switched to the high branch at the next sampled
current `0.89`. The reverse sweep stayed high through `0.82`. The
switching current has `0.01` resolution and is a finite-rate trajectory
observation; it is not an additional bifurcation certificate. The
absorbing-region theorem explains why lowering current alone does not
undo the high latch. A separate 1.4 s stress waveform alternating
`-1,-10,-1000,0,+1000,-1000,0` stayed in the rectangle; the lowest
observed readiness was `0.999999951` and the lowest voltage was
`-0.663570072`. This numerical check illustrates the theorem and is
not its proof.

![Sampled ACC attraction basins and current sweep](results/acc_basin_hysteresis_2026-10-06.png)

There is also a simple event obstruction outside the latch. If
`I(t)<=1`, `v(0)<1`, and `r>=0`, then at `v=1` the voltage derivative is
`(I-1)/0.05-(120+30|I|)r^2<=0`. Thus the subthreshold half-plane is
forward invariant and there are no upward events. A prior trajectory
starting *above* the threshold can have initial occupancy, but this is
not an upward crossing from below.

## 3. Quantitative consequence for PES

At a constant-current equilibrium, away from a fold,

\[
 \frac{dr_*}{dI}=-\frac{H_I}{H_r},\qquad
 H_I=50r_*(1-r_*)V_I,\qquad
 V_I=\frac{1+0.05(120)r_*^2}
             {[1+0.05(120+30I)r_*^2]^2}\quad(I>0). \tag{3}
\]

At `I=0.87`, the high branch has `dr*/dI≈5.20×10^-24`, whereas
`dv*/dI≈0.10149`. This separates **readiness information loss** from
voltage information: a voltage readout can still react to current,
while the prescribed clipped-readiness activity is exactly constant.
On the low branch, the activity itself saturates at `r>=10^-5`.
Inserting `r=10^-5` into the exact low equilibrium parameterization gives
`I≈0.7697216913`; already at `I=0.87`, the low branch has `r≈0.00179`
and `a=1`. Consequently the two distinct attracting states at `I=0.87`
are **indistinguishable to this activity readout**.

For a tiny decoder with two cells both inside `R`, its feature vector is
`a=(1,1)`. The empirical Gram matrix is

\[
 G=\frac1N\sum_k a_ka_k^T=
 \begin{bmatrix}1&1\\1&1\end{bmatrix},
 \qquad \lambda_{\min}(G)=0. \tag{4}
\]

With fixed decoder weights, its output is only the constant `w1+w2`.
For a nonconstant target over the same window, the minimum fixed-weight
mean-square error is the target's empirical variance. Ordinary or
normalized PES cannot identify the weight difference or create missing
temporal features. An online-changing decoder may chase a target during
training, but that does not give a transferable frozen decoder.
This theorem explains the earlier two-cell full-gate rank-zero result
without treating PES optimization failure as the only possible cause.
It does not imply that internal-weight sensitivity, a voltage readout,
or a different gate gain would fail in the same way.

## 4. Small operating-region map

To separate feedback and readout effects, a further two-cell fixture uses
the externally specified signal
`y(t)=A[0.8 sin(2π1.3t+φ)+0.2 sin(2π3.7t-0.4φ)]` as the target and
current splitter `I1=.75+1.25 max(y,0)`,
`I2=.75+1.25 max(-y,0)`. A two-weight least-squares decoder is fitted
on a 4 s `φ=0` waveform and tested on a fresh-state 4 s `φ=.77`
waveform. This is a **feature adequacy diagnostic**, not an online PES
training result. The model's self-feedback `gamma` and gate-readout gain
vary; the voltage readout is an additional reference. The Gram ratio is
`lambda_min/lambda_max` on training features. A ratio near one does not
guarantee fast PES learning if the absolute eigenvalues are very small.

At the higher amplitude `A=.35`, selected rows are:

| `gamma` | Readout/gain | Gram ratio | Gram max | Fresh-phase LS RMSE | Saturated test features |
|---:|---|---:|---:|---:|---:|
| 0 | readiness ×1 | 0.9604 | 0.00365 | 0.09115 | 0% |
| 0 | readiness ×100 | 0.9563 | 0.3237 | 0.09316 | 32.4% |
| 0 | readiness ×100000 | 0.1232 | 1.1542 | 0.12592 | 56.5% |
| 0 | voltage | 0.0101 | 1.3675 | **0.07515** | 0% |
| 0.5 | readiness ×100000 | 0.1705 | 1.0237 | 0.10587 | 50.3% |
| 2 | readiness ×100000 | 0.0133 | 1.8570 | 0.20295 | 94.8% |

The unrounded values are retained in the raw CSV. At `A=.08`,
all feedback strengths gave nearly the same readiness-decoder fit
(`≈0.0278` RMSE at gain `10^5`), so that easy regime conceals the
high-drive latch. At `A=.35`, reducing feedback and gain gives a more
informative readiness feature. The voltage readout can be better on
this signal, which is consistent with the equilibrium derivative in
(3). All 10 model/amplitude test trajectories had zero upward events
and zero threshold occupancy; these are continuous-state decoding
results.

An online PES follow-up trained a zero-initialized two-weight decoder for
12 s at `A=.35`, froze it, and evaluated a fresh 4 s phase. The same
five declared step sizes (`0.0002,0.0008,0.0032,0.0128,0.0512`) were
used in three regimes. Selected rows illustrate the mechanisms:

| Regime | PES step | Last 4 s online train RMSE | Frozen fresh-phase RMSE | Late Gram minimum |
|---|---:|---:|---:|---:|
| `gamma=0`, readiness gain 100 | 0.0008 | 0.08440 | **0.09384** | 0.34509 |
| `gamma=2`, readiness gain 100000 | 0.0008 | 0.18756 | 0.21515 | **0** |
| `gamma=2`, readiness gain 100000 | 0.0512 | **0.00960** | 0.23128 | **0** |
| `gamma=0`, voltage | 0.0032 | 0.11467 | 0.16505 | 0.01438 |

The high-step full-ACC decoder nearly eliminates **online** training
error by moving its weights with the target, yet its frozen decoder
transfers poorly. This is exactly the distinction required by the
rank-one feature theorem; a falling online loss alone would falsely
suggest a learned reusable representation. The reduced gate with
moderate gain has a full-rank late Gram and a frozen PES error close to
its independently fitted linear floor (`0.09316`). The voltage
features have a lower static approximation floor but a much smaller
Gram eigenvalue, so these five ordinary PES rates do not optimize their
finite-horizon frozen transfer. These are illustrative single-signal
runs, not a held-out-selected ranking or a broad learning benchmark.
All three PES regimes had zero test upcrossings and occupancy.

## 5. Reproduction and next research decision

| Item | Source | Output |
|---|---|---|
| 256-bit equilibria, 48 starts, sweep, 121 basin starts | `acc_basin_hysteresis.jl` | `results/acc_basin_hysteresis_2026-10-06.csv` |
| Extreme-current waveform | `acc_absorbing_latch.jl` | `results/acc_absorbing_latch_2026-10-06.txt` |
| Figure | `plot_acc_basin.py` | `results/acc_basin_hysteresis_2026-10-06.png` |
| Independent-target feature map | `acc_feature_operating_map.jl` | `results/acc_feature_operating_map_2026-10-06.csv` |
| Online PES rates and frozen transfer | `acc_pes_operating_map.jl` | `results/acc_pes_operating_map_2026-10-06.csv` |

Run the basin/latch scripts with
`julia --startup-file=no --compile=min theory/<script>`; use
`julia --startup-file=no -O1 theory/acc_feature_operating_map.jl` and
the same command for `acc_pes_operating_map.jl`; use
`python theory/plot_acc_basin.py` for the figure. The
feature map's compiled run completed in about 3 seconds; the earlier
standard-library small-memory scripts used about 250--280 MiB working
set. The figure was visually checked.
These are mechanism studies, not a benchmark or biological validation.
The basin grid, stress pulse, and operating map are finite numerical observations; the
invariant rectangle and its PES rank consequence are mathematical claims
under the stated model assumptions.

**Next experiment:** carry the full-rank candidate (`gamma=0`, readiness
gain 100) into a two- or three-cell recurrent fixture with an
independently specified target. Compare decoder PES, exact forward
sensitivity for one internal weight, and a matched two-state continuous
control under the same declared training and validation budget. Vary
initial conditions and test phases; keep voltage, readiness, occupancy,
and upward-event metrics separate. The full-ACC clipped-readiness
configuration remains a negative control because the invariant region
prevents a general learnability claim there.
