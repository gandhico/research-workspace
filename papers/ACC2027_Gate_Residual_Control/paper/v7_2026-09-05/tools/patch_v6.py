"""Build ACC2027_v6.tex from ACC2027.tex.

Every insertion is marked with a `% [v6]` comment so it can be located,
edited, or reverted individually. Run:  python patch_v6.py
"""
from __future__ import annotations

import io
import shutil

SRC = "ACC2027.tex"
DST = "ACC2027_v6.tex"

shutil.copyfile(SRC, DST)
s = io.open(DST, encoding="utf-8").read()
n = 0


def sub(old: str, new: str, tag: str) -> None:
    global s, n
    if old not in s:
        raise SystemExit(f"PATCH FAILED [{tag}]: anchor not found")
    if s.count(old) != 1:
        raise SystemExit(f"PATCH FAILED [{tag}]: anchor is not unique")
    s = s.replace(old, new, 1)
    n += 1
    print(f"  ok  {tag}")


# ---------------------------------------------------------------------------
# 1. preamble: TikZ for the architecture figures
# ---------------------------------------------------------------------------
sub(
    r"""\newcommand{\R}{\mathbb R}""",
    r"""% [v6] TikZ support for the architecture figures in figures/arch/.
\usepackage{tikz}
\usetikzlibrary{arrows.meta,positioning,fit,backgrounds,calc}
\input{figures/arch/arch_style.tex}

\newcommand{\R}{\mathbb R}""",
    "preamble/tikz")

# ---------------------------------------------------------------------------
# 2. introduction: point at the architecture figure
# ---------------------------------------------------------------------------
sub(
    r"""explicit state/readout equations, and actuator interfaces;""",
    r"""explicit state/readout equations, and actuator interfaces
(Fig.~\ref{fig:arch});""",
    "intro/ref-arch")

# ---------------------------------------------------------------------------
# 3. architecture figure* (new Fig. 1), placed before the vehicle photographs
# ---------------------------------------------------------------------------
ARCH_FIG = r"""% [v6] Architecture overview. Source: figures/arch/archA2p.tex
% (editable draw.io version: figures/arch/architectures.drawio, page A2).
\begin{figure*}[t]
\centering
\resizebox{\textwidth}{!}{\input{figures/arch/archA2p.tex}}
\caption{CMG--PES residual architecture. The classical path (light blocks)
is fixed: shortest-path quaternion error \eqref{eq:theta}, PD law
\eqref{eq:pd}, and rotor allocation \eqref{eq:mixer} are never adapted. The
neuromorphic path (heavy blocks) encodes the clipped baseline as paired
currents \eqref{eq:encoding}, evolves $2m$ coupled membrane--gate units
\eqref{eq:cmg}, and decodes a bounded residual \eqref{eq:readout} that is
\emph{added} to the saturated baseline \eqref{eq:residual}. Only the
$m\times2m$ decoder $W_k$ adapts, through the projected PES update
\eqref{eq:pes}; setting $\beta=0$ recovers the baseline exactly. Dashed
blocks are computed from measurements rather than being physical
subsystems.}
\label{fig:arch}
\end{figure*}

"""
sub(r"""\begin{figure}[!h]
\centering
\includegraphics[width=\linewidth]{\detokenize{all/skydio_crazyflie_models_cropped (1)}}""",
    ARCH_FIG + r"""\begin{figure}[!h]
\centering
\includegraphics[width=\linewidth]{\detokenize{all/skydio_crazyflie_models_cropped (1)}}""",
    "fig/arch")

# ---------------------------------------------------------------------------
# 4. reference the orphaned vehicle-photograph figure
# ---------------------------------------------------------------------------
sub(
    r"""signals in Fig.~\ref{fig:scale}.""",
    r"""signals in Fig.~\ref{fig:scale}; the corresponding airframes are shown
in Fig.~\ref{fig:models}.""",
    "ref/fig:models")

