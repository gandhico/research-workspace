# `quadrotor.py` — Full 12-State Quadrotor Model

> **Companion notes.** Mathematical mirror of `quadrotor.py`: the *coupled,
> nonlinear* rigid-body quadrotor that the Phase-3 decoupled subsystems
> approximate. Part of the **Coaxial Tri-Rotor Project** study log.

**Phase:** 3 (full model) · **Convention:** $z$-up · **Source:** Victor's
baseline `Quad_control_2026.py`, itself eqs. 2.30–2.35 of García-Carrillo et al.[^source]

---

## 0. What this module is

Phases 2–3 gave *decoupled* channels (altitude; three attitude axes; two
position cascades). This module is the **ground truth** they approximate: one
12-state nonlinear model in which thrust and attitude are fully coupled through
the vehicle's orientation.

### State vector (12 states, $z$-up)

```
X = [x, dx, y, dy, z, dz, psi, dpsi, theta, dtheta, phi, dphi]
     0   1  2   3  4   5    6     7     8      9     10    11
```

| Index | Symbol | Meaning | | Index | Symbol | Meaning |
|:-----:|:------:|:--------|---|:-----:|:------:|:--------|
| 0,1 | $x,\dot x$ | N–S position, velocity | | 6,7 | $\psi,\dot\psi$ | **yaw**, rate |
| 2,3 | $y,\dot y$ | E–W position, velocity | | 8,9 | $\theta,\dot\theta$ | **pitch**, rate |
| 4,5 | $z,\dot z$ | altitude, velocity | | 10,11 | $\phi,\dot\phi$ | **roll**, rate |

Note the angle ordering in the state is **yaw, pitch, roll** ($\psi, \theta, \phi$).

### Inputs (4)

$$
\mathbf{v} = [\,u,\ \tau_\psi,\ \tau_\theta,\ \tau_\phi\,]
$$

- $u$ — total thrust $[\text{N}]$ (mass-normalised in the equations via $u/m$;
  $u_{\text{hover}} = mg$ as in Phase 2);
- $\tau_\psi, \tau_\theta, \tau_\phi$ — angular-acceleration commands
  $[\text{rad s}^{-2}]$ (inertia folded into the gains, as in Phase 3).

Four inputs for six rigid-body DOF — the model is **underactuated** (§2.4).

### Parameters

```python
M = 0.9
G = 9.81
@dataclass
class QuadParams:
    m: float = M
    g: float = G
```

Same Victor's quad: $m = 0.9\ \text{kg}$, $g = 9.81\ \text{m s}^{-2}$.[^source]

---

## 1. The dynamics — `quad_deriv`

```python
dX[0] = dx
dX[1] = u * (sin(phi)*sin(psi) + cos(phi)*cos(psi)*sin(theta)) / m
dX[2] = dy
dX[3] = u * (cos(phi)*sin(theta)*sin(psi) - cos(psi)*sin(phi)) / m
dX[4] = dz
dX[5] = u * (cos(theta)*cos(phi)) / m - g
dX[6] = dpsi;   dX[7]  = tau_psi
dX[8] = dtheta; dX[9]  = tau_theta
dX[10]= dphi;   dX[11] = tau_phi
```

### 1.1 Translational dynamics: rotating the thrust vector

The rotors produce thrust along the **body** $z$-axis only: in body coordinates
the thrust vector is $[0, 0, u]^\top$. To get the inertial-frame acceleration,
rotate that body vector into the inertial frame by the orientation matrix $R$,
add gravity, and divide by mass:

$$
m\,\ddot{\mathbf{r}} = R\begin{bmatrix} 0 \\ 0 \\ u \end{bmatrix} - \begin{bmatrix} 0 \\ 0 \\ mg \end{bmatrix}
\;\Longrightarrow\;
\ddot{\mathbf{r}} = \frac{u}{m}\,R\,\mathbf{e}_3 - g\,\mathbf{e}_3,
\qquad \mathbf{e}_3 = [0,0,1]^\top. \tag{1}
$$

Only the **third column** of $R$ survives ($R\mathbf{e}_3 = R_{:,3}$). The
orientation uses the **ZYX (yaw–pitch–roll)** Euler sequence,
$R = R_z(\psi)\,R_y(\theta)\,R_x(\phi)$, whose third column is

$$
R_{:,3} =
\begin{bmatrix}
\sin\phi\sin\psi + \cos\phi\cos\psi\sin\theta \\[2pt]
\cos\phi\sin\theta\sin\psi - \cos\psi\sin\phi \\[2pt]
\cos\theta\cos\phi
\end{bmatrix}. \tag{2}
$$

