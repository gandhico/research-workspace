# Stronger baselines and five controllers — executive summary

> **Update 2026-09-21 — Izhikevich under the CMG protocol (v14).** The Izhikevich advantage quoted below was on the fixed-PD baseline. On the tuned PD+ff (rho=3) with the same gate, score, noise and bursts it is level with or below CMG on Full3/Hard45 and far worse on Roll/Yaw360 (geo-mean error x2.6 X2 / x1.8 CF2 the baseline's), at ~10x CMG's realized effort (reduced grid, 33 runs; `final_robustness_gating_2026-09-20/REPORT_IZHIKEVICH_A3.md`).
>
> **Update 2026-09-20 — robustness and gating (v13, 7 pages).** Against the tuned PD+ff baseline: the paper's CF2 rho=3 row had used beta=0.05; a saturation-aware output gate makes beta=0.5 safe noise-free (CF2 36.5%, X2 37.3% geo-mean) but CF2 diverges on Hardstep under measurement noise (rotor-level saturation), so CF2 uses beta=0.2 (22.4%). Under noise the benefit survives only on Full3/Hard45 (11% X2, 4% CF2); Roll/Yaw360 sit at the noise floor and are neutral to slightly negative. Hardstep cannot be made a gain by any gate tried (ceiling +0.3%). Burst-phase disturbance error −14% (X2) / −6% (CF2). Details: `final_robustness_gating_2026-09-20\README.md`.
>
> **Update 2026-09-16 — Hardstep resolved, and the feedforward results are now in the paper.**
> Hardstep's large error is not a defect: its reference commands 63–111° steps every 2 s, and
> **97–99% of the reported mean is unavoidable slew**. Scored by settling time to a 5° band, the
> residual is a large and consistent win at the canonical bandwidth (**X2 −31%, CF2 −42%**), and the
> ρ=3 regression is explained by the loop passing the paper's own 9.6 rad/s PES corner. A
> pre-registered hypothesis — that the torque limits were mis-scaled on X2 yaw — was tested and
> **refuted**: ℓ from diag(J) exceeds rotor capability by 2.3× and makes X2 far worse (15.3° → 89.8°).
> Details: `baseline_restatement_2026-09-16/HARDSTEP_FINDINGS_2026-09-16.md`.
>
> **Current paper: `paper/v12_2026-09-16_final/` (11 pages at full figure size; a 10-page variant
> differing only in figure scaling is in the same folder).** It is built on Gandhi's
> Hespanha-structured abstract and introduction, merges the primary matrix, noise, ladder and
> neuron-family results into one two-column table, and addresses all 20 of Dr. Sandoval's purple
> comments compactly — correcting the three that were wrong (L_r is a quadratic-growth constant, the
> latched PES is lagged *proportional* action, and β = 0.5 is far outside the certificate). Audit:
> `paper/v12_2026-09-16_final/AUDIT_v12_2026-09-16.md`, reproducible via
> `baseline_restatement_2026-09-16/audit_v12.py`.

2026-09-10/11. MuJoCo, X2 and CF2 (1.5× rotors), noise-free unless stated,
one run per cell (deterministic). Every tuning choice below is an interior
optimum, and every CMG residual authority β was chosen by a rule fixed in code
before its results existed. Details are in the linked reports.

## 1. The baselines in the paper were held back

**Attitude missions (Table V).** The PD damps absolute rate `−k_ω ω`, though
the paper's eq. (6) defines the rate error `ω_e = ω − R(q_e)ᵀω_d`.
- Adding reference-rate feedforward removes **76–99%** of PD's error on the
  moving-reference missions.
- Its bandwidth was **~3× below its own optimum** (interior at 3× on both
  airframes, noise-free *and* under the paper's realistic noise). Hardstep's
  actuator saturation is what caps it.
- **Bandwidth-tuned PD+ff beats CMG-on-PD in every Table V cell**, Hardstep
  included (X2 Hardstep 0.266 vs 0.359 rad).

**6-DOF cascade.** The inner loop already had rate feedforward; the outer loop
had none, and both airframes were under-tuned (X2's documented "ceiling"
`wn_att = 4` does not hold — 6 to 24 rad/s are stable).
- Flatness feedforward plus re-tuning cuts moving-reference position error by
  **98–99%** on both airframes.

## 2. Five controllers on the same missions

Gandhi's Aero 2 formulations, 3-axis, with feedforward, each bandwidth-tuned.
Change vs tuned PD+ff on the smooth missions:

| family | X2 | CF2 | note |
|---|---|---|---|
| **Backstepping** (computed torque) | **+30–42%** | **+65–98%** | the strongest baseline; it adds `J ω̇_d + ω×Jω` |
| LQR | +29–41% | +62–95% | ≈ backstepping, as theory predicts |
| MPC (unconstrained, aero2 form) | +17–32% | +60–95% | ≈ LQR without active constraints |
| NMPC (aero2 grid, fixed) | ≈ backstepping (±1.5%) | ≈ backstepping | same accuracy at a 20× lower update rate |
| SMC | −118% to −176% | mixed | underperforms as parameterised |

No controller meaningfully beats PD+ff on **Hardstep** — an actuator limit,
not a control-structure problem.

## 3. Where CMG–PES earns its place

| CMG on top of | X2 | CF2 |
|---|---|---|
| tuned 6-DOF cascade (PD+ff) | **−13% to −25%** position error on Circle/Full6; Waypoint +7% | **−13% to −21%**; Waypoint +3.5% |
| tuned PD+ff, attitude | **helps** (geo-ratio 0.64) | **helps, modestly** (0.94) |
| SMC | **helps** (0.85) | does not |
| LQR / backstepping / MPC / NMPC | **does not** (1.02–1.05) | **does not** (1.64–1.68) |
| backstepping, inertia 0.6× / 1.6× wrong | does not (1.01–1.12) | does not |
| backstepping, unmodelled disturbance | **helps: +5–8%** on smooth missions | **helps: +5–8%** (Hardstep excluded, post hoc) |

**The pattern is coherent.** The residual learns what the baseline does not
model. It helps model-free baselines and disturbance rejection; with an
accurate — or even a moderately wrong — model there is little left to learn,
and on near-perfect baselines it adds a small error floor (~10⁻⁴ rad).
Its teaching signal is error-proportional (`y* = −k_e e_q`), so it cannot
learn the *structure* of a model error; a residual meant for that needs a
teaching signal built for it.

## 4. What this means for the paper

- Restate the baseline: tuned PD + rate feedforward, not "well-tuned PD".
  The 17–60% headline is against a structurally handicapped baseline.
- The defensible contribution: **CMG–PES is complementary to model-free control
  and to disturbance rejection** — substantial over PD+ff on smooth missions,
  modest (5–8%) alongside a model-based controller under unmodelled
  disturbance — with the negative results reported.
- The 6-DOF numbers should be restated against the tuned cascade.

## 5. Integrity and provenance items found along the way

1. **Table V CMG values** now reproduce only to ≤ 2.1×10⁻⁶ relative (two CMG
   modules were edited after the runs; no earlier copy exists). No printed
   value changes. One-line provenance note.
2. **Table VI measures noisy error.** Under noise, `qerr` is computed from the
   noisy measurement, so it contains the sensor noise (floor σ√(8/π) =
   0.032 rad, matched to 6×10⁻⁵). Yaw360's 60.6% → 47.8% drop is largely that
   floor, not degraded control. Report true error, or say so.
3. **CF2 disturbance wording.** The paper says "scaled by the inertia ratio";
   the value used (0.15 mN m) is 2.5× that and loads CF2's axes to 28–52% of
   their limits (X2: 21–35%). The 50.2% result is valid (no saturation).
4. **`sweep_final_2026_09_05.py`** said 0.004 N m for that study — 14× CF2's
   torque limit, and not what produced the results. Fixed to 0.00015.
   **The advisor package still ships 0.004** and should be rebuilt or
   annotated.
5. The five aero2 controllers damp absolute rate as well — the same
   feedforward gap applies to the Aero 2 comparisons.

## Reports

| topic | file |
|---|---|
| PID and PD+feedforward (attitude) | `nengo_nef_replication_2026-08-29/results/pid_baseline_2026-09-10/BASELINES_REPORT_2026-09-10.md` |
| 6-DOF feedforward and re-tuning | `six_dof_expansion_2026-08-31/results/ff6_2026-09-10/FF6_FINDINGS_2026-09-10.md` |
| five controllers, CMG on each, mismatch, disturbance | `nengo_nef_replication_2026-08-29/results/baselines_2026-09-10/TRACK2_REPORT_2026-09-10.md` |
| applying the architecture to other controllers | `…/baselines_2026-09-10/CONSIDERATIONS.md` |
| CF2 disturbance provenance | `…/results/final_sweep_2026-09-05/PROVENANCE_NOTE_2026-09-11.md` |
| status figure | `…/baselines_2026-09-10/status_2026-09-10.png` |

Canonical runners were never modified; every variant is generated by a patch
script and regression-checked bit-for-bit against the published runs.
