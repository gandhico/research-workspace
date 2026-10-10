# HyperLIF small-network readouts: gate, membrane, conductance, and combinations

**6 October 2026.** This responds to the request to test information in the
gate and other internal signals. It continues
`ACC_ABSORBING_LATCH_AND_PES_IDENTIFIABILITY_2026-10-06.md`.
All results use two paired ACC-type cells, the same fixed external
sinusoidal current splitter, standard-library Julia, and no dataset,
GPU, automatic differentiation, or large model. They are readout and
online-decoder mechanism studies, not recognition benchmarks.

## 1. Readouts and evaluation design

The drive is `u(t)=0.35[0.8 sin(2π1.3t+φ)+0.2 sin(2π3.7t-0.4φ)]`, with
`I1=.75+1.25 max(u,0)` and `I2=.75+1.25 max(-u,0)`. We test both the
same-time target `y(t)=u(t)` and a causal memory target
`y(t)=u(t-0.02 s)` (plus a 0.05 s delay in the diagnostic grid).
For the initial interval `t<delay`, the delayed target is defined as
zero, matching the un-driven prehistory of the fresh cell.
Training uses phase `φ=0`; two fresh-state phases, `0.77` and `1.91`,
are evaluated separately. Each trajectory lasts 12 s. The first 4 s
are the **cold-start** window and the last 4 s are the **settled**
window. The cell has no hard reset at a threshold event; the event
surface is monitored only.

Thirteen causal readout sets were compared:

| Signal family | Two-cell feature definition |
|---|---|
| Raw gate | `(r1,r2)` |
| Clipped gate | `(clip(10^5 r1),clip(10^5 r2))` |
| Membrane | `(v1,v2)` |
| Full conductance | `((120+30\|I1\|)r1²,(120+30\|I2\|)r2²)` |
| Gate-only conductance | `(120r1²,120r2²)` |
| Reset current | `(c1v1,c2v2)` |
| Gate target and gate flux | sigmoid target, or `(r_new-r_old)/dt` |
| Membrane difference rate | `(v_new-v_old)/dt` |
| Combinations | `v+r`, `v+c`, `r+c`, and `v+r+c` |

The gate-only conductance control removes the **direct applied-current
factor** from full conductance. For least-squares diagnostics, each
feature is centered and scaled using only its training window; columns
with training standard deviation `<=10^-12` are dropped, and a bias is
fitted. A thin SVD supplies the linear coefficients and effective rank.
The quoted fresh-phase RMSE pools the two evaluation phases equally.
The fits are diagnostic approximation limits for these readouts, not
claims that PES will attain them in a finite online run.

### Local state observability calculation

The readout comparison has a simple mathematical interpretation. For a
single cell with known, locally constant input, let
`x=(v,r)`, `F=dot(v)`, `G=dot(r)`, and
`s=σ[α(v-1+γr)]`. The first two continuous-time output derivatives
give the local observability matrices

\[
 \mathcal O_{r}=\begin{bmatrix}
 0&1\\ \alpha s(1-s)/\tau_r&(\alpha\gamma s(1-s)-1)/\tau_r
 \end{bmatrix},\quad
 \det\mathcal O_r=-\frac{\alpha s(1-s)}{\tau_r}, \tag{1}
\]

\[
 \mathcal O_{v}=\begin{bmatrix}1&0\\
 -(1/\tau_v+Cr^2)&-2Crv
 \end{bmatrix},\quad
 \det\mathcal O_v=-2Crv,\quad C=120+30|I|. \tag{2}
\]

Thus the **raw gate is locally state-observable in exact arithmetic**
when its sigmoid slope is nonzero, but that determinant becomes
exponentially small on the high latch. At `I=0.87`, the high gate has
`1-r≈10^-24`, so `|det O_r|≈10^-20`; Float64 rounds the gate to one.
The clipped gate has zero output derivative once saturated, so its
local observability is lost exactly in the implemented readout.
Voltage retains a nonzero determinant when `r,v,C` are nonzero, while
it can become ill-conditioned near `r=0`. A pair exposing both `v`
and raw `r` directly has an identity instantaneous state Jacobian,
although a particular trajectory can still have a poor feature Gram
for target learning. State observability, target approximation, and
PES excitation are different requirements.

