# `coaxial_trirotor.py` — Coaxial Y6 Trirotor Plant

> **Companion notes.** Mathematical mirror of `coaxial_trirotor.py`: the
> project's **headline airframe** (Phase 5). This is the *full* body-frame
> rigid-body model — body-frame velocities with Coriolis terms, complete Euler
> moment equations, gyroscopics, and the Euler kinematic map — i.e. exactly the
> pieces the quadrotor model (Phase 3-full) **dropped**. Part of the **Coaxial
> Tri-Rotor Project** study log.

**Phase:** 5 · **Convention:** body-frame velocities, $z$-up ·
**Source:** `y6_model.py`, after Mehndiratta & Kayacan [M] and Czyba et al. [C].[^M][^C]

---

## 0. What this module is, and what is new

The airframe is a **Y6**: three arms in an equilateral triangle, each carrying a
**coaxial rotor pair** (one on top, one on bottom) — six rotors total.

**Rotor numbering** [M]: front arm = 3, 4; back-right = 1, 2; back-left = 5, 6;
**odd (1, 3, 5) = top**, **even (2, 4, 6) = bottom**.

### What changes versus the quadrotor (Phases 2–4)

| Feature | Quadrotor (`quadrotor.py`) | Coaxial Y6 (this file) |
|:--------|:---------------------------|:-----------------------|
| Rotors | 4 | 6, in 3 coaxial pairs; $F_i = K_F\Omega_i^2$ |
| Velocities | inertial $\dot x,\dot y,\dot z$ | **body-frame** $u,v,w$ (Coriolis terms appear) |
| Rotation dynamics | decoupled $\ddot\alpha=\tau$ | **full Euler** eqs. with $qr, rp, pq$ coupling |
| Euler kinematics | dropped | **restored**: $T_{EB}$ map (eq. 3) |
| Gyroscopics | none | from the coaxial pairs (eq. 12) |
| Yaw mechanism | $+/-/+/-$ spin pattern | **coaxial top-vs-bottom drag split** (eq. 10z) |
| Allocation | trivial | genuine **6×4 mixer** (§5) |

### State (12), body-frame, $z$-up

```
0:X 1:Y 2:Z   3:u 4:v 5:w   6:phi 7:theta 8:psi   9:p 10:q 11:r
```

| Idx | Sym | Meaning | | Idx | Sym | Meaning |
|:---:|:---:|:--------|---|:---:|:---:|:--------|
| 0–2 | $X,Y,Z$ | **Earth**-frame position | | 6–8 | $\phi,\theta,\psi$ | roll, pitch, yaw |
| 3–5 | $u,v,w$ | **body**-frame velocity | | 9–11 | $p,q,r$ | **body**-frame angular rate |

The shift to **body-frame** $u,v,w,p,q,r$ is the structural change driving
everything below: derivatives in a rotating frame pick up cross terms
$\boldsymbol\omega\times(\cdot)$.

---

## 1. Parameters and geometry — `TrirotorParams`

```python
m=1.412; g=9.81
l1=0.28          # front-arm lever (arm radius)
l2=0.243         # lateral lever of back arms  = l1*sin60
l3=0.14          # longitudinal lever of back arms = l1*cos60
Ixx=0.014965; Iyy=0.021915; Izz=0.034433; Ixz=0.0
Jp=6e-5          # propeller inertia (gyroscopic)
KF=6.85e-6       # F_i   = KF * Omega_i^2
Ktau=3.35e-7     # tau_i = Ktau * Omega_i^2
omega_max=900
```

