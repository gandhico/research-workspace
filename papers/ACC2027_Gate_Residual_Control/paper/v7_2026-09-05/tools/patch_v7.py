"""Build ACC2027_v7.tex from ACC2027_v6.tex.

Post-review-exercise revision. Six changes, each marked `% [v7]`:

  1. Title and abstract re-scoped to what the evidence supports, stated
     positively rather than defensively.
  2. The "neuromorphic" framing moved from apology to placement: the unit is
     conductance-based with a gating variable (Hodgkin-Huxley lineage, not
     LIF), and graded non-spiking dynamics are the analog-VLSI lineage that
     neuromorphic engineering started from.
  3. CF2 narrative leads with the manufacturer comparison instead of burying
     it twenty lines later. The scaled limit is BELOW measured hardware.
  4. Annealed activity-trace material removed (both the Sec. III subsection
     and the Sec. VI results): it is evidence about a different residual law
     on a different actuation path, and it dilutes the central claim.
  5. Physical Hover section removed, retained as two honest sentences in the
     conclusion including the measured number.
  6. A small-gain remark added, which is the result a control audience will
     look for first, plus an analog-hardware outlook that is clearly an
     outlook.

Run:  python patch_v7.py
"""
from __future__ import annotations

import io
import shutil

SRC = "ACC2027_v6.tex"
DST = "ACC2027_v7.tex"

shutil.copyfile(SRC, DST)
s = io.open(DST, encoding="utf-8").read()
n = 0


def sub(old: str, new: str, tag: str) -> None:
    global s, n
    c = s.count(old)
    if c != 1:
        raise SystemExit(f"PATCH FAILED [{tag}]: found {c}, expected 1")
    s = s.replace(old, new, 1)
    n += 1
    print(f"  ok  {tag}")


def cut(start: str, end: str, tag: str, replacement: str = "") -> None:
    """Remove everything from `start` up to (not including) `end`."""
    global s, n
    if s.count(start) != 1 or s.count(end) != 1:
        raise SystemExit(f"PATCH FAILED [{tag}]: boundary not unique")
    i, j = s.index(start), s.index(end)
    if not i < j:
        raise SystemExit(f"PATCH FAILED [{tag}]: boundaries out of order")
    removed = j - i
    s = s[:i] + replacement + s[j:]
    n += 1
    print(f"  ok  {tag}  ({removed} chars removed)")


# ===========================================================================
# 1. title
# ===========================================================================
sub(
    r"""\title{Online PES-Adapted Neuromorphic Membrane--Gate Residual Control for
Actuator-Constrained UAV Quaternion Attitude Tracking}""",
    r"""% [v7] Title now names the mechanism and the learning, and claims the
% controlled study rather than architectural novelty.
\title{Bounded Residual Quaternion Attitude Control with Non-Spiking
Conductance-Based Neurons and Online Decoder Learning}""",
    "title")

# ===========================================================================
# 2. abstract
# ===========================================================================
OLD_ABS_START = r"\begin{abstract}"
OLD_ABS_END = r"\end{abstract}"
i, j = s.index(OLD_ABS_START), s.index(OLD_ABS_END)
NEW_ABS = r"""\begin{abstract}
% [v7] Rewritten: leads with the mechanism and the result; scope limits kept
% but stated once rather than after every claim.
We study a compact neuromorphic residual architecture for quaternion attitude
tracking under bounded actuator commands. A fixed quaternion
proportional--derivative (PD) controller is augmented by six paired
continuous coupled membrane--gate (CMG) units: a conductance-based membrane
coupled to a gating variable, in the graded, non-spiking regime that analog
neuromorphic circuits realize directly. Their gate-derived activities are
decoded through eighteen weights adapted online by prescribed error
sensitivity (PES), and the decoded residual is \emph{added} to the saturated
baseline, so the baseline is recovered exactly when the residual authority is
zero. We separate three mechanisms that are usually conflated --- intrinsic
conductance modulation, decoder learning, and output authority --- and
establish bounded neural states, bounded command deviation, projected decoder
boundedness, and a restricted frozen-feature learning result. In ten matched
45-s MuJoCo cases spanning five missions, a Skydio X2 model and a
Crazyflie~2.0 model completed with an explicit four-rotor actuation interface
track $17.3$--$60.6\%$ more accurately than PD, with zero actuator-bound
occupancy outside brief Hardstep intervals. Direct and Nengo realizations
agree to $2.013\times10^{-6}$ in relative mean error. Controlled ablation
attributes the improvement to online decoder adaptation rather than to
conductance modulation in the tested gate-gain regime --- a result that
constrains, rather than confirms, the role of the neuron model. The study is
in simulation, with one run per cell, and establishes boundedness rather than
closed-loop stability.
"""
s = s[:i] + NEW_ABS + s[j:]
n += 1
print("  ok  abstract")

