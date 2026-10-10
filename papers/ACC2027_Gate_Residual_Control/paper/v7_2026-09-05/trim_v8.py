"""Fix the stale reference and tighten the v8 additions to fit nine pages."""
from __future__ import annotations

import io

P = "ACC2027_v8.tex"
s = io.open(P, encoding="utf-8").read()
n = 0


def sub(old: str, new: str, tag: str) -> None:
    global s, n
    c = s.count(old)
    if c != 1:
        raise SystemExit(f"FAILED [{tag}]: found {c}, expected 1")
    s = s.replace(old, new, 1)
    n += 1
    print(f"  ok  {tag}")


sub(r"\ref{sec:models}", r"\ref{sec:problem}", "stale-ref")

# --- noise subsection: same content, fewer words ---------------------------
sub(r"""Table~\ref{tab:mujoco} uses noise-free state feedback and one run per cell.
To bound what that costs, every cell was rerun with zero-mean Gaussian noise
added to the attitude and rate estimates at two levels, two seeds each
(Table~\ref{tab:noise}).

Across all twenty noisy cells the seed standard deviation of the reduction
is between $0.002\%$ and $0.031\%$, three orders of magnitude below the
effect itself. Under this disturbance model the missions are therefore
effectively deterministic, and a single run per condition is an adequate
estimator; noise \emph{magnitude}, not seed, is the axis that matters.

The magnitude response is not uniform. Full3, Hard45, and Hardstep move by
less than one point between clean and realistic noise. Yaw360 loses
$12.8$ points on both models: its absolute error is the smallest in the
matrix, so a fixed noise floor consumes a larger share of the ratio while
the PD reference error itself grows by about $10\%$. Roll moves the other
way, from $17.4\%$ to $32.2\%$, which is consistent with the residual
having more to correct once the baseline is disturbed. Under realistic
noise the range across the matrix is $18.1$--$55.8\%$, narrower at both
ends than the noise-free $17.3$--$60.6\%$. The two models agree to within
$0.4$ points in every cell, which is an independent check on the CF2
actuation interface of Sec.~\ref{sec:problem}.""",
    r"""Table~\ref{tab:mujoco} uses noise-free feedback and one run per cell.
Every cell was therefore rerun with zero-mean Gaussian noise on the attitude
and rate estimates, at two levels and two seeds (Table~\ref{tab:noise}).

Across the twenty noisy cells the seed standard deviation of the reduction
is $0.002$--$0.031\%$, three orders of magnitude below the effect: under
this disturbance model the missions are effectively deterministic, and noise
\emph{magnitude}, not seed, is the axis that matters. The magnitude response
is not uniform. Full3, Hard45, and Hardstep move by under one point. Yaw360
loses $12.8$ points on both models, its absolute error being the smallest in
the matrix, so a fixed noise floor takes a larger share of the ratio. Roll
moves the other way, $17.4\%$ to $32.2\%$, consistent with the residual
having more to correct once the baseline is disturbed. The realistic-noise
range is $18.1$--$55.8\%$, narrower at both ends than $17.3$--$60.6\%$, and
the two models agree within $0.4$ points in every cell.""",
    "noise-prose")

# --- disturbance subsection: same content, fewer words ---------------------
sub(r"""The missions above track a moving reference. A complementary test holds the
equilibrium attitude and applies a multi-sine body torque in bursts, so the
controller is observed entering a disturbance, adapting inside it, and then
holding a decoder adapted to a disturbance that has stopped
(Fig.~\ref{fig:hover_int}).

Before the first burst the residual norm is $O(10^{-16})$ and both
controllers hold the equilibrium exactly: the augmented loop is inert when
the baseline is already exact. During bursts the mean error falls from
$11.50^\circ$ to $6.65^\circ$ ($42.2\%$); during the quiet intervals it
falls from $1.21^\circ$ to $0.99^\circ$ ($18.0\%$). Repeating the study on
CF2 with the disturbance scaled by the inertia ratio gives a $50.2\%$
reduction, so the effect is not specific to one airframe.

Extending to $180$\,s and sixteen bursts separates two behaviours that the
short run cannot. Burst-phase reduction is flat across the run,
$43.3\%$ in the first episode and $40.6\%$ in the seventeenth. Quiet-phase
reduction instead improves monotonically after the first episodes, from
$25.6\%$ to $63.4\%$, while $\|W_k-W_0\|_F$ grows from $0.14$ to $0.75$.
The decoder is therefore accumulating a correction that is reused across
episodes rather than relearning each one, and the accumulation improves
recovery rather than degrading it. Two caveats attach. In the second
episode the augmented loop is $4\%$ \emph{worse} than the baseline in the
quiet phase, the only such interval observed. And the displacement is still
growing at $180$\,s with $\max_i|W_{k,i}|=1.09$, inside $\mathcal W$ but not
saturated, so these runs do not establish that retention converges on
longer missions.""",
    r"""A complementary test holds the equilibrium attitude and applies a
multi-sine body torque in bursts, so the controller is seen entering a
disturbance, adapting inside it, and then holding a decoder adapted to a
disturbance that has stopped (Fig.~\ref{fig:hover_int}).

Before the first burst the residual norm is $O(10^{-16})$: the augmented
loop is inert when the baseline is already exact. During bursts the mean
error falls from $11.50^\circ$ to $6.65^\circ$ ($42.2\%$), and during the
quiet intervals from $1.21^\circ$ to $0.99^\circ$ ($18.0\%$). The same study
on CF2, with the disturbance scaled by the inertia ratio, gives $50.2\%$.

Over $180$\,s and sixteen bursts the burst-phase reduction stays flat
($43.3\%$ to $40.6\%$) while the quiet-phase reduction improves from
$25.6\%$ to $63.4\%$ and $\|W_k-W_0\|_F$ grows from $0.14$ to $0.75$. The
decoder accumulates a correction reused across episodes rather than
relearning each one, and that accumulation improves recovery. Two caveats:
in the second episode the augmented loop is $4\%$ \emph{worse} in the quiet
phase, the only such interval observed; and the displacement is still
growing at $180$\,s, with $\max_i|W_{k,i}|=1.09$ inside $\mathcal W$ but not
saturated, so retention is not shown to converge on longer missions.""",
    "disturbance-prose")

# --- float sizing ----------------------------------------------------------
sub(r"\includegraphics[width=0.98\linewidth]{hover_intermittent}",
    r"\includegraphics[width=0.88\linewidth]{hover_intermittent}",
    "figure-size")

sub(r"\label{tab:noise}\centering\small", r"\label{tab:noise}\centering\footnotesize",
    "table-size")

io.open(P, "w", encoding="utf-8").write(s)
print(f"\ntrimmed {P} ({n} changes)")
