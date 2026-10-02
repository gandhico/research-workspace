# `altitude_1dof.py` — 1-DOF Vertical (Altitude) Plant

> **Companion notes.** This markdown file is the mathematical mirror of
> `altitude_1dof.py`. It follows the module top-to-bottom, pairing each code
> element with the equation it implements. Part of the **Coaxial Tri-Rotor
> Project** study log.

**Phase:** 2 (pedagogical anchor) · **Role:** plant (no controller) ·
**Convention:** $z$-up · **State:** $\mathbf{s} = [z,\ \dot z]$

---

## 0. What this module is

The module is the **simulated vehicle**, restricted to one degree of freedom:
vertical motion. It contains *no* controller. Its only job is the map

$$
\text{thrust command } u \;\longmapsto\; \text{resulting motion } (z, \dot z).
$$

The governing principle, stated in the docstring, is that this file is the
**single source of truth** for the altitude dynamics: the classical controller
and the Nengo (spiking-neural) controller both drive *this very plant*. The
benchmark is therefore fair — any performance gap comes from the controllers,
never from a difference in the simulated physics.[^paper1]

| Symbol | Meaning | Units |
|:------:|:--------|:-----:|
| $z$ | altitude (positive up) | m |
| $\dot z$ | vertical velocity | m s⁻¹ |
| $u$ | total rotor thrust (the control input) | N |
| $m$ | vehicle mass | kg |
| $g$ | gravitational acceleration | m s⁻² |

---

## 1. The core equation (module docstring)

```python
#   z_ddot = u/m - g
# the full vertical channel
#   z_ddot = u * cos(theta) * cos(phi) / m - g
# collapses to the 1-DOF form above (cos0*cos0 = 1).
```

### Derivation

Model the vehicle as a point mass $m$ on the vertical axis. Two forces act:
thrust $u$ **upward** $(+)$, weight $mg$ **downward** $(-)$. Newton's second law
along the upward $z$-axis:

$$
m\,\ddot z \;=\; \underbrace{u}_{\text{thrust}} \;-\; \underbrace{mg}_{\text{weight}}.
$$

Dividing by the mass gives the **entire plant**:

$$
\boxed{\;\ddot z \;=\; \dfrac{u}{m} - g\;} \tag{1}
$$

### Why the 3-D channel collapses to (1)

In a real multirotor, thrust acts along the **body** $z$-axis. Under roll $\phi$
and pitch $\theta$, only the vertical *component* opposes gravity:

