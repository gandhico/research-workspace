"""
run_exp02.py  —  Phase-3 benchmark: quadrotor subsystems, classical vs NEF.

Subsystems (Victor's decoupled quad model):
  * attitude axes : roll (phi), pitch (theta), yaw (psi)   -- double integrators
  * cascades      : x via pitch, y via roll                -- outer/inner + virtual cmd

Outputs:
  results/summaries/exp02_metrics.csv
  results/csv/exp02_attitude_timeseries.csv, exp02_cascade_timeseries.csv
  results/plots/exp02_attitude.png, exp02_cascade.png
"""
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np, pandas as pd, nengo
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

from src.models.subsystems import attitude_rk4, cascade_rk4, G
from src.controllers_classical.subsystem_pd import (
    ATT_GAINS, CAS_GAINS, CAS_SIGN, attitude_tau, cascade_control,
    natural_freq_att, damping_att)
from src.controllers_nengo.subsystem_nef import build_attitude_net, build_cascade_net
from src.utils.metrics import step_metrics_general, stability_note

DT, T_ATT, T_CAS, T_STEP, SEED = 0.001, 6.0, 12.0, 1.0, 1
ATT_TARGET = {"roll": 0.20, "pitch": 0.20, "yaw": 0.50}      # rad
CAS_TARGET = {"x": 2.0, "y": 2.0}                            # m
# NEF ensemble radii tuned per attitude axis (good decode resolution)
ATT_RADII = {"roll":  dict(r_err=0.4, r_rate=1.5, r_u=15.0),
             "pitch": dict(r_err=0.4, r_rate=1.5, r_u=15.0),
             "yaw":   dict(r_err=0.7, r_rate=1.5, r_u=8.0)}

RESULTS = ROOT / "results"
for sub in ("csv", "summaries", "plots"):
    (RESULTS / sub).mkdir(parents=True, exist_ok=True)


def att_ref(axis):
    tgt = ATT_TARGET[axis]
    return lambda t: tgt if t >= T_STEP else 0.0


def cas_ref(axis):
    tgt = CAS_TARGET[axis]
    return lambda t: tgt if t >= T_STEP else 0.0


# ----------------------------------------------------------------- classical
def run_att_classical(axis):
    g = ATT_GAINS[axis]; rf = att_ref(axis)
    n = int(T_ATT / DT); s = np.zeros(2)
    t = np.zeros(n); a = np.zeros(n); u = np.zeros(n); r = np.zeros(n)
    for k in range(n):
        tk = k * DT; ar = rf(tk)
        tau = attitude_tau(s, ar, 0.0, g)
        s = attitude_rk4(s, tau, DT)
        t[k], a[k], u[k], r[k] = tk, s[0], tau, ar
    return t, a, u, r


def run_cas_classical(axis):
    g = CAS_GAINS[axis]; sgn = CAS_SIGN[axis]; rf = cas_ref(axis)
    n = int(T_CAS / DT); s = np.zeros(4)
    t = np.zeros(n); p = np.zeros(n); ang = np.zeros(n); u = np.zeros(n)
    r = np.zeros(n); ad = np.zeros(n)
    for k in range(n):
        tk = k * DT; pr = rf(tk)
        tau, a_des = cascade_control(s, pr, g, sgn)
        s = cascade_rk4(s, tau, sgn, DT)
        t[k], p[k], ang[k], u[k], r[k], ad[k] = tk, s[0], s[2], tau, pr, a_des
    return t, p, ang, u, r, ad


# ----------------------------------------------------------------- NEF
def run_att_nef(axis, neuron_type):
    net = build_attitude_net(ATT_GAINS[axis], DT, att_ref(axis),
                             neuron_type=neuron_type, seed=SEED, **ATT_RADII[axis])
    with nengo.Simulator(net, dt=DT, progress_bar=False) as sim:
        sim.run(T_ATT)
    t = sim.trange()
    return t, sim.data[net.p_state][:, 0], sim.data[net.p_u][:, 0], sim.data[net.p_ref][:, 0]