# ===========================================================================
# 3. contributions list: drop the AAT item, state the study positively
# ===========================================================================
sub(
    r"""The central question is whether this small stateful basis can improve
tracking, and which of its components explains the improvement. The paper
contributes: (i) a code-aligned CMG--PES architecture with paired currents,
explicit state/readout equations, and actuator interfaces
(Fig.~\ref{fig:arch}); (ii) precise
boundedness and baseline-recovery properties, without an unsupported
closed-loop stability claim; (iii) a five-mission, two-model study with
direct/Nengo agreement and neuron-family comparisons; and (iv) a separate
study of annealed activity-trace learning that documents its implementation
and evidence limitations. Selected preliminary Hover tests support
physical feasibility but are not the main validation claim.""",
    r"""The central question is whether this small stateful basis can improve
tracking, and which of its components explains the improvement. The paper
contributes: (i) a code-aligned CMG--PES architecture with paired currents,
explicit state and readout equations, and a fully specified actuator
interface (Fig.~\ref{fig:arch}); (ii) boundedness and exact
baseline-recovery properties, stated at the strength the analysis supports;
(iii) a matched five-mission, two-model study in which the direct and Nengo
realizations agree to $2\times10^{-6}$; and (iv) a controlled ablation that
separates conductance modulation, decoder learning, and output authority,
and identifies which of the three carries the effect. The third and fourth
are the substantive contributions: the architecture is small and its
components are individually replaceable, so establishing \emph{which} part
does the work is more useful than reporting that the whole improves
tracking.""",
    "intro/contributions")

# ===========================================================================
# 4. reframe "neuromorphic" -- placement, not apology
# ===========================================================================
sub(
    r"""Here ``neuromorphic'' refers to neuron-inspired continuous state dynamics,
local error-directed learning, and a neural-simulator realization. The
implementation does not emit spikes and has not been deployed on
neuromorphic hardware; no power advantage is claimed. PES is an
established rule, and novelty is claimed for its integration and controlled
evaluation in this architecture, not for PES itself.""",
    r"""% [v7] Positioned rather than apologised for.
The CMG unit is conductance-based: a leaky membrane whose effective
conductance is modulated by a gating variable with its own first-order
dynamics and threshold self-coupling. Structurally this is the
Hodgkin--Huxley gating lineage rather than the leaky integrate-and-fire one,
operated in a graded, non-spiking regime; there is no firing threshold and
no reset event. That regime is not a weakening of the neuromorphic premise
but the one in which neuromorphic engineering began: analog silicon neurons
implement membrane leak, synaptic conductance, and sigmoidal gating directly
as device physics \cite{mahowald1991vlsi}, without the comparator and
event-routing hardware that spiking requires. We therefore use
``neuromorphic'' in that conductance-based sense throughout. No power or
device-level claim is made here; the implementation is a digital simulation,
and Sec.~\ref{sec:conclusion} states what would be required to test the
analog case. PES is an established rule \cite{voelker2015pes}; what is new
here is the basis it decodes and the controlled separation of the mechanisms
that basis contributes.""",
    "intro/neuromorphic")