$$
\ddot z \;=\; \frac{u\,\cos\theta\,\cos\phi}{m} - g. \tag{1'}
$$

This module pins the attitude flat, $\phi = \theta = 0$, so
$\cos 0 \cdot \cos 0 = 1$ and the projection factor vanishes, recovering (1).
The simplification isolates the vertical channel so altitude control can be
studied with nothing else moving. Later phases unpin $\phi, \theta$ and **(1′)
returns in full**.

---

## 2. Parameters — the `AltitudeParams` dataclass

```python
@dataclass
class AltitudeParams:
    m: float = 0.9                 # kg     vehicle mass (Victor's quad)
    g: float = 9.81                # m/s^2  gravity
    u_min: float = 0.0             # N      rotors cannot produce downward thrust
    thrust_to_weight: float = 2.5  # -      sets the upper actuator limit
```

`P` is **not a vector** — it is a *named* parameter set, accessed by label
(`P.m`, `P.g`), never by index. Mathematically it is the constant set
$\{m, g, u_{\min}, T/W\}$ that defines **which vehicle** is being flown, as
opposed to the time-varying state $\mathbf{s}$ and input $u$.

The plant of record is Victor's quad, $m = 0.9\ \text{kg}$.[^victor]

### 2.1 Hover thrust — the feed-forward term

```python
@property
def u_hover(self) -> float:
    return self.m * self.g
```

Set $\ddot z = 0$ in (1) (no vertical acceleration):

$$
\frac{u}{m} - g = 0
\;\Longrightarrow\;
u_{\text{hover}} = mg = 0.9 \times 9.81 = 8.829\ \text{N}. \tag{2}
$$

This is the thrust that exactly cancels gravity. Controllers command
$u = u_{\text{hover}} + (\text{correction})$, so feedback handles only
*deviations* rather than rediscovering gravity every tick — a deliberate
conditioning choice.

### 2.2 Saturation limits

```python
@property
def u_max(self) -> float:
    return self.thrust_to_weight * self.m * self.g
```

Rotors spin one way only, so they cannot produce downward thrust:
$u_{\min} = 0$. The upper limit is fixed by the thrust-to-weight ratio
$T/W = 2.5$:

$$
u_{\max} = \frac{T}{W}\,mg = 2.5 \times 0.9 \times 9.81 = 22.07\ \text{N}. \tag{3}
$$

### 2.3 Acceleration envelope (a consequence worth stating)

Substituting the limits into (1) bounds the achievable acceleration:

$$
a_{\uparrow,\max} = \frac{u_{\max}}{m} - g = 2.5g - g = +1.5\,g = +14.7\ \text{m s}^{-2},
$$

$$
a_{\downarrow,\max} = \frac{u_{\min}}{m} - g = 0 - g = -g = -9.81\ \text{m s}^{-2}.
$$

The envelope is **asymmetric**: the vehicle pushes *up* at $1.5g$ but can only
fall at $1g$ (free-fall, thrust cut to zero). **Any descent controller has
strictly weaker authority than an ascent controller** — a real constraint that
reappears the moment descent commands are issued.

---

## 3. Saturation — `clip_thrust`

```python
def clip_thrust(u, P: AltitudeParams) -> float:
    return float(np.clip(u, P.u_min, P.u_max))
```

A single clip enforces §2.2 and §2.3 simultaneously:

$$
u_{\text{sat}} = \operatorname{clip}(u,\, u_{\min},\, u_{\max})
= \min\!\big(\max(u,\, u_{\min}),\; u_{\max}\big). \tag{4}
$$

---

## 4. The dynamics — `dynamics` (state-space form)

```python
def dynamics(state, u: float, P: AltitudeParams) -> np.ndarray:
    z, zdot = state
    zddot = u / P.m - P.g
    return np.array([zdot, zddot])
```

With $\mathbf{s} = [z, \dot z]^\top$, differentiating componentwise and inserting
(1):

$$
\dot{\mathbf{s}}
= \begin{bmatrix} \dot z \\ \ddot z \end{bmatrix}
= \begin{bmatrix} \dot z \\ \dfrac{u}{m} - g \end{bmatrix}
\quad\Longleftrightarrow\quad
\texttt{np.array([zdot, zddot])}.
$$

In matrix form this is an **affine** system $\dot{\mathbf{s}} = A\mathbf{s} + Bu + \mathbf{w}$:

$$
\dot{\mathbf{s}}
= \underbrace{\begin{bmatrix} 0 & 1 \\ 0 & 0 \end{bmatrix}}_{A} \mathbf{s}
+ \underbrace{\begin{bmatrix} 0 \\ 1/m \end{bmatrix}}_{B} u
+ \underbrace{\begin{bmatrix} 0 \\ -g \end{bmatrix}}_{\mathbf{w}}. \tag{5}
$$

This is a **double integrator** (position is the integral of velocity; velocity
the integral of acceleration) with input gain $1/m$ and a constant gravity bias.
Both eigenvalues of $A$ sit at the origin — the open-loop plant is only
marginally stable (a free mass drifts), which is exactly why feedback is needed
to hold an altitude. The pair $(A, B)$ is the canonical second-order plant the
later controllers are tuned against.

---

## 5. The integrator — `rk4_step` (RK4 + zero-order hold)

This is the heart of the simulation, so it gets the full treatment.

```python
def rk4_step(state, u: float, dt: float, P: AltitudeParams) -> np.ndarray:
    k1 = dynamics(state, u, P)
    k2 = dynamics(state + 0.5 * dt * k1, u, P)
    k3 = dynamics(state + 0.5 * dt * k2, u, P)
    k4 = dynamics(state + dt * k3, u, P)
    return state + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
```

### 5.1 The initial-value problem

`dynamics()` gives the continuous *derivative* $\dot{\mathbf{s}} = f(\mathbf{s}, u)$.
To advance the sim we must solve the initial-value problem (IVP)

$$
\dot{\mathbf{s}}(t) = f\big(\mathbf{s}(t), u\big),
\qquad \mathbf{s}(t_n) = \mathbf{s}_n, \tag{6}
$$

over one step $h \coloneqq \texttt{dt}$, producing
$\mathbf{s}_{n+1} \approx \mathbf{s}(t_n + h)$. This plant is linear and solvable
in closed form, but the project's later phases (trig attitude couplings, rotor
aerodynamics) are genuinely nonlinear with no elementary solution. A numerical
integrator is mandatory there, so — per the docstring — the *same* integrator is
used now, making the discretisation byte-for-byte identical across every phase.

