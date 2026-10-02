"""Check the numbers behind 'why chi has no effect' using the paper's parameters (Table I)."""
import numpy as np

alpha_h, gamma, g0, g1, Ib, Ig, G, tau, tau_r = 50.0, 2.0, 120.0, 30.0, 0.75, 1.25, 1e5, 0.05, 0.005
v_th, v_rest, v_reset = 1.0, 0.0, 0.0
sig = lambda x: 1.0 / (1.0 + np.exp(-x))

# 1. resting state: I = Ib, gate shut
v_rest_state = (v_rest + Ib)              # membrane fixed point when c ~ 0
r_rest = sig(alpha_h * (v_rest_state - v_th))   # gate fixed point with r ~ 0
print(f"rest: v = {v_rest_state:.3f},  r = sigma(-12.5) = {r_rest:.3e}")
c0 = g0 * r_rest**2
c1 = (g0 + g1 * Ib) * r_rest**2
print(f"rest conductance  chi=0: {c0:.2e} 1/s   chi=1: {c1:.2e} 1/s   vs leak 1/tau = {1/tau:.0f} 1/s")
print(f"rest activity a = clip(G r) = {min(G*r_rest, 1):.3f}")

# 2. latched state: r = 1
for I in (Ib, Ib + Ig):
    for chi in (0, 1):
        c = (g0 + chi * g1 * I) * 1.0
        lam = 1 / tau + c
        v_star = ((v_rest + I) / tau + c * v_reset) / lam
        b = sig(alpha_h * (v_star - v_th + gamma * 1.0))
        print(f"latched I={I:.2f} chi={chi}: c = {c:6.1f}  v* = {v_star:.4f}  gate target b = {b:.12f}  a = {min(G*1.0,1):.1f}")

# 3. can a latched gate ever close?  worst case v = 0 (lowest reachable), r = 1
print("worst-case gate target with v=0, r=1:", f"{sig(alpha_h * (0 - v_th + gamma)):.15f}", "(1 - b =", f"{1 - sig(alpha_h*(0-v_th+gamma)):.2e})")
# 4. relative size of the input-dependent shunt
for I in (Ib, Ib + Ig):
    print(f"chi*g1*I / g0 at I={I:.2f}: {g1*I/g0:.3f}")
