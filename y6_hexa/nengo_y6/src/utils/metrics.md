# `metrics.py` — Step-Response & Control-Effort Benchmark Metrics

> **Companion notes.** Mathematical mirror of `metrics.py` (in `src/utils`). This
> is the **benchmark layer**: it turns raw simulation traces into the standard
> control-performance numbers, and it is what makes the classical-vs-Nengo
> comparison fair. Part of the **Coaxial Tri-Rotor Project** study log.

**Layer:** `src/utils` (analysis, not a plant) · **Shared by:** every experiment

---

## 0. What this module is, and why it is trace-based

The very first plant (`altitude_1dof.md` §0) promised a **single source of truth**
so that "the benchmark compares controllers on a byte-for-byte identical plant."
This module is the other half of that promise: a fixed set of metrics computed
the *same way* for every controller.

The governing design choice, stated in the docstring, is that **all metrics come
from the actual simulation traces** $(t, y, u)$ — no analytic shortcuts. This is
essential, not stylistic: a classical PID has a clean closed-form step response,
but a **Nengo spiking-network controller has no transfer function** to read
rise-time or overshoot off. Measuring everything from the trace is the *only* way
to score both controllers on one ruler. The metric set (the project's standing
benchmark requirement):

> rise time (10–90%), settling time (±2%), overshoot %, steady-state error,
> IAE, ISE, control energy, control effort beyond hover, saturation %, tracking
> RMSE, plus a one-line stability note.

Throughout, the tracking **error** is

$$
e(t) = \text{target} - y(t), \qquad \text{amp} = \text{target} - y_0, \tag{0}
$$

with $y_0$ the output at the start of the analysis window $t \ge t_{\text{step}}$.

---

## 1. Time-domain helpers — `_rise_time`, `_settling_time`

### 1.1 Rise time (10–90%)

```python
lo, hi = y0 + 0.1*amp, y0 + 0.9*amp
i_lo = np.argmax(y >= lo)      # first index crossing 10%
i_hi = np.argmax(y >= hi)      # first index crossing 90%
return t[i_hi] - t[i_lo]
```

The time the output takes to climb from 10% to 90% of the step amplitude:

$$
t_r = t_{90\%} - t_{10\%},
\qquad
t_{p\%} = \min\{\,t : y(t) \ge y_0 + p\cdot\text{amp}\,\}. \tag{1}
$$

**Idiom.** `np.argmax(y >= lo)` exploits that `argmax` returns the **first**
maximal index; on a boolean array the first `True` (value 1) is the first
crossing. The guards `np.any(...)` handle "never reached" (since `argmax` would
otherwise return 0), returning `NaN`. `NaN` is also returned if `amp == 0` (no
step to rise through).

### 1.2 Settling time (±2% band)

```python
tol = abs(band * amp)
outside = np.abs(y - target) > tol
last = np.where(outside)[0][-1]      # last excursion outside the band
return t[last+1] - t[0]
```

The time after which the response **stays** inside a tolerance band
$\pm\,\text{band}\cdot|\text{amp}|$ around the target:

$$
t_s = t_{k^\star + 1} - t_0,
\qquad
k^\star = \max\{\,k : |y_k - \text{target}| > \text{band}\cdot|\text{amp}|\,\}. \tag{2}
$$

It finds the **last** sample outside the band and reports the time of the next
one. Returns $0$ if never outside (already settled), and `NaN` if still outside
at the window's end (**never settled** — the signal `stability_note` keys on).
The default band is $0.02$ (±2%).

---

## 2. Step metrics — `step_metrics`

The remaining step-response numbers, over the window $t \ge t_{\text{step}}$.

### 2.1 Overshoot

$$
M_p = \max\!\left(0,\ \frac{\max_t y(t) - \text{target}}{|\text{amp}|}\times 100\%\right). \tag{3}
$$

Peak excursion above target as a percentage of step amplitude, clamped at $0$ so
a response that never exceeds target reports no overshoot. (For a textbook
second-order system this equals $100\,e^{-\pi\zeta/\sqrt{1-\zeta^2}}$, but here it
is **measured**, not assumed — see §0.)

### 2.2 Steady-state error