Substituting (2) into (1) gives the three translational rows **exactly as coded**:

$$
\boxed{
\begin{aligned}
\ddot x &= \frac{u}{m}\big(\sin\phi\sin\psi + \cos\phi\cos\psi\sin\theta\big), \\
\ddot y &= \frac{u}{m}\big(\cos\phi\sin\theta\sin\psi - \cos\psi\sin\phi\big), \\
\ddot z &= \frac{u}{m}\cos\theta\cos\phi - g.
\end{aligned}} \tag{3}
$$

For reference, the full ZYX matrix (only its third column enters the dynamics):

$$
R =
\begin{bmatrix}
c\psi c\theta & c\psi s\theta s\phi - s\psi c\phi & c\psi s\theta c\phi + s\psi s\phi \\
s\psi c\theta & s\psi s\theta s\phi + c\psi c\phi & s\psi s\theta c\phi - c\psi s\phi \\
-s\theta & c\theta s\phi & c\theta c\phi
\end{bmatrix},
\quad (c\!\cdot \equiv \cos, \ s\!\cdot \equiv \sin).
$$

### 1.2 The $z$-equation is the Phase-2 prophecy fulfilled

The altitude row of (3),

$$
\ddot z = \frac{u\cos\theta\cos\phi}{m} - g,
$$

is **exactly** the 3-D vertical channel written in `altitude_1dof.md` eq. (1′).
Phase 2 pinned $\phi = \theta = 0$ so $\cos 0 \cos 0 = 1$ and it collapsed to
$\ddot z = u/m - g$. Here the attitude is unpinned and the projection factor
$\cos\theta\cos\phi$ returns in full, as foreshadowed.

### 1.3 A useful invariant

Because $R_{:,3}$ is a column of a rotation matrix, it is a **unit vector**:
$\lVert R_{:,3}\rVert = 1$. Hence from (1),

$$
\big\lVert \ddot{\mathbf{r}} + g\,\mathbf{e}_3 \big\rVert = \frac{u}{m}.
$$

The thrust never changes the *magnitude* of the (gravity-removed) acceleration —
attitude only **redirects** a fixed-magnitude $u/m$ acceleration vector. Tilting
to gain horizontal acceleration necessarily steals from the vertical, which is
why altitude and horizontal control are coupled.

### 1.4 Rotational dynamics: decoupled double integrators

```python
dX[7] = tau_psi;  dX[9] = tau_theta;  dX[11] = tau_phi
```

$$
\ddot\psi = \tau_\psi, \qquad \ddot\theta = \tau_\theta, \qquad \ddot\phi = \tau_\phi. \tag{4}
$$

Each Euler angle is an **independent double integrator** driven by its
(normalised) angular-acceleration command — exactly the Phase-3 attitude axis
($\ddot\alpha = \tau$), now appearing three times.

> **Honest scope of "full."** This model is *fully coupled in translation*
> (eq. 3) but *simplified in rotation* (eq. 4). True rigid-body rotation obeys
> Euler's equations $I\dot{\boldsymbol\omega} + \boldsymbol\omega\times I\boldsymbol\omega = \boldsymbol\tau$
> with a nonlinear Euler-rate kinematic map between body rates
> $\boldsymbol\omega$ and angle rates $(\dot\psi,\dot\theta,\dot\phi)$. The
> baseline drops the gyroscopic coupling and the kinematic map, treating each
> angle as a clean double integrator. So "12-state" = full translational
> coupling + decoupled linear rotation. This is a deliberate modelling choice
> inherited from the source.[^source]

---

## 2. Structure, underactuation, and the link to Phase 3

### 2.1 State-space shape

The system is a 12-D nonlinear ODE $\dot X = f(X, \mathbf{v})$ that splits into

$$
\underbrace{\dot x, \dot y, \dot z, \dot\psi, \dot\theta, \dot\phi}_{\text{6 kinematic rows (trivial)}}
\quad\Big|\quad
\underbrace{\ddot x, \ddot y, \ddot z}_{\text{3 nonlinear (translation)}},\ 
\underbrace{\ddot\psi, \ddot\theta, \ddot\phi}_{\text{3 linear (rotation)}}.
$$

The kinematic rows just copy velocities into the derivative; all the physics
lives in the six dynamic rows.

### 2.2 Underactuation