The triangle: the front arm points along $+x_b$ at radius $l_1$. The two back
arms sit at $\pm120^\circ$, so each resolves into a **lateral** component
$l_2 = l_1\sin 60^\circ = 0.243$ m (the roll lever) and a **longitudinal**
component $l_3 = l_1\cos 60^\circ = 0.14$ m (the back arms' pitch lever).
Inertia is heavier than the quad ($m = 1.412$ kg vs $0.9$). With $I_{xz}=0$ the
inertia tensor is diagonal and positive-definite (see §4.4).

---

## 2. Attitude kinematics — `R_EB` and `T_EB`

### 2.1 Rotation, body → Earth

```python
def R_EB(phi, theta, psi):  # body -> Earth, z-up
    ...
```

$R_{EB} = R_z(\psi)\,R_y(\theta)\,R_x(\phi)$ — the same ZYX sequence as the
quadrotor, mapping a body vector to Earth coordinates:

$$
R_{EB} =
\begin{bmatrix}
c\theta c\psi & s\phi s\theta c\psi - s\psi c\phi & c\phi s\theta c\psi + s\phi s\psi \\
c\theta s\psi & s\phi s\theta s\psi + c\psi c\phi & c\phi s\theta s\psi - s\phi c\psi \\
-s\theta & s\phi c\theta & c\phi c\theta
\end{bmatrix}. \tag{1}
$$

It is used to convert the body velocity into the Earth-frame position rate
(§4.5). Its third column is still the body-$z$ (thrust) axis in Earth
coordinates; being a rotation matrix, $R_{EB}^\top$ rotates Earth → body — which
is how gravity enters the body force equations (§4.3).

### 2.2 Euler kinematic map (the piece the quad dropped)

```python
def T_EB(phi, theta):   # [phidot,thetadot,psidot] = T_EB @ [p,q,r]
    ...
```

Body angular rates $(p,q,r)$ are **not** the Euler-angle derivatives. The map
between them is

$$
\begin{bmatrix}\dot\phi\\\dot\theta\\\dot\psi\end{bmatrix}
= T_{EB}\begin{bmatrix}p\\q\\r\end{bmatrix},
\quad
T_{EB} =
\begin{bmatrix}
1 & s\phi\tan\theta & c\phi\tan\theta \\
0 & c\phi & -s\phi \\
0 & s\phi/c\theta & c\phi/c\theta
\end{bmatrix}. \tag{2,3}
$$

The quadrotor model assumed $\dot\alpha \equiv \text{rate}$, i.e. $T_{EB} = I$;
that is the small-angle truncation of (3). The exact map has a **singularity at
$\theta = \pm 90^\circ$** ($\tan\theta, 1/\cos\theta \to \infty$) — the classic
Euler-angle **gimbal lock**, a known limitation of any Euler representation
(quaternions avoid it, at the cost of a 4th angle state).

---

## 3. Rotor forces — `rotor_forces`

```python
Om = alpha * omega
F = KF * Om**2
tau_drag = Ktau * Om**2
```

Each rotor's aerodynamic thrust and reaction (drag) torque are **quadratic** in
its speed:

$$
F_i = K_F\,(\alpha_i \Omega_i)^2,
\qquad
\tau_{\text{drag},i} = K_\tau\,(\alpha_i \Omega_i)^2,
\qquad i = 1,\dots,6. \tag{4}
$$

The factor $\alpha_i \in [0,1]$ is a per-rotor **health**: $\alpha_i = 1$ healthy,
$\alpha_i = 0$ a dead rotor. It is the **fault-tolerance hook** — the whole point
of the [M] reference is reconfigurable control after a rotor failure (§7).

---

## 4. The dynamics — `state_derivative`

### 4.1 Total thrust and the reaction moments (the mixer)

Total thrust along body-$z$:

$$
F_z = \sum_{i=1}^{6} F_i. \tag{5}
$$

The three body torques from the thrust pattern follow the triangular geometry:

```python
tpx = ((F5+F6) - (F1+F2)) * l2
tpy = (F3+F4)*l1 - (F1+F2+F5+F6)*l3
tpz = (tau1+tau3+tau5) - (tau2+tau4+tau6)
```

$$
\begin{aligned}
\tau_x^{\text{prop}} &= l_2\big[(F_5+F_6) - (F_1+F_2)\big]
&&\text{(roll: back-left vs back-right)} \\
\tau_y^{\text{prop}} &= l_1(F_3+F_4) - l_3(F_1+F_2+F_5+F_6)
&&\text{(pitch: front arm vs back arms)} \\
\tau_z^{\text{prop}} &= (\tau_1+\tau_3+\tau_5) - (\tau_2+\tau_4+\tau_6)
&&\text{(yaw: tops vs bottoms — eq. 10z)}
\end{aligned} \tag{6,7,8}
$$

- **Roll** (6): only the two *back* arms have a lateral offset $\pm l_2$; the
  front arm sits on the centreline ($y=0$) and cannot roll the vehicle.
- **Pitch** (7): the front pair acts at $+l_1$, the four back rotors at $-l_3$;
  their thrust difference pitches the craft.
- **Yaw** (8) — *the defining Y6 feature*. A quad yaws by spinning two rotors CW
  and two CCW. Here, each coaxial pair is **counter-rotating** (top vs bottom),
  so the net body-$z$ drag torque is the difference between **all tops**
  $(\tau_1+\tau_3+\tau_5)$ and **all bottoms** $(\tau_2+\tau_4+\tau_6)$. To yaw,
  speed up every top relative to every bottom (or vice versa). Yaw is therefore
  controlled by a **collective top/bottom drag split**, not by individual rotor
  signs.

### 4.2 Gyroscopic moments

```python
sum_odd  = Om[0]+Om[2]+Om[4]      # tops
sum_even = Om[1]+Om[3]+Om[5]      # bottoms
tgx = Jp * q * (sum_even - sum_odd)
tgy = Jp * p * (sum_odd  - sum_even)
```

A spinning rotor has angular momentum $h = J_p\Omega$ about body-$z$. When the
airframe rotates at body rate $\boldsymbol\omega$, each rotor exerts a
gyroscopic reaction $\propto \boldsymbol\omega \times h\,\hat{\mathbf z}$. Summed
over the pairs, the **net** rotor angular momentum is
$J_p(\Sigma_{\text{top}} - \Sigma_{\text{bot}})$, so

$$
\tau_x^{\text{gyro}} = J_p\,q\,(\Sigma_{\text{bot}} - \Sigma_{\text{top}}),
\qquad
\tau_y^{\text{gyro}} = J_p\,p\,(\Sigma_{\text{top}} - \Sigma_{\text{bot}}). \tag{12}
$$

Because tops and bottoms nearly cancel, this net effect is small (it scales with
the same top–bottom imbalance that produces yaw). The total applied torques are

$$
\tau_x = \tau_x^{\text{prop}} + \tau_x^{\text{gyro}}, \quad
\tau_y = \tau_y^{\text{prop}} + \tau_y^{\text{gyro}}, \quad
\tau_z = \tau_z^{\text{prop}}. \tag{9}
$$

### 4.3 Force equations (body frame, with Coriolis)

```python
udot = r*v - q*w + g*sin(theta)
vdot = p*w - r*u - g*sin(phi)*cos(theta)
wdot = q*u - p*v - g*cos(phi)*cos(theta) + Fz/m
```

In a body frame rotating at $\boldsymbol\omega = [p,q,r]$, Newton's law for the
body velocity $\mathbf{v}_b = [u,v,w]$ is

$$
m\big(\dot{\mathbf{v}}_b + \boldsymbol\omega \times \mathbf{v}_b\big) = \mathbf{F}_b
\;\Longrightarrow\;
\dot{\mathbf{v}}_b = \frac{\mathbf{F}_b}{m} - \boldsymbol\omega \times \mathbf{v}_b. \tag{13}
$$

The $-\boldsymbol\omega\times\mathbf{v}_b$ terms are the **Coriolis / transport**
terms absent from the quadrotor (whose velocities were inertial). The body force
$\mathbf{F}_b$ is thrust along $+z_b$ plus gravity rotated into the body via
$R_{EB}^\top$:

$$
\mathbf{F}_b = \begin{bmatrix}0\\0\\F_z\end{bmatrix} + R_{EB}^\top\begin{bmatrix}0\\0\\-mg\end{bmatrix}
= \begin{bmatrix} mg\sin\theta \\ -mg\sin\phi\cos\theta \\ F_z - mg\cos\phi\cos\theta \end{bmatrix}.
$$

With $\boldsymbol\omega\times\mathbf{v}_b = [\,qw-rv,\ ru-pw,\ pv-qu\,]$,
equation (13) yields **exactly the coded rows**:

$$
\boxed{
\begin{aligned}
\dot u &= rv - qw + g\sin\theta, \\
\dot v &= pw - ru - g\sin\phi\cos\theta, \\
\dot w &= qu - pv - g\cos\phi\cos\theta + \tfrac{F_z}{m}.
\end{aligned}} \tag{10}
$$

### 4.4 Moment equations (full $I_{xz}$-coupled Euler)

```python
D = Ixx*Izz - Ixz**2
pdot = (1/D)*( (-p*q*Ixz + q*r*(Iyy-Izz))*Izz
             - ( q*r*Ixz + p*q*(Ixx-Iyy))*Ixz + tau_x*Izz - tau_z*Ixz )
qdot = p*r*(Izz-Ixx)/Iyy - (r**2 - p**2)*(Ixz/Iyy) + tau_y/Iyy
rdot = (1/D)*( ( q*r*Ixz + p*q*(Ixx-Iyy))*Ixx
             - (-p*q*Ixz + q*r*(Iyy-Izz))*Ixz + tau_z*Ixx - tau_x*Ixz )
```

These solve Euler's rigid-body rotation equation

$$
\mathbf{I}\,\dot{\boldsymbol\omega} + \boldsymbol\omega \times (\mathbf{I}\boldsymbol\omega) = \boldsymbol\tau,
\qquad
\mathbf{I} = \begin{bmatrix} I_{xx} & 0 & -I_{xz} \\ 0 & I_{yy} & 0 \\ -I_{xz} & 0 & I_{zz} \end{bmatrix}, \tag{11}
$$

for $\dot{\boldsymbol\omega}$. The $p$- and $r$-equations couple through $I_{xz}$
(the aircraft's $x$–$z$ symmetry-plane product of inertia), so inverting that
$2\times2$ block introduces the determinant $D = I_{xx}I_{zz} - I_{xz}^2$; the
$q$-equation stays separate. **Here $I_{xz}=0$**, so $D = I_{xx}I_{zz}$ and (11)
collapses to the textbook diagonal-inertia Euler equations:

$$
\boxed{
\begin{aligned}
I_{xx}\dot p &= \tau_x + (I_{yy} - I_{zz})\,qr, \\
I_{yy}\dot q &= \tau_y + (I_{zz} - I_{xx})\,rp, \\
I_{zz}\dot r &= \tau_z + (I_{xx} - I_{yy})\,pq.
\end{aligned}} \tag{14}
$$

The $qr, rp, pq$ terms are the **inertial cross-coupling** the quadrotor model
omitted (it used $\ddot\alpha = \tau$). The code keeps the general $I_{xz}$ form
for fidelity and future-proofing, with $I_{xz}=0$ reducing it to (14).

### 4.5 Assembling the derivative

```python
xdot[IX:IZ+1]   = R_EB(phi,theta,psi) @ [u,v,w]   # body vel -> Earth pos rate
xdot[IU:IW+1]   = [udot, vdot, wdot]              # eq. (10)
xdot[IPHI:IPSI+1] = T_EB(phi,theta) @ [p,q,r]     # eq. (2,3)
xdot[IP:IR+1]   = [pdot, qdot, rdot]              # eq. (14)
```

The 12-vector splits into two kinematic transforms ($R_{EB}$ for position,
$T_{EB}$ for Euler angles) and two dynamic blocks (force eq. 10, moment eq. 14).
This is the **complete** rigid-body model: nothing is decoupled or
small-angle-truncated except where $I_{xz}=0$ removes a term.

---

## 5. Control allocation — the 6×4 mixer

This file maps **rotor speeds → wrench**. The controller needs the inverse
(**wrench → rotor speeds**), supplied by `src/allocation` (mixer of [C][^C]).
Writing $n_i \equiv \Omega_i^2$ (so $F_i = K_F n_i$, $\tau_{\text{drag},i} = K_\tau n_i$),
the wrench is **linear** in $n_i$:

$$
\begin{bmatrix} F_z \\ \tau_x \\ \tau_y \\ \tau_z \end{bmatrix}
= M
\begin{bmatrix} n_1 \\ n_2 \\ n_3 \\ n_4 \\ n_5 \\ n_6 \end{bmatrix},
\quad
M =
\begin{bmatrix}
K_F & K_F & K_F & K_F & K_F & K_F \\
-K_F l_2 & -K_F l_2 & 0 & 0 & K_F l_2 & K_F l_2 \\
-K_F l_3 & -K_F l_3 & K_F l_1 & K_F l_1 & -K_F l_3 & -K_F l_3 \\
K_\tau & -K_\tau & K_\tau & -K_\tau & K_\tau & -K_\tau
\end{bmatrix}. \tag{15}
$$

$M$ is $4\times 6$ (read off directly from eqs. 5–8, ignoring the small
gyroscopic correction). The allocation inverts it with a **pseudo-inverse**: six
rotors realise a four-component wrench, so there are **two redundant DOF** — and
that redundancy is exactly what permits **fault-tolerant reconfiguration** (lose
a rotor, re-solve over the survivors). This is the "input map" change flagged at
the end of `quadrotor.md`: $R_{:,3}$ geometry is intact, but the mapping from
actuators to wrench is now a genuine non-trivial mixer.

---

## 6. The integrator — `rk4_step`

The same RK4 + ZOH scheme as every phase (`altitude_1dof.md` §5), on 12 states
with the rotor speeds $\boldsymbol\Omega$ and health $\boldsymbol\alpha$ held
constant across the step. The vector field is **strongly nonlinear** — Coriolis
products, $\sin/\cos$ gravity projection, $qr/rp/pq$ inertial coupling, and the
$\tan\theta$ in $T_{EB}$ — so RK4 is firmly in its approximate regime
($\mathcal{O}(h^5)$ local, $\mathcal{O}(h^4)$ global). Reusing the identical
scheme keeps the discretisation consistent with every earlier plant, as
established back in Phase 2.

---

## 7. Software wiring and fault tolerance — `TrirotorPlantNode`

```python
class TrirotorPlantNode:      # input = 6 rotor speeds [rad/s] -> 12 states
    def __init__(self, dt, x0=None, alpha_fn=None, P=TrirotorParams()):
        self.alpha_fn = alpha_fn or (lambda t: np.ones(6))
        ...
    def __call__(self, t, omega):
        self.state = rk4_step(self.state, omega, self.alpha_fn(t), self.dt, self.P)
        return self.state
```

The same stateful `nengo.Node` loop-closing pattern, now
$\boldsymbol\Omega \in \mathbb{R}^6 \mapsto X \in \mathbb{R}^{12}$. The new
ingredient is **`alpha_fn(t)`**: a time-varying per-rotor health vector that
**injects faults**. A healthy run uses $\boldsymbol\alpha \equiv \mathbf{1}$;
setting, say, $\alpha_2(t \ge t_f) = 0$ kills the bottom rotor of the back-right
arm at $t_f$, and the fault-tolerant allocation (§5) must redistribute the wrench
over the remaining five. This is the experimental core of the [M] paper.[^M]

---

## 8. Derived quantities

**Hover.** All six rotors share the weight:

$$
F_z^{\text{hover}} = mg = 1.412 \times 9.81 = 13.85\ \text{N},
\qquad
F_i^{\text{hover}} = \frac{mg}{6} = 2.309\ \text{N}.
$$

The per-rotor hover speed inverts eq. (4):

$$
\Omega_{\text{hover}} = \sqrt{\frac{mg}{6 K_F}}
= \sqrt{\frac{13.85}{6 \times 6.85\times10^{-6}}}
= 580.5\ \text{rad s}^{-1} \approx 5544\ \text{RPM},
$$

which is $0.645\,\Omega_{\max}$ — comfortable headroom.

**Thrust-to-weight at $\Omega_{\max}$:**

$$
\frac{6 K_F \Omega_{\max}^2}{mg}
= \frac{6 \times 6.85\times10^{-6} \times 900^2}{13.85}
= \frac{33.29}{13.85} = 2.40,
$$

comparable to the quad's 2.5 (`altitude_1dof.md` §2.3).

---

## 9. Summary

The coaxial Y6 is the project's full-fidelity, body-frame, 12-state rigid-body
plant:

- **Kinematics**: $R_{EB}$ (eq. 1) carries body velocity to Earth position;
  $T_{EB}$ (eq. 3) carries body rates to Euler-angle rates — the map the quad
  dropped, with gimbal lock at $\theta = \pm 90^\circ$.
- **Forces** (eq. 10): body-frame Newton with Coriolis $\boldsymbol\omega\times\mathbf{v}_b$
  and gravity rotated through $R_{EB}^\top$.
- **Moments** (eq. 14): full Euler equations with $qr/rp/pq$ coupling
  ($I_{xz}=0 \Rightarrow$ diagonal form), plus gyroscopics (eq. 12).
- **Y6 signature**: six rotors in coaxial pairs; $F_i = K_F\Omega_i^2$; **yaw by
  top-vs-bottom drag split** (eq. 8); a real **6×4 mixer** (eq. 15) with two
  redundant DOF enabling **fault tolerance** via `alpha_fn`.
- Same **RK4 + ZOH** integrator, now firmly approximate.

**Threads to watch in later modules**

- The **allocation** module that inverts $M$ (eq. 15) — pseudo-inverse, and how
  it reconfigures when a rotor's $\alpha \to 0$.
- The **controller** producing the wrench $[F_z, \tau_x, \tau_y, \tau_z]$ —
  likely position → attitude → rate nested loops, now over the full Euler model.
- Whether the **Nengo** controller works in the body frame directly or on a
  reduced/linearised model.
- How the **fault-tolerant** behaviour is tested (fault timing via `alpha_fn`,
  recovery metrics).

---

## References

[^M]: A. Mehndiratta, E. Kayacan, "Reconfigurable Fault-tolerant NMPC for a Y6
    Coaxial Tricopter with Complete Loss of One Rotor," IEEE Conf. on Control
    Technology and Applications (CCTA), 2018 — plant model and parameters
    (Table I).

[^C]: R. Czyba et al., "Development of Co-Axial Y6-Rotor UAV — Design,
    Mathematical Modeling, Rapid Prototyping and Experimental Validation,"
    Int. Conf. on Unmanned Aircraft Systems (ICUAS), 2015 — control-allocation
    (mixer).
