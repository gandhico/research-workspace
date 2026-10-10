# Internal connection learning in two coupled cells: horizon and gate regime

**6 October 2026.** This executes the next step in
[`RESEARCH_STATUS_AND_NEXT_2026-10-06.md`](RESEARCH_STATUS_AND_NEXT_2026-10-06.md).
It extends the earlier single-regime [reduced-CMG connection study](PES_CONTINUATION_FOLDS_AND_TINY_NETWORK_2026-10-06.md)
and the first [HH comparison](HH_HYPERLIF_TINY_COMPARISON_2026-10-06.md).
All runs are standard-library Julia, scalar-state streaming, with no AD
tape, dataset, GPU, or large package stack. The result is about **one
teacher-generated internal connection**, not a recognition benchmark or
general network learning claim.

## 1. Declared model and derivative

Each pair has one learned directed connection `θ` from cell 2 to cell 1
and one fixed reciprocal connection. Currents use states from the **start**
of each 0.5 ms observation interval; they are held fixed while a canonical
HH cell integrates with 20 RK4 steps of 0.025 ms:

\[
I_1=I_b+8\max(u,0)+\theta q(V_2),\qquad
I_2=I_b+8\max(-u,0)+0.5q(V_1),\quad
q(V)=\sigma[(V+60)/10].
\]

The teacher uses `θ*=0.7`; the student starts at zero. The supervised
output is `(V1−V2)/20`. `hh_quiet` uses `I_b=0` and the standard −65 mV
rest initialization; `hh_tonic` uses `I_b=8` from that same initialization;
`hh_eq8` uses `I_b=8` but initializes both cells at the **uncoupled**
constant-`I=8` equilibrium. The fixed reciprocal current means that this
last point is *not* a coupled-system equilibrium. All three use the same
1-second waveform with phase `0` for training, fresh phase `0.77` for
validation, and phase `1.91` for one test. There is no test selection.

For `S_i=∂x_i/∂θ`, the **exact forward sensitivity of the discretized
sample-and-hold model** uses

\[
\partial_\theta I_1=q(V_2)+\theta q'(V_2)S_{V2},\qquad
\partial_\theta I_2=0.5q'(V_1)S_{V1},\qquad
\dot S_i=J_{HH}(x_i)S_i+e_V\partial_\theta I_i
\]

inside each held-current interval. The detached **local eligibility**
keeps only `∂θI1≈q(V2)` and sets `∂θI2≈0`, while still propagating each
cell's own sensitivity. Both are constant-memory traces. The internal
update after each fixed-`θ` episode is

\[
\theta\leftarrow\Pi_{[-1.5,1.5]}
\left(\theta-\eta\,\frac{\overline{(y-y^*)J}}
 {\overline{J^2}+10^{-6}}\right),\qquad J=\partial_\theta y.
\]

This is a **normalized PES-style eligibility update**; it is not the
unmodified decoder PES of the ACC paper. The exact-trace numerator is the
fixed-episode voltage loss gradient. The local numerator is approximate.
Gains `0.25,0.5,1` are selected separately for each method on validation.

## 2. Full horizon versus short-to-long horizon

Both schedules make **18 parameter updates**. The full schedule uses
18 one-second episodes (36,000 observation steps). The continuation
schedule uses three updates at each of `20,50,100,250,500,1000 ms`
(11,520 observation steps). The latter therefore uses fewer simulated
steps as well as changing the optimization path. It is a mechanism test,
not a matched wall-clock comparison.

| HH regime | Method | Full-horizon selected `θ`, test RMSE | Continuation selected `θ`, test RMSE | Teacher test upcrossings |
|---|---|---:|---:|---:|
| Quiet | exact | `0.7000`, `3.6×10⁻¹⁶` | `0.7000`, `0` | 0 |
| Quiet | local | `0.7000`, `0` | `0.7000`, `0` | 0 |
| Tonic from rest | exact | `−0.0663`, `2.109` | `0.7000`, `4.6×10⁻¹³` | 131 |
| Tonic from rest | local | `−0.0654`, `2.109` | `0.7000`, `4.4×10⁻¹³` | 131 |
| Near uncoupled equilibrium | exact | `1.4991`, `1.627` | `0.7000`, `5.4×10⁻¹²` | 66 |
| Near uncoupled equilibrium | local | `1.4118`, `1.648` | `0.7000`, `5.1×10⁻¹²` | 66 |

The full-horizon results and finite-difference check are in
[`results/hh_coupled_weight_learning_2026-10-06.csv`](results/hh_coupled_weight_learning_2026-10-06.csv);
the continuation gradients and validation-selected tests are in
[`results/hh_coupled_horizon_audit_2026-10-06.csv`](results/hh_coupled_horizon_audit_2026-10-06.csv).
The teacher model at exactly `θ*=0.7` reproduces its target and crossing
count to numerical precision, so poor full-horizon scores are optimization
failures on this **realizable** fixture, not lack of representational
capacity.

