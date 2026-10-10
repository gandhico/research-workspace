# Canonical HH, HyperLIF, and adaptive leaky cells: a tiny learning study

**6 October 2026.** This is a low-memory mechanism experiment, continuing
[`HH_JAXLEY_BASELINE_EVIDENCE_2026-10-06.md`](HH_JAXLEY_BASELINE_EVIDENCE_2026-10-06.md)
and the prior [multi-signal HyperLIF readout study](MULTISIGNAL_READOUTS_GATE_MEMBRANE_CONDUCTANCE_2026-10-06.md).
It is not a benchmark reproduction of Jaxley's detailed HH-type network.
The canonical HH parameters are those of the conventional four-state
voltage/sodium/potassium/leak formulation, in the lineage of the
[original Hodgkin–Huxley paper](https://doi.org/10.1113/jphysiol.1952.sp004764).

## Model, task, and learning rule

Two uncoupled cells receive rectified branches of the same signal
`u(t)=0.35[0.8 sin(2π1.3t+φ)+0.2 sin(2π3.7t−0.4φ)]` for 12 seconds. The
decoder target is `u(t−20 ms)`, with zero prehistory. The phases are `0`
(train), `0.77` (validation), and `1.91` (one held-out test), always with
fresh cell states. A zero predictor has test RMSE **0.2045**.

The models and currents are explicitly **regime probes, not matched
operating-point calibrations**:

| Model | States per cell | Current to each branch | Initial state |
|---|---:|---|---|
| `hh_rest` | `V,m,h,n` | `8 max(±u,0)` µA/cm² | standard −65 mV resting gates |
| `hh_tonic` | `V,m,h,n` | `8+8 max(±u,0)` µA/cm² | standard −65 mV resting gates |
| `hh_eq8` | `V,m,h,n` | same as `hh_tonic` | exact constant-current `I=8` equilibrium |
| `hyper_g0` | `v,r` | `0.75+1.25 max(±u,0)` | `(0,0)`, gate feedback `γ=0` |
| `hyper_g2` | `v,r` | same | `(0,0)`, gate feedback `γ=2` |
| `leaky_adaptive` | `V,a` | `7+4 max(±u,0)` | `(−65,0)` |

The leaky control obeys `τV V̇=−(V+65)+2I−a` and
`τa ȧ=0.25(V+65)−a`, with `τV=50 ms`, `τa=25 ms`. It is a **continuous
adaptive leaky state**, with no hard threshold reset; it is not a standard
spike-reset ALIF network. Its linear transfer function is

\[
\frac{V(s)+65}{I(s)}=
\frac{2(1+0.025s)}{(1+0.05s)(1+0.025s)+0.25}.
\]

This explicit two-state filter is an important control: useful delayed
information does not by itself imply a special advantage for nonlinear
HyperLIF gating.

HH uses classical `g_Na=120`, `g_K=36`, `g_L=0.3` mS/cm²,
`E_Na=50`, `E_K=−77`, and `E_L=−54.387` mV. Coupled HH ODEs use RK4 at
`0.025 ms`; all models are observed at `0.5 ms`. HyperLIF uses the same
frozen-target/frozen-conductance substeps as the earlier ACC readout study.

The only trained quantities in the task comparison are **linear decoder
weights**. Each readout is centered and standardized from its training
trajectory alone, excluding nearly constant columns. Normalized online
PES takes the discrete form

\[
w_{k+1}=w_k+\frac{\eta\,[y_k-w_k^\top(1,x_k)]}{1+\|x_k\|_2^2}(1,x_k).
\]

Four learning rates are selected on the validation cold/settled pooled
RMSE; the final test is then evaluated once. A train-set SVD least-squares
decoder gives a representation/optimization diagnostic, not an online
learning result. Causal 20 and 50 ms low-pass readouts add decoder states;
they are not free intrinsic HH gates. Applied current itself is never a
decoder feature. HyperLIF's *full* conductance does contain an algebraic
`|I|` factor, so the state-only conductance is the cleaner gate control.

## Held-out 20 ms delay results

| Regime and readout | Features | PES test RMSE | LS test RMSE | Test upcrossings |
|---|---:|---:|---:|---:|
| HH subthreshold, voltage | 2 | 0.05061 | 0.04937 | 0 |
| HH subthreshold, all raw gates | 6 | 0.03955 | 0.00854 | 0 |
| HH subthreshold, all gates + 20 ms causal filter | 6 | **0.00993** | 0.00933 | 0 |
| HH subthreshold, `n` only + 20 ms filter | 2 | **0.01045** | 0.00888 | 0 |
| HH tonic from −65 mV, voltage | 2 | 0.20618 | 0.20461 | 1,551 |
| HH tonic from −65 mV, voltage+gates + 50 ms filter | 8 | 0.09985 | 0.06886 | 1,551 |
| HyperLIF `γ=0`, voltage | 2 | 0.05290 | 0.05072 | 0 |
| HyperLIF `γ=0`, voltage+raw gate | 4 | 0.03673 | 0.03607 | 0 |
| HyperLIF `γ=0`, voltage+state-only conductance | 4 | 0.03543 | 0.03480 | 0 |
| HyperLIF `γ=2`, voltage+gate | 4 | 0.19455 | 0.12321 | 0 |
| Adaptive leaky control, voltage | 2 | 0.02896 | 0.02780 | 0 |
| Adaptive leaky control, voltage+adaptation | 4 | 0.01461 | 0.00517 | 0 |

The full grid, including same-time targets, individual HH `m/h/n` gates,
all low-pass variants, validation scores, event counts, and occupancy counts,
is [`results/hh_hyperlif_tiny_pes_2026-10-06.csv`](results/hh_hyperlif_tiny_pes_2026-10-06.csv).
The primary observation is conditional: **gates are informative in the
subthreshold regime, but spiking alone does not guarantee a useful
instantaneous linear feature.** The two-state linear control beats the
tested unfiltered HyperLIF decoder on this particular slow signal. The
best HH subthreshold score needs a causal readout filter and therefore
additional state and features. No superiority ranking follows from these
different operating points, current scales, or feature budgets.

## A basin-dependent failure at the same HH current

At constant `I=8`, numerical equilibrium is
`(V,m,h,n)=(-60.353376,0.090066,0.430453,0.390635)`.
The numerically evaluated Jacobian eigenvalues (per ms) are approximately
`−4.6903`, `−0.1350`, and `−0.03446 ± 0.56684i`: this equilibrium is
**locally linearly stable**. Yet a 4-second constant-current trajectory
started from the standard −65 mV rest state yields 250 crossings, with
late mean interspike interval **16.008 ms**; the equilibrium state yields
zero crossings. Holding its gates fixed at the equilibrium values while
perturbing only voltage by ±2 mV yielded no late crossings, whereas a
perturbation of ±5 mV did. These finite trajectories support coexistence
of a stable fixed point and sustained firing for the tested paths; they do
not prove a complete basin boundary or a periodic-orbit theorem.
See [`results/hh_local_audit_2026-10-06.csv`](results/hh_local_audit_2026-10-06.csv)
and [`results/hh_constant_basin_2026-10-06.csv`](results/hh_constant_basin_2026-10-06.csv).

The driven `hh_eq8` condition makes the learning consequence concrete.
The training phase remains subthreshold (**zero events**), whereas fresh
validation and test phases enter spiking after **7.275 ms** and **5.100 ms**
and produce **776** and **775** crossings. Consequently, the best tested
PES readout still has test RMSE **0.494**, worse than the 0.2045 zero
predictor. Train-only standardization magnifies the extrapolation because
the test features occupy a different dynamical regime. This is an explicit
example of why phase/initial-state changes must be included when claiming
learnability.

## Exact local parameter sensitivity and its limitation

For `x=(V,m,h,n)` and sodium conductance `g_Na`, the smooth-trajectory
sensitivity `S=∂x/∂g_Na` obeys

\[
\dot S=J(x,I,g_{Na})S+b(x),\qquad
b(x)=\bigl[-m^3h(V-E_{Na})/C,0,0,0\bigr]^\top,
\]

with fixed initial state and `S(0)=0`. The [forward-sensitivity script](hh_forward_sensitivity.jl)
integrates this 4-component tangent alongside the four HH states using
the same RK4 stages. It differentiates **continuous voltage/gate dynamics**,
not hard crossing counts or branch changes. At constant `I=8` from −65 mV,
the 12-second terminal `∂V/∂g_Na` is **164.839 mV/(mS/cm²)**;
a centered `±0.001` conductance finite difference gives **164.828**
(relative difference `6.8×10⁻⁵`). At the fixed stable equilibrium start,
the corresponding tangent is only **0.01440**. The large difference is a
property of operating trajectory and horizon, not a contradiction between
derivative methods. The complete check is
[`results/hh_forward_sensitivity_2026-10-06.csv`](results/hh_forward_sensitivity_2026-10-06.csv).

This supplies a constant-memory reference for internal-parameter learning.
It also warns that a locally correct gradient can be unhelpful when a
parameter update or new input phase crosses an attraction-basin boundary.
That issue should be studied before transferring a successful decoder-only
PES result to trainable HH or HyperLIF internal conductances.

## Numerical and resource checks

Halving HH RK4 step to `0.0125 ms` preserved **all upcrossing counts** in
the three tested phases of the three HH conditions; tonic voltage RMS
differences were `0.014–0.015 mV` (some sample occupancy counts differed
by one). See [`results/hh_resolution_audit_2026-10-06.csv`](results/hh_resolution_audit_2026-10-06.csv).
The main run sampled a peak Windows process working set of **375.4 MiB**;
this includes the Julia runtime and SVD workspaces, not just stored data.
Only the current model's three `24,000×14` feature matrices are retained
(about 8.1 MB of raw Float64 feature data), plus small derived matrices.

## Next precise experiment

Use an actual **coupled two-cell** system and learn one internal connection
with exact forward sensitivity and a declared PES-style local approximation.
Train and test across a small grid of initial basins and currents rather
than one phase. Match readout feature count and external filter state count
between HH, HyperLIF, and the adaptive leaky control. Report whether the
local rule tracks exact sensitivity in a fixed smooth regime and how it
fails near switching or saturated-gate conditions. This study has not yet
tested recurrent HH learning or an evidence-integration task.

### Reproduce

From this directory, run `julia --startup-file=no hh_hyperlif_tiny_pes.jl`,
`hh_local_audit.jl`, `hh_constant_basin.jl`,
`hh_forward_sensitivity.jl`, and `hh_resolution_audit.jl`, directing their
CSV output to `results/` as named above. No package installation or large
dataset is needed.