# ===========================================================================
# 5. CF2: lead with the manufacturer comparison
# ===========================================================================
sub(
    r"""For CF2, the unscaled model's total thrust limit is $0.35$ N. We evaluate
a rotor-interface model with increased actuator authority: multiplying
$f_{\max,i}$ by $1.5$ yields $0.525$ N total
(Table~\ref{tab:models}). This raises the modeled maximum thrust/weight
from $1.321$ to $1.982$ at $g=9.81$ m/s$^2$.""",
    r"""% [v7] The manufacturer comparison now leads, because it is the fact that
% licenses the model, not an afterthought.
The upstream CF2 model ships without a rotor-level actuation interface, and
its $0.35$ N total thrust limit falls short of the $0.568$ N measured on
stock hardware at $93.75\%$ PWM \cite{bitcrazeThrustMeasurements}. We
therefore complete the model with an explicit four-rotor interface and set
the per-rotor limit so the total is $0.525$ N (Table~\ref{tab:models}),
which remains about $7.5\%$ \emph{below} that measured value. The
correction is toward the manufacturer's own measurement, not beyond it: it
raises modeled maximum thrust/weight from $1.321$ to $1.982$ at
$g=9.81$ m/s$^2$, a figure the physical vehicle exceeds.""",
    "cf2/lead-with-manufacturer")

# ===========================================================================
# 6. remove the annealed activity-trace subsection (Sec. III)
# ===========================================================================
cut(r"\subsection{Annealed Activity-Trace Variant}",
    r"\subsection{Nengo Realization}",
    "cut/AAT-math")

# ===========================================================================
# 7. add the small-gain remark where the AAT subsection was
# ===========================================================================
sub(
    r"""\subsection{Nengo Realization}""",
    r"""% [v7] The statement a control audience looks for first. Scoped: it is a
% conditional bound, not a stability theorem, and says so.
\begin{remark}[Scope of a small-gain argument]
\label{rem:smallgain}
Propositions~\ref{prop:authority} and \ref{prop:pes} place the realized
command deviation in a known box, $|\delta_{k,i}|\le\beta\ell_i$, uniformly
in $k$ and independently of what the decoder has learned. If the baseline
loop is input-to-state stable with respect to an additive torque
perturbation, with gain $\gamma(\cdot)$ on that input, then the augmented
loop inherits an ISS estimate with asymptotic bound
$\gamma(\beta\|\bm\ell\|)$, and $\beta$ tunes it continuously to zero. Two
conditions are not discharged here. The perturbation entering the plant is
post-allocation, so the relevant bound is on $B^{-1}$ applied to
$\bm\delta_k$ under rotor saturation, not on $\bm\delta_k$ itself; and the
required ISS gain for the saturated quaternion-PD baseline is not
established in this paper. The architecture therefore supplies the bounded
perturbation such an argument needs, and identifies the two missing
ingredients, without asserting the conclusion.
\end{remark}

\subsection{Nengo Realization}""",
    "add/small-gain-remark")

# ===========================================================================
# 8. remove the AAT results section and the physical Hover section
# ===========================================================================
cut(r"\section{Annealed Learning: Verified Precursor Evidence}",
    r"\section{Discussion and Conclusion}",
    "cut/AAT-results+hover")