def run_cas_nef(axis, neuron_type):
    net = build_cascade_net(CAS_GAINS[axis], CAS_SIGN[axis], DT, cas_ref(axis),
                            neuron_type=neuron_type, seed=SEED)
    with nengo.Simulator(net, dt=DT, progress_bar=False) as sim:
        sim.run(T_CAS)
    t = sim.trange()
    return (t, sim.data[net.p_state][:, 0], sim.data[net.p_state][:, 2],
            sim.data[net.p_u][:, 0], sim.data[net.p_ref][:, 0], sim.data[net.p_ades][:, 0])


# ----------------------------------------------------------------- run all
print("=== Experiment 02: subsystems (classical vs NEF-LIF) ===")
metrics = {}
att_runs = {}
for axis in ("roll", "pitch", "yaw"):
    g = ATT_GAINS[axis]
    print(f"  attitude {axis}: Kp={g.Kp} Kd={g.Kd} (wn={natural_freq_att(g):.2f}, "
          f"zeta={damping_att(g):.2f})")
    tc, ac, uc, rc = run_att_classical(axis)
    tn, an, un, rn = run_att_nef(axis, nengo.LIF())
    att_runs[axis] = dict(classical=(tc, ac, uc, rc), nef=(tn, an, un, rn))
    tgt = ATT_TARGET[axis]
    mc = step_metrics_general(tc, ac, uc, tgt, T_STEP); mc["stability"] = stability_note(mc)
    mn = step_metrics_general(tn, an, un, tgt, T_STEP); mn["stability"] = stability_note(mn)
    metrics[f"{axis}_classical"] = mc
    metrics[f"{axis}_nef"] = mn

cas_runs = {}
for axis in ("x", "y"):
    print(f"  cascade {axis}: outer {CAS_GAINS[axis]}")
    tc, pc, angc, uc, rc, adc = run_cas_classical(axis)
    tn, pn, angn, un, rn, adn = run_cas_nef(axis, nengo.LIF())
    cas_runs[axis] = dict(classical=(tc, pc, angc, uc, rc, adc),
                          nef=(tn, pn, angn, un, rn, adn))
    tgt = CAS_TARGET[axis]
    mc = step_metrics_general(tc, pc, uc, tgt, T_STEP); mc["stability"] = stability_note(mc)
    mn = step_metrics_general(tn, pn, un, tgt, T_STEP); mn["stability"] = stability_note(mn)
    metrics[f"{axis}pos_classical"] = mc
    metrics[f"{axis}pos_nef"] = mn

# ----------------------------------------------------------------- table + csv
df = pd.DataFrame(metrics).T
df.index.name = "subsystem_controller"
show = ["rise_time_s", "settling_time_s", "overshoot_pct", "sse", "iae", "ise",
        "control_energy", "ctrl_effort", "tracking_rmse"]
pd.set_option("display.width", 170)
pd.set_option("display.float_format", lambda v: f"{v:.4f}")
print("\n=== BENCHMARK METRICS (Phase 3) ===")
print(df[show].to_string())
df.to_csv(RESULTS / "summaries" / "exp02_metrics.csv")

# attitude timeseries csv
La = min(len(att_runs[a]["classical"][0]) for a in att_runs)
ats = pd.DataFrame({"time_s": att_runs["roll"]["classical"][0][:La]})
for axis in att_runs:
    ats[f"{axis}_ref"] = att_runs[axis]["classical"][3][:La]
    ats[f"{axis}_classical"] = att_runs[axis]["classical"][1][:La]
    ats[f"{axis}_nef"] = att_runs[axis]["nef"][1][:La]
ats.to_csv(RESULTS / "csv" / "exp02_attitude_timeseries.csv", index=False)

