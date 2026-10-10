# A finite-horizon gate observability bound and a PES decoder rank test

Date: 2026-10-06. This continues the two-cell gate/membrane/conductance readout study. It gives analytic conditions for a **single locally linearized cell with a known input** and for a finite-window linear decoder. It does not prove global nonlinear observability, network learnability, or a generalization advantage.

## 1. The gate can be state-informative yet numerically unusable

Write the frozen-input linearization at an operating point as `dot δx=A δx`, `δx=(δv,δr)`, `A=[[a,b],[c,d]]`, with raw gate output `δy=[0,1]δx`. For the ACC-type readiness equation,

`c=∂dot r/∂v = α s(1-s)/τ_r`, where `s=σ[α(v−1+γr)]`.

Let `W_r(T)=∫_0^T exp(Aᵀt) C_rᵀ C_r exp(At) dt`, `C_r=[0,1]`, and choose `M≥||A||₂`. The voltage-initial-direction output is `y(t)=e₂ᵀ exp(At)e₁`. Because `y(0)=0` and `dot y=c x₁+d y`, while `|x₁(t)|≤exp(Mt)`, variation of constants gives

`|y(t)|≤|c| t exp(Mt)`.

Therefore

`λ_min(W_r(T)) ≤ e₁ᵀ W_r(T)e₁ ≤ c² T³ exp(2MT)/3`.  **(1)**

This is an upper bound: it proves that no uniform positive observability margin exists as the sigmoid slope tends to zero on a latch. It does not establish a lower bound at moderate slope. For a short horizon with fixed nonzero `c`, direct expansion gives `λ_min(W_r(T)) = c²T³/12 + O(T⁴)`; the leading `1/12` results from subtracting the squared cross term in the two-by-two Gramian. If `c=0`, the linearized voltage direction is unobservable from raw gate alone. If the implemented *clipped* gate is saturated, its output Jacobian is zero and `W_clip(T)=0` exactly within that clipping region.

By contrast, if membrane and raw gate are both exposed directly, `C_vr=I₂`. Since `σ_min(exp(At))≥exp(−Mt)`, their state-observability Gramian obeys

`W_vr(T) ≽ [(1−exp(−2MT))/(2M)] I₂` for `M>0`, with limit `T I₂` when `M=0`.  **(2)**

This is a local state-reconstruction fact under the frozen linearization. It does **not** say that either state changes enough along a particular training trajectory to identify all decoder coefficients or represent an external target.

## 2. A finite-window bound for the PES feature Gram

Let the decoder feature vector contain a bias and a gate, `φ_k=(1,...,r_k,...)`, and let `G_N=N⁻¹Σ φ_k φ_kᵀ`. Suppose `|r_k−r₀|≤ε` on the training window. Choose the unit coefficient vector with bias entry `−r₀/sqrt(1+r₀²)`, gate entry `1/sqrt(1+r₀²)`, and every other entry zero. Its Rayleigh quotient gives

`λ_min(G_N) ≤ ε²/(1+r₀²)`.  **(3)**

The inequality holds regardless of what voltage, conductance, reset-current, or derivative columns are added: the selected bias/gate direction remains nearly null. With `r₀=1` and a clipped latch (`ε=0` in the implemented readout), the full decoder Gram is singular. Additional informative columns may still predict the target well; the individual bias and gate weights are then not uniquely identifiable from that window. Projection or regularization can select a weight vector but cannot create information about this null direction.

For the settled full-conductance readout, `c_i=(120+30I_i)r_i²`, a nearly constant high gate leaves a direct applied-current path. In the exact `r₁=r₂=1` limit of the paired split drive, `c₁−c₂=37.5u(t)`, so a same-time target can be decoded algebraically even though the gate columns are unidentifiable. A good conductance score in that regime is evidence for the input path, not for dynamic gate information. The delayed target and the raw-gate ablation in the companion study test temporal information more directly.

## 3. Consequence for tiny-network learning experiments

Report three separate quantities: (i) a local state-observability margin or its bound, (ii) the trajectory's decoder-feature Gram spectrum after explicitly stated scaling, and (iii) held-out target error. The first concerns reconstructing `(v,r)` under known drive; the second concerns identifying a chosen linear decoder on a finite trajectory; the third concerns task representation and transfer. None implies either of the others without extra assumptions. For a coupled network, cross-cell paths change `A` and may restore a direction hidden in one cell; equations (1)–(2) must then be recomputed for the actual coupled Jacobian. The near-collinear decoder-feature argument (3) remains valid whenever a gate feature stays near a constant, independent of those dynamics.

This gives a precise claim for the advisors: the gate is potentially rich in the dynamic reduced-feedback regime, while the high clipped gate has a provably vanishing state-observability margin and a near-null PES decoder direction. It supports restricting or actively avoiding the latch before claiming gate-based learning, rather than treating a nearly constant gate as a useful nonlinear feature.
