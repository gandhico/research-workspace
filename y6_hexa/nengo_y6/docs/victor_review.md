# Review of Victor's Baseline — Neuromorphic Coaxial-Trirotor / Quadrotor Control

**Reviewer pass:** Phase 1 (read-only audit). **Date:** 2026-06-17.
**Scope (as approved):** *everything* in `baseline_victor\`, plus `01_Code\` folded in as
the "real coaxial trirotor" alternative. Victor's quadrotor is treated as the **main /
foundation** project; the `01_Code` Y6 is the **coaxial-trirotor target** we mine for the paper.

> **Honesty note (per project rules).** Nothing in this review was *executed* in this
> session. Every verdict below comes from reading the PDFs and source files, plus hand
> derivation. Any number quoted from the existing repo (e.g. RMSE figures in
> `01_Code/PROGRESS.md`, the step-response plots in `Neuromorphic_Rep.pdf`) is labelled
> **[as reported — not re-run by me]**. Re-running and producing a real benchmark table
> is Phase 2+ work.

---

## 0. Source map (what I actually read)


| Artifact | Path | What it is |
|---|---|---|
| **Neuromorphic report** | `baseline_victor\Neuromorphic_Rep.pdf` (39 pp) | Theory + **full quadrotor NEF derivation** (Algorithms 1–6) + Simulink-vs-Nengo step responses |
| **ComRob draft** | `baseline_victor\2026_Comrob_Hexa_Neural.pdf` (4 pp) | Skeleton of the target paper, *"SNN Control… of a Coaxial Hexarotor UAV"* |
| **Classical quad (authoritative)** | `…\Codigos de Matlab 2025b\Quad_control_2026.py` | Runnable pure-Python cascaded-PD quadrotor (García-Carrillo model) |
| **Quad params** | `…\Values_Quadrotor_model.m`, `Datos_quadri_Victor.m` | `m, g, I, gains` |
| **State-space stub** | `…\SS_quadri.m` | Incomplete/buggy linearization scratch file |
| **Nengo quad (per axis)** | `…\Codigos\Quad1Z.py, Quad1X.1.py, Quad1Phi.py, Quad1Psi.py, …` | Per-axis NEF controllers (match the PDF algorithms) |
| **Nengo quad (combined)** | `…\Codigos\Combinaciones\*.py` | Multi-axis combinations |
| **NEF tutorials** | `…\Codigos\Una_Neurona, Suma, Integrador, ballandplate, …` (+`.cfg`) | Pedagogical Nengo-GUI building blocks |
| **Simulink models** | `…\Modelo_1gdl.slx, Quadrotor_model_2020.slx, Quadri_*` | **Cannot open here — no MATLAB.** Audited via the `.m`/`.py` ports + PDF |
| **Y6 trirotor plant** | `01_Code\y6_model.py` | Rigorous 12-state coaxial Y6 (Mehndiratta + Czyba) |
| **Y6 controllers** | `01_Code\y6_nef_*.py, y6_snn_*.py, y6_full_snn.py, y6_pes_ftc.py` | 8-stage Node→NEF→SNN→PES roadmap |
| **Y6 log** | `01_Code\PROGRESS.md`, `run_baseline.py`, `RUNNERS.md` | Equations-as-implemented + validation claims |
| **Quad Nengo evolution** | `github_gandhi\*`, `github_anel\*` | x–θ cascade in 3 versions; full-xyz Nengo |

**Terminology fixed for the whole project:** *Coaxial Trirotor = Y6 = "Coaxial Hexarotor."*
Three arms at 120°, each carrying a **coaxial top+bottom rotor pair** → 6 motors, 4
independent virtual commands `(T, τ_x, τ_y, τ_z)`. The paper draft says "hexarotor";
the code says "Y6 tricopter"; your brief says "coaxial trirotor." Same airframe.

---

## 1. What the work currently *is* (with evidence)

Picking from your menu — the honest classification is:

> **A pure-simulation, full-state (6-DOF / 12-state), virtual-command *cascaded* flight
> controller, implemented both classically (PD + gravity feed-forward) and
> neuromorphically (NEF/Nengo, spiking LIF), and benchmarked for *fidelity* against a
> MATLAB-Simulink reference. It is *not* hardware-oriented yet.**

Evidence:

- **Pure simulation / full-state.** `Quad_control_2026.py:36-58` integrates the full
  12-state `[x,ẋ,y,ẏ,z,ż,ψ,ψ̇,θ,θ̇,φ,φ̇]` with `solve_ivp` over 50 s. `y6_model.py:105-163`
  is a full 12-state nonlinear Y6 with RK4. No sensor/actuator hardware anywhere.
- **Virtual-command cascade.** Position errors generate **virtual attitude commands**
  `θ_d = atan2(−(k_p e_x+k_d ė_x), g)` and `φ_d` (`Quad_control_2026.py:76-80`), which the
  inner attitude PD tracks. Classic underactuated outer→inner structure.
- **Neuromorphic approximation.** `Quad1Z.py` builds `nengo.Ensemble`s (default **spiking
  LIF**) and maps the plant to neural dynamics via NEF Principle 3 (`fz_fun`/`gz_fun`,
  lines 38-44). The Y6 stack goes further: rate-NEF → LIF-SNN → neural integrators → NEF
  allocation → PES learning (`PROGRESS.md` §11-17).
- **MATLAB-Simulink benchmark (fidelity).** `Neuromorphic_Rep.pdf` Figs 7/10/12 overlay
  `Ref / *_simulink / *_nengo` for Z, X, Y step responses; `Datos_quadri_Victor.m:19-44`
  loads `simulink_data_*.csv` to compare against the Simulink run. The loose-root
  `simulink_data_*.csv` and `quad_xyz_*.csv` are these traces.
- **Not hardware-oriented.** The only "real-world" hook is an *X-Plane data* node sketched
  in the ComRob `Fig. 3` — an ambition, not an implementation.

**Crucial framing point (affects the paper).** The existing benchmark is **fidelity /
equivalence** ("the SNN reproduces the conventional Newton–Euler/Simulink result"), **not
a performance-superiority claim** ("neuromorphic beats classical"). The ComRob abstract
itself says *"comparing the SNN-based representation with a conventional Newton–Euler
formulation in MATLAB."* The paper must be honest about this: the contribution is
**feasibility + equivalence + a route to neuromorphic-hardware energy benefits**, not
"lower overshoot than PID."

---

## 2. Equation-level audit

Notation: position `ξ=(x,y,z)`, Euler angles `η=(φ,θ,ψ)` (roll, pitch, yaw), body rates
`Ω=(p,q,r)`, mass `m`, gravity `g`, inertia `I_xx,I_yy,I_zz`, total thrust `u` (a.k.a. `T`),
per-rotor thrust `F_i`, rotor drag torque `τ_i`, body moments `M_φ,M_θ,M_ψ` (a.k.a.
`τ_x,τ_y,τ_z`), lever arms `l_1,l_2,l_3`.

### 2.1 Translational dynamics — ✅ correct (mind the frame sign)

As implemented (`Quad_control_2026.py:46-50`, z-up) and in `Neuromorphic_Rep.pdf` p.20:

$$
m\ddot{x}=u\,(\sin\phi\sin\psi+\cos\phi\cos\psi\sin\theta),\quad
m\ddot{y}=u\,(\cos\phi\sin\theta\sin\psi-\cos\psi\sin\phi),\quad
m\ddot{z}=u\,\cos\theta\cos\phi-mg .
$$

This is the standard reduced rigid-body model (García-Carrillo, *Quad Rotorcraft Control*,
Springer 2013, Eq. 2.30–2.35). **Verdict: correct.** Two documentation issues only:

- **Frame inconsistency.** `Neuromorphic_Rep`/`Quad_control_2026.py`/`y6_model.py` use
  **z-up** (`+mg` subtracted). The **ComRob draft Eq. 5 uses NED z-down** (`z̈=−u cosθcosφ/m + g`).
  Both are individually valid but **opposite**. *Fix:* pick one (recommend **z-up**, to match
  all the code) and state it once.
- **Dimensional slip.** `Neuromorphic_Rep` p.20 writes `mz̈ = u cosθcosφ − g`; the last term
  must be `−mg`. Typo (the code has it right).

### 2.2 Rotational dynamics — ⚠ depends on which document

There are **two different attitude models** in the baseline, and they disagree:

| Source | Form | Verdict |
|---|---|---|
| `Quad_control_2026.py:52-56`, `Neuromorphic_Rep` p.21 | **Decoupled near-hover:** `φ̈=τ_φ/I_xx`, `θ̈=τ_θ/I_yy`, `ψ̈=τ_ψ/I_zz` | ✅ correct *as a simplification* (drops gyroscopic/Coriolis `−Ω×IΩ`) |
| `y6_model.py:140-152`, `PROGRESS.md` §4.3 | **Full `I_xz`-coupled Newton–Euler** `İΩ = −Ω×IΩ + τ` | ✅ correct and more rigorous |
| **ComRob draft Eq. 5** | `φ̈ = M_φ/I_xx + φ̇\tanθ\,M_θ/I_xx + \tanθ\,M_ψ/I_zz`, etc. | ❌ **garbled** — see below |

**The ComRob Eq. 5 rotational rows are incorrect** and inconsistent with everything that
actually runs. They appear to be a mangled attempt at the Euler-rate transform `η̈`: a bare
`φ` (not `φ̇`) appears in `ψ̈`, the inertia indices are mixed, and the terms don't reduce to
the implemented `φ̈=τ_φ/I_xx`. **Fix:** replace Eq. 5's rotational rows with **either**
(a) the clean decoupled model actually used in the quad code, **or** (b) the full coupled
form from `y6_model.py`. Recommend (b) for the trirotor section, (a) for the quad-baseline
section, and say which is which.

**Recurring inertia-labelling errors in `Neuromorphic_Rep.pdf`** (writeup only — harmless in
the code because `Quad_control_2026.py` feeds `τ` *as angular acceleration* and uses
`I_xx=I_yy`):

| Page | Printed | Should be |
|---|---|---|
| p.21 | `ψ̈ = τ_ψ/I_yy` | `τ_ψ/I_zz` |
| p.25 | `ψ̈ = τ_ψ/I_xx` | `τ_ψ/I_zz` |
| p.29 | `θ̈ = τ_θ/I_xx` | `τ_θ/I_yy` |

(`φ̈=τ_φ/I_xx` is fine.) Numerically benign in the sim only because `Values_Quadrotor_model.m`
sets `I_xx=I_yy=0.01`; for the Y6, `I_xx≠I_yy` so these **must** be corrected before reuse.

### 2.3 Rotor thrust / torque — ✅ correct (Y6), ➖ absent (quad)

- **Y6** (`y6_model.py:87-99`): `F_i = K_F Ω_i²`, `τ_i = K_τ Ω_i²`, with fault scaling
  `Ω_i = α_i ω_i` (`α_i∈[0,1]`, 1=healthy, 0=dead). Steady-state momentum-theory lumped
  model. **Verdict: correct, literature-grounded** (`K_F=6.85e-6`, `K_τ=3.35e-7`,
  `ω_max=900`).
- **Quad** (Victor): the per-rotor `F_i↔Ω_i` map is **not modelled** — the quad works
  directly in `u` and `τ` ("virtual" forces). Fine for the pedagogical baseline, but it
  means the quad has **no motor saturation / allocation** layer. The Y6 supplies that.

### 2.4 Control allocation (mixer) — ✅ correct (Y6), ⚠ check the quad/ComRob levers

- **Y6** (`y6_model.py:118-129`, `PROGRESS.md` §8): geometry reconciled between Czyba and
  Mehndiratta (one equilateral frame; `l_2=l_1\sin60°`, `l_3=l_1\cos60°`). Moments:
  $$
  \tau_x=\big[(F_5{+}F_6)-(F_1{+}F_2)\big]l_2,\;\;
  \tau_y=(F_3{+}F_4)l_1-(F_1{+}F_2{+}F_5{+}F_6)l_3,\;\;
  \tau_z=(\tau_1{+}\tau_3{+}\tau_5)-(\tau_2{+}\tau_4{+}\tau_6).
  $$
  Yaw via **top-minus-bottom drag-torque split** — the defining feature of a coaxial
  airframe. The forward mixer `F = A[T,τ_x,τ_y,τ_z]ᵀ` and inversion
  `ω=clip(√(F/K_F),0,ω_max)` are both present. **Verdict: correct and the strongest part of
  the whole baseline.**
- **ComRob draft hexa moments** (Eq. 5 region): yaw `M_ψ = τ_1+τ_3+τ_5−τ_2−τ_4−τ_6` ✅
  matches the Y6 code; but the **roll/pitch lever labels look swapped** (`M_φ` printed with
  `l_1`, should be `l_2`; pitch shows `l_2/l_3`, should be `l_1`(front)/`l_3`(back)). *Fix:*
  align Eq. 5 with the validated `PROGRESS.md §8` assignment.
- **Quad yaw allocation** (`Neuromorphic_Rep` p.20): `M_ψ = τ_{m1}+τ_{m4}+τ_{m2}−τ_{m3}`
  has **3 plus / 1 minus** — ❌ not a balanced reaction-torque pattern (should alternate,
  e.g. `τ_1−τ_2+τ_3−τ_4`). Typo in the quad writeup; the Y6 code is right.

### 2.5 Altitude dynamics + control — ✅ correct

Hover/feedback-linearization (`Quad_control_2026.py:61-62`, `Neuromorphic_Rep` p.21):
$$
u=\frac{1}{\cos\theta\cos\phi}\big(mg-k_{p_z}e_z-k_{v_z}\dot e_z\big),\qquad e_z=z-z_d .
$$
PD + gravity feed-forward with tilt compensation. **Verdict: correct.** The Y6 form
(`y6_model.py:245`) is identical with a `max(cosφcosθ,0.5)` guard against the singularity at
90° tilt — a nice robustness touch the quad lacks.

### 2.6 Attitude / position cascade — ✅ correct

Outer→inner virtual-command law (`Quad_control_2026.py:76-80`, `Neuromorphic_Rep` p.28-36):
$$
\theta_d=\operatorname{atan2}\!\big(-(k_{p_x}e_x+k_{v_x}\dot e_x),\,g\big),\quad
\phi_d=\operatorname{atan2}\!\big((k_{p_y}e_y+k_{v_y}\dot e_y)\cos\theta,\,g\big),
$$
with inner PD `τ_θ=−k_{pθ}(θ−θ_d)−k_{vθ}θ̇`, etc. This is the standard small-angle
inversion `ẍ≈g\tanθ`. **Verdict: correct.** One simplifying assumption is used silently and
should be *stated*: `ψ≈0` and x/z decoupling are assumed when reducing `ẍ` to `g\tanθ`
(`Neuromorphic_Rep` p.28-29).

### 2.7 `SS_quadri.m` — ❌ buggy scratch file (do not reuse)

`SS_quadri.m` attempts a linear state-space `[A,B]` but: (i) `x_dot = A.*x + B.*u` uses
**element-wise** `.*` instead of matrix multiply; (ii) references undefined `tau_psi`,
`K_m`, `k_m` (case mismatch); (iii) `R_y`-style inconsistencies. Treat as abandoned. (The
PDF's `R_y` also prints its middle row as `[0,0,0]` instead of `[0,1,0]` — typo; the
*composed* `R` on p.19 is nonetheless correct and matches `y6_model.R_EB`.)

### Audit summary table

| Block | Quad (Victor) | Y6 (`01_Code`) | Action |
|---|---|---|---|
| Translational | ✅ (z-up) | ✅ | Standardize frame; fix `mg` typo |
| Rotational | ✅ decoupled / ❌ ComRob Eq.5 | ✅ full coupled | Replace ComRob Eq.5; fix inertia labels |
| Thrust/torque `F_i,τ_i` | ➖ not modelled | ✅ | Adopt Y6 actuator model |
| Allocation | ⚠ lever/yaw typos | ✅ coaxial split | Adopt Y6 mixer; fix ComRob levers |
| Altitude | ✅ | ✅ (+singularity guard) | — |
| Cascade x/y→θ/φ | ✅ | ✅ | State `ψ≈0` assumption |
| State-space `SS_quadri.m` | ❌ buggy | n/a | Discard |

---

## 3. Control-design audit

**Hierarchy (both quad and Y6) — sound and identical in spirit:**

```
ref(x,y,z,ψ) → [outer position PD + gravity FF] → (T, φ*, θ*, ψ*)
            → [inner attitude PD] → (τ_x, τ_y, τ_z)
            → [allocation] → ω_1..6 (Y6 only) → [plant] → state feedback