Lc = min(len(cas_runs[a]["classical"][0]) for a in cas_runs)
cts = pd.DataFrame({"time_s": cas_runs["x"]["classical"][0][:Lc]})
for axis in cas_runs:
    cts[f"{axis}_ref"] = cas_runs[axis]["classical"][4][:Lc]
    cts[f"{axis}_classical"] = cas_runs[axis]["classical"][1][:Lc]
    cts[f"{axis}_nef"] = cas_runs[axis]["nef"][1][:Lc]
cts.to_csv(RESULTS / "csv" / "exp02_cascade_timeseries.csv", index=False)

# ----------------------------------------------------------------- plots
fig, ax = plt.subplots(2, 3, figsize=(13, 6), sharex=True)
for j, axis in enumerate(("roll", "pitch", "yaw")):
    tc, ac, uc, rc = att_runs[axis]["classical"]
    tn, an, un, rn = att_runs[axis]["nef"]
    ax[0, j].plot(tc, np.degrees(rc), "g--", lw=1, label="ref")
    ax[0, j].plot(tc, np.degrees(ac), "k", lw=1.2, label="classical")
    ax[0, j].plot(tn, np.degrees(an), "r", lw=1, alpha=.8, label="NEF")
    ax[0, j].set_title(f"{axis}"); ax[0, j].grid(alpha=.3)
    ax[1, j].plot(tc, uc, "k", lw=1); ax[1, j].plot(tn, un, "r", lw=.8, alpha=.8)
    ax[1, j].grid(alpha=.3); ax[1, j].set_xlabel("t [s]")
ax[0, 0].set_ylabel("angle [deg]"); ax[1, 0].set_ylabel(r"$\tau$ [rad/s$^2$]")
ax[0, 0].legend(loc="lower right", fontsize=8)
fig.suptitle("Exp02 — attitude subsystems: classical vs NEF")
plt.tight_layout(); plt.savefig(RESULTS / "plots" / "exp02_attitude.png", dpi=120)

fig2, ax2 = plt.subplots(2, 2, figsize=(11, 6), sharex=True)
ang_name = {"x": r"$\theta$ (pitch)", "y": r"$\phi$ (roll)"}
for j, axis in enumerate(("x", "y")):
    tc, pc, angc, uc, rc, adc = cas_runs[axis]["classical"]
    tn, pn, angn, un, rn, adn = cas_runs[axis]["nef"]
    ax2[0, j].plot(tc, rc, "g--", lw=1, label="ref")
    ax2[0, j].plot(tc, pc, "k", lw=1.2, label="classical")
    ax2[0, j].plot(tn, pn, "r", lw=1, alpha=.8, label="NEF")
    ax2[0, j].set_title(f"{axis} position"); ax2[0, j].grid(alpha=.3)
    ax2[1, j].plot(tc, np.degrees(adc), "b--", lw=.9, label="a_des (virtual cmd)")
    ax2[1, j].plot(tc, np.degrees(angc), "k", lw=1.1, label="angle classical")
    ax2[1, j].plot(tn, np.degrees(angn), "r", lw=.9, alpha=.8, label="angle NEF")
    ax2[1, j].set_title(ang_name[axis]); ax2[1, j].grid(alpha=.3); ax2[1, j].set_xlabel("t [s]")
ax2[0, 0].set_ylabel("position [m]"); ax2[1, 0].set_ylabel("angle [deg]")
ax2[0, 0].legend(loc="lower right", fontsize=8); ax2[1, 0].legend(loc="upper right", fontsize=7)
fig2.suptitle("Exp02 — position cascades (virtual-command control): classical vs NEF")
plt.tight_layout(); plt.savefig(RESULTS / "plots" / "exp02_cascade.png", dpi=120)

print("\nstability:")
for k in metrics:
    print(f"  {k:18s} {metrics[k]['stability']}")
print("\nsaved: exp02_metrics.csv, exp02_*_timeseries.csv, exp02_attitude.png, exp02_cascade.png")