### 5.2 The RK4 scheme

Classical four-stage, fourth-order Runge–Kutta:[^rk4]

$$
\begin{aligned}
\mathbf{k}_1 &= f(\mathbf{s}_n,\, u), \\
\mathbf{k}_2 &= f\big(\mathbf{s}_n + \tfrac{h}{2}\mathbf{k}_1,\; u\big), \\
\mathbf{k}_3 &= f\big(\mathbf{s}_n + \tfrac{h}{2}\mathbf{k}_2,\; u\big), \\
\mathbf{k}_4 &= f\big(\mathbf{s}_n + h\,\mathbf{k}_3,\; u\big),
\end{aligned}
\qquad
\boxed{\;\mathbf{s}_{n+1} = \mathbf{s}_n + \frac{h}{6}\big(\mathbf{k}_1 + 2\mathbf{k}_2 + 2\mathbf{k}_3 + \mathbf{k}_4\big)\;} \tag{7}
$$

The weights $\tfrac{1}{6}(1, 2, 2, 1)$ are a **Simpson's-rule quadrature** in
disguise: $\mathbf{k}_1, \mathbf{k}_4$ are endpoint slopes, $\mathbf{k}_2, \mathbf{k}_3$
the doubly weighted midpoint slopes. Butcher tableau:

$$
\begin{array}{c|cccc}
0 & & & & \\
\tfrac12 & \tfrac12 & & & \\
\tfrac12 & 0 & \tfrac12 & & \\
1 & 0 & 0 & 1 & \\
\hline
& \tfrac16 & \tfrac13 & \tfrac13 & \tfrac16
\end{array}
$$

### 5.3 Accuracy

The RK4 weights are chosen so the method's Taylor expansion matches the true
solution **through order $h^4$**. The first mismatch is at $h^5$:

- **Local truncation error** (one step): $\mathbf{s}(t_n + h) - \mathbf{s}_{n+1} = \mathcal{O}(h^5)$.
- **Global error** (over $N = T/h$ steps): $\mathcal{O}(h^4)$ — hence "fourth-order".

**Corollary.** RK4 integrates *exactly* any IVP whose exact solution is a
polynomial in $t$ of degree $\le 4$, because then every Taylor term beyond $h^4$
vanishes and the order-4 agreement becomes equality. This is the key to §5.6.

### 5.4 Zero-order hold (ZOH)

In (7), $u$ is identical in all four stages — it is held **constant** across the
step. This is not just convenient; it is physically faithful: a digital
controller computes one thrust per tick and holds it until the next. So within
$[t_n, t_n + h)$ the system (5) has *constant* forcing

$$
b \coloneqq \frac{u}{m} - g \ (\text{fixed during the step}),
\qquad
\dot{\mathbf{s}} = A\mathbf{s} + \mathbf{c}, \quad
\mathbf{c} = \begin{bmatrix} 0 \\ b \end{bmatrix}.
$$

### 5.5 Exact discretisation via the matrix exponential

For a linear time-invariant system with constant input, (6) has the closed-form
(variation-of-constants) solution

$$
\mathbf{s}(t_n + h) = e^{Ah}\,\mathbf{s}_n
+ \left( \int_0^h e^{A\sigma}\,\mathrm{d}\sigma \right) \mathbf{c}. \tag{8}
$$

Everything hinges on $e^{Ah}$. **Lemma:** $A^2 = 0$ (the matrix is *nilpotent*):

$$
A^2 = \begin{bmatrix} 0 & 1 \\ 0 & 0 \end{bmatrix}\begin{bmatrix} 0 & 1 \\ 0 & 0 \end{bmatrix} = \begin{bmatrix} 0 & 0 \\ 0 & 0 \end{bmatrix}.
$$

