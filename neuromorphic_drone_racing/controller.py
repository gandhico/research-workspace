"""
controller.py  --  one controller for a heterogeneous fleet.

Outer loop (all vehicles):  f_w = m (a_r + Kp (p_r - p) + Kd (v_r - v) + g e_z)     [world force at CoM]

Underactuated (X2, CF2, Y6):  geometric SO(3) control (Lee, Leok & McClamroch 2010)
    b3d = f_w/|f_w|,  b1c = [cos psi, sin psi, 0],  b2d = b3d x b1c/|.|,  R_d = [b2d x b3d, b2d, b3d]
    T   = f_w . (R e3)
    e_R = 1/2 vee(R_d^T R - R^T R_d),  e_w = w - R^T R_d w_d,
    w_d from the reference jerk j (differential flatness):  h = m/|f| (j - (b3.j) b3),
          w_d = [-h.b2, h.b1, psi_dot b3_z]   (reference-only; a finite difference of the
          feedback-laden R_d was tried and destabilised the loop)
    tau = J (-kR e_R - kW e_w) + w x J w,  roll/pitch kR = min(140, 0.5 alpha_max), kW = 1.8 sqrt(kR),
          alpha_max = the vehicle's max roll/pitch acceleration at hover (LP over its allocation);
          yaw kR=25, kW=10 with e_R,z
          clipped to +/-0.35 (yaw authority from rotor drag torque is ~10x below tilt authority)
    wrench rows used: [Fz, tau_x, tau_y, tau_z]; on saturation, bounded least squares with the
    yaw row weighted 0.05 (thrust and tilt keep priority)

Fully actuated (Omnicopter): attitude held at R_d = Rz(psi) R_0 (R_0 = its upright pose) and the
    whole body-frame wrench [R^T f_w ; tau] is allocated (same law as omnicopter/control/hover.py).

Allocation (all vehicles): u = argmin ||B u - w||  s.t. ctrlrange, with B built from the MJCF:
    column j = [ R_sj g_j[0:3] ;  R_sj g_j[3:6] + (r_sj - r_com) x R_sj g_j[0:3] ]   (body frame, about CoM)
so the SAME code allocates 4 (X2, CF2), 6 (Y6) or 8 reversible (Omnicopter) rotors.
"""
import numpy as np
import mujoco
from scipy.optimize import lsq_linear

G = 9.81
E3 = np.array([0.0, 0.0, 1.0])


def vee(S):
    return np.array([S[2, 1], S[0, 2], S[1, 0]])


def Rz(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])


def minjerk(p0, p1, s, T):
    s = np.clip(s, 0, 1)
    a, b, c = 10*s**3 - 15*s**4 + 6*s**5, (30*s**2 - 60*s**3 + 30*s**4)/T, (60*s - 180*s**2 + 120*s**3)/T**2
    d = p1 - p0
    return p0 + d*a, d*b, d*c