# ---------------------------------------------------------------------------
# 5. nomenclature table* (new Table I)
# ---------------------------------------------------------------------------
NOMEN = r"""% [v6] Nomenclature. Every symbol that appears in an equation is listed
% once here; the bracketed tag is the equation that defines it.
\begin{table*}[t]
\caption{Nomenclature. Parenthesised tags give the defining equation.
Vectors are bold; $\odot$ and $\oslash$ are elementwise product and
quotient; $\clip_{[a,b]}$ and $\sat_{\bm\ell}$ act elementwise.}
\label{tab:nomen}\centering\scriptsize
\setlength{\tabcolsep}{4pt}
\renewcommand{\arraystretch}{1.08}
\begin{tabular}{@{}l>{\raggedright\arraybackslash}p{0.185\textwidth}l>{\raggedright\arraybackslash}p{0.185\textwidth}l>{\raggedright\arraybackslash}p{0.185\textwidth}@{}}
\toprule
\multicolumn{6}{@{}l}{\textit{Attitude, plant, and notation}}\\
$q,\;q_d$ & state / reference quaternion & $q_e$ & error quaternion, $q_d\otimes q^{-1}$ & $q_{e,0},\bm q_{e,v}$ & scalar and vector parts\\
$\bm e_q$ & shortest-path error \eqref{eq:theta} & $\theta_q$ & error angle \eqref{eq:theta} & $\bm\omega$ & body angular rate\\
$J$ & inertia tensor & $Q$ & body-to-inertial rotation & $\otimes$ & quaternion product\\
$\odot,\oslash$ & elementwise $\times$, $\div$ & $\sgnp$ & sign, with $\sgnp(0)=1$ & $\sigma$ & logistic function\\
\midrule
\multicolumn{6}{@{}l}{\textit{Fixed baseline and actuator interface}}\\
$\bm\tau_0=\bm u_0$ & baseline torque \eqref{eq:pd} & $K_q,K_\omega$ & PD gains \eqref{eq:pd} & $\bm\tau_{\max}$ & per-axis torque bound\\
$\omega_n,\zeta$ & design frequency, damping & $\bm\ell$ & per-channel command bound & $\sat_{\bm\ell}$ & saturation at $\pm\bm\ell$\\
$B$ & allocation matrix \eqref{eq:allocationmatrix} & $\bm f$ & rotor forces \eqref{eq:mixer} & $T$ & collective thrust \eqref{eq:collective}\\
$\kappa_i$ & rotor reaction coefficient & $m$ & torque channels, $m=3$ & $M$ & vehicle mass\\
\midrule
\multicolumn{6}{@{}l}{\textit{Coupled membrane--gate unit}}\\
$v_j$ & membrane state \eqref{eq:cmg} & $r_j$ & gate state \eqref{eq:cmg} & $c_j$ & shunt conductance \eqref{eq:cmg}\\
$\bar{\bm u}$ & normalized baseline \eqref{eq:encoding} & $\bm I^{\pm},\bm I$ & paired currents \eqref{eq:encoding} & $I_b,I_g$ & current offset and gain\\
$\tau,\tau_r$ & membrane, gate time constants & $v_{\rm th}$ & gate threshold & $v_{\rm rest},v_{\rm reset}$ & rest level, reversal level\\
$\gamma$ & gate self-coupling & $\alpha_h$ & logistic sharpness & $\chi$ & conductance switch, $\chi\in\{0,1\}$\\
$g_0,g_1$ & conductance gains & $G$ & activity gain, $G=10^5$ & $h$ & integration step\\
$b_{j,k}$ & gate target \eqref{eq:gate_step} & $r^+_{j,k},v^+_{j,k}$ & updated states \eqref{eq:mem_step} & $\lambda_{j,k},d_{j,k}$ & frozen membrane coefficients\\
\midrule
\multicolumn{6}{@{}l}{\textit{Decoder, online learning, and residual authority}}\\
$\bm a_k$ & clipped activity \eqref{eq:readout} & $W_k$ & decoder \eqref{eq:readout} & $W_0=[I_m,-I_m]$ & initial decoder\\
$\bm s_k$ & clipped readout \eqref{eq:readout} & $\bm y^*_k$ & PES target \eqref{eq:pes} & $\bm\varepsilon_k$ & PES error \eqref{eq:pes}\\
$k_e,k^*_\omega$ & target gains \eqref{eq:pes} & $\eta$ & per-step learning rate & $\lambda_W$ & per-step decoder decay\\
$\Pi_{\mathcal W},W_{\max}$ & projection and weight bound & $\beta$ & residual authority \eqref{eq:residual} & $\bm u_k,\bm\delta_k$ & applied command, deviation \eqref{eq:residual}\\
\midrule
\multicolumn{6}{@{}l}{\textit{Annealed variant and reported metrics}}\\
$\bm z_k$ & activity trace \eqref{eq:aat} & $\rho(s)$ & trace factor \eqref{eq:aat} & $s=t/T$ & mission progress\\
$\eta_0$ & initial annealed rate & $\bar\theta_q$ & mean quaternion-angle error & $S$ & actuator-bound occupancy [\%]\\
\bottomrule
\end{tabular}
\end{table*}

"""
sub(
    r"""\section{Simulation Models, Attitude Baseline, and Actuator Interface}""",
    NOMEN + r"""\section{Simulation Models, Attitude Baseline, and Actuator Interface}""",
    "tab/nomenclature")

