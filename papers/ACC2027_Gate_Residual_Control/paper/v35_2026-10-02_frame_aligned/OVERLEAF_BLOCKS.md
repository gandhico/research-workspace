# Overleaf blocks: Dr. Sandoval's review → your manuscript `ACC2027 (10).tex` (PDF 35)

## Instructions for the Overleaf agent

Apply the MAIN blocks (0, 2, 3a, 3b, 4, 5) to the main `.tex`, exactly as written. Each FIND string occurs
once in the current file. Do not change anything else. Text that changed in response to the review is wrapped
in `\textcolor{purple}{...}`, Steven's own convention, so the PDF shows him every change. If a FIND string
does not match character for character (line breaks or spaces), locate the passage by the description and
replace it with the REPLACE text.

Block 1 (allocation matrix B): **no edit**. Steven highlighted the thrust row `1 1 1 1`; it is already in your
file and matches the code (`B = [1; p_y; -p_x; kappa]` in `drone.py::_mixer`).

Checked locally: your file plus the main blocks compiles to **8 pages** with no undefined references, and
about four lines remain free on page 8.

**For the submission PDF**, keep the markup but print it black by adding this line just before
`\begin{document}`; delete it to show the purple again:

```latex
\definecolor{purple}{rgb}{0,0,0} % print review marks in black
```


---

## MAIN blocks

### Block 0: Preamble: load xcolor for the purple marks (as in Steven's file)

FIND
```latex
\usepackage{graphicx}
```

REPLACE
```latex
\usepackage{graphicx}
\usepackage{xcolor} % track changes (Sandoval review)
```


### Block 2: Eq. (15), PD+ff: Steven's frame-aligned rate error, plus the disclosure from the re-run

FIND
```latex
obtained by replacing $\bm\omega$ with the rate-tracking error
$\bm\omega-\bm\omega_d$:
\begin{equation}
 \bm u_0^{\rm ff}=\sat_{\bm\ell}\bigl(-\bm k_q\odot\bm e_q-\bm k_\omega\odot(\bm\omega-\bm\omega_d)\bigr),
 \label{eq:pdff}
\end{equation}
```

REPLACE
```latex
obtained by replacing $\bm\omega$ with the \textcolor{purple}{frame-aligned} rate-tracking error \textcolor{purple}{$\bm\omega_e$ of \eqref{eq:errkin}}
\begin{equation}
 \bm u_0^{\rm ff}=\sat_{\bm\ell}\bigl(-\bm k_q\odot\bm e_q-\bm k_\omega\odot\textcolor{purple}{\bm\omega_e}\bigr).
 \label{eq:pdff}
\end{equation}
\textcolor{purple}{The reported runs damp $\bm\omega-\bm\omega_d$, which differs from $\bm\omega_e$ by at most $\theta_q\|\bm\omega_d\|$; with $\bm\omega_e$ the primary result of Sec.~\ref{sec:baselines} becomes $37.4\%/22.5\%$, and the $\rho=1$ rows of Table~\ref{tab:all} and the LQR, PID+ff, SMC, and MPC results change by at most $0.5$\,pp.}
```


### Block 3a: Eq. (24) lead-in: state that the rate weight is zero in every run

FIND
```latex
weighting attitude and rate error, respectively:
\begin{align}
```

REPLACE
```latex
weighting attitude and rate error, respectively \textcolor{purple}{(all reported runs use $k_\omega^*=0$, so $\bm y_k^*$ depends on $\bm e_{q,k}$ only)}:
\begin{align}
```


### Block 3b: Eq. (24): Steven's frame-aligned rate error in the PES target

FIND
```latex
-k_\omega^*\bm\omega_k),\\
```

REPLACE
```latex
-k_\omega^*\textcolor{purple}{\bm\omega_{e,k}}),\\
```


### Block 4: After the gate, Eq. (28): Steven's anti-windup sentence, corrected to what the code does

FIND
```latex
and leaves the PES update \eqref{eq:pes} untouched. Since
```

REPLACE
```latex
and leaves the PES update \eqref{eq:pes} untouched. \textcolor{purple}{Because PES uses the ungated residual $\bm s_k$ rather than the physically applied $\tilde s_{k,i}$, the mask never enters $\bm\varepsilon_k$, an implicit anti-windup property: the gate cannot by itself wind up the decoder. PES still adapts on a blocked axis, which leaves the settling tail of Sec.~\ref{sec:failure}; freezing those rows instead gave the same X2 Hardstep result in development ($-2.1\%$ vs.\ $-2.0\%$).} Since
```


