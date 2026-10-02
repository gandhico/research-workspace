# P3 Fusion Plan — Gate-State + Adaptive/Learned Residual Control (flagship IEEE journal)

Date: 2026-07-20 · Supersedes the P3/P4 split scaffold
Status input consulted: `PAPER_PORTFOLIO_DECISION.md`, `AI_AGENT_RESEARCH_WORKFLOW.md`,
`PROGRESS_REGISTER.md`, `REVIEWER_ADVISOR_AUDIT.md`, `paper3_fused_..._proposal.tex`,
`paper4_adaptive_learned_..._proposal.tex`, Paper 4 draft (`01_HyperLIF_Gate_Residual/v2_clean/paper/main2.tex`,
`sec_mujoco_gate_mechanism.tex`, `docs/2026_07_05_results_params_runners.md`),
Paper 5 (`10_Paper5_Learned_Gate_Control/paper/main.tex`, `docs/full_results_dossier.md`),
STN-PID-PES note (`.../imported_notes/2026_04_29_stn_pid_pes_mujoco_results.md`).

---

## 0. One-line thesis

**A single continuous, bounded neuron state — the HyperLIF gate `r(t)` — is a control
residual, and the *decode* is the design axis: a fixed decode gives a safe, selective,
near-silent residual; the adaptive conductance is provably inert in gate mode; and an
online-learned decode unlocks 57–87% error reduction that generalizes across platforms
where a hand-tuned adaptive baseline fails.** The same neuron/gate is portable across
Python, Nengo/NEF, and Julia/APEX — tying P3 to P1 and P2.

Why fuse: alone, the fixed-gate result is honestly modest (the project's own diagnosis:
"+7.4% is half-PD detuning, the gate is a passenger"). Alone, the learned-gate result
lacks the mechanism/safety/boundary framing. Fused, they become one disciplined arc:
**fixed = safety/selectivity, adaptive = boundary, learned = performance** — the kind of
honest ladder reviewers reward, and the direct answer to the TNNLS "practical advantage
unclear" rejection.

---

## 1. Contributions (fused, claim-classified per the workflow)

| # | Contribution | Class | Evidence today |
|---|---|---|---|
| C1 | Gate-state residual: decode a HyperLIF gate as a smooth, bounded, demand-gated residual on a classical quaternion backbone; safe augmentation, `β=0` recovers baseline exactly | **Safe** | MuJoCo CF2/X2 + hardware (Qube 60 s ×12, Aero2 HIL 22-cond); selectivity/timing/economy |
| C2 | Boundary result: adaptive conductance is inert in gate mode — `r≈3.7e-6 ⇒ r²≈1.4e-11 ⇒ g≈2e-9 ≪ 1/τ=20`; HyperLIF ≡ Adaptive bit-for-bit (fixed **and** learned decode) | **Safe** | July-5 dossier + independent reproduction 2026-07-19 (X2/CF2 full gate_gain sweep) |
| C3 | Online-learned decode: a local delta-rule / e-prop on the 3×6 decode `W` unlocks large error reduction (CF2 hard45 0.038 = 86.7%, X2 0.129 ≈ 57%), **beats** the hand-tuned STN-PID-PES teacher, and **generalizes across platforms** where STN-PES ≈ classical on X2 | **Qualified** (needs multi-seed + ablations) | Paper-5 dossier; `learned_gate_experiment.py` |
| C4 | Performance–robustness characterization: the learning *target* (PD-style `−k_err·e − k_rate·ω`) is the governing knob; documented frontier + failure modes (imitation diverges by covariate shift; leak alone does not fix step-flip) | **Qualified** | Paper-5 §3–4, §6 |
| C5 | Cross-substrate reproducible neuromorphic controller: same gate in Python + Nengo/NEF + Julia/APEX; hardware selectivity on real Qube + Aero2 | **Exploratory→Qualified** | Python done; Nengo neuron parity (P2) + Julia forward parity (P1) exist, control-in-loop pending |

Non-negotiable: never attribute a gate-mode improvement to "Adaptive" (C2). Never headline
the 0.038 champion without the k_rate robustness frontier (C4).

---

## 2. Paper architecture (section map)

