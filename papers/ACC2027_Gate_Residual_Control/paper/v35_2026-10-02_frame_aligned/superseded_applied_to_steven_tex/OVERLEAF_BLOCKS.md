# Overleaf blocks: resolving Dr. Sandoval's highlighted edits (v34 → v35, 2026-10-02)

## Instructions for the Overleaf agent

Apply the five replacements below to the main `.tex` file, exactly as written. Each FIND string occurs once in the v34 source.
Do not change anything else. Together they remove every `\textcolor{purple}{...}` highlight; after applying them, the
source should contain no `textcolor{purple}`.

Local check: v34 with these blocks compiles to **8 pages**, with no undefined references, and the page-8 fill is
unchanged from v34.

---

### Block 1: allocation matrix, Eq. (10). Remove the highlight; the content stays the same.

FIND
```latex
\textcolor{purple}{1} & \textcolor{purple}{1} & \textcolor{purple}{1} & \textcolor{purple}{1} \\
```
REPLACE
```latex
1 & 1 & 1 & 1 \\
```

### Block 2: PD+ff, Eq. (15). Keep the frame-aligned law and state what the reported runs implement.

FIND
```latex
obtained by replacing $\bm\omega$ with the \textcolor{purple}{frame-aligned} rate-tracking error
\textcolor{purple}{$\bm\omega_e$}
\begin{equation}
 \bm u_0^{\rm ff}=\sat_{\bm\ell}\bigl(-\bm k_q\odot\bm e_q-\bm k_\omega\odot\textcolor{purple}{\bm\omega_e}\bigr),
 \label{eq:pdff}
\end{equation}
```
REPLACE
```latex
obtained by replacing $\bm\omega$ with the frame-aligned rate-tracking error $\bm\omega_e$ of \eqref{eq:errkin}
\begin{equation}
 \bm u_0^{\rm ff}=\sat_{\bm\ell}\bigl(-\bm k_q\odot\bm e_q-\bm k_\omega\odot\bm\omega_e\bigr).
 \label{eq:pdff}
\end{equation}
The reported runs damp $\bm\omega-\bm\omega_d$, which differs from $\bm\omega_e$ by at most $\theta_q\|\bm\omega_d\|$; with $\bm\omega_e$ the primary result of Sec.~\ref{sec:baselines} becomes $37.4\%/22.5\%$ and the LQR, PID+ff, SMC, and MPC results change by at most $0.22$\,pp.
```

### Block 3: PES target, Eq. (24). Two edits in the same paragraph.

3a FIND
```latex
weighting attitude and rate error, respectively
\begin{align}
```
3a REPLACE
```latex
weighting attitude and rate error, respectively (all reported runs use $k_\omega^*=0$, so $\bm y_k^*$ depends on $\bm e_{q,k}$ only)
\begin{align}
```

3b FIND
```latex
-k_\omega^*\textcolor{purple}{\bm\omega_{e,k}}),\\
```
3b REPLACE
```latex
-k_\omega^*\bm\omega_{e,k}),\\
```

### Block 4: anti-windup sentence after the gate, Eq. (28)

FIND
```latex
\textcolor{purple}{Because PES uses the ungated residual $\bm s_k$ rather than the physically applied $\tilde s_{k,i}$, this provides an implicit anti-windup mechanism: the network satisfies its local learning objective and stops updating even if the physical plant remains saturated.}
```
REPLACE
```latex
Because PES uses the ungated $\bm s_k$, the mask never enters $\bm\varepsilon_k$ and cannot by itself wind up the decoder; PES still adapts on a blocked axis (Sec.~\ref{sec:failure}), and freezing those rows gave the same X2 Hardstep result in development ($-2.1\%$ vs.\ $-2.0\%$).
```

### Block 5: gate bistability and contraction condition (Sec. VI-C, "Gate/activity regime")

