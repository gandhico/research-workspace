# ACC closed-loop stability: proof options and exact boundary of the present claim

Date: 2026-10-06. Source: `C:/Users/gandhico/Downloads/Online_PES_Decoder_HyperLIF_Residual_Control___Quaternion_Tracking (39).pdf`, especially Sections II–V and Remark 2. This note is a proposed theorem and proof route, **not a completed closed-loop proof**.

## What the attached paper already proves

Proposition 1 proves, for the implemented discrete CMG step and projected PES decoder, gate and membrane invariance, bounded weights, `u_k in U`, `|u_k-u_{0,k}|_i <= beta ell_i`, and exact requested-baseline recovery at `beta=0`. It does not prove stability of the rigid body, feasibility of the requested wrench after rotor clipping, asymptotic tracking, or decoder convergence. Remark 2 proves a contraction only for fixed nonzero features and a fixed target with inactive leak, readout clipping and projection.

The exact allocation mismatch is

`e_alloc = P_tau B { sat_[0,fmax]( B^{-1}[T;u] ) - B^{-1}[T;u] }`,

where `P_tau` selects torque rows. Thus `tau_act = u0 + delta + e_alloc`, `delta=u-u0`. A requested torque bound is not an actuator torque bound unless `e_alloc` is included.

## Recommended main result: regional practical input-to-state stability

1. Use the shortest-path quaternion chart `q_{e,0}>0` and `z=(e_q,omega_e)`. Exclude the 180-degree switching surface. For a constant reference, on a region where the baseline command is not clipped, the linearized baseline error system is

   `dot z = A z + [0;J^{-1}d] + O(||z||^2)`,

   `A = [0, (1/2)I; -J^{-1}K_q, -J^{-1}K_omega]`,

   `d = delta + e_alloc + tau_p + tau_d`.

   With `J,K_q,K_omega` positive definite, the damped mechanical linearization is Hurwitz. For `Q=Q^T>0`, obtain `P=P^T>0` from `A^T P+P A=-Q`. Use `V=z^T P z`, and bound the nonlinear terms on a small chart/unsaturated region. The resulting inequality has the form

   `dot V <= -c3 ||z||^2 + c4 ||z|| D`, with

   `D = beta ||ell||_2 + ||e_alloc||_bar + ||tau_p+tau_d||_bar`.

   More generally include `d_ref` from time-varying reference and feedforward mismatch. The paper's reported implementation uses `omega-omega_d` rather than exact `omega_e`; its stated error bound `||omega_e-(omega-omega_d)|| <= theta_q ||omega_d||` must enter `d_ref` (or be absorbed in a small-gain condition).

2. By Young's inequality, if `c1||z||^2 <= V <= c2||z||^2`,

   `dot V <= -[c3/(2c2)]V + [c4^2/(2c3)]D^2`.

   Consequently the state is ultimately bounded by a radius proportional to `D`, provided the initial condition and `D` keep the trajectory inside the region where the estimates and torque feasibility hold. For constant `D`, the displayed constants yield `limsup ||z|| <= (c4/c3)sqrt(c2/c1) D`. The exact numerical coefficients require a certified region and bounds on the nonlinear remainder. Zero residual and zero disturbance recover local asymptotic (indeed exponential) baseline tracking on this unsaturated chart; `beta=0` by itself does not null allocator error or disturbances.

3. To remove allocator mismatch on a declared operating set, certify **rotor headroom**, not just an axis torque box. Let `f0=B^{-1}[T;u0]`. Because `|delta_j|<=beta ell_j`, a sufficient margin for every possible residual is

   `m_i = beta sum_j |(B^{-1})_(i,j+1)| ell_j`,

   `m_i <= f0_i <= fmax_i-m_i` for each rotor `i`.

   Then `B^{-1}[T;u0+delta]` is feasible and `e_alloc=0`. If these margins fail, retain an explicit bound on `e_alloc` in `D` and prove only conditional practical stability. The output gate in equation (28) does not guarantee this margin: it checks an axis torque limit, while rotor clipping couples axes and collective thrust.