Six rigid-body DOF $(x, y, z, \psi, \theta, \phi)$ are driven by **four** inputs
$(u, \tau_\psi, \tau_\theta, \tau_\phi)$. The three torques directly actuate the
three angles, and $u$ sets the thrust magnitude — but $x$ and $y$ have **no
direct input**. They move only when the vehicle tilts so that $R_{:,3}$ acquires
horizontal components (eq. 3). Horizontal motion is therefore controlled
*indirectly through attitude* — the defining underactuation of a quadrotor, of
which the Phase-3 cascade was the reduced-order expression.

### 2.3 The Phase-3 subsystems are *exact reductions* of this model

This is the unifying result of the whole modelling effort. Hold altitude (so the
altitude loop keeps $\ddot z = 0$, i.e. $\dfrac{u}{m} = \dfrac{g}{\cos\theta\cos\phi}$)
and set yaw $\psi = 0$. Substituting into the $x$-row of (3):

$$
\ddot x \Big|_{\psi=0,\,\text{$z$ held}}
= \frac{u}{m}\cos\phi\sin\theta
= \frac{g}{\cos\theta\cos\phi}\cos\phi\sin\theta
= g\,\frac{\sin\theta}{\cos\theta}
= g\tan\theta. \tag{5}
$$

This is **exactly** the Phase-3 cascade with $s = +1$ (`subsystems.md` eq. 3) —
and it is exact for any $\theta, \phi$, not just small angles. The $y$-row reduces
similarly:

$$
\ddot y \Big|_{\psi=0,\,\text{$z$ held}}
= -\,\frac{g}{\cos\theta}\tan\phi
\;\xrightarrow[\ \theta\ \text{small}\ ]{}\;
-g\tan\phi, \tag{6}
$$

matching the cascade with $s = -1$. Likewise the rotational rows (4) **are** the
Phase-3 attitude axes verbatim. So the decoupled plants we studied are not ad-hoc
approximations: they are this model evaluated near hover with $\psi \approx 0$.

---

## 3. The integrator — `quad_rk4`

```python
def quad_rk4(X, u, tau_psi, tau_theta, tau_phi, dt, P=QuadParams()):
    a = (u, tau_psi, tau_theta, tau_phi, P)
    k1 = quad_deriv(X, *a)
    k2 = quad_deriv(X + 0.5*dt*k1, *a)
    k3 = quad_deriv(X + 0.5*dt*k2, *a)
    k4 = quad_deriv(X + dt*k3, *a)
    return X + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)
```

The **same** RK4 + ZOH scheme as every prior phase (`altitude_1dof.md` §5), now
on 12 states with all four inputs held constant across the step (the tuple `a`).
The vector field (3) is **fully nonlinear** in the angles (products of $\sin$ and
$\cos$), so — as with the Phase-3 cascade — RK4 is *not* exact here:

$$
\text{local error } = \mathcal{O}(h^5), \qquad \text{global error } = \mathcal{O}(h^4).
$$

This is the culmination of the integrator thread that began in Phase 2: the
scheme chosen there "because later phases are genuinely nonlinear" now runs on
the genuinely nonlinear plant, identically, keeping the controller benchmark
clean across every channel from the exact linear anchor to this coupled model.

---

## 4. Reference trajectories and initial condition

### 4.1 Altitude reference — `z_ref`

A piecewise ramp/hold profile:

$$
z_{\text{ref}}(t) =
\begin{cases}
0, & t < 0, \\
t/10, & 0 \le t < 10 \quad (\text{ramp } 0 \to 1), \\
1, & 10 \le t < 20 \quad (\text{hold}), \\
-0.05\,t + 2, & 20 \le t < 30 \quad (\text{ramp } 1 \to 0.5), \\
0.5, & t \ge 30 \quad (\text{hold}).
\end{cases} \tag{7}
$$

(The coded expression for the descent segment,
$t\frac{0.5-1}{30-20} + \big(1 - 20\frac{0.5-1}{30-20}\big)$, is the line through
$(20, 1)$ and $(30, 0.5)$, i.e. slope $-0.05$, intercept $2$.) The profile
exercises tracking through climbs, holds, and a descent.

### 4.2 Horizontal references — `x_ref`, `y_ref` (slow sinusoid)

```python
_F = 0.1 / (2 * np.pi)        # chosen so that 2*pi*_F = 0.1 rad/s
```

The constant is rigged so the effective angular frequency is exactly
$\omega = 2\pi\,\_F = 0.1\ \text{rad s}^{-1}$ (period $2\pi/\omega \approx 62.8\ \text{s}$):

