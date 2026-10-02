"""
run_exp01.py  —  Phase-2 benchmark: classical PD vs. NEF (spiking & rate)
on the 1-DOF altitude plant.

Outputs (all numbers come from runs executed here — nothing illustrative):
  results/csv/exp01_altitude_timeseries.csv   z & u traces for each controller
  results/summaries/exp01_metrics.csv         the benchmark table
  results/plots/exp01_altitude.png            altitude + thrust comparison

Run:  python experiments/exp01_altitude_1dof/run_exp01.py
"""
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]   # ...\02_..._Paper_Development
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import nengo
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.models.altitude_1dof import AltitudeParams, rk4_step, step_reference
from src.controllers_classical.altitude_pd import (
    AltitudeGains, classical_thrust, natural_freq, damping_ratio)
from src.controllers_nengo.altitude_nef import build_network
from src.utils.metrics import step_metrics, stability_note

# ---------------------------------------------------------------- config
P = AltitudeParams()
G = AltitudeGains()
DT = 0.001          # s   (shared by classical RK4 and the Nengo simulator)
T_END = 10.0        # s
T_STEP = 1.0        # s   step instant
Z_TARGET = 1.0      # m   step height
SEED = 1

RESULTS = ROOT / "results"
(RESULTS / "csv").mkdir(parents=True, exist_ok=True)
(RESULTS / "summaries").mkdir(parents=True, exist_ok=True)
(RESULTS / "plots").mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------- runs
def run_classical():
    n = int(T_END / DT)
    state = np.array([0.0, 0.0])
    t = np.zeros(n); z = np.zeros(n); u = np.zeros(n); r = np.zeros(n)
    for k in range(n):
        tk = k * DT
        zref = step_reference(tk, T_STEP, Z_TARGET)
        uc = classical_thrust(state, zref, 0.0, P, G)
        state = rk4_step(state, uc, DT, P)
        t[k], z[k], u[k], r[k] = tk, state[0], uc, zref
    return t, z, u, r


def run_nef(neuron_type):
    net = build_network(P, G, DT, T_STEP, Z_TARGET,
                        neuron_type=neuron_type, seed=SEED)
    with nengo.Simulator(net, dt=DT, progress_bar=False) as sim:
        sim.run(T_END)
    t = sim.trange()
    z = sim.data[net.p_state][:, 0]
    u = sim.data[net.p_u][:, 0]
    r = sim.data[net.p_ref][:, 0]
    return t, z, u, r


print("=== Experiment 01: 1-DOF altitude — classical vs NEF ===")
print(f"plant: m={P.m} kg, g={P.g} m/s^2, u_hover={P.u_hover:.3f} N, "
      f"u_max={P.u_max:.3f} N")
print(f"gains: Kp={G.Kp}, Kd={G.Kd}  ->  omega_n={natural_freq(P,G):.3f} rad/s, "
      f"zeta={damping_ratio(P,G):.3f}")
print(f"step:  {Z_TARGET} m at t={T_STEP}s,  dt={DT}s,  T={T_END}s\n")

runs = {}
print("running classical ...");      runs["classical"]   = run_classical()
print("running NEF (LIF spiking)..."); runs["nef_spiking"] = run_nef(nengo.LIF())
print("running NEF (rate) ...");      runs["nef_rate"]    = run_nef(nengo.RectifiedLinear())

# ---------------------------------------------------------------- metrics
metrics = {}
for name, (t, z, u, r) in runs.items():
    md = step_metrics(t, z, u, Z_TARGET, T_STEP, P)
    md["stability"] = stability_note(md)
    metrics[name] = md

df = pd.DataFrame(metrics).T
df.index.name = "controller"

# pretty console table
show_cols = ["rise_time_s", "settling_time_s", "overshoot_pct", "sse_m",
             "iae", "ise", "control_energy", "ctrl_effort_beyond_hover",
             "saturation_pct", "tracking_rmse_m"]
pd.set_option("display.width", 160)
pd.set_option("display.float_format", lambda v: f"{v:.4f}")
print("\n=== BENCHMARK METRICS ===")
print(df[show_cols].to_string())
print("\nstability:")
for name in metrics:
    print(f"  {name:12s} {metrics[name]['stability']}")

# ---------------------------------------------------------------- save CSVs
df.to_csv(RESULTS / "summaries" / "exp01_metrics.csv")

L = min(len(v[0]) for v in runs.values())
ts = pd.DataFrame({"time_s": runs["classical"][0][:L],
                   "z_ref_m": runs["classical"][3][:L]})
for name, (t, z, u, r) in runs.items():
    ts[f"z_{name}_m"] = z[:L]
    ts[f"u_{name}_N"] = u[:L]
ts.to_csv(RESULTS / "csv" / "exp01_altitude_timeseries.csv", index=False)

# ---------------------------------------------------------------- plot
fig, ax = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
colors = {"classical": "k", "nef_spiking": "tab:red", "nef_rate": "tab:blue"}
labels = {"classical": "classical PD", "nef_spiking": "NEF (LIF spiking)",
          "nef_rate": "NEF (rate)"}
for name, (t, z, u, r) in runs.items():
    ax[0].plot(t, z, color=colors[name], lw=1.2, label=labels[name],
               alpha=0.9 if name != "classical" else 1.0)
    ax[1].plot(t, u, color=colors[name], lw=1.0, alpha=0.8)
ax[0].plot(runs["classical"][0], runs["classical"][3], "g--", lw=1.0, label="reference")
ax[0].set_ylabel("altitude z [m]"); ax[0].legend(loc="lower right"); ax[0].grid(alpha=.3)
ax[0].set_title("Exp01 — 1-DOF altitude: classical PD vs NEF")
ax[1].axhline(P.u_hover, ls=":", c="g", lw=.8, label="hover")
ax[1].axhline(P.u_max, ls="--", c="r", lw=.6)
ax[1].set_ylabel("thrust u [N]"); ax[1].set_xlabel("time [s]"); ax[1].grid(alpha=.3)
ax[1].legend(loc="upper right")
plt.tight_layout()
plt.savefig(RESULTS / "plots" / "exp01_altitude.png", dpi=120)
print(f"\nsaved: {RESULTS/'plots'/'exp01_altitude.png'}")
print(f"saved: {RESULTS/'summaries'/'exp01_metrics.csv'}")
print(f"saved: {RESULTS/'csv'/'exp01_altitude_timeseries.csv'}")