class VehicleController:
    def __init__(self, m, prefix, root, traj, fully_actuated=False, R0=np.eye(3),
                 kp=6.0, kd=4.6, kR=140.0, kW=24.0, kR_yaw=25.0, kW_yaw=10.0,
                 t_takeoff=3.0, t_start=4.0, auth_frac=0.5):
        self.m, self.pre, self.traj = m, prefix, traj
        self.bid = m.body(f"{prefix}/{root}").id
        self.mass = float(m.body_subtreemass[self.bid])
        self.full, self.R0 = fully_actuated, R0
        self.kp, self.kd, self.kR, self.kW = kp, kd, kR, kW
        self.kR_yaw, self.kW_yaw = (kR, kW) if fully_actuated else (kR_yaw, kW_yaw)
        self.t_takeoff, self.t_start = t_takeoff, t_start          # climb, then join the line at t_start
        # inertia about CoM in the BODY frame
        Ri = np.zeros(9); mujoco.mju_quat2Mat(Ri, m.body_iquat[self.bid]); Ri = Ri.reshape(3, 3)
        self.J = Ri @ np.diag(m.body_inertia[self.bid]) @ Ri.T
        com = m.body_ipos[self.bid]
        self.act = [i for i in range(m.nu) if m.actuator(i).name.startswith(prefix + "/")]
        B = np.zeros((6, len(self.act)))
        for j, a in enumerate(self.act):
            s = m.actuator_trnid[a, 0]
            assert m.site_bodyid[s] == self.bid
            Rs = np.zeros(9); mujoco.mju_quat2Mat(Rs, m.site_quat[s]); Rs = Rs.reshape(3, 3)
            g = m.actuator_gear[a]
            F = Rs @ g[:3]
            B[:3, j] = F
            B[3:, j] = Rs @ g[3:] + np.cross(m.site_pos[s] - com, F)
        self.B = B
        self.lo, self.hi = m.actuator_ctrlrange[self.act, 0], m.actuator_ctrlrange[self.act, 1]
        self.rows = slice(0, 6) if fully_actuated else [2, 3, 4, 5]
        self.Bs = B[self.rows]
        self.Bpinv = np.linalg.pinv(self.Bs)
        self.p_start = None
        self.tw = self.thrust_to_weight()
        # attitude bandwidth from the vehicle's own authority: kR <= AUTH_FRAC * alpha_max,
        # alpha_max = max roll/pitch angular acceleration available at hover (LP on B)
        self.alpha_max = self.tilt_authority()
        if not fully_actuated and auth_frac is not None:
            self.kR = min(kR, auth_frac*self.alpha_max)
            self.kW = 2*0.9*np.sqrt(self.kR)
        self.log = dict(t=[], p=[], p_ref=[], u=[], sat=[])

    # ---------------------------------------------------------------- capability from the MJCF
    def thrust_to_weight(self):
        """max vertical force with zero net torque (and zero lateral force if fully actuated),
        within actuator bounds, divided by weight.  Linear program over the allocation."""
        from scipy.optimize import linprog
        if self.full:
            # upright pose: world up = body axis R0^T e3
            up_b = self.R0.T @ E3
            A_eq = np.vstack([self.B[3:], self.B[:3] - np.outer(up_b, up_b @ self.B[:3])])
            c = -(up_b @ self.B[:3])
        else:
            A_eq, c = self.B[3:], -self.B[2]
        res = linprog(c, A_eq=A_eq, b_eq=np.zeros(A_eq.shape[0]), bounds=list(zip(self.lo, self.hi)))
        return float(-res.fun/(self.mass*G))

    def tilt_authority(self):
        """min over roll/pitch of the max angular acceleration at hover collective [rad/s^2]."""
        from scipy.optimize import linprog
        out = []
        up_b = self.R0.T @ E3
        for ax in (0, 1):
            e = np.zeros(3); e[ax] = 1.0
            rows = [self.B[3 + (ax + 1) % 3], self.B[3 + (ax + 2) % 3]]
            rhs = [0.0, 0.0]
            if self.full:
                rows += list(self.B[:3]); rhs += list(self.mass*G*up_b)
            else:
                rows.append(self.B[2]); rhs.append(self.mass*G)
            res = linprog(-self.B[3 + ax], A_eq=np.array(rows), b_eq=np.array(rhs),
                          bounds=list(zip(self.lo, self.hi)))
            out.append(-res.fun/self.J[ax, ax] if res.status == 0 else np.inf)
        return float(min(out))

    # ---------------------------------------------------------------- state
    def state(self, d):
        R = d.xmat[self.bid].reshape(3, 3)
        v6 = np.zeros(6)
        mujoco.mj_objectVelocity(self.m, d, mujoco.mjtObj.mjOBJ_BODY, self.bid, v6, 0)   # [w; v] world, at CoM
        return d.xipos[self.bid].copy(), v6[3:], R, R.T @ v6[:3]

    def reference(self, t):
        if t < self.t_start:                              # take-off + join: min-jerk from the podium
            p_line = self.traj.ref(self.traj.t0)[0]
            hover = self.p_start + np.array([0, 0, 1.2])
            if t < self.t_takeoff:
                p, v, a = minjerk(self.p_start, hover, t/self.t_takeoff, self.t_takeoff)
            else:
                T = self.t_start - self.t_takeoff
                p, v, a = minjerk(hover, p_line, (t - self.t_takeoff)/T, T)
            return p, v, a, self.traj.yaw_ref(self.traj.t0)
        p, v, a = self.traj.ref(t - self.t_start + self.traj.t0)
        return p, v, a, self.traj.yaw_ref(t - self.t_start + self.traj.t0)

    # ---------------------------------------------------------------- control
    def __call__(self, d):
        t = d.time
        p, v, R, w = self.state(d)
        if self.p_start is None:
            self.p_start = p.copy()
        p_r, v_r, a_r, psi = self.reference(t)
        # reference jerk and yaw rate by central difference of the (smooth) reference only
        h = 0.03                                # > reference grid spacing at race speed
        _, _, a_p, psi_p = self.reference(t + h)
        _, _, a_m, psi_m = self.reference(max(t - h, 0.0))
        j_r = (a_p - a_m)/(t + h - max(t - h, 0.0))
        if (t - h) < self.t_start <= (t + h) or (t - h) < self.t_takeoff <= (t + h):
            j_r = np.zeros(3)                  # phase hand-over: no spurious jerk spike
        psi_dot = ((psi_p - psi_m + np.pi) % (2*np.pi) - np.pi)/(t + h - max(t - h, 0.0))
        f_w = self.mass*(a_r + self.kp*(p_r - p) + self.kd*(v_r - v) + G*E3)
        if self.full:
            Rd = Rz(psi) @ self.R0
        else:
            b3 = f_w/np.linalg.norm(f_w)
            b1c = np.array([np.cos(psi), np.sin(psi), 0.0])
            b2 = np.cross(b3, b1c); b2 /= np.linalg.norm(b2)
            Rd = np.column_stack([np.cross(b2, b3), b2, b3])
        # differential-flatness body-rate feed-forward (Mellinger & Kumar 2011), expressed
        # in the desired frame; from the REFERENCE only, so no derivative of feedback enters
        if self.full:
            wd = np.array([0.0, 0.0, psi_dot]) @ np.eye(3)
            wd = Rd.T @ np.array([0.0, 0.0, psi_dot])
        else:
            T_mag = max(np.linalg.norm(f_w), 0.2*self.mass*G)
            hw = self.mass/T_mag*(j_r - (b3 @ j_r)*b3)
            wd = np.array([-hw @ b2, hw @ np.cross(b2, b3), psi_dot*b3[2]])
        wd_body = R.T @ Rd @ wd
        eR = 0.5*vee(Rd.T @ R - R.T @ Rd)
        # roll/pitch at full bandwidth; yaw softer and error-clipped (yaw authority of rotor
        # drag torque is ~10x smaller than tilt authority on X2/CF2/Y6), see module docstring
        kR = np.array([self.kR, self.kR, self.kR_yaw])
        kW = np.array([self.kW, self.kW, self.kW_yaw])
        eR[2] = np.clip(eR[2], -0.35, 0.35)
        tau = self.J @ (-kR*eR - kW*(w - wd_body)) + np.cross(w, self.J @ w)
        if self.full:
            wrench = np.concatenate([R.T @ f_w, tau])
        else:
            wrench = np.concatenate([[f_w @ R[:, 2]], tau])
        u = self.Bpinv @ wrench
        sat = bool(np.any(u < self.lo - 1e-9) or np.any(u > self.hi + 1e-9))
        if sat:                                           # bounded least squares only when needed
            W = np.ones(len(wrench)); W[-1] = 0.05        # yaw is sacrificed first
            u = lsq_linear(self.Bs*W[:, None], wrench*W, bounds=(self.lo, self.hi), method="bvls").x
        d.ctrl[self.act] = u
        L = self.log
        L["t"].append(t); L["p"].append(p); L["p_ref"].append(p_r); L["u"].append(u.copy()); L["sat"].append(sat)
