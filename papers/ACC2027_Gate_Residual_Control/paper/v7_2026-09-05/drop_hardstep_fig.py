"""Remove fig:hardstep_attitude to fit nine pages.

Rationale: the new Table~\\ref{tab:noise} reports Hardstep quantitatively for
both platforms at three noise levels, so this figure is the only float whose
information is now fully duplicated by a table. It is also the smallest
effect in the matrix. Every other figure and table is untouched.

To restore it, revert this script's two edits and drop one of the
non-destructive squeezes in squeeze_v8.py.
"""
from __future__ import annotations

import io

P = "ACC2027_v8.tex"
s = io.open(P, encoding="utf-8").read()

FIG = r"""\begin{figure}[t]
\centering
\includegraphics[width=0.62\linewidth]{X2/Hardstep/x2_hardstep_attitude}
\caption{X2 Hardstep: attitude tracking time series (hard step reference).}
\label{fig:hardstep_attitude}
\end{figure}

"""
assert FIG in s, "figure block not found verbatim"
s = s.replace(FIG, "", 1)

OLD_REF = (r"""neural activity that produced it; Fig.~\ref{fig:hardstep_attitude} shows
the Hardstep case, where the reduction is smallest and the only nonzero
bound occupancy occurs.""")
NEW_REF = (r"""neural activity that produced it. Hardstep, the smallest reduction and the
only case with nonzero bound occupancy, is reported in
Tables~\ref{tab:mujoco} and \ref{tab:noise}.""")
assert OLD_REF in s, "cross-reference not found verbatim"
s = s.replace(OLD_REF, NEW_REF, 1)

io.open(P, "w", encoding="utf-8").write(s)
print("removed fig:hardstep_attitude and rewrote its cross-reference")