$$
e_{\text{ss}} = \text{target} - \overline{y}\big|_{\text{last }\Delta_{\text{ss}}\text{ seconds}}, \tag{4}
$$

the offset between target and the mean output over the final `ss_window` seconds
(default $1$ s). Averaging suppresses noise/ripple so the residual offset is
read cleanly.

### 2.3 Error integrals — IAE and ISE

$$
\text{IAE} = \int_{t_{\text{step}}}^{T} |e(t)|\,\mathrm{d}t,
\qquad
\text{ISE} = \int_{t_{\text{step}}}^{T} e(t)^2\,\mathrm{d}t. \tag{5,6}
$$

Two classic performance indices with different emphasis: **ISE** squares the
error, so it punishes large transient deviations heavily but tolerates small
lingering ones; **IAE** weights all error linearly, so it punishes slow,
persistent tails. A controller can win on one and lose on the other — reporting
both characterises the trade-off.

### 2.4 Control metrics — energy, effort, saturation

$$
\underbrace{E = \int u^2\,\mathrm{d}t}_{\text{control energy}},
\qquad
\underbrace{E_{\Delta} = \int (u - u_{\text{hover}})^2\,\mathrm{d}t}_{\text{effort beyond hover}}. \tag{7,8}
$$

**Control energy** (7) is the squared $L^2$ norm of the command — a proxy for
total actuator use. **Effort beyond hover** (8) subtracts the hover feed-forward
$u_{\text{hover}} = mg$ first (recall `altitude_1dof.md` Result 1.1 / eq. 2): since
that term merely holds gravity, $E_\Delta$ isolates the work the **feedback**
actually does. Two controllers may use similar total energy but very different
*active* effort.

**Saturation** is the fraction of time the command is pinned at an actuator limit
(recall `clip_thrust`, Result 1.2):

$$
\text{sat}\% = \frac{100}{N}\sum_{k=1}^{N}
\mathbb{1}\!\big[\,u_k \le u_{\min}+\epsilon \ \text{ or }\ u_k \ge u_{\max}-\epsilon\,\big]. \tag{9}
$$

High saturation means the controller is running out of authority — a red flag
even if the output looks acceptable.

### 2.5 Tracking RMSE

$$
\text{RMSE} = \sqrt{\frac{1}{N}\sum_{k=1}^{N} e_k^2} = \sqrt{\operatorname{mean}(e^2)}. \tag{10}
$$

Note the relation to ISE: for a window of length $T_w$, $\text{ISE} \approx \text{RMSE}^2\,T_w$
— RMSE is the time-normalised, same-units-as-output version of ISE, which is why
both appear (one comparable across runs of equal length, one in physical units).

---

## 3. The numerical integrator behind the integrals — `np.trapezoid`

IAE, ISE, and the control integrals (5)–(8) are evaluated by the **trapezoidal
rule** on the sampled trace: for samples $f_k$ at times $t_k$,

$$
\int_{t_0}^{t_N} f\,\mathrm{d}t \approx \sum_{k=0}^{N-1} \frac{f_k + f_{k+1}}{2}\,(t_{k+1}-t_k). \tag{11}
$$

This is the running "integrator" of the analysis layer, mirroring the RK4
integrator of the plant layer — but a different tool for a different job. The
plant is advanced with **RK4** ($\mathcal{O}(h^4)$ global) because it sits *inside*
the feedback loop, where error compounds. The metrics use the **trapezoidal rule**
($\mathcal{O}(\Delta t^2)$ global) because it is a *post-hoc* summary of a dense,
already-computed trace, where second-order accuracy is plenty. (`np.trapezoid` is
the NumPy ≥ 2.0 name for the former `np.trapz`.)

---

## 4. Generic version — `step_metrics_general`

Same metrics, but for **any subsystem with no gravity/hover** (the Phase-3
attitude and cascade plants). The differences:

- **`u_ref`** replaces $u_{\text{hover}}$ in the effort integral (8): the
  equilibrium command. For a **torque** input it is $0$ — recall the attitude
  axis $\ddot\alpha = \tau$ has *no* gravity bias (`subsystems.md` §1), so its
  resting command is zero, unlike the altitude plant's $mg$.