Because $A^2 = 0$, every term of order $\ge 2$ in the series
$e^{Ah} = \sum_{k\ge 0} (Ah)^k / k!$ vanishes, leaving exact finite expressions:

$$
e^{Ah} = I + Ah = \begin{bmatrix} 1 & h \\ 0 & 1 \end{bmatrix},
\qquad
\int_0^h e^{A\sigma}\,\mathrm{d}\sigma = Ih + \tfrac{h^2}{2}A = \begin{bmatrix} h & \tfrac{h^2}{2} \\ 0 & h \end{bmatrix}.
$$

Substituting into (8) gives the **exact ZOH update**:

$$
\mathbf{s}_{n+1}^{\text{exact}} = \mathbf{s}_n + h\big(A\mathbf{s}_n + \mathbf{c}\big) + \tfrac{h^2}{2} A\mathbf{c}. \tag{9}
$$

### 5.6 RK4 is *exact* on this plant

**Proposition.** For the ZOH altitude plant ($A^2 = 0$, constant $\mathbf{c}$),
one RK4 step (7) equals the exact update (9) identically, for every $h$.

**Proof.** With $f(\mathbf{s}) = A\mathbf{s} + \mathbf{c}$, evaluate the stages
using $A^2 = 0$ throughout:

$$
\begin{aligned}
\mathbf{k}_1 &= A\mathbf{s}_n + \mathbf{c},
& A\mathbf{k}_1 &= A^2\mathbf{s}_n + A\mathbf{c} = A\mathbf{c}, \\
\mathbf{k}_2 &= \mathbf{k}_1 + \tfrac{h}{2}A\mathbf{k}_1 = \mathbf{k}_1 + \tfrac{h}{2}A\mathbf{c},
& A\mathbf{k}_2 &= A\mathbf{c}, \\
\mathbf{k}_3 &= \mathbf{k}_1 + \tfrac{h}{2}A\mathbf{k}_2 = \mathbf{k}_1 + \tfrac{h}{2}A\mathbf{c} = \mathbf{k}_2,
& A\mathbf{k}_3 &= A\mathbf{c}, \\
\mathbf{k}_4 &= \mathbf{k}_1 + h\,A\mathbf{k}_3 = \mathbf{k}_1 + h\,A\mathbf{c}.
\end{aligned}
$$

Summing with the RK4 weights:

$$
\mathbf{k}_1 + 2\mathbf{k}_2 + 2\mathbf{k}_3 + \mathbf{k}_4 = 6\,\mathbf{k}_1 + 3h\,A\mathbf{c},
$$

so

$$
\mathbf{s}_{n+1} = \mathbf{s}_n + \frac{h}{6}\big(6\mathbf{k}_1 + 3h\,A\mathbf{c}\big)
= \mathbf{s}_n + h\big(A\mathbf{s}_n + \mathbf{c}\big) + \tfrac{h^2}{2}A\mathbf{c},
$$

which is exactly (9). $\blacksquare$

> **One-line alternative.** With $A^2 = 0$, the exact trajectory (9) is a degree-2
> polynomial in $h$, and by the corollary of §5.3 RK4 is exact on polynomials of
> degree $\le 4$. The explicit stages above show the *mechanism*: nilpotency
> collapses $\mathbf{k}_2 = \mathbf{k}_3$ and terminates the series.

### 5.7 Then why RK4 here?

If the step is exact, even cheap Euler would be *inexact* (it drops the
$\tfrac{h^2}{2}A\mathbf{c}$ term, $\mathcal{O}(h^2)$ error). The real reason is
**cross-phase consistency**: the nonlinear later phases genuinely need a
fourth-order integrator, and reusing (7) verbatim guarantees the controllers are
compared on an identical discretisation pipeline. Exactness on this linear anchor
is a free bonus that removes integrator error as a confound in Phase 2.

---

## 6. Reference signal — `step_reference`

```python
def step_reference(t, t_step=1.0, z_target=1.0, z0=0.0) -> float:
    return z_target if t >= t_step else z0
```

A textbook unit step: hold $z_0 = 0$ until $t_{\text{step}} = 1\,\text{s}$, then
jump to $z_{\text{target}} = 1\,\text{m}$:

$$
z_{\text{ref}}(t) =
\begin{cases}
z_0, & t < t_{\text{step}}, \\
z_{\text{target}}, & t \ge t_{\text{step}}.
\end{cases} \tag{10}
$$

