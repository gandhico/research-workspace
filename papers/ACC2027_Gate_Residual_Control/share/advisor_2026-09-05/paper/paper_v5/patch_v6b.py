"""Stage 2 of the v6 build: pay for the new architecture figures and the
nomenclature table by removing duplicated float area.

Run after patch_v6.py.  Every change is marked `% [v6]`.

Reductions, in order of how little they cost the reader:
  R1  fig:scale and fig:models showed the same two aircraft twice.
      They are merged into one three-panel figure*.
  R2  the six result plots are set to 0.86\\linewidth instead of \\linewidth.
  R3  fig:hardstep_neurons is dropped; two neural-activity panels
      (Hard45 and CF2 Yaw360) already cover the same ground.
"""
from __future__ import annotations

import io

DST = "ACC2027_v6.tex"
s = io.open(DST, encoding="utf-8").read()
n = 0


def sub(old: str, new: str, tag: str, count: int = 1) -> None:
    global s, n
    found = s.count(old)
    if found != count:
        raise SystemExit(f"PATCH FAILED [{tag}]: found {found}, expected {count}")
    s = s.replace(old, new)
    n += 1
    print(f"  ok  {tag}")


# ---------------------------------------------------------------------------
# R1  merge the two vehicle figures into one three-panel figure*
# ---------------------------------------------------------------------------
OLD_SCALE = r"""\begin{figure}[!h]
\centering
\includegraphics[width=\linewidth]{\detokenize{all/skydio_crazyflie_models_cropped (1)}}
\caption{Skydio X2 (X2) and Crazyflie~2.0 (CF2) MuJoCo model geometries. The shown axis triads are body-frame axes; they are rigidly attached to the vehicle and therefore rotate with the vehicle relative to the inertial (world) frame (cf. $Q\!:\,\text{body}\to\text{inertial}$ in Sec.~\ref{sec:problem}).}
\label{fig:scale}
\end{figure}

\begin{figure*}[t]
\centering
\begin{minipage}[t]{0.48\textwidth}\centering
\includegraphics[width=\linewidth]{\detokenize{all/crazyflie2_cropped (1)}}
\end{minipage}\hfill
\begin{minipage}[t]{0.48\textwidth}\centering
\includegraphics[width=\linewidth]{all/skydiox2_cropped}
\end{minipage}
\caption{Hardware-Drones and MuJoCo model geometries used in simulation: CF2 (left) and X2 (right).}
\label{fig:models}
\end{figure*}"""

NEW_MODELS = r"""% [v6] fig:scale and fig:models were merged: both showed the same two
% aircraft. The old \ref{fig:scale} call sites now point here.
\begin{figure*}[t]
\centering
\begin{minipage}[b]{0.31\textwidth}\centering
\includegraphics[width=\linewidth]{\detokenize{all/crazyflie2_cropped (1)}}
\end{minipage}\hfill
\begin{minipage}[b]{0.31\textwidth}\centering
\includegraphics[width=\linewidth]{all/skydiox2_cropped}
\end{minipage}\hfill
\begin{minipage}[b]{0.34\textwidth}\centering
\includegraphics[width=\linewidth]{\detokenize{all/skydio_crazyflie_models_cropped (1)}}
\end{minipage}
\caption{Vehicles and simulation models. Left: CF2 hardware and MuJoCo
model. Centre: X2 hardware and MuJoCo model. Right: both geometries at
relative scale. The axis triads are body-frame axes: they are rigidly
attached to the vehicle and therefore rotate with it relative to the
inertial (world) frame (cf.\ $Q\!:\,\text{body}\to\text{inertial}$ in
Sec.~\ref{sec:problem}).}
\label{fig:models}
\end{figure*}"""

sub(OLD_SCALE, NEW_MODELS, "R1/merge-vehicle-figs")

sub(r"""signals in Fig.~\ref{fig:scale}; the corresponding airframes are shown
in Fig.~\ref{fig:models}.""",
    r"""signals in Fig.~\ref{fig:models}.""",
    "R1/ref-1")

sub(r"""the relevant center-of-mass moment arms. Figure~\ref{fig:scale} fixes the""",
    r"""the relevant center-of-mass moment arms. Figure~\ref{fig:models} fixes the""",
    "R1/ref-2")

# ---------------------------------------------------------------------------
# R2  trim the result-plot width
# ---------------------------------------------------------------------------
for stem in ["X2/Hard45/x2_hard45_classical_vs_cmg",
             "X2/Hard45/x2_hard45_neurons",
             "X2/Hardstep/x2_hardstep_attitude",
             "CF2/Yaw360/cf2_yaw360_classical_vs_cmg",
             "CF2/Yaw360/cf2-rotor_yaw360_neurons"]:
    sub(r"\includegraphics[width=\linewidth]{%s}" % stem,
        r"\includegraphics[width=0.86\linewidth]{%s}" % stem,
        f"R2/{stem.split('/')[-1]}")

# ---------------------------------------------------------------------------
# R3  drop the third, redundant neural-activity panel
# ---------------------------------------------------------------------------
sub(r"""\begin{figure}[t]
\centering
\includegraphics[width=\linewidth]{X2/Hardstep/x2_hardstep_neurons}
\caption{X2 Hardstep: neural activity for the CMG residual controller.}
\label{fig:hardstep_neurons}
\end{figure}

""", "", "R3/drop-hardstep-neurons")

sub(r"""neural activity that produced it; Figs.~\ref{fig:hardstep_attitude} and
\ref{fig:hardstep_neurons} show the Hardstep case, where the reduction is
smallest and the only nonzero bound occupancy occurs.""",
    r"""neural activity that produced it; Fig.~\ref{fig:hardstep_attitude} shows
the Hardstep case, where the reduction is smallest and the only nonzero
bound occupancy occurs.""",
    "R3/fix-ref")

io.open(DST, "w", encoding="utf-8").write(s)
print(f"\nupdated {DST}  ({n} reductions applied)")
