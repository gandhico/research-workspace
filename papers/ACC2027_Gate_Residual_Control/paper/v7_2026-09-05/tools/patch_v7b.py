"""Follow-up to patch_v7: the nomenclature still lists annealed-variant
symbols whose defining equation was removed. Keep the reported metrics,
drop the AAT rows.
"""
from __future__ import annotations

import io

DST = "ACC2027_v7.tex"
s = io.open(DST, encoding="utf-8").read()

old = (r"""\multicolumn{6}{@{}l}{\textit{Annealed variant and reported metrics}}\\
$\bm z_k$ & activity trace \eqref{eq:aat} & $\rho(s)$ & trace factor \eqref{eq:aat} & $s=t/T$ & mission progress\\
$\eta_0$ & initial annealed rate & $\bar\theta_q$ & mean quaternion-angle error & $S$ & actuator-bound occupancy [\%]\\""")

new = (r"""\multicolumn{6}{@{}l}{\textit{Reported metrics}}\\
$\bar\theta_q$ & mean quaternion-angle error & $S$ & actuator-bound occupancy [\%] & $n$ & runs per reported cell\\""")

if old not in s:
    raise SystemExit("PATCH FAILED: nomenclature AAT rows not found verbatim")
s = s.replace(old, new, 1)

# the earlier "runs per reported cell" entry is now duplicated
dup = r"""$\bm f_{\max}$ & per-rotor force bound & $g$ & gravity, $9.81$\,m/s$^2$ & $n$ & runs per reported cell\\"""
rep = r"""$\bm f_{\max}$ & per-rotor force bound & $g$ & gravity, $9.81$\,m/s$^2$ & $\bm 1$ & vector of ones\\"""
if dup in s:
    s = s.replace(dup, rep, 1)
    print("  deduplicated the 'runs per cell' entry")

# and the now-duplicated vector-of-ones entry from the notation block
dup2 = r"""$\bm 1$ & vector of ones & $I_m$ & identity of order $m$ & $\R$ & real numbers\\"""
rep2 = r"""$I_m$ & identity of order $m$ & $\R$ & real numbers & $\Pi$ & Euclidean projection\\"""
if dup2 in s:
    s = s.replace(dup2, rep2, 1)
    print("  deduplicated the 'vector of ones' entry")

io.open(DST, "w", encoding="utf-8").write(s)
print("nomenclature updated")