For full conductance `h=C(I)r²` at fixed known current, its first
two-derivative observability determinant is
`-(2Cr)² αs(1-s)/τr`: the state dependence still runs through `r`
and inherits the gate-slope problem. Yet
`∂h/∂I=30 sign(I)r²` is a **direct input path**. This
explains why its target-decoding score can improve even when the gate
itself carries essentially no state variation.

## 2. The gate is informative when it remains dynamic

Selected same-time target results (fresh-phase linear-fit RMSE) are:

| Gate feedback | Readout | Cold start | Settled |
|---:|---|---:|---:|
| `γ=0` | raw gate | 0.09047 | 0.08426 |
| `γ=0` | clipped gate | 0.13015 | 0.13008 |
| `γ=0` | membrane | 0.07688 | 0.07763 |
| `γ=0` | **membrane + raw gate** | **0.06527** | **0.06540** |
| `γ=0` | membrane + full conductance | 0.06361 | 0.06379 |
| `γ=0` | membrane + gate + conductance | 0.06368 | 0.06392 |
| `γ=2` | raw gate | 0.20385 | 0.20547 |
| `γ=2` | membrane | 0.19680 | 0.01170 |
| `γ=2` | membrane + raw gate | 0.15396 | 0.01170 |
| `γ=2` | full conductance | 0.20061 | `≈2×10^-15` |
| `γ=2` | gate-only conductance | 0.20383 | 0.20547 |
| `γ=2` | membrane + gate + conductance | **0.02248** | `≈10^-15` |

At `γ=0`, the gate adds useful, transferable information to membrane
voltage. It lowers cold RMSE from `0.07688` to `0.06527` and settled
RMSE from `0.07763` to `0.06540`. Its state is a nonlinear, filtered
summary of voltage history, so this complementarity is plausible and
worth studying as a learning representation. The result is specific to
this simple waveform and linear decoder.

The intermediate `γ=0.5` case shows that *which gate observable* matters:
the clipped gate alone achieved cold/settled RMSE `0.11577/0.11578`,
while raw gate alone gave `0.18515/0.18443`. A nonlinear gate transform
can help a linear readout, although the gain `10^5` is an aggressive
choice and should be tested over a broader target family.

At the ACC `γ=2` setting, the raw gate helps during the transient but
is constant on the settled window. Its two settled columns have
effective rank zero under the stated `10^-12` variation threshold;
adding them to membrane changes no settled fit. This matches the
invariant-latch theorem in the preceding note. A transient `v+r+c`
fit improves substantially over `v+c` (`0.02248` versus `0.06982`),
so a gate can still convey **transition history** before the latch.

![Cold-start and settled readout transfer](results/acc_multisignal_readout_2026-10-06.png)

## 3. Why full conductance becomes exactly decodable

The exceptionally small settled error for full conductance at `γ=2`
needs a mechanistic interpretation. In the limiting case `r1=r2=1`,
and because both injected currents are positive,

\[ 
 c_1-c_2=30(I_1-I_2)=30(1.25)u(t)=37.5u(t). \tag{3}
\]

Thus `u(t)=(c1-c2)/37.5` is an exact algebraic input path in that
limiting case. On the sampled settled trajectory both gates stayed
within a few Float64 ulps of one, and the maximum identity residual
was `1.33×10^-15`. The numerical settled linear-fit error is likewise
at roundoff, about `2×10^-15`. In the continuous equations the gates
remain slightly below one, so this identity is approximate but
extraordinarily accurate in the latched region.
Gate-only conductance `120r²` has rank zero and cannot reconstruct the
waveform there. **Full conductance is informative, but this particular
information is carried by its direct current multiplier.** It should
not be attributed to rich gate dynamics or event coding.

The 20 ms delayed target removes the exact same-time identity. At
`γ=0`, the settled linear-fit errors are `0.05085` for membrane alone,
`0.03601` for membrane plus raw gate, and `0.03467` for membrane plus
full conductance. This is a more direct test of temporal information in
the gate. At `γ=2`, settled raw gate remains uninformative (`0.20554`),
while membrane plus conductance reaches `0.00941`; the voltage and
same-time input conductance jointly carry a useful short memory trace.
The 50 ms delay grid is saved as a robustness check, not an optimized
delay benchmark.

## 4. Can PES use the mixed signals?

For each readout, a normalized online PES decoder is trained over 12 s:

