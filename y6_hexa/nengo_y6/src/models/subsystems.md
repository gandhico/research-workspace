# `subsystems.py` — Phase-3 Quadrotor Subsystem Plants

> **Companion notes.** Mathematical mirror of `subsystems.py`. Two reusable
> *decoupled* plants from Victor's quad model: a single rotational axis and a
> position→attitude cascade. Part of the **Coaxial Tri-Rotor Project** study log.

**Phase:** 3 · **Convention:** $z$-up · **Matches:** `Quad_control_2026.py`[^quadctrl]

---

## 0. What this module is

Phase 2 (`altitude_1dof.py`) gave the vertical channel. Phase 3 supplies the
**rotational and horizontal channels** as two reusable plants, under Victor's
**decoupled model**: the full 6-DOF quadrotor is split into independent
single-axis channels, each valid near hover, each getting its own controller.[^victor]

| Plant | Channels it serves | State | Input |
|:------|:-------------------|:------|:-----:|
| `AttitudeAxis` | roll $\phi$, pitch $\theta$, yaw $\psi$ | $[\text{angle},\ \text{rate}]$ | $\tau$ |
| `CascadeAxis` | $x$ via pitch, $y$ via roll | $[\text{pos},\ \text{vel},\ \text{angle},\ \text{rate}]$ | $\tau$ |

The full decoupled architecture across phases:

$$
\underbrace{z}_{\text{Phase 2}}
\;\;\big|\;\;
\underbrace{\phi,\ \theta,\ \psi}_{\text{Phase 3: AttitudeAxis} \times 3}
\;\;\big|\;\;
\underbrace{x,\ y}_{\text{Phase 3: CascadeAxis} \times 2}
$$

### Module globals

```python
G = 9.81
TILT_MAX = np.radians(35.0)        # = 0.6109 rad
```

$g = 9.81\ \text{m s}^{-2}$; the tilt limit $\theta_{\max} = 35^\circ = 0.6109\ \text{rad}$
caps how far the cascade may lean (see §2.4).

---

## 1. Single rotational axis — `attitude_deriv`

```python
def attitude_deriv(state, tau):
    angle, rate = state
    return np.array([rate, tau])
```

### Derivation

For one principal body axis (decoupled, no gyroscopic cross-terms), Euler's
rotational equation is

$$
I\,\ddot{\alpha} = \tau_{\text{phys}},
$$

with $I$ the axis inertia and $\tau_{\text{phys}}$ the physical torque $[\text{N·m}]$.
Define the **inertia-normalised** input $\tau \coloneqq \tau_{\text{phys}} / I$
(the inertia is "folded into the gains," exactly as in
`Quad_control_2026.py`[^quadctrl]). Then

$$
\boxed{\;\ddot{\alpha} = \tau\;} \tag{1}
$$

where $\alpha \in \{\phi, \theta, \psi\}$ is whichever angle this instance
represents. **Note on units:** because inertia is absorbed, $\tau$ here carries
units of angular *acceleration* $[\text{rad s}^{-2}]$, i.e. it is a commanded
angular acceleration, not a raw torque.

**Contrast with altitude (Phase 2).** The altitude plant was
$\ddot z = u/m - g$ — a double integrator *with a constant gravity bias*. The
attitude axis is $\ddot\alpha = \tau$ — a double integrator *with no bias*,
because gravity acts at the centre of mass and produces **no torque** about it
(thrust and CM aligned). Same skeleton, one fewer term.

### State-space form

With $\mathbf{s} = [\alpha,\ \dot\alpha]^\top$:

$$
\dot{\mathbf{s}}
= \begin{bmatrix} \dot\alpha \\ \ddot\alpha \end{bmatrix}
= \begin{bmatrix} \text{rate} \\ \tau \end{bmatrix}
\quad\Longleftrightarrow\quad
\texttt{np.array([rate, tau])},
$$

