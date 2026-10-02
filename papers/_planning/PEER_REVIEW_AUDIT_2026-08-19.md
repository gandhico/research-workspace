# Peer-Review-Style Audit — P1, P2, P3 (2026-08-19)

Written as an honest external reviewer would, not as a cheerleader. Grounded in the deep
code/results verification done tonight (raw registry aggregation, PDF rebuilds, bug fixes) —
not a surface read of the abstracts.

---

## P1 — HyperLIF Learning

**Real contribution**: A mechanistically-motivated, honestly-scoped characterization of when a
continuous-reset gated LIF neuron helps (temporal tasks: SHD, SSC, DVS gesture) versus adds
little (near-static N-MNIST), backed by a genuinely clever falsification test — a gate-only
readout that's structurally blind for LIF but strongly informative for HyperLIF. That's a real
mechanistic finding, not just a benchmark number.

**Pros**
- Six individually falsifiable claims, each explicitly bounded (not "HyperLIF is better," but
  "HyperLIF is better *here*, not *there*, and here's why").
- The ALIF/PLIF reviewer-baseline extension pre-empts the single most predictable reviewer
  objection ("weak baseline") — and does so honestly: ALIF *wins* two of the four shortlist
  settings. The paper says so plainly instead of hiding it.
- Every number I checked tonight (baseline-shortlist, architecture-transfer, and the two
  previously-untraceable tables) matched the raw registries to 3-4 decimals. This is not
  massaged data.

**Cons — the ones a reviewer will actually raise**
- Absolute accuracies sit below optimized benchmark systems (the paper says so itself) — fine
  for a mechanistic study, but it means this cannot be pitched as a performance paper without
  inviting exactly the pushback the paper is trying to avoid.
- The Julia/APEX cross-framework validation is weak in absolute terms (~24-25% on a 20-class
  task) — reviewers will likely question whether this "confirms" anything beyond a qualitative
  direction. The paper scopes it honestly as non-headline evidence, which is the right call,
  but expect a reviewer to ask why it's included at all if it's this weak.
- The deep-residual (`convres`) failure case is a real, unresolved hole in the "transfers across
  architectures" claim, not just a caveat.
- Six claims is a lot for one paper. A tighter reviewer will ask you to cut to the strongest
  three and move the rest to supplementary material.