1. Introduction — SNN control discreteness problem; the gate as a continuous decodable state; the fixed→adaptive→learned thesis; explicit link to P1 (temporal readout) and P2 (NEF reference).
2. Related work + formal positioning table — vs coRNN/UnICORNN/LEM, Izhikevich/SRM, PLIF/GLIF/ALIF-LSNN, surrogate-LIF, adaptive/L1 control, residual RL. (Reuses the P1 comparison table, re-pointed to control.)
3. System & baseline — quaternion PD backbone; MuJoCo CF2/X2; Qube/Aero2 hardware; missions; metric `J`.
4. Gate-state residual architecture — pair-coded currents, HyperLIF gate ODEs, decode `W`, demand gate `g_d`, blend, saturation. (Merge Paper-4 §method + `sec_mujoco_gate_mechanism.tex`.)
5. **Fixed decode** — selectivity/timing/economy; honest half-PD diagnosis; hardware pillar (Qube/Aero2).
6. **Adaptive boundary** — analytic + empirical equivalence; scope to one neuron; how to make adaptation matter (voltage/event path).
7. **Learned decode** — delta-rule / e-prop; results across platforms/missions; beats STN-PES; robustness frontier; negative results.
8. **Cross-substrate** — Python/Nengo/Julia gate parity; (in-loop demo or documented future path).
9. Discussion, limitations (hardware learned-decode pending; single-neuron scope; sim-to-real), conclusion.

Working title options:
- "Continuous Gate-State Residuals for Neuromorphic Quadrotor Control: Fixed, Adaptive, and Online-Learned Gating of a HyperLIF Neuron"
- "From Safe to Skilled: Learned Gate-State Residual Control with HyperLIF Neurons"

---

## 3. Experiment matrix (target)

- Platforms: CF2, X2 (MuJoCo) + Qube Servo 3, Aero2 (hardware).
- Missions: roll, full3, hard45, hardstep, yaw360.
- Controllers: classical PD; fixed gate; adaptive-gate; adaptive-voltage/event; STN-PID-PES (teacher/baseline); online_pes; eprop_anneal; degrading refs (direct LIF, Izhikevich, Nengo LIF-rate).
- Ablations: timing-shuffled, frozen-gate, energy-matched, gain-matched, no-blend, fixed-vs-learned decode, k_rate∈{0,0.3,1.0} sweep, imitation (negative), platform-normalized.
- Metrics: `J`, qerr mean/peak, RMSE/axis, control energy, saturation/fault count, gate duty/selectivity, seed stability — all **mean ± std, paired seed tests, failure/NaN counts**.
- Cross-substrate: max `|r_python − r_nengo|`, `|r_python − r_julia|` parity table + one shared gate-trajectory figure.

Required-artifact table (extends the scaffold):

| Artifact | Status | Action |
|---|---|---|
| Fixed-gate cross-platform (J, qerr) | Exists | Verify, add seeds |
| Gate-gain sweep (X2+CF2) | **Done 2026-07-19** | Drop in (Table) |
| Adaptive≡HyperLIF equivalence | Exists | Present as boundary (C2) |
| Learned decode CF2/X2 × missions | Exists | Add ≥5 seeds + std |
| k_rate robustness frontier | Exists | Formalize as figure |
| Timing-shuffled / frozen / energy-matched | Partial (Aero2 HW) | Add MuJoCo learned-mode |
| STN-PES teacher comparison | Exists | Keep as baseline row |
| Imitation negative result | Exists | Keep (honesty) |
| Hardware fixed-gate (Qube/Aero2) | Exists | Format rows |
| Hardware learned-decode | **Pending** | Needs rig/SDK |
| Cross-substrate gate parity | Pending | New (see §4) |

---

## 4. Cross-substrate architecture (Julia · Python · Nengo/NEF) — the portability spine

Define the mechanism ONCE, instantiate three ways, prove parity:

```
core spec (shared):   HyperLIF state {v, r}, pair-coded currents I_pos/I_neg(τ_norm),
                      decode Δτ = W·[r_pos; r_neg], demand gate g_d, blend β, sat.
Python  (primary):    MuJoCo loop — done (learned_gate_experiment.py).
Nengo/NEF:            reuse the calibrated custom NeuronType from P2; run the SAME gate
                      residual; deliver r(t) forward-parity (min) or Nengo-in-the-loop (stretch).
Julia/APEX:           reuse P1 shared-weight parity harness (apex_v2_shared_weight_trace_compare);
                      deliver r(t) forward-parity for the control currents.
Deliverable:          parity table (max |Δr| across substrates) + one overlaid gate figure.
```

