"""Stage 3: close the gaps the symbol-coverage check found.

check_symbols.py flagged symbols that appear in displayed equations but not
in the nomenclature: the reference/error body rates, the quaternion rotation
matrix, the height loop's variables, the per-rotor force bound, and
gravity -- which is a distinct quantity from the conductance gains g0, g1
despite the shared letter. That clash is called out explicitly.
"""
from __future__ import annotations

import io

DST = "ACC2027_v6.tex"
s = io.open(DST, encoding="utf-8").read()
n = 0


def sub(old: str, new: str, tag: str) -> None:
    global s, n
    if s.count(old) != 1:
        raise SystemExit(f"PATCH FAILED [{tag}]: found {s.count(old)}, expected 1")
    s = s.replace(old, new, 1)
    n += 1
    print(f"  ok  {tag}")


# extra row in the attitude/plant group
sub(
    r"""$\odot,\oslash$ & elementwise $\times$, $\div$ & $\sgnp$ & sign, with $\sgnp(0)=1$ & $\sigma$ & logistic function\\""",
    r"""$\bm\omega_d,\bm\omega_e$ & reference and error rate \eqref{eq:errkin} & $R(\cdot)$ & rotation matrix of a quaternion & $z,z_d,\dot z$ & height, reference, rate \eqref{eq:collective}\\
$\odot,\oslash$ & elementwise $\times$, $\div$ & $\sgnp$ & sign, with $\sgnp(0)=1$ & $\sigma$ & logistic function\\
$\bm 1$ & vector of ones & $I_m$ & identity of order $m$ & $\R$ & real numbers\\""",
    "nomen/attitude-row")

# extra row in the actuator group; g is gravity, not a conductance gain
sub(
    r"""$\kappa_i$ & rotor reaction coefficient & $m$ & torque channels, $m=3$ & $M$ & vehicle mass\\""",
    r"""$\kappa_i$ & rotor reaction coefficient & $m$ & torque channels, $m=3$ & $M$ & vehicle mass\\
$\bm f_{\max}$ & per-rotor force bound & $g$ & gravity, $9.81$\,m/s$^2$ & $n$ & runs per reported cell\\""",
    "nomen/actuator-row")

sub(
    r"""$g_0,g_1$ & conductance gains & $G$ & activity gain, $G=10^5$ & $h$ & integration step\\""",
    r"""$g_0,g_1$ & conductance gains (distinct from $g$) & $G$ & activity gain, $G=10^5$ & $h$ & integration step\\""",
    "nomen/g-clash")

# the initial-decoder cell now duplicates the identity entry above
sub(
    r"""$\bm a_k$ & clipped activity \eqref{eq:readout} & $W_k$ & decoder \eqref{eq:readout} & $W_0=[I_m,-I_m]$ & initial decoder\\""",
    r"""$\bm a_k$ & clipped activity \eqref{eq:readout} & $W_k$ & decoder \eqref{eq:readout} & $W_0$ & initial decoder, $[I_m,-I_m]$\\""",
    "nomen/dedupe-Im")

io.open(DST, "w", encoding="utf-8").write(s)
print(f"\nupdated {DST}  ({n} patches applied)")