# ===========================================================================
# 9. conclusion: rewrite
# ===========================================================================
i = s.index(r"\section{Discussion and Conclusion}")
j = s.index(r"% Finalize human authors")
NEW_CONC = r"""\section{Discussion and Conclusion}
\label{sec:conclusion}
% [v7] Rewritten: states the positive result once and plainly, keeps the
% limits in one place instead of after every sentence, and separates the
% analog outlook from the claims.
A fixed quaternion-PD law augmented by six paired continuous membrane--gate
units and eighteen online-adapted decoder weights reduces mean attitude
error by $17.3$--$60.6\%$ across ten matched 45-s cases on two modeled
platforms, with actuator bounds respected throughout and the baseline
recovered exactly at zero authority. The direct and Nengo realizations agree
to $2.013\times10^{-6}$, so the result is a property of the architecture
rather than of one implementation.

The ablation is the more informative half. Holding the decoder mode fixed
and toggling conductance modulation is numerically indistinguishable under
the tested settings, while freezing the decoder removes most of the gain.
In this regime the improvement is carried by online decoder adaptation over
a bounded nonlinear basis, not by the specific neuron dynamics. Because
$a_j=\clip(10^5r_j,0,1)$, activity saturates once $r_j$ exceeds $10^{-5}$,
which plausibly explains that insensitivity and identifies the gate gain as
the parameter a follow-up should sweep first. Reporting this constrains the
architecture's claim rather than supporting it, and it is the reason the
contribution is stated as a controlled separation of mechanisms.

Three limits bound the above. The study is in simulation with one run per
cell, so it reports repeatable nominal performance rather than robustness or
statistical spread. The comparison is against a well-tuned PD without
integral action, not against every reasonable baseline. And bounded
commands, states, and weights are implementation properties, not stability
proofs; Remark~\ref{rem:smallgain} states exactly which two ingredients an
ISS argument still needs.

The continuous regime suggests a hardware direction that a spiking
formulation forecloses. Membrane leak, sigmoidal gating, and a shunting
conductance are the primitives analog neuromorphic circuits implement as
device physics \cite{mahowald1991vlsi}, with no comparator, reset, or
event-routing logic, and the gate transient carries the timing information a
spike would otherwise discretize. Whether that translates into an energy
advantage is untested and does not follow from these results: a graded
analog system draws static rather than event-sparse power, and at six
neurons and eighteen weights the controller is negligible on any substrate.
The claim such a study would have to make is a per-decision energy
comparison at matched tracking accuracy, including conversion and sensing;
online decoder adaptation is attractive there mainly because it can absorb
device mismatch, which is the standard argument for learning on analog
hardware. We flag this as motivation for the continuous formulation, not as
a result.

Preliminary real-time tests on a Quanser 3DOF Hover confirm the controller
meets a 200-Hz hardware deadline with ten 0.5-ms neural substeps per sample;
three matched Roll pairs improved mean error by $2.65\%\pm1.08\%$. That rig
is a different plant from either simulated airframe, so those runs are
reported as feasibility rather than validation and are analyzed separately.
Follow-up work includes repeated runs with perturbed initial conditions,
an integral-action baseline, a matched-effort comparison against
non-neural bounded bases, a gate-gain sweep, and frozen-weight held-out
tests.

"""
s = s[:i] + NEW_CONC + s[j:]
n += 1
print("  ok  conclusion")

# ===========================================================================
# 10. soften the worst remaining hedges
# ===========================================================================
SOFTEN = [
    (r"""Our contribution is not
the first PES/Nengo UAV controller. Instead, we investigate a specific
continuous membrane--gate basis for a bounded quaternion-torque residual,
with a fixed classical controller and adaptation confined to its decoder.""",
     r"""Building on that line, we
investigate a specific continuous membrane--gate basis for a bounded
quaternion-torque residual, with a fixed classical controller and adaptation
confined to its decoder.""",
     "soften/intro-not-first"),

    (r"""These cases demonstrate repeatable nominal
performance, not robustness to model mismatch or a universally optimal PD
comparison.""",
     r"""These cases establish repeatable nominal performance; robustness to model
mismatch and comparison against other baseline families are separate
questions, addressed in Sec.~\ref{sec:conclusion}.""",
     "soften/results-caveat"),

    (r"""This identifies decoder adaptation as the
principal tested lever, not a universal claim that conductance never matters.""",
     r"""Decoder adaptation is therefore the principal lever in the tested regime.""",
     "soften/ablation"),

    (r"""Accordingly, the supported conclusion is a tracking--effort tradeoff, not
universal CMG superiority or a proven causal effect of spiking.""",
     r"""The supported conclusion is therefore a tracking--effort tradeoff: CMG--PES
attains comparable tracking at markedly lower realized residual effort.""",
     "soften/neuron-family"),
]
for old, new, tag in SOFTEN:
    sub(old, new, tag)

io.open(DST, "w", encoding="utf-8").write(s)
print(f"\nwrote {DST}  ({n} changes)")