This closes the portfolio's P3 gap "connect the controller to the Nengo reference instead of
a parallel duplicate neuron" and makes the trilogy a single portable-core story.

Decision needed (see §7): how far to push Julia/Nengo *control-in-loop* for THIS paper vs
citing P1/P2 and showing gate-signal parity only.

---

## 5. Readiness & critical path

Current fused readiness ≈ **65%** (fixed 90 / boundary 100 / learned-MuJoCo 85 /
learned-hardware 0 / cross-substrate 35).

- Phase 0 — Scaffold merge: one sectioned source from main2.tex + Paper-5 main.tex; delete disproven "Adaptive beats fixed" Contribution 3 (already flagged); unify J+qerr reporting. *(agent, no compute)*
- Phase 1 — Statistics: ≥5 seeds for fixed + learned on CF2/X2 × {hard45, hardstep}; mean±std, paired tests, failure counts. *(Python, runnable here)*
- Phase 2 — Ablations: timing-shuffled, frozen-gate, energy-matched, k_rate sweep, imitation-negative as tables. *(Python, runnable here)*
- Phase 3 — Cross-substrate: Nengo gate parity (+ in-loop if chosen); Julia forward parity; shared gate figure. *(needs P1/P2 envs)*
- Phase 4 — Hardware: learned-decode on Aero2 HIL + Qube (needs SDK + rig); fixed-gate hardware rows already exist. *(blocked on hardware)*
- Phase 5 — Adaptive-active (optional): voltage/event-mode residual — either a positive extension or a reinforced boundary. *(Python)*
- Phase 6 — Submission: figures, IEEE build, claim ledger, reproducibility bundle, advisor review.

Compute note (this machine): MuJoCo 3.8/3.9 present → Phases 1/2/5 runnable now. Quanser SDK
absent → Phase 4 hardware blocked. Nengo/Julia parity depends on P1/P2 envs.

---

## 6. Honest feedback / risks to manage

1. Fixed gate is "half-PD detuning" (your own diagnosis). This is *why* the fusion is
   necessary — fixed carries safety/selectivity, learned carries performance. Do not submit
   the fixed-gate story alone.
2. Champion cherry-pick risk: 0.038 "aggressive" **flips/diverges on hardstep** (J=2.18).
   Always present the k_rate frontier (0=champion, 0.3=generalist, 1.0=damped). The dossier
   already does this — keep the discipline.
3. Multi-seed variance: online rules are seed-sensitive; ≥5 seeds + failure counts are a
   reviewer non-negotiable (TNNLS audit item).
4. Hardware learned-decode is the single biggest gap; if the rig stays unavailable, frame
   as "MuJoCo-validated, hardware fixed-gate anchor, learned-decode-on-hardware in progress."
5. Cross-substrate: claim *gate-signal parity* (defensible) — call Nengo/Julia control-in-loop
   "demonstrated" only if actually run; otherwise "future path."
6. Two distinct "adaptive/learned" threads must stay disentangled: STN-PID-PES (adaptive PID
   gains, weak on X2) vs learned HyperLIF decode (generalizes). The email conflated them; the
   paper must not.

---

## 7. Decisions I need from you (blocking the scope freeze)

1. **Venue/scope:** flagship journal (RA-L, T-RO, IEEE T-Cybernetics, or L-CSS) vs conference-first.
   Recommend RA-L (fits length, robotics audience, fast) or T-Cybernetics if we deepen theory.
2. **Hardware in P3:** include Qube/Aero2 real-hardware as a pillar (strong, but learned-decode-on-hardware
   needs the rig/SDK) vs keep P3 MuJoCo-only with hardware separate. Recommend include (fixed-gate
   hardware now + learned-gate hardware as fast-follow).
3. **Cross-substrate depth for THIS paper:** (a) Python + mention, (b) Python+Nengo parity,
   (c) full Python+Nengo+Julia parity. Recommend (b) minimum, (c) if time.
4. **Learned gate = main result or strong secondary?** Given 57–87% replicated across platforms,
   recommend co-headline (main), with the honest robustness framing.
```