- **Saturation** (9) is reported only if both `u_min` and `u_max` are supplied
  (some channels have no modelled actuator clamp).
- **`settle_abs`** optionally replaces the *relative* band of (2) with an
  **absolute** tolerance. This matters when the target is near zero (e.g.
  regulating an angle back to $0$): then $\text{amp} \approx 0$ and a relative
  band $\text{band}\cdot|\text{amp}|$ collapses to a meaningless near-zero
  threshold, so an absolute band is the correct choice.

Return keys drop the unit suffixes (`sse`, `tracking_rmse` → `rmse`) so the same
code serves metres, radians, or whatever the channel's output is.

---

## 5. Trajectory tracking — `tracking_metrics`

For **continuous references** (sinusoids, ramps) rather than steps — exactly the
$z$-ramp and $x,y$-sinusoid references from `quadrotor.md` §4. Step-only concepts
(rise/settling/overshoot) are dropped; what remains is

$$
\text{RMSE},\quad \text{IAE},\quad \text{ISE},\quad
\max_t|e(t)|,\quad |e(T)|, \tag{12}
$$

i.e. the same error integrals (5)–(6), (10) plus the **worst-case** and **final**
absolute errors — the natural figures of merit for following a moving set-point.
Control energy (7) is included if the command trace is provided. Here the error
is $e = \text{ref}(t) - y(t)$ with $\text{ref}$ time-varying, evaluated over
$t \ge t_0$.

---

## 6. Stability verdict — `stability_note`

```python
if np.isnan(metrics["settling_time_s"]):
    return "UNSTABLE/UNSETTLED: did not enter the settling band within the window"
if abs(sse) < tol:
    return "stable; settled within tolerance"
return "stable but residual steady-state offset"
```

A one-line qualitative classification built from two already-computed numbers:

$$
\text{verdict} =
\begin{cases}
\text{unstable/unsettled}, & t_s = \text{NaN} \ (\text{eq. 2 never settled}), \\
\text{stable, in tolerance}, & |e_{\text{ss}}| < \text{tol}, \\
\text{stable, residual offset}, & \text{otherwise}.
\end{cases} \tag{13}
$$

It reads `sse_m` or `sse` so it works for both the altitude and the generic
return dicts. Note this is a *practical* verdict over a finite window, not a
formal (Lyapunov/eigenvalue) stability proof — "did the trace settle?", not "is
the closed loop provably stable?".

---

## 7. Summary

`metrics.py` is the benchmark ruler that scores every controller identically and
**from traces only**, so classical and Nengo controllers are directly comparable:

- **Transient** (eqs. 1–3): rise time, settling time, overshoot.
- **Accuracy** (eqs. 4–6, 10): steady-state error, IAE, ISE, RMSE.
- **Cost** (eqs. 7–9): control energy, effort beyond the equilibrium hold,
  saturation %.
- **Integration** (eq. 11): trapezoidal rule — the analysis-layer counterpart of
  the plant's RK4.
- **Three entry points**: `step_metrics` (altitude, hover-aware),
  `step_metrics_general` (any subsystem, `u_ref`/`settle_abs`), `tracking_metrics`
  (sinusoid/ramp), plus a one-line `stability_note`.

It ties back to the project's founding requirement: identical plant (Phase 2) +
identical metrics (here) = a controller comparison with no confounds.

**Threads to watch in later modules**

- The **classical** controller whose traces feed these metrics first (the
  baseline numbers).
- The **Nengo** controller scored on the *same* functions — the headline
  comparison.
- Which indices the project privileges when ranking controllers (likely IAE/ISE
  for accuracy and effort-beyond-hover for cost).
- How fault-tolerance runs (`alpha_fn`, `coaxial_trirotor.md` §7) are scored —
  presumably via `tracking_metrics` plus a settling check after the fault.

---

## References

This module implements standard control-systems performance indices (rise/settling
time, overshoot, IAE/ISE, steady-state error) as found in any classical control
text (e.g. Ogata, *Modern Control Engineering*; Franklin, Powell & Emami-Naeini,
*Feedback Control of Dynamic Systems*). The trace-based, controller-agnostic
framing is the project's own requirement, set so that spiking-network controllers
without a transfer function can be benchmarked alongside classical ones.