4. For the paper's time-varying mission, the cleanest theorem is conditional on an ISS Lyapunov inequality for the **specific baseline and reference class**, with the actual allocator included. The constant-reference local proof above provides a transparent base case. To claim a mission-wide result, bound `omega_d`, `dot omega_d`, feedforward/model error, passive torque, external torque, sampling error, and altitude-dependent collective thrust; verify a common region and actuator margin. Do not extend the local chart result through a 180-degree error or a saturated transient without another argument.

The adaptive CMG–PES subsystem can then be connected by the bounded interface from Proposition 1; no claim that PES is descending the tracking loss is needed. This is the strongest tractable proof with the controller as written, but it yields a **practical bound**, not guaranteed improvement over PD.

## Other proof options, ordered by usefulness

| Option | Claim available | Extra conditions / limitation |
|---|---|---|
| Exact rotor-feasibility certificate | Converts requested residual bound into realized torque bound | Needs mission-wise or region-wise rotor headroom; useful even without a tracking theorem. |
| Sampled-data ISS/UUB | Same practical claim for the implemented hold and discrete updates | Need one-step rigid-body remainder and a certified step size; avoids treating the fixed-step simulation as a continuous controller. |
| Small-gain / passivity interconnection | Modular stability if baseline ISS gain times residual incremental gain is below one | A bounded residual alone does not imply a small incremental gain; latch, hard clipping and changing PES weights make a uniform gain difficult. Restrict to a graded, unsaturated region or redesign the residual. |
| Adaptive Lyapunov cancellation and parameter convergence | Potential asymptotic tracking with a representable matched disturbance and persistent excitation | Requires a new update tied to the plant tracking error and a realizable regressor. Current PES target is a clipped error proxy, while the gate, leak, projection, output saturation and allocation violate the usual cancellation identity. |
| Global attitude stability | Usually needs hybrid quaternion control and actuator feasibility | The present shortest-path branch and bounded torque cannot support a global smooth claim. |

## Separate decoder lemma; do not call it closed-loop stability

With fixed `a`, inactive clipping/projection/leak, and a varying target, the exact PES recursion is

`epsilon_(k+1) = (1-eta||a||^2) epsilon_k + (y*_(k+1)-y*_k)`.

With changing features add `-W_(k+1)(a_(k+1)-a_k)`. Thus `0<eta||a||^2<2` is a contraction of the homogeneous error, but target and feature variation force a nonzero error. In a high-gate clipped basin, feature rank can collapse even with bounded neuron states; see `ACC_ABSORBING_LATCH_AND_PES_IDENTIFIABILITY_2026-10-06.md`.

## Friday proof checklist

- [x] State exactly what Proposition 1 and Remark 2 establish.
- [x] Identify the missing torque term from rotor clipping and a sufficient rotor-headroom condition.
- [x] Formulate a regional ISS/UUB theorem and identify its Lyapunov function route.
- [ ] Calculate `P`, a certified chart radius, and nonlinear remainder constants for X2 and CF2.
- [ ] Bound allocator mismatch and reference acceleration over each mission; report intervals where headroom fails.
- [ ] Establish a sampled-data inequality for the controller/plant update actually used.
- [ ] Decide whether a redesigned adaptive law is needed for asymptotic learning/tracking claims.

## Figures generated from saved exploratory CSVs

- `results/current_readout_results_2026-10-06.png`: 20 ms delayed PES readout ablation, with separate scales by model.
- `results/current_learning_limits_2026-10-06.png`: held-out independent-target transfer and horizon-gradient reversal.
- `results/hyper_phase_basin_map_2026-10-06.png`: dependence of final gate basin on phase and one-weight parameter.

These are tiny exploratory tasks, not matched HH/HyperLIF performance benchmarks or validation of the proposed closed-loop theorem.