### Block 5: Sec. VI-C, Gate/activity regime: Steven's contraction condition, made exact (and 'Thus' removed)

FIND
```latex
the gate is bistable: for frozen $v_j$ its equilibria fold
```

REPLACE
```latex
the gate is bistable\textcolor{purple}{; a strictly graded, non-latching gate requires $\alpha_h\gamma\le4$ (since $\max\sigma'(x)=1/4$, $\alpha_h\gamma<4$ makes the frozen-$v_j$ gate map a contraction). Here,} for frozen $v_j$ its equilibria fold
```


---

## OPTIONAL blocks (your decision)

Block 6 is our flag. Blocks 7a–7e are edits Steven made **without** purple marks; they appear when his file is
diffed against yours. They are style only: citation placement, IEEE-style no colon before a display, and one
word. He also typeset B with `IEEEeqnarray` and joined the paragraph after the collective-thrust display; those
are layout-only and not listed. If you apply 7b–7d, drop the colon at the end of Block 3a as well for consistency.

### Block 6: Reproducibility footnote (our flag, not Steven's): the repository is private until acceptance

FIND
```latex
Code and run archives accompany the submission as a reproducibility package.
```

REPLACE
```latex
\textcolor{purple}{Code, configurations, and per-run summary results will be released upon acceptance.}
```


### Block 7a: Steven, unmarked: citation placement for the rotational dynamics

FIND
```latex
inertial coordinates, and let $\bm\omega$ be the body angular velocity. The
rotational dynamics are \cite{schaub2018amss}
```

REPLACE
```latex
inertial coordinates, and let $\bm\omega$ be the body angular velocity. Following \cite{schaub2018amss}, the
rotational dynamics are
```


### Block 7b: Steven, unmarked: no colon before the collective-thrust display

FIND
```latex
Collective thrust remains classical, with $z_d=1$ m:
```

REPLACE
```latex
Collective thrust remains classical, with $z_d=1$ m
```


### Block 7c: Steven, unmarked: no colon before the current-pair display

FIND
```latex
form positive/negative current pairs:
```

REPLACE
```latex
form positive/negative current pairs
```


### Block 7d: Steven, unmarked: no colon before the CMG display

FIND
```latex
membrane state $v_j$ and gate $r_j$:
```

REPLACE
```latex
membrane state $v_j$ and gate $r_j$
```


### Block 7e: Steven, unmarked: proof wording

FIND
```latex
the componentwise saturation in \eqref{eq:gate_step} therefore preserves
```

REPLACE
```latex
the componentwise saturation in \eqref{eq:gate_step} preserves
```


---

## How each of Steven's highlights was resolved (for your reply)

| # | His highlight | Resolution | Evidence |
|---|---|---|---|
| 1 | Thrust row of B | Correct as written; no edit | `drone.py::_mixer` builds `B = [1; p_y; -p_x; kappa]` |
| 2 | Eq. (15): frame-aligned ω_e | Adopted, since it is the correct form per (8). The reported runs used ω − ω_d, and the paper now says so with the re-run effect | Primary geometric-mean reduction 37.297 → 37.358% (X2), 22.421 → 22.495% (CF2); ρ = 1 rows 57.83 → 58.31%, 57.58 → 57.87%; LQR, PID+ff, SMC, MPC within 0.22 pp; Roll, Hardstep, Yaw360 unchanged |
| 3 | Eq. (24): ω_e in the PES target | Adopted for consistency; it has no effect because the rate weight is zero, which the text now states | k_ω* = 0 (Table I) in all 821 residual runs |
| 4 | Implicit anti-windup | His framing is kept, but the claim is narrowed. The gate is output-only, so PES keeps adapting while an axis is blocked (which causes the Hardstep tail); "stops updating" is therefore not what happens. What holds is that the mask never enters the learning error | Runner: "PES target/error/update are never masked"; freeze-PES screen (true anti-windup), X2 Hardstep, noise-free, seed 1: −2.1% vs −2.0% |
| 5 | Contraction condition α_hγ < 4 | Kept. Graded for every v_j holds iff α_hγ ≤ 4; < 4 is the contraction condition. "Thus" became "Here", since the folds do not follow from the condition | Folds ±0.888 recomputed by the claims verifier |

## Still being re-run (frame-aligned sandbox)

NMPC, noise, disturbance, the Izhikevich Table II runs, the reduced-CMG controls and the Fig. 4 ladder are still running.
The neuron-basis study has finished: CMG, the non-neural bases and LIFRate change by at most 0.1 pp, while the
Izhikevich geometric-mean increase on X2 moves from 18.9% to 19.7%. That Izhikevich value is not claimed in Block 2.
