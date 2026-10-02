"""Exact Python port of Quadri_Victor_combination_PID_R2025a (1 kHz discrete loop).

Purpose: re-run the classical baseline with PD inner (attitude) loops
(ki_psi = ki_theta = ki_phi = 0) to match the SNN controller's structure,
without a MATLAB round-trip. The port replicates, operation for operation:
  ref_quad_local_pid.m  ->  pid_quad_controller.m  ->  plant_quad_victor_rk4.m
with the unit-delay state/integral memories of the generated model.

Validation mode first reproduces the ORIGINAL run (small attitude integrals)
and compares against results/Quadri_Victor_combination_PID_R2025a_timeseries.csv.

Outputs (PD-inner variant):
  results/Quadri_Victor_combination_PDinner_timeseries.csv  (same columns)
"""
import os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------- parameters (victor_pid_params.m) ----------------
dt = 0.001
m, g = 1.0, 9.81
k_sig = 1.0
z_amp, x_amp, y_amp, psi_ref_v = 3.0, 1.0, 1.5, 0.0
kp = dict(z=40.0, x=1.6, y=3.0, psi=7.0, theta=120.0, phi=40.0)
kd = dict(z=5.0, x=5.0, y=2.0, psi=4.0, theta=8.0, phi=8.0)
KI_FULL = dict(z=2.0, x=0.08, y=0.10, psi=0.20, theta=1.5, phi=1.0)
tilt_lim = np.deg2rad(35.0)
den_min, u_min, u_max = 0.25, 0.0, 3.0 * m * g
tau_lim = dict(psi=20.0, theta=80.0, phi=80.0)
int_lim = dict(xy=5.0, z=5.0, att=2.0)
T_STOP = 60.0
Y_DELAY = 15.0

def sigmoid_ref(t, amp, k, center):
    q = np.exp(-k * (t - center))
    den = 1.0 + q
    return amp / den, amp * k * q / (den * den)

def ref_fun(t):
    z_ref, _ = sigmoid_ref(t, z_amp, k_sig, 4.0)
    x_ref, dx_ref = sigmoid_ref(t, x_amp, k_sig, 5.0)
    if t < Y_DELAY:
        y_ref, dy_ref = 0.0, 0.0
    else:
        y_ref, dy_ref = sigmoid_ref(t - Y_DELAY, y_amp, k_sig, 5.0)
    return np.array([x_ref, dx_ref, y_ref, dy_ref, z_ref, 0.0, psi_ref_v])

def sat(x, lim):
    return min(max(x, -lim), lim)

def wrap_pi(x):
    return (x + np.pi) % (2 * np.pi) - np.pi

def controller(ref, state, int_state, ki):
    x, dx, y, dy, z, dz, psi, dpsi, th, dth, ph, dph = state
    ex, edx = ref[0] - x, ref[1] - dx
    ey, edy = ref[2] - y, ref[3] - dy
    ez, edz = ref[4] - z, -dz
    epsi, edpsi = wrap_pi(ref[6] - psi), -dpsi

    integ = int_state.copy()
    integ[0] = sat(int_state[0] + dt * ex, int_lim['xy'])
    integ[1] = sat(int_state[1] + dt * ey, int_lim['xy'])
    integ[2] = sat(int_state[2] + dt * ez, int_lim['z'])
    integ[3] = sat(int_state[3] + dt * epsi, int_lim['att'])

    ax = kp['x'] * ex + ki['x'] * integ[0] + kd['x'] * edx
    ay = kp['y'] * ey + ki['y'] * integ[1] + kd['y'] * edy
    uz = kp['z'] * ez + ki['z'] * integ[2] + kd['z'] * edz

    th_d = sat(np.arctan2(ax, g), tilt_lim)
    ph_d = sat(np.arctan2(-ay * np.cos(th), g), tilt_lim)

    eth, edth = th_d - th, -dth
    eph, edph = ph_d - ph, -dph
    integ[4] = sat(int_state[4] + dt * eth, int_lim['att'])
    integ[5] = sat(int_state[5] + dt * eph, int_lim['att'])

    u = min(max((m * g + uz) / max(np.cos(th) * np.cos(ph), den_min), u_min), u_max)
    tpsi = sat(kp['psi'] * epsi + ki['psi'] * integ[3] + kd['psi'] * edpsi, tau_lim['psi'])
    tth = sat(kp['theta'] * eth + ki['theta'] * integ[4] + kd['theta'] * edth, tau_lim['theta'])
    tph = sat(kp['phi'] * eph + ki['phi'] * integ[5] + kd['phi'] * edph, tau_lim['phi'])

    cmd = np.array([u, tpsi, tth, tph, th_d, ph_d, ax, ay, uz])
    err = np.array([ex, ey, ez, epsi, eth, eph, *integ])
    return cmd, err, integ