```

- **Implemented vs described:**
  - Quad: **fully implemented** end-to-end in `Quad_control_2026.py` (classical) and
    per-axis in `Quad1*.py` (Nengo). The PDF's Algorithms 1–6 (Z, ψ, X+θ, Y+φ) correspond
    1:1 to the code.
  - Y6: **fully implemented** classical (`y6_model.baseline_control`) **and** an 8-stage
    neural roadmap, all marked ✅ in `PROGRESS.md`, with allocation + FTC.
- **Controller type:** PD + gravity feed-forward throughout. **No integral action** in the
  baseline (acknowledged in `PROGRESS.md §9.3` and `nengo_x_theta_three_versions_explanation.md`,
  which reports a residual `~0.15 m` steady-state x-error in the PD-only Nengo quad). The Y6
  SNN stack *does* add neural integrators (Stage 4) and PES learning (Stage 7).
- **Gains:** quad uses `k_pz=40,k_vz=5; k_pθ=120,k_vθ=8; …` (`Values_Quadrotor_model.m`);
  Y6 uses a different, gentler set (`Gains` in `y6_model.py:213-223`). They are **not the
  same vehicle** (m=0.9 vs 1.412 kg, different inertias), so gains can't be shared — a port
  must re-tune.
- **Known weaknesses:** PD-only steady-state offset; aggressive quad gains caused bang-bang
  saturation in the Nengo port until softened (documented evolution V1→V3 in
  `github_gandhi`); attitude pinned to 0 in the isolated `Quad1Z.py`.

---

## 4. Nengo / NEF-implementation audit

**The NEF mapping is textbook-correct.** Both Victor's quad and the Y6 use Eliasmith's
**Principle 3** to realize a state-space system `ẋ=Ax+Bu` in recurrently-connected neurons
via the synaptic filter `h(s)=1/(1+τs)`:
$$
A' = \tau A + I,\qquad B' = \tau B,
$$
so the recurrent population reproduces the plant/integrator dynamics
(`Quad1Z.py:38-44`, `Neuromorphic_Rep` p.13-16, 22-23). **Verdict: sound.** Specific notes:

- **Derivative via dual synapses** (`Quad1Z.py:56-63`, PDF Eq. 14): `ė ≈ [e(τ)−e(2τ)]/τ`
  using two connections with synapses `(0.05, 0.1)` and transforms `(+20,−20)`. A finite-
  difference derivative in spike space — workable and standard, but **noisy**; it is the main
  source of jitter in the plots. A cleaner `nengo.Lowpass`/`Alpha`-filtered differentiator or
  representing velocity as a state dimension (as the Y6 does) is preferable.
- **Nonlinearities kept in Nodes** (the pragmatic NEF choice): `√(F/K_F)`, `atan2`,
  division by `cosθcosφ`. The Y6 keeps `F→ω`, yaw-trig, and clipping as `Node`s
  (`y6_nef_position.py:43-61, 164-170`) and only the *bilinear yaw-mixing* and PD/allocation
  in ensembles. Reasonable; honest about what is and isn't "neural."
- **Spiking vs rate:** Victor's `Quad1*.py` use default **LIF (spiking)**. The Y6 has an
  explicit ladder: `RectifiedLinear` (rate) → `LIF` (spikes) → integrators → PES. Good for a
  fidelity-vs-spike-noise story.
- **Radius / saturation tuning** is done by hand (`Sx, St, Sz` in `Quad1Z.py:19-21`;
  per-ensemble radii in `y6_nef_position.py`). This is the usual NEF chore; it's present and
  sensible but undocumented — worth a short table in the paper.
- **PES fault-tolerant control** (`y6_pes_ftc.py`, `PROGRESS.md §16`): online decoder
  learning `ΔD=−η E aᵀ` to compensate a killed rotor at t=6 s. Elegant, and a genuinely
  novel angle — but **out of scope for a 6-page paper** (see §6).

**Reproducibility caveats (must fix before any run):**
- Hardcoded Windows paths `E:\Users\Usuario\…` in `Quad1Z.py:103` and `Datos_quadri_Victor.m`
  — will fail on this machine.
- `python-control` not installed (non-blocking; scipy covers step metrics).
- Simulink `.slx` cannot be opened here — the Simulink half of Figs 7/10/12 is **not
  reproducible without MATLAB**; we reproduce its *role* with the Python classical baseline.

---

## 5. Gaps blocking publication (prioritized)

**P0 — must fix for a credible paper**
1. **No quantitative benchmark table.** Existing results are eyeball-overlay plots. Your
   standing metric set (rise/settling/overshoot/SSE/IAE/ISE/control energy/saturation%/
   tracking RMSE + stability note) does not exist yet. *This is the single biggest gap.*
2. **ComRob draft is a 4-page skeleton:** empty subsystem Eqs. 6–12, empty Results/
   Conclusions, **placeholder references** (`[1] J. Doe`), figures stamped *"Reemplazar esta
   figura,"* and **quadrotor block diagrams (U1–U4) on a hexarotor paper.**
3. **Equation corrections** from §2 (ComRob Eq. 5 rotational rows; inertia labels; yaw-
   allocation sign; frame convention). A reviewer *will* catch these.

**P1 — needed for a strong paper**
4. **One vehicle, one frame, one notation.** Reconcile quad (m=0.9, z-up, `τ`-as-accel) vs
   Y6 (m=1.412, z-up, full `I`). Decide what the paper's "baseline" and "target" actually are.
5. **Honest comparison axis.** Decide and state whether the benchmark is *classical-vs-neuromorphic
   performance* (needs identical plant + identical refs + metrics) or *SNN-fidelity-vs-conventional*
   (equivalence). Don't blur them.
6. **Reproducible runners.** De-hardcode paths; one `python run_*.py` per experiment that
   emits CSV + plot + metrics.

**P2 — polish**
7. Derivative noise (replace dual-synapse diff where it matters).
8. Integral action / steady-state error story (PD→PID or neural integrator) made explicit.
9. Figure quality + TikZ block diagrams that actually show 6 rotors and the coaxial split.

---

## 6. Proposed development plan (Phases 2–6) + scope cuts + the single contribution

### 6.1 Recommended single contribution (the 6-page paper)

> **An all-neuromorphic NEF/Nengo cascaded flight controller for a coaxial Y6 trirotor —
> position + attitude + the coaxial control-allocation — benchmarked, with quantitative
> closed-loop metrics, against a classical cascaded-PD controller on the *same* plant, using
> the quadrotor as the validation baseline.**

Why this framing:
- It puts the **strongest, most novel asset (the coaxial allocation realized in NEF, Stage 6)**
  at the center — that's what makes it a *trirotor* paper and not "yet another NEF quadrotor."
- The **quadrotor is the validation baseline** (your stated structure): show the method
  reproduces a known result, then show it scales to the redundant coaxial airframe.
- It is **provable in 6 pages with real numbers** — one plant, one metrics table, 2–3 figures.

### 6.2 Recommended scope cuts (move to `docs/`, not the paper)

- ❌ PES fault-tolerant control (Stage 7) — its own paper.
- ❌ Full HH/conductance/event-based theory from `Neuromorphic_Rep.pdf` — background, → `docs/`.
- ❌ Ball-and-plate example — pedagogy, → `docs/`.
- ❌ The 8-stage SNN ladder — keep **one** representative neural controller in the paper;
  document the ladder in `docs/nengo_design.md`.
- ❌ X-Plane / MIL-SIL-HIL roadmap — one sentence in Conclusions, full version → `docs/implementation_path.md`.

### 6.3 Staged build (each stage: plant eq → classical → Nengo → run → CSV/plots → metrics → 2–3 sentence interpretation)

| Phase | Deliverable | Reuses |
|---|---|---|
| **2 — 1-DOF altitude** (pedagogical anchor) | `z̈=u/m−g`; classical PD+FF; NEF equivalent; block diagram; runnable sim; benchmark row | `Quad1Z.py`, `Quad_control_2026.Quad_u` |
| **3 — Subsystems** | roll/pitch/yaw + x/y cascade + virtual commands; per-axis metrics | Algorithms 2–6; `Quad1*.py` |
| **4 — Full quadrotor baseline** | classical + Nengo full 6-DOF; full benchmark; this is the **validation baseline** | `Quad_control_2026.py`; `full_quadrotor_xyz_nengo.py` |
| **5 — Coaxial trirotor (headline)** | Y6 geometry, coaxial thrust/torque, allocation matrix `A`, state-space, **explicit math diff vs quad**; classical + NEF + benchmark | `y6_model.py`, `y6_nef_*` |
| **6 — Paper assembly** | `paper/main.tex` (IEEEtran, 2-col, ~6 pp, English), TikZ diagrams, real figures, `references.bib` | the ComRob draft as a *starting skeleton to be corrected* |

### 6.4 Math diff quad → trirotor (the spine of Phase 5)

| Aspect | Quadrotor | Coaxial Y6 trirotor |
|---|---|---|
| Rotors / commands | 4 / 4 (square) | 6 / 4 (**redundant**) |
| Yaw torque | rotor-spin reaction, 2+2 alternating | **top−bottom coaxial drag split** per arm |
| Allocation | 4×4 invertible | **6×4** (null space → top/bottom split choice) |
| Lever arms | single `l` | `l_1` (front), `l_2,l_3` (back projections) |
| Gyroscopic | often dropped | `τ_gyro=J_P …` between top/bottom sets |
| Fault tolerance | none | coaxial redundancy enables it (→ future work) |

This table *is* the paper's novelty hinge and should appear (condensed) in §III.

### 6.5 What I would build first (on your go-ahead)

Phase 2 only: a clean `src/models/altitude_1dof.py` + `src/controllers_classical/` +
`src/controllers_nengo/`, one runner that emits `results/csv/exp01_*.csv`, a plot, and the
**first real benchmark row** (so we validate the metric pipeline on the simplest possible
plant before scaling up). Then stop again for your review.

---

## 7. Open questions for you (before Phase 2)

1. **Paper vehicle of record:** keep Victor's `m=0.9` quad as the validation baseline and
   the `m=1.412` Mehndiratta Y6 as the trirotor — or unify on one parameter set?
2. **Benchmark axis:** classical-vs-neuromorphic *performance* (my recommendation) or
   SNN-fidelity-vs-conventional *equivalence* (the ComRob draft's current framing)? Or both,
   with one as primary?
3. **Spiking level for the paper's neural controller:** rate-NEF (clean plots) or LIF-SNN
   (true spikes, noisier) as the headline result?
4. **Authorship / continuity:** the ComRob draft already lists you + CINVESTAV co-authors.
   Should the new `paper/main.tex` start from that file's structure, or be rebuilt clean and
   reconciled afterward?

*(These are also surfaced as a checklist; I'll proceed on your answers and will not write
build code until you approve this plan.)*