**Where to publish**: This reads as a *mechanism* paper, not a *benchmark* paper. A venue that
rewards that framing — a neuromorphic-computing-focused journal (IEEE TCDS, *Neuromorphic
Computing and Engineering*) or a computational-neuroscience venue — is a better fit than a
general ML venue that will default to comparing raw accuracy against SOTA. If targeting TNNLS
(matching P2/P3's portfolio), the intro needs to state up front, unapologetically, "this is a
controlled mechanistic study, not a benchmark competition" — and mean it in the framing, not
just the fine print.

---

## P2 — HyperLIF in Nengo/NEF

**Real contribution**: The first validated, capability-audited NEF/Nengo reference
implementation of a continuous-gate LIF variant — exact numerical parity with the reference
math, an analytically-predicted depolarization-block onset that matches simulation to high
precision, and an honestly-reported backend-portability limitation. This is infrastructure the
rest of the HyperLIF program (P1's Julia arm, P3's control work) can build on — that's the
pitch, and it's a legitimate one.

**Pros**
- Exceptional internal rigor. The claim-by-claim audit (✅ validated / 🔬 exploratory /
  🔮 future work), each tied to a named CSV, is the kind of discipline most papers don't do for
  themselves before a reviewer forces them to.
- 91% self-assessed readiness is not inflated — I verified the results tree is current (no
  changes since the audit date) and every "paper-ready" claim really does have a matching file.

**Cons — the ones a reviewer will actually raise**
- This is fundamentally a validation/implementation paper. The most likely reviewer question is
  "what's the scientific contribution beyond confirming the theory manuscript is numerically
  correct?" The paper needs an explicit, early answer to that — right now it's implied, not
  stated.
- 27 pages is long for a reference-implementation paper. The audit already flags this; it needs
  actually doing, not just noting.
- **The elephant in the room**: a related earlier draft was already rejected by TNNLS for
  "practical advantage unclear." If P2 doesn't explicitly address *why this reframing answers
  that specific objection*, the same reviewer complaint can resurface even from a different
  reviewer at the same or a different venue. (Tonight's backup recovered the actual reviewer
  comments — `TNNLS_reviewer_comments.tex` on D: — worth reading verbatim before finalizing this
  paper's framing, not just working from the one-line summary.)

**Where to publish**: Given the direct TNNLS rejection history, re-submitting to TNNLS without
substantially reframing the contribution is a real risk — same criticism, possibly same
reviewers. A NEF/Nengo-tools-specific venue (*Neuromorphic Computing and Engineering*, a
tools/infrastructure track) sidesteps the "practical advantage" question entirely, since
infrastructure papers are judged on rigor and utility, not novelty of result. If your advisors
want to stay in TNNLS/general-ML-journal territory, the paper needs to lead with "this is the
validated substrate three other results depend on," not "here's a Nengo implementation."

---

## P3 — Gate-Residual Control (flagship — but read this section carefully)

**Real contribution, once fused**: A disciplined three-step ladder — fixed decode (safe,
modest, ~7%), adaptive conductance (a provable *null* result, not a failure), learned decode
(+86.7% CF2 / ~57% Skydio X2, beats a hand-tuned adaptive baseline, generalizes where that
baseline doesn't). That ladder, told as one story, directly answers "practical advantage
unclear." Told as two separate, unfused papers, it doesn't.

**Pros**
- The learned-decode result is genuinely the strongest number in the whole portfolio, and it's
  not a cherry-pick — the paper also reports the performance-robustness frontier (the `k_rate`
  knob) and a negative result (behavioral cloning diverges via covariate shift) alongside it.
  That's honest science, not a highlight reel.
- The Adaptive≡Fixed equivalence is proven *analytically*, not just observed empirically
  (`r≈3.7e-6 ⇒ r²≈1.4e-11 ⇒ g≈2e-9 ≪ 1/τ=20`) — that's a real mechanism-level finding, and I
  independently verified the exact same numbers appear in both papers' separate result files.

**Cons — including two I only found by actually trying to build and read these tonight**
- **Not fused.** As two separate documents, `fixed_adaptive`'s own contribution reads as
  modest (1.2-6.4% improvement) and `learned`'s headline lacks the safety/mechanism framing
  that makes the ladder compelling. Split, they're two decent papers. Combined, they're a
  strong one. This is the single highest-leverage thing to fix before submission, and it needs
  your advisors' input on the 4 open scope questions in the fusion plan — not something to
  auto-generate.
- **The learned-gate result's generating code doesn't exist anywhere I can find** — not on this
  machine, not on the D: backup, confirmed by an actual search tonight, not an assumption. If a
  reviewer or your advisors ask "can I see the code," there's currently no good answer. This
  needs resolving (GitHub? another machine?) before submission, ideally before your advisors
  even ask.
- **I found an internal self-contradiction in `fixed_adaptive` tonight** that survived
  apparently without anyone (human or AI) doing a full read-through: the Contributions list and
  Results-opening sentence claimed "Adaptive outperforms Fixed," directly contradicting the
  paper's own later Results section, which proves the opposite. I fixed it, but its presence
  means the draft hadn't had a careful full read before tonight — worth a final complete
  read-through before this goes to any external reviewer, in case there's another one I missed.
- **The PDF had literally never been compiled on this machine before tonight** (no LaTeX
  installed at all) — rebuilding surfaced 3 missing figures that had gone unnoticed. Same
  lesson: build early, build often, don't let a draft's own compile status go unverified for
  weeks.
- The headline learned-gate number is simulation-only (MuJoCo). The *fixed*-decode result has
  real hardware validation (Qube, Aero2 HIL per the fusion plan) but the *learned* result does
  not yet. A reviewer will ask whether +86.7% survives contact with real hardware — right now,
  that's untested, not just unreported.

**Where to publish**: Once fused, this is strong enough for a real controls/robotics venue —
**IEEE Robotics and Automation Letters (RA-L)** or **IEEE Transactions on Robotics** are natural
fits given the quadrotor hardware angle, and RA-L in particular rewards exactly this kind of
tight, well-characterized result with a clear headline number. If you want to stay in the
neuromorphic-systems space instead, IEEE TCDS is a reasonable alternative. Given the direct
TNNLS rejection was specifically about "practical advantage," and TNNLS is a *learning systems*
journal rather than a controls journal, a controls-focused venue may make the practical-advantage
argument automatically easier to land than trying TNNLS again — but that's exactly the kind of
call that belongs to your advisors, not to me.

---

## Portfolio-level observation (worth saying explicitly to your advisors)

P1 (mechanism) → P2 (validated NEF infrastructure) → P3 (real control application) is a
coherent research arc, not three unrelated papers. That's worth stating as a deliberate
narrative when you present this — it's a stronger pitch than "here are three papers," and it's
true, not spin: P3's neuron *is* the one P1 studies and P2 validates.