def dyn(x, cmd):
    u, tpsi, tth, tph = cmd[0], cmd[1], cmd[2], cmd[3]
    psi, th, ph = x[6], x[8], x[10]
    dX = np.zeros(12)
    dX[0] = x[1]
    dX[1] = u * (np.sin(ph) * np.sin(psi) + np.cos(ph) * np.cos(psi) * np.sin(th)) / m
    dX[2] = x[3]
    dX[3] = u * (np.cos(ph) * np.sin(th) * np.sin(psi) - np.cos(psi) * np.sin(ph)) / m
    dX[4] = x[5]
    dX[5] = u * (np.cos(th) * np.cos(ph)) / m - g
    dX[6] = x[7];  dX[7] = tpsi
    dX[8] = x[9];  dX[9] = tth
    dX[10] = x[11]; dX[11] = tph
    return dX

def plant_rk4(state, cmd):
    h = dt
    k1 = dyn(state, cmd)
    k2 = dyn(state + 0.5 * h * k1, cmd)
    k3 = dyn(state + 0.5 * h * k2, cmd)
    k4 = dyn(state + h * k3, cmd)
    return state + (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)

def simulate(ki, psi0=0.0):
    n = int(round(T_STOP / dt)) + 1
    state = np.zeros(12)
    state[6] = psi0          # initial yaw offset (psi state)
    integ = np.zeros(6)
    T = np.arange(n) * dt
    REF = np.zeros((n, 7)); ST = np.zeros((n, 12)); CMD = np.zeros((n, 9)); ERR = np.zeros((n, 12))
    for k in range(n):
        r = ref_fun(T[k])
        cmd, err, integ_next = controller(r, state, integ, ki)
        REF[k], ST[k], CMD[k], ERR[k] = r, state, cmd, err
        state = plant_rk4(state, cmd)
        integ = integ_next
    return T, REF, ST, CMD, ERR

HEADER = ("time_s,ref_x_ref,ref_dx_ref,ref_y_ref,ref_dy_ref,ref_z_ref,ref_dz_ref,ref_psi_ref,"
          "state_x,state_dx,state_y,state_dy,state_z,state_dz,state_psi,state_dpsi,"
          "state_theta,state_dtheta,state_phi,state_dphi,"
          "cmd_u,cmd_tau_psi,cmd_tau_theta,cmd_tau_phi,cmd_theta_des,cmd_phi_des,"
          "cmd_ax_cmd,cmd_ay_cmd,cmd_uz_cmd,"
          "err_ex,err_ey,err_ez,err_epsi,err_etheta,err_ephi,"
          "err_Ix,err_Iy,err_Iz,err_Ipsi,err_Itheta,err_Iphi")

if __name__ == "__main__":
    # ---- 1) validate port against the existing Simulink export ----
    #      (needs the Simulink export; run the .slx and export the logged signals first)
    simcsv = os.path.join(ROOT, "results", "Quadri_Victor_combination_PID_R2025a_timeseries.csv")
    if os.path.isfile(simcsv):
        S = np.genfromtxt(simcsv, delimiter=",", skip_header=1)
        T, REF, ST, CMD, ERR = simulate(KI_FULL)
        nn = min(len(T), S.shape[0])
        d_state = np.max(np.abs(ST[:nn] - S[:nn, 8:20]))
        d_cmd = np.max(np.abs(CMD[:nn] - S[:nn, 20:29]))
        print(f"VALIDATION vs Simulink CSV: max|state diff| = {d_state:.3e}, max|cmd diff| = {d_cmd:.3e}")
    else:
        print("Simulink export not found; skipping the port validation step.")
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)

    # ---- 2) PD inner loops: attitude integral gains set to zero ----
    ki_pd = dict(KI_FULL, psi=0.0, theta=0.0, phi=0.0)
    T, REF, ST, CMD, ERR = simulate(ki_pd)
    out = os.path.join(ROOT, "results", "Quadri_Victor_combination_PDinner_timeseries.csv")
    M = np.column_stack([T, REF, ST, CMD, ERR])
    np.savetxt(out, M, delimiter=",", header=HEADER, comments="", fmt="%.12g")
    print("wrote", out)

    # ---- 3) PD inner + yaw initial condition (matches SNN spinup mission) ----
    PSI0 = 0.08   # rad; classical analog of the SNN yaw spinup peak (0.084 rad)
    T, REF, ST, CMD, ERR = simulate(ki_pd, psi0=PSI0)
    out = os.path.join(ROOT, "results", "Quadri_Victor_combination_PDinner_psi0_timeseries.csv")
    M = np.column_stack([T, REF, ST, CMD, ERR])
    np.savetxt(out, M, delimiter=",", header=HEADER, comments="", fmt="%.12g")
    print("wrote", out)