FIND
```latex
Since $\alpha_h\gamma=100>4$, the gate is bistable\textcolor{purple}{; a strictly graded, non-latching state mathematically requires the contraction condition $\alpha_h\gamma<4$ (since $\max \sigma'(x)=1/4$). Thus,} for frozen $v_j$ its equilibria fold at $v_j\approx0.888$ (onset) and $v_j\approx-0.888$ (release).
```
REPLACE
```latex
Since $\max\sigma'=1/4$, the frozen-$v_j$ gate equilibrium $r_j=\sigma(\alpha_h(v_j-v_{\rm th}+\gamma r_j))$ is unique (graded, non-latching) for every $v_j$ iff $\alpha_h\gamma\le4$; here $\alpha_h\gamma=100$, so the gate is bistable, with folds at $v_j\approx0.888$ (onset) and $-0.888$ (release).
```

---

## Optional block 6: reproducibility footnote (not one of Dr. Sandoval's highlights; your decision)

The repository is **private until acceptance**, so reviewers following the link get a 404. Raw traces are also not
distributed. The current sentence ("Code and run archives accompany the submission...") therefore overstates what a
reviewer can access.

FIND
```latex
Code and run archives accompany the submission as a reproducibility package.\footnote{\url{https://github.com/gandhico/online-pes-neuromorphic-residual-control}}
```
REPLACE
```latex
Code, configurations, and per-run summary results will be released upon acceptance.\footnote{\url{https://github.com/gandhico/online-pes-neuromorphic-residual-control}}
```

---

## Why each change (for the reply to Dr. Sandoval)

| # | His highlight | Resolution | Evidence |
|---|---|---|---|
| 1 | Thrust row of B | Correct as written; highlight removed | `src/gra_control/platforms/drone.py::_mixer`: `B = [1; p_y; -p_x; kappa]` |
| 2 | Eq. (15) frame-aligned ω_e | Kept: it is the correct form per (8). The runs used ω − ω_d; the frame-aligned re-run shows a negligible effect, and the paper now says so | Primary geometric-mean reduction 37.297 → 37.358% (X2), 22.421 → 22.495% (CF2); largest per-mission change 0.56 pp (X2 Hard45); Roll, Hardstep and Yaw360 unchanged; LQR −0.19/+0.07, PID+ff +0.01/+0.08, SMC +0.22/+0.20, MPC −0.13/+0.07 pp |
| 3 | Eq. (24) ω_e in the PES target | Kept for consistency with (15); the rate term has zero weight in every run, so no result depends on it | k_ω* = 0 (Table I) in all 821 residual runs |
| 4 | "implicit anti-windup ... stops updating" | Narrowed: the gate is output-only, so PES keeps adapting while an axis is blocked, which causes the Hardstep settling tail. What does hold is that the mask never enters the learning error, so the gate itself does not wind up W | Runner: "PES target/error/update are never masked"; freeze-PES screen, X2 Hardstep, noise-free, seed 1: −2.1% vs −2.0% for the gate |
| 5 | Contraction condition α_hγ < 4 | Kept and made exact: a unique equilibrium for every v_j holds iff α_hγ ≤ 4 (r = σ(c + b r) has three fixed points for some c iff b > 4). "Thus" removed, since the folds do not follow from the condition | Folds ±0.888 recomputed in the verifier (claim "gate folds v_on/v_off") |

## Still running (frame-aligned sandbox `frame_aligned_2026-10-02/`)

The NMPC, noise and disturbance runs, Izhikevich, the neuron-basis study, the ρ = 1 ladder (Table II, 57.8/57.6), the
reduced-CMG controls (46.3/28.6) and the Fig. 4 ladder are still being re-run. When they finish, the comparison script
will produce `FRAME_ALIGNED_COMPARISON.md` covering all 75 verifier rows. If every row stays as small as the rows above,
the final version can switch all numbers to the frame-aligned run, and the sentence in Block 2 then becomes a
one-line implementation note.