\[
 w_{k+1}=w_k+\eta\,
 \frac{(y_k-\widehat y_k)[1;x_k]}{1+\|[1;x_k]\|^2},
 \qquad \widehat y_k=w_k^T[1;x_k]. \tag{4}
\]

The features `x` are standardized by an **unlabelled training-only**
prepass. The same steps `η∈{10^-4,4·10^-4,1.6·10^-3,6.4·10^-3}` are
used for every readout. For each readout, the step is chosen by the
root-mean-square of the cold and settled errors on phase `0.77`;
phase `1.91` is then reported without selecting on it. Frozen decoder
weights are evaluated on fresh cell states. Selected rows for the
20 ms delayed target are:

| Feedback | Readout | Chosen PES step | Held-out cold RMSE | Held-out settled RMSE |
|---:|---|---:|---:|---:|
| `γ=0` | raw gate | 0.0004 | 0.07954 | 0.07150 |
| `γ=0` | membrane | 0.0004 | 0.05537 | 0.05055 |
| `γ=0` | **membrane + raw gate** | 0.0016 | **0.03695** | **0.03649** |
| `γ=0` | membrane + conductance | 0.0016 | 0.03575 | 0.03528 |
| `γ=2` | raw gate | 0.0001 | 0.20385 | 0.20825 |
| `γ=2` | membrane + gate + conductance | 0.0064 | 0.16522 | 0.05670 |

This PES result independently supports the gate's contribution at
`γ=0`: adding raw gate to membrane improves both held-out windows on
the delayed target. At `γ=2`, the very large cold-to-settled shift
prevents this one fixed PES decoder from approaching the best separate
linear fits in both regimes. If PES is trained repeatedly **only on the
settled** `γ=2` window, full conductance reaches `5.51×10^-7` held-out
RMSE after ten passes, while raw gate remains near `0.21`. That
settled success uses the direct-current identity (3). It is not
evidence that the latched gate recovered information.

Across all tested trajectories the upward-event and threshold-occupancy
counts were zero. These are analog state and algebraic readouts. There
are no seed statistics or learned internal weights in this readout
study; the earlier one-weight forward-sensitivity experiment remains
the separate credit-assignment result.

## 5. Reproduction and next theory step

| Purpose | Script | Raw output |
|---|---|---|
| Same-time linear fits | `acc_multisignal_readout.jl` | `results/acc_multisignal_readout_2026-10-06.csv` |
| 20 and 50 ms delayed fits | `acc_delayed_readout.jl` | `results/acc_delayed_readout_2026-10-06.csv` |
| Same-time normalized PES | `acc_multisignal_pes.jl` | `results/acc_multisignal_pes_2026-10-06.csv` |
| 20 ms delayed normalized PES | `acc_multisignal_pes.jl 0.02` | `results/acc_multisignal_pes_delay020_2026-10-06.csv` |
| Validation-selected PES summaries | `summarize_multisignal_pes.py` | `results/acc_multisignal_pes_delay020_selected_2026-10-06.csv` |
| Settled-only PES control | `acc_settled_pes.jl` | `results/acc_settled_pes_2026-10-06.csv` |
| Figure | `plot_multisignal_readouts.py` | `results/acc_multisignal_readout_2026-10-06.png` |

From the project root, run Julia with `julia --startup-file=no -O1
theory/<script>` and Python with `python theory/<script>`. The data
arrays hold at most three `24000×19` Float64 matrices, roughly 11 MB
of trajectory values, plus small readout matrices and Julia runtime.
All outputs are exploratory deterministic fixtures. The figure was
visually inspected.

Next, extend the local determinants (1)--(2) to **finite-horizon
observability and decoder Gramians**, including when the gate adds a
linearly independent temporal direction and when the direct `I` term in
conductance acts as an input bypass. Then compare PES and one-weight
forward sensitivity on an independently specified recurrent memory
task using a matched continuous-state control. Gate-rich claims should
be stated for the operating region and readout actually measured.

**Analytic continuation, later 2026-10-06:**
`GATE_OBSERVABILITY_DECODER_GRAM_BOUNDS_2026-10-06.md` now supplies a
finite-horizon upper bound proportional to the squared sigmoid slope,
a positive local bound for jointly observed membrane and raw gate, and
a finite-window near-null direction for the bias-plus-latched-gate PES
decoder Gram. It separates state observability from coefficient
identifiability and held-out target error. The independent recurrent
memory comparison remains open.