$$
\dot{\mathbf{s}}
= \underbrace{\begin{bmatrix} 0 & 1 \\ 0 & 0 \end{bmatrix}}_{A}\mathbf{s}
+ \underbrace{\begin{bmatrix} 0 \\ 1 \end{bmatrix}}_{B}\tau. \tag{2}
$$

Same nilpotent $A$ as Phase 2; the input gain is now $1$ (not $1/m$) because
$\tau$ is already normalised. Both eigenvalues at the origin — a free axis
drifts, so feedback is required to hold an angle.

---

## 2. The cascade — `cascade_deriv` (position via tilt)

```python
def cascade_deriv(state, tau, s, g=G):
    pos, vel, ang, rate = state
    a = np.clip(ang, -TILT_MAX, TILT_MAX)
    return np.array([vel, s * g * np.tan(a), rate, tau])
```

### 2.1 The underactuation problem

A quadrotor **cannot push itself sideways directly** — there is no horizontal
thruster. The only way to accelerate horizontally is to **tilt** so a component
of the (vertical) thrust points sideways. Horizontal position is thus driven by
attitude: an *outer* position loop riding on top of the *inner* attitude loop of
§1. Four states are governed by one input — the channel is **underactuated**.

### 2.2 Deriving $\ddot x = g\tan\theta$

Take the thrust magnitude $T$ with the vehicle pitched by $\theta$, and assume
the **altitude loop holds $z$** (so the vertical thrust component continuously
balances weight — this is exactly what justifies treating the channels as
decoupled):

$$
\text{vertical balance:}\quad T\cos\theta = mg
\;\Longrightarrow\; T = \frac{mg}{\cos\theta}.
$$

The horizontal component of that same thrust then accelerates the vehicle:

$$
m\,\ddot x = T\sin\theta = \frac{mg}{\cos\theta}\sin\theta = mg\tan\theta
\;\Longrightarrow\;
\boxed{\;\ddot x = g\tan\theta\;} \tag{3}
$$