At `θ=0` in tonic HH, the full-one-second exact loss gradient is
`+3.64193`, moving a descent update **away** from the teacher's positive
connection. At 20 ms it is `−0.20683`; it remains negative through
500 ms in this trajectory. The short window thus enters the teacher's
basin before the spike-phase mismatch dominates the long-horizon loss.
At 20 ms and gain 1, three exact updates reach `θ≈0.70048`; after the
50 ms stage it reaches `0.7` to printed precision. This is a concrete
continuation effect, not a theorem that short windows always help.

The exact gradient at zero agrees with a central difference: tonic HH
`3.64193259` versus `3.64205206` for a `10⁻⁴` weight step.
Across `θ=0,0.35,0.65` and 20/1000 ms, a finer `10⁻⁵` difference checks
the tangent in
[`results/hh_coupled_gradient_grid_2026-10-06.csv`](results/hh_coupled_gradient_grid_2026-10-06.csv).
The local trace is **not globally accurate**: at tonic `θ=0.35` and
one second it gives `0.12487` versus exact gradient `0.00719`.
Its success under continuation therefore cannot be interpreted as an
exact-gradient guarantee.

With the gain fixed to 1 from the main `θ*=0.7` validation run, an
exploratory sweep of teacher weights `0.3,0.5,0.7,0.9` recovered each
connection to printed precision for all three HH initial regimes and
both eligibility methods. This tests a narrow one-parameter family;
it is not independent-task generalization. See
[`results/hh_coupled_weight_sweep_2026-10-06.csv`](results/hh_coupled_weight_sweep_2026-10-06.csv).

## 3. HyperLIF gate access and saturation

The coupled ACC-type HyperLIF pair uses
`I1=.75+1.25 max(u,0)+θ(v2−.75)`,
`I2=.75+1.25 max(−u,0)+.9(v1−.75)`, with `θ*=0.7` and
gate feedback `γ=0` or `2`. Targets are teacher voltage difference,
raw-gate difference, or their stated sum. Exact and local eligibility
use the corresponding membrane/gate tangent. The same 18-update
full versus continuation schedules and validation-selected gains apply.
All these one-second trajectories have **zero threshold upcrossings and
zero occupancy**: learning uses continuous states.

| Regime/readout | Full exact: selected `θ`, test RMSE | Full local: selected `θ`, test RMSE | Continuation exact: selected `θ`, test RMSE | Continuation local: selected `θ`, test RMSE |
|---|---:|---:|---:|---:|
| `γ=0`, voltage | `0.7000`, ≈0 | `0.6999`, 0.000155 | `0.7000`, 0 | `0.7000`, <10⁻⁹ |
| `γ=2`, voltage | `0.5792`, 0.829 | `0.7000`, 0.000045 | `0.7000`, 0 | `0.7000`, <10⁻⁷ |
| `γ=2`, gate only | `0.6909`, 0.00920 | `0.6673`, 0.0303 | `0.4704`, 0.123 | `0.5641`, 0.0904 |
| `γ=2`, voltage+gate | `0.4818`, 1.327 | `0.7000`, 0.000038 | `0.7000`, 0 | `0.7000`, <10⁻⁷ |

The complete grid is
[`results/hyper_coupled_regime_learning_2026-10-06.csv`](results/hyper_coupled_regime_learning_2026-10-06.csv).
In the saturated `γ=2` gate-only case, initial exact eligibility energy
`mean J²` is **3.196** in the first 200 ms and approximately
**3.8×10⁻³³** in the final 200 ms. Information about the connection is
present mainly in the transition; the settled gate is effectively
uninformative in Float64. A long gate-only run can still use its repeated
initial transients, explaining the reasonably close full-horizon result.
The short-to-long schedule emphasizes its early windows and is not the
best schedule for this gate-only readout. Voltage retains a path to the
internal weight after the gate saturates.

The full-horizon local rule sometimes outperforms the exact-gradient
update in this nonconvex single-parameter fixture. This is an optimizer
path observation. It does not mean the local trace is more faithful:
for `γ=2` voltage at `θ=0`, its gradient is `−2.763` versus the exact
`−0.675`. A biased eligibility can act like a different step direction
or gain; later tasks must compare tuning, stability, and unseen targets.

## 4. What has been saved and what remains

The scripts are
[`hh_coupled_weight_learning.jl`](hh_coupled_weight_learning.jl),
[`hh_coupled_horizon_audit.jl`](hh_coupled_horizon_audit.jl),
[`hh_coupled_gradient_grid.jl`](hh_coupled_gradient_grid.jl),
[`hh_coupled_weight_sweep.jl`](hh_coupled_weight_sweep.jl), and
[`hyper_coupled_regime_learning.jl`](hyper_coupled_regime_learning.jl).
The HH continuation run sampled **302.1 MiB** peak process working set;
the HyperLIF coupled run sampled **312.5 MiB**. These are process-level
Windows samples including Julia compilation/runtime, not data-only
storage. The principal network state and sensitivity storage remains
constant with trajectory length.

The next scientific test must use an **independent external target**
(such as delayed signal reconstruction or a tiny evidence-integration
task), with a jointly or fairly fitted readout. Otherwise exact teacher
parameter recovery may overstate practical learning. We also need a
matched two-state leaky coupled control, multiple input waveforms/initial
states, and numerical resolution checks for the coupled HH optimization
path. Claims about task generalization or superiority should wait for
those controls.