The step response is the standard controller probe — from it one reads rise
time, overshoot, settling time, and steady-state error. The 1-second delay lets
any start-up transient settle so the measured response is clean.

---

## 7. Software wiring — `AltitudePlantNode` (closing the loop in Nengo)

```python
class AltitudePlantNode:        # size_in=1 (thrust u), size_out=2 (state [z, zdot])
    def __init__(self, P, dt, x0=(0.0, 0.0)):
        self.P, self.dt = P, dt
        self.state = np.array(x0, dtype=float)
        self.last_u = P.u_hover           # start balanced, not in free-fall
    def __call__(self, t, u):
        u_cmd = clip_thrust(np.atleast_1d(u)[0], self.P)
        self.last_u = u_cmd
        self.state = rk4_step(self.state, u_cmd, self.dt, self.P)
        return self.state
```

Nengo builds **spiking** neural networks via the Neural Engineering
Framework.[^nengo] A `nengo.Node` is a non-neural element embeddable in such a
network; here it wraps the plant:

$$
\texttt{AltitudePlantNode}:\quad
\underbrace{u \in \mathbb{R}^1}_{\texttt{size\_in}}
\;\longmapsto\;
\underbrace{[z, \dot z] \in \mathbb{R}^2}_{\texttt{size\_out}}.
$$

The essential property is **statefulness**: a pure function is memoryless, but a
plant must remember where it is, so the node stores `self.state` between calls.
Each tick, `__call__(t, u)`:

1. clips the incoming thrust to $[u_{\min}, u_{\max}]$  — eq. (4);
2. records it in `last_u`  (diagnostics);
3. integrates one $h$ via RK4 + ZOH  — eq. (7);
4. returns the updated $[z, \dot z]$.

That returned state is what the controller reads next tick to compute the next
thrust. **Holding state inside the node is exactly what closes the feedback
loop:**

$$
u \;\to\; \boxed{\text{PlantNode}} \;\to\; [z, \dot z] \;\to\; \boxed{\text{Controller}} \;\to\; u \;\to\; \cdots
$$

`last_u` is initialised to $u_{\text{hover}}$ (eq. 2) so the first tick starts
from a balanced hover rather than from zero thrust (instantaneous free-fall).

---

## 8. Summary

This module is a **double-integrator plant** $\ddot z = u/m - g$
(eqs. 1, 5), equipped with a hover feed-forward $u_{\text{hover}} = mg$ (eq. 2),
asymmetric thrust saturation $0 \le u \le 2.5\,mg$ giving an acceleration
envelope $+1.5g / -1g$ (§2.3), and an RK4 + ZOH integrator that is provably
**exact** on this linear anchor (§5.6). A stateful `nengo.Node` holds the state
and thereby closes the loop, so the classical and neural controllers compete on
byte-for-byte identical physics.

**Threads to watch in later modules**

- How the classical controller selects $u$ around $u_{\text{hover}}$ (anticipated:
  PD/PID on $z$ and $\dot z$, matched to the $A$ of eq. 5).
- How that correction is *represented in neurons* for the Nengo version.
- The asymmetric envelope (§2.3) re-emerging when descent commands appear.
- The projection factor $\cos\theta\cos\phi$ of eq. (1′) returning when attitude
  is unpinned.

---

## References

[^paper1]: Plant of record, "Paper 1" — Victor's quadrotor model, defined in
    `Values_Quadrotor_model.m`. Used as the common physics baseline across the
    classical-vs-Nengo controller benchmark in this project.

[^victor]: Victor's quad mass $m = 0.9\ \text{kg}$, from
    `Values_Quadrotor_model.m`.

[^rk4]: Classical fourth-order Runge–Kutta method. See e.g. Butcher,
    *Numerical Methods for Ordinary Differential Equations* (Wiley), or Hairer,
    Nørsett & Wanner, *Solving Ordinary Differential Equations I* (Springer),
    for the order conditions and the Butcher-tableau formalism.

[^nengo]: Nengo / the Neural Engineering Framework (NEF). Eliasmith & Anderson,
    *Neural Engineering* (MIT Press, 2003); Bekolay et al., "Nengo: a Python
    tool for building large-scale functional brain models," *Frontiers in
    Neuroinformatics* (2014).