$$
x_{\text{ref}}(t) = y_{\text{ref}}(t) = \sin(0.1\,t),
\qquad
\dot x_{\text{ref}}(t) = \dot y_{\text{ref}}(t) = 0.1\cos(0.1\,t). \tag{8}
$$

Since $x_{\text{ref}} \equiv y_{\text{ref}}$, the commanded path is an oscillation
along the diagonal $y = x$. The velocity references (`x_ref_dot`, `y_ref_dot`)
are the analytic derivatives, available as **feed-forward** terms for the
horizontal controller.

### 4.3 Initial condition — `X0`

```python
X0 = [0.1, 0, -0.1, 0, 0, 0, 0.1, 0, 0, 0, 0, 0]
```

A small perturbation from the origin: $x_0 = 0.1$, $y_0 = -0.1$, $\psi_0 = 0.1$,
all else zero — enough to make the regulator work without being violent.

---

## 5. Software wiring — `QuadPlantNode`

```python
class QuadPlantNode:          # input [u, tau_psi, tau_theta, tau_phi] -> 12 states
    def __init__(self, dt, x0=None, P=QuadParams()):
        self.dt, self.P = dt, P
        self.state = (X0.copy() if x0 is None else np.array(x0, float))
    def __call__(self, t, v):
        u, tp, tt, tph = v
        self.state = quad_rk4(self.state, u, tp, tt, tph, self.dt, self.P)
        return self.state
```

The same stateful `nengo.Node` loop-closing pattern (`altitude_1dof.md` §7),
scaled up:

$$
\texttt{QuadPlantNode}:\quad
\underbrace{[\,u, \tau_\psi, \tau_\theta, \tau_\phi\,] \in \mathbb{R}^4}_{\texttt{size\_in}}
\;\longmapsto\;
\underbrace{X \in \mathbb{R}^{12}}_{\texttt{size\_out}}.
$$

Hold state between ticks, integrate one $h$ per call, return all 12 states for
the controller layer to read. The loop closes exactly as before:

$$
\mathbf{v} \;\to\; \boxed{\text{QuadPlantNode}} \;\to\; X \;\to\; \boxed{\text{Controller}} \;\to\; \mathbf{v} \;\to\; \cdots
$$

---

## 6. Summary

The full quadrotor is a 12-state nonlinear plant $\dot X = f(X, \mathbf{v})$:

- **Translation** (eq. 3) is the body thrust $[0,0,u]^\top$ rotated into the
  inertial frame by the ZYX matrix and offset by gravity — the dynamics are the
  third column $R_{:,3}$ (eq. 2), a unit vector, so attitude *redirects* a
  fixed-magnitude $u/m$ acceleration (§1.3).
- **Rotation** (eq. 4) is three decoupled double integrators
  $\ddot\alpha = \tau$ — full coupling in translation, simplified linear rotation.
- It is **underactuated** (4 inputs, 6 DOF); $x, y$ move only via tilt.
- The Phase-3 subsystems are its **exact near-hover reductions**
  (eqs. 5–6): $\ddot x = g\tan\theta$, $\ddot\alpha = \tau$.
- The shared **RK4 + ZOH** integrator is now fully approximate
  ($\mathcal{O}(h^4)$ global), completing the thread opened in Phase 2.

**Threads to watch in later modules**

- The controller producing $\mathbf{v} = [u, \tau_\psi, \tau_\theta, \tau_\phi]$,
  likely a nested loop: outer position → desired tilt $(\theta_d, \phi_d)$ →
  inner attitude → torques.
- How the controller inverts the coupling (eq. 3) — e.g. solving for the tilt
  that yields a desired horizontal acceleration.
- Whether the **Nengo** controller represents the trig coupling directly in
  neurons or uses the linearised/decoupled reductions for gain design.
- How this baseline is later adapted from the **quadrotor** to the **coaxial
  tri-rotor** (the project's namesake) — what changes in $R_{:,3}$ and the input
  map.

---

## References

[^source]: E. Espinoza, `Quad_control_2026.py` (baseline). The model is a
    faithful port of eqs. 2.30–2.35, p. 28, of L. R. García-Carrillo, A. E. Dzul,
    R. Lozano, C. Pégard, *Quad Rotorcraft Control: Vision-Based Hovering and
    Navigation* (Springer, 2013). Vehicle constants ($m = 0.9$ kg) from
    `Values_Quadrotor_model.m`.
