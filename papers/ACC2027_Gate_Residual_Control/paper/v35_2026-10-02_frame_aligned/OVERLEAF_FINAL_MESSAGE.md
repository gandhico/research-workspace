Apply these 13 replacements to the main .tex file exactly as written. Each FIND text occurs once. Change
nothing else: no rewording, no reformatting, and no other edits to equations, tables or numbers. If a FIND
differs only in spaces or line breaks, match it by content. Afterwards, recompile and confirm the PDF is
still 8 pages.

### 1. Preamble: load xcolor and print the review marks in black for submission
FIND:
```latex
\usepackage{graphicx}
```

REPLACE WITH:
```latex
\usepackage{graphicx}
\usepackage{xcolor} % track changes (Sandoval review)
\definecolor{purple}{rgb}{0,0,0} % submission: review marks print black; delete this line to show them
```

### 2. Sec. II-C, Eq. (15): frame-aligned rate error, plus a disclosure of what the reported runs used
FIND:
```latex
obtained by replacing $\bm\omega$ with the rate-tracking error
$\bm\omega-\bm\omega_d$:
\begin{equation}
 \bm u_0^{\rm ff}=\sat_{\bm\ell}\bigl(-\bm k_q\odot\bm e_q-\bm k_\omega\odot(\bm\omega-\bm\omega_d)\bigr),
 \label{eq:pdff}
\end{equation}
```

REPLACE WITH:
```latex
obtained by replacing $\bm\omega$ with the \textcolor{purple}{frame-aligned} rate-tracking error \textcolor{purple}{$\bm\omega_e$ of \eqref{eq:errkin}}
\begin{equation}
 \bm u_0^{\rm ff}=\sat_{\bm\ell}\bigl(-\bm k_q\odot\bm e_q-\bm k_\omega\odot\textcolor{purple}{\bm\omega_e}\bigr).
 \label{eq:pdff}
\end{equation}
\textcolor{purple}{The reported runs damp $\bm\omega-\bm\omega_d$, which differs from $\bm\omega_e$ by at most $\theta_q\|\bm\omega_d\|$; with $\bm\omega_e$ the primary result of Sec.~\ref{sec:baselines} becomes $37.4\%/22.5\%$, and the $\rho=1$ rows of Table~\ref{tab:all} and the LQR, PID+ff, SMC, and MPC results change by at most $0.5$\,pp.}
```

### 3. Sec. III-B, before Eq. (24): the rate weight is zero in every run (Steven's colon removal included)
FIND:
```latex
weighting attitude and rate error, respectively:
\begin{align}
```

REPLACE WITH:
```latex
weighting attitude and rate error, respectively \textcolor{purple}{(all reported runs use $k_\omega^*=0$, so $\bm y_k^*$ depends on $\bm e_{q,k}$ only)}
\begin{align}
```

### 4. Eq. (24): frame-aligned rate error in the PES target
FIND:
```latex
-k_\omega^*\bm\omega_k),\\
```

REPLACE WITH:
```latex
-k_\omega^*\textcolor{purple}{\bm\omega_{e,k}}),\\
```

### 5. Sec. III-B, after Eq. (28): anti-windup sentence
FIND:
```latex
and leaves the PES update \eqref{eq:pes} untouched. Since
```

REPLACE WITH:
```latex
and leaves the PES update \eqref{eq:pes} untouched. \textcolor{purple}{Because PES uses the ungated residual $\bm s_k$ rather than the physically applied $\tilde s_{k,i}$, the mask never enters $\bm\varepsilon_k$, an implicit anti-windup property: the gate cannot by itself wind up the decoder. PES still adapts on a blocked axis, which leaves the settling tail of Sec.~\ref{sec:failure}; freezing those rows instead gave the same X2 Hardstep result in development ($-2.1\%$ vs.\ $-2.0\%$).} Since
```

### 6. Sec. VI-C, Gate/activity regime: contraction condition
FIND:
```latex
the gate is bistable: for frozen $v_j$ its equilibria fold
```

REPLACE WITH:
```latex
the gate is bistable\textcolor{purple}{; a strictly graded, non-latching gate requires $\alpha_h\gamma\le4$ (since $\max\sigma'(x)=1/4$, $\alpha_h\gamma<4$ makes the frozen-$v_j$ gate map a contraction). Here,} for frozen $v_j$ its equilibria fold
```

### 6b. Sec. III-B, Eq. (23) (Steven): split into (23a)-(23c) in the paper's notation; no text refers to Eq. (23)
FIND:
```latex
\begin{equation}
 \begin{aligned}
 \bm a_k&=\sat_{[0,1]}(G\bm r_k^+),\qquad W_0=[I_m,-I_m],\\
 \bm s_k&=\sat_{[-1,1]}(W_k\bm a_k).
 \end{aligned}
 \label{eq:readout}
\end{equation}
```

REPLACE WITH:
```latex
\begin{subequations}\label{eq:readout}
\begin{align}
 \bm a_k&=\sat_{[0,1]}(G\bm r_k^+),\label{eq:activity}\\
 W_0&=[I_m,-I_m],\label{eq:decoder_init}\\
 \bm s_k&=\sat_{[-1,1]}(W_k\bm a_k).\label{eq:decoder_output}
\end{align}
\end{subequations}
```

### 7. Sec. VI-A, reproducibility sentence: the repository is private until acceptance
FIND:
```latex
Code and run archives accompany the submission as a reproducibility package.
```

REPLACE WITH:
```latex
\textcolor{purple}{Code, configurations, and per-run summary results will be released upon acceptance.}
```

### 8. Sec. II-A: citation placement (Steven)
FIND:
```latex
inertial coordinates, and let $\bm\omega$ be the body angular velocity. The
rotational dynamics are \cite{schaub2018amss}
```

REPLACE WITH:
```latex
inertial coordinates, and let $\bm\omega$ be the body angular velocity. Following \cite{schaub2018amss}, the
rotational dynamics are
```

### 9. Sec. II-B: no colon before the collective-thrust display (Steven)
FIND:
```latex
Collective thrust remains classical, with $z_d=1$ m:
```

REPLACE WITH:
```latex
Collective thrust remains classical, with $z_d=1$ m
```

### 10. Sec. III-A: no colon before the current-pair display (Steven)
FIND:
```latex
form positive/negative current pairs:
```

REPLACE WITH:
```latex
form positive/negative current pairs
```

### 11. Sec. III-A: no colon before the CMG display (Steven)
FIND:
```latex
membrane state $v_j$ and gate $r_j$:
```

REPLACE WITH:
```latex
membrane state $v_j$ and gate $r_j$
```

### 12. Sec. V, proof: wording (Steven)
FIND:
```latex
the componentwise saturation in \eqref{eq:gate_step} therefore preserves
```

REPLACE WITH:
```latex
the componentwise saturation in \eqref{eq:gate_step} preserves
```