sub(
    r"""For $m$ torque channels and $2m$ units, normalize the clipped baseline and
form positive/negative current pairs:""",
    r"""Symbols are collected in Table~\ref{tab:nomen}.
For $m$ torque channels and $2m$ units, normalize the clipped baseline and
form positive/negative current pairs:""",
    "ref/tab:nomen")

# ---------------------------------------------------------------------------
# 6. CMG unit figure inside Sec. III
# ---------------------------------------------------------------------------
CMG_FIG = r"""% [v6] CMG unit coupling topology. Source: figures/arch/archB1c.tex
% (editable draw.io version: figures/arch/architectures.drawio, page B1).
\begin{figure}[t]
\centering
\resizebox{0.95\columnwidth}{!}{\input{figures/arch/archB1c.tex}}
\caption{Coupling topology of one CMG unit, cf.~\eqref{eq:cmg}. The
membrane sets the gate target; the gate acts back on the membrane twice,
shifting its own activation threshold through $\gamma$ and shunting the
membrane through $c_j\propto r_j^2$. With $\chi=1$ the shunt is
additionally input dependent. The dynamics are continuous: there is no
threshold-triggered spike and no discrete reset, and only $a_j$ leaves the
unit.}
\label{fig:cmgunit}
\end{figure}

"""
sub(
    r"""The logistic gate target depends on $v_j$, while $r_j$ shifts that target
and modulates membrane conductance.""",
    CMG_FIG + r"""The logistic gate target depends on $v_j$, while $r_j$ shifts that target
and modulates membrane conductance (Fig.~\ref{fig:cmgunit}).""",
    "fig/cmgunit")

# ---------------------------------------------------------------------------
# 7. cross-reference the four orphaned result figures
# ---------------------------------------------------------------------------
sub(
    r"""These cases demonstrate repeatable nominal
performance, not robustness to model mismatch or a universally optimal PD
comparison.""",
    r"""These cases demonstrate repeatable nominal
performance, not robustness to model mismatch or a universally optimal PD
comparison. Figures~\ref{fig:tracking} and \ref{fig:hard45_neurons} show
the X2 Hard45 case, the largest smooth-mission gain, together with the
neural activity that produced it; Figs.~\ref{fig:hardstep_attitude} and
\ref{fig:hardstep_neurons} show the Hardstep case, where the reduction is
smallest and the only nonzero bound occupancy occurs.""",
    "ref/x2-figs")

sub(
    r"""Figure~\ref{fig:states} distinguishes the membrane, raw gate, and clipped
activity using the same recorded trajectory rather than equating them.""",
    r"""Figure~\ref{fig:states} shows the CF2 Yaw360 case, the largest reduction
in Table~\ref{tab:mujoco}, and Fig.~\ref{fig:cf2_yaw360_neurons}
distinguishes the membrane, raw gate, and clipped activity using that same
recorded trajectory rather than equating them.""",
    "ref/cf2-figs")

# ---------------------------------------------------------------------------
# 8. cross-reference the annealed-variant table
# ---------------------------------------------------------------------------
sub(
    r"""On Hard45, AAT is slightly better than PES for CF2 and worse for X2.""",
    r"""On Hard45, AAT is slightly better than PES for CF2 and worse for X2
(Table~\ref{tab:aat}).""",
    "ref/tab:aat")

io.open(DST, "w", encoding="utf-8").write(s)
print(f"\nwrote {DST}  ({n} patches applied)")
