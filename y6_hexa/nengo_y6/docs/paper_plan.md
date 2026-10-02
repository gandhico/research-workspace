# Paper Plan — Two-Paper Strategy

**Decisions locked 2026-06-17 (from your Phase-1 feedback):**

1. **Two papers**, not one.
2. **Paper 1 is the priority** and is built **first**.
3. **Benchmark axis for both papers:** *neuromorphic (NEF/Nengo) vs. classical performance* —
   same plant, same references, full quantitative metric set
   (rise time, settling time, overshoot, steady-state error, IAE, ISE, control energy,
   saturation %, tracking RMSE, + stability note).
4. **Advisor context:** L. R. García-Carrillo (NMSU) is your advisor; his Springer 2013
   *Quad Rotorcraft Control* is the plant model of record for Paper 1 — a natural, citable
   backbone, not a coincidence.

---

## Paper 1 — *priority* (target: ComRob, IEEE 2-col, 6 pp, English)

**Working title:** *A Neuromorphic NEF Flight Controller: From a Quadrotor Baseline toward a
Coaxial Trirotor.*

**Arc:** Victor's quadrotor is the **foundation and the validation baseline**; we then
**evolve the same NEF controller toward our coaxial trirotor**, importing specific ideas from
the `01_Code` Y6 (the coaxial allocation, the top/bottom yaw split, motor saturation). The
paper's spine is: *the neuromorphic controller that validates on the quad transfers, with one
new allocation layer, to the redundant coaxial airframe — and we prove it with numbers.*

**Single contribution (one sentence):**
> An NEF/Nengo cascaded controller, validated against classical cascaded-PD on a quadrotor,
> is **extended to a coaxial trirotor by replacing only the control-allocation layer**, and
> is benchmarked head-to-head (neuromorphic vs. classical) with full closed-loop metrics on
> both airframes.

**Plant of record:** García-Carrillo reduced model (`Quad_control_2026.py`), **z-up**,
`m=0.9`, `I_xx=I_yy=0.01, I_zz=0.03`. Trirotor evolution adopts the **coaxial allocation +
actuator model** from the Y6 (`y6_model.py`) layered on the *same* control structure (re-tuned
gains; the trirotor section may use the Y6 inertias where the coaxial geometry requires it,
stated explicitly).

**Section outline (≈6 pp):**
1. **Abstract** — neuromorphic NEF controller, quad→coaxial trirotor, performance benchmark.
2. **Introduction** — motivation (energy-efficient spiking control for UAVs), compressed
   related work, explicit contribution statement.
3. **UAV models** — quad reduced model (condensed) + the coaxial-trirotor *diff* (6 rotors/4
   commands, top−bottom yaw split, `6×4` allocation). Full derivations → `docs/mathematical_model.md`.
4. **Controller design** — classical cascaded PD + gravity FF; NEF/Nengo mapping (Principle 3,
   `A'=τA+I`, `B'=τB`); the one new allocation layer.
5. **Simulation & benchmark setup** — same refs, same plant, metric definitions, gains table.
6. **Results** — classical vs. NEF table (both airframes) + 2–3 figures (step/track + control effort).
7. **Conclusion** — feasibility + equivalence + brief path to neuromorphic hardware.
+ **References** — real bib (García-Carrillo, Eliasmith NEF, Mehndiratta, Czyba, …).

**Reuses / corrects:** the `2026_Comrob_Hexa_Neural.pdf` skeleton — but with the §2 fixes from
`victor_review.md` (frame, inertia labels, Eq. 5 rotational rows, yaw sign, real refs, 6-rotor
block diagrams).

---

## Paper 2 — secondary (target venue TBD: journal / next conference)

**Working title:** *Spiking Neural Control of a Coaxial Y6 Trirotor: a Full-SNN Design from
First Principles.*

**Intent (your words):** *"our purpose for the Y6 coaxial, taking totally ideas from the SOTA
and out of Victor's work."* Built **independently of Victor's lineage**, grounded in `00_SOTA`
(Mehndiratta CCTA-2018, Czyba ICUAS-2015, the tri-rotor modelling refs, the NEF-LQR /
neuromorphic-estimator papers). This is where the **full rigor** lives: full `I_xz`-coupled
dynamics, the 8-stage Node→NEF→SNN→PES ladder, neural integrators, and **fault-tolerant
control** (coaxial redundancy → survive a rotor loss).

**Likely contribution:** an end-to-end spiking (LIF) flight controller for the coaxial Y6 —
including NEF control allocation and PES online fault adaptation — benchmarked vs. classical,
with the FTC scenario as the differentiator. Most of this **already exists** in `01_Code`;
Paper 2 is largely *formalize + benchmark + write up*, after Paper 1 ships.

---

## Shared build pipeline (serves both papers)

One reusable `src/` + `experiments/` stack; both papers draw from it.

| Phase | Build | Primarily serves |
|---|---|---|
| **2** | 1-DOF altitude: `z̈=u/m−g`, classical PD+FF, NEF equiv, **first real metrics row** | Paper 1 (validates the metric pipeline) |
| **3** | Quad subsystems: roll/pitch/yaw + x/y cascade, virtual commands, per-axis metrics | Paper 1 |
| **4** | Full quadrotor (classical + NEF), full benchmark — **the validation baseline** | Paper 1 |
| **5** | Coaxial-trirotor evolution: Y6 geometry + allocation onto the same controller; math diff; benchmark | Paper 1 (headline) → seeds Paper 2 |
| **6** | Assemble **Paper 1** `paper/main.tex` (ComRob) | Paper 1 |
| **(later)** | Formalize the full-SNN + FTC Y6 from SOTA; assemble **Paper 2** | Paper 2 |

**Standing rule:** every experiment emits real `results/csv/*.csv` + plot + a metrics row.
No illustrative-only numbers (per project rules).

---

## Immediate next step (awaiting your go-ahead)

**Phase 2 only:** build `src/models/altitude_1dof.py`, a classical PD+FF controller, its NEF
equivalent, one runner emitting `results/csv/exp01_*.csv` + a plot + the first benchmark row,
and a minimal block diagram. Then **stop again** for your review before scaling to Phase 3.

Open (non-blocking) items: Paper 2's venue; whether Paper 1's trirotor section uses Y6 inertias
or scaled-quad inertias (recommend: state both, use Y6 where geometry demands).
