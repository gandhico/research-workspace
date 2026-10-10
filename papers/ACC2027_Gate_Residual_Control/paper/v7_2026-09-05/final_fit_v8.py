"""Last fit to nine pages: shrink the decorative vehicle photographs and
tighten two sentences. No result, figure, or table is removed.
"""
from __future__ import annotations

import io

P = "ACC2027_v8.tex"
s = io.open(P, encoding="utf-8").read()
n = 0


def swap(old: str, new: str, tag: str) -> None:
    global s, n
    if old not in s:
        raise SystemExit(f"FAILED [{tag}]")
    s = s.replace(old, new, 1)
    n += 1
    print(f"  ok  {tag}")


# the three drone photographs are decorative next to Fig. 1
swap(r"\begin{minipage}[b]{0.29\textwidth}", r"\begin{minipage}[b]{0.24\textwidth}",
     "vehicles-1")
swap(r"\begin{minipage}[b]{0.29\textwidth}", r"\begin{minipage}[b]{0.24\textwidth}",
     "vehicles-2")
swap(r"\begin{minipage}[b]{0.31\textwidth}", r"\begin{minipage}[b]{0.26\textwidth}",
     "vehicles-3")

# two sentences that can carry the same content in fewer words
swap(r"""Yaw360
loses $12.8$ points on both models, its absolute error being the smallest in
the matrix, so a fixed noise floor takes a larger share of the ratio. Roll
moves the other way, $17.4\%$ to $32.2\%$, consistent with the residual
having more to correct once the baseline is disturbed. The realistic-noise
range is $18.1$--$55.8\%$, narrower at both ends than $17.3$--$60.6\%$, and
the two models agree within $0.4$ points in every cell.""",
     r"""Yaw360
loses $12.8$ points on both models: its absolute error is the smallest in the
matrix, so a fixed noise floor takes a larger share of the ratio. Roll moves
the other way, $17.4\%$ to $32.2\%$, consistent with the residual having more
to correct once the baseline is disturbed. The realistic-noise range is
$18.1$--$55.8\%$, narrower at both ends than $17.3$--$60.6\%$.""",
     "noise-trim")

swap(r"""The
decoder accumulates a correction reused across episodes rather than
relearning each one, and that accumulation improves recovery. Two caveats:
in the second episode the augmented loop is $4\%$ \emph{worse} in the quiet
phase, the only such interval observed; and the displacement is still
growing at $180$\,s, with $\max_i|W_{k,i}|=1.09$ inside $\mathcal W$ but not
saturated, so retention is not shown to converge on longer missions.""",
     r"""The
decoder accumulates a correction reused across episodes rather than
relearning each one. Two caveats: in the second episode the augmented loop
is $4\%$ \emph{worse} in the quiet phase, the only such interval observed;
and the displacement is still growing at $180$\,s, with
$\max_i|W_{k,i}|=1.09$ inside $\mathcal W$ but not saturated, so retention is
not shown to converge on longer missions.""",
     "disturbance-trim")

io.open(P, "w", encoding="utf-8").write(s)
print(f"\nfitted ({n} changes)")