The $\tan$ is the **exact** coupling (Victor's $x$-control, p. 28[^victor]) — not
a small-angle approximation.

### 2.3 One sign parameter for both channels

```
x via pitch:   x_ddot = +g·tan(theta)     s = +1
y via roll:    y_ddot = -g·tan(phi)       s = -1
```

Both horizontal channels share structure (3); they differ only by a sign:

$$
\ddot{(\text{pos})} = s\,g\,\tan(\text{angle}),
\qquad s = +1\ (x/\text{pitch}),\quad s = -1\ (y/\text{roll}). \tag{4}
$$

The sign $s$ encodes the orientation relationship between a positive rotation
about a body axis and the direction of the resulting horizontal thrust
component, in the project's $z$-up frame: a positive pitch drives $+x$, whereas a
positive roll drives $-y$. A single parameter $s = \pm 1$ therefore lets one
function serve both channels.

### 2.4 The tilt clip

```python
a = np.clip(ang, -TILT_MAX, TILT_MAX)
```

The angle fed to $\tan$ is clipped to $\pm\theta_{\max} = \pm 35^\circ$. This is
both a safety and a modelling limit:

- as $\theta \to 90^\circ$, $\tan\theta \to \infty$ and the required thrust
  $T = mg/\cos\theta \to \infty$ — the altitude-hold assumption of §2.2 breaks;
- clipping keeps the vehicle in the regime where the decoupled model is valid.

The clip caps the horizontal acceleration at

$$
a_{\text{horiz,max}} = g\tan\theta_{\max} = 9.81 \times \tan 35^\circ
= 9.81 \times 0.700 = 6.87\ \text{m s}^{-2} \approx 0.70\,g. \tag{5}
$$

### 2.5 State-space form (now nonlinear)

With $\mathbf{s} = [\text{pos},\ \text{vel},\ \text{ang},\ \text{rate}]^\top$ and
$a = \operatorname{clip}(\text{ang}, \pm\theta_{\max})$:

$$
\dot{\mathbf{s}}
= \begin{bmatrix} \text{vel} \\ s\,g\,\tan(a) \\ \text{rate} \\ \tau \end{bmatrix}. \tag{6}
$$

This is a **cascade**: the inner pair $(\text{ang}, \text{rate})$ is the linear
double integrator of §1, $\ddot a = \tau$; the outer pair $(\text{pos}, \text{vel})$
is driven by the inner angle through the *nonlinear* term $s\,g\,\tan(a)$. Because
of $\tan$, the system is **not** affine in the state — this is the first
genuinely nonlinear plant in the project (see §3).

**Small-angle view (control intuition).** For $|a|$ small, $\tan a \approx a$, so

$$
\ddot{(\text{pos})} \approx s\,g\,(\text{ang}),
\qquad \ddot{(\text{ang})} = \tau
\;\Longrightarrow\;
\frac{\mathrm{d}^4(\text{pos})}{\mathrm{d}t^4} \approx s\,g\,\tau. \tag{7}
$$

Horizontal position sits **four integrators** away from the torque input — which
is precisely why horizontal control demands a carefully tuned cascade rather than
a single feedback term.

---

## 3. The integrators — `attitude_rk4` and `cascade_rk4`

```python
def attitude_rk4(state, tau, dt):
    k1 = attitude_deriv(state, tau)
    k2 = attitude_deriv(state + 0.5 * dt * k1, tau)
    k3 = attitude_deriv(state + 0.5 * dt * k2, tau)
    k4 = attitude_deriv(state + dt * k3, tau)
    return state + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
```

Both functions are the **same classical RK4 + zero-order-hold** scheme developed
in `altitude_1dof.md` §5 (with $\tau$, $s$, $g$ held constant across the step):

$$
\mathbf{s}_{n+1} = \mathbf{s}_n + \frac{h}{6}\big(\mathbf{k}_1 + 2\mathbf{k}_2 + 2\mathbf{k}_3 + \mathbf{k}_4\big),
\qquad h = \texttt{dt}. \tag{8}
$$

But the two plants behave very differently under it.

### 3.1 Attitude: RK4 is still *exact*

The attitude axis (2) is affine, $\dot{\mathbf{s}} = A\mathbf{s} + \mathbf{c}$
with $\mathbf{c} = [0, \tau]^\top$, and $A^2 = 0$ exactly as in Phase 2.
Therefore the **exactness proposition carries over verbatim**: one RK4 step
equals the exact ZOH update for every $h$. (Proof identical to
`altitude_1dof.md` §5.6 — nilpotency collapses $\mathbf{k}_2 = \mathbf{k}_3$ and
terminates the matrix-exponential series.) No integrator error in the rotational
channels.

### 3.2 Cascade: RK4 is *not* exact — and this is the point

The cascade (6) is **nonlinear**: $\dot{(\text{vel})} = s g \tan(a)$ depends on
the state through $\tan$, so there is no constant $A$ with $A^2 = 0$ and the
Phase-2 argument fails. Concretely, over a ZOH step the inner angle evolves as a
quadratic,

$$
a(t) = a_0 + r_0 t + \tfrac{1}{2}\tau t^2,
$$

so $\dot{(\text{vel})} = s g \tan\big(a(t)\big)$ is the tangent of a quadratic —
**not** a polynomial in $t$. Hence $\text{vel}(t)$ is not a polynomial, the
degree-$\le 4$ exactness corollary does not apply, and RK4 incurs its generic

$$
\text{local error } = \mathcal{O}(h^5),
\qquad \text{global error } = \mathcal{O}(h^4).
$$

This is the **foreshadowed payoff** from Phase 2: the docstring there justified
RK4 by appeal to "later phases [with] $\sin/\cos$ couplings [that] are genuinely
nonlinear." This cascade *is* that phase. RK4 is no longer overkill — its
fourth-order accuracy is now doing real work, and the cross-phase reuse of the
identical scheme is what keeps the controller benchmark clean.

---

## 4. Software wiring — the plant nodes

```python
class AttitudePlantNode:        # input tau -> output [angle, rate]
    def __init__(self, dt, x0=(0.0, 0.0)):
        self.dt = dt
        self.state = np.array(x0, float)
    def __call__(self, t, tau):
        self.state = attitude_rk4(self.state, float(np.atleast_1d(tau)[0]), self.dt)
        return self.state

class CascadePlantNode:         # input tau -> output [pos, vel, angle, rate]
    def __init__(self, dt, s, x0=(0.0, 0.0, 0.0, 0.0), g=G):
        self.dt, self.s, self.g = dt, s, g
        self.state = np.array(x0, float)
    def __call__(self, t, tau):
        self.state = cascade_rk4(self.state, float(np.atleast_1d(tau)[0]),
                                 self.s, self.dt, self.g)
        return self.state
```

Both are **stateful `nengo.Node`s**, exactly the loop-closing pattern from
`altitude_1dof.md` §7: hold the state between ticks, integrate one $h$ per call,
return the new state for the controller to read next tick.

$$
\texttt{AttitudePlantNode}:\ \tau \in \mathbb{R}^1 \longmapsto [\alpha, \dot\alpha] \in \mathbb{R}^2,
$$
$$
\texttt{CascadePlantNode}:\ \tau \in \mathbb{R}^1 \longmapsto [\text{pos}, \text{vel}, \alpha, \dot\alpha] \in \mathbb{R}^4.
$$

`CascadePlantNode` additionally carries the channel sign `s` (= $+1$ for
$x$/pitch, $-1$ for $y$/roll) and $g$, so a single class instantiates both
horizontal channels. Unlike Phase 2, there is no `AltitudeParams` object — the
constants $g$ and $\theta_{\max}$ live as module globals, since these plants are
inertia-normalised and need no per-vehicle mass.

The feedback loop closes identically:

$$
\tau \;\to\; \boxed{\text{PlantNode}} \;\to\; \text{state} \;\to\; \boxed{\text{Controller}} \;\to\; \tau \;\to\; \cdots
$$

> **Inputs / references.** This file defines only plants; the input is the inner
> torque $\tau$. Set-points (the desired angle or position) are supplied by the
> controller layer — to appear in a later module — not here.

---

## 5. Summary

Two decoupled plants complete the near-hover quadrotor model:

- **Attitude axis** $\ddot\alpha = \tau$ (eqs. 1–2): a bias-free double
  integrator serving roll, pitch, and yaw. Affine with $A^2 = 0$, so RK4 is
  **exact** (inherits Phase-2 §5.6).
- **Cascade** $\ddot{(\text{pos})} = s\,g\,\tan(\text{ang})$, $\ddot{(\text{ang})} = \tau$
  (eqs. 3–6): the underactuated horizontal channel, position driven by tilt,
  one sign $s = \pm 1$ covering $x$/pitch and $y$/roll, tilt clipped to
  $35^\circ$. **Nonlinear** ($\tan$), so RK4 is **not** exact — the first plant
  where the integrator's fourth-order accuracy is load-bearing.

**Threads to watch in later modules**

- The controller layer that produces $\tau$ for each axis (and the position
  set-points feeding the cascade outer loop).
- How the cascade's inner/outer loops are tuned given the four-integrator
  separation of eq. (7).
- The small-angle linearisation (7) likely reused for gain design, with the
  exact $\tan$ retained in the plant for fidelity.
- Whether the Nengo controller represents $\tan$ directly in neurons or works
  from the linearised form.

---

## References

[^quadctrl]: `Quad_control_2026.py` — the reference quadrotor controller this
    module matches; the inertia-normalised torque form $\ddot\alpha = \tau$ with
    inertia folded into the gains is set there (lines 52–56).

[^victor]: Victor's decoupled quadrotor model. Plant of record for the project;
    the exact $\tan$ horizontal coupling $\ddot x = g\tan\theta$ is from the
    $x$-control derivation, p. 28. Vehicle constants in `Values_Quadrotor_model.m`.
