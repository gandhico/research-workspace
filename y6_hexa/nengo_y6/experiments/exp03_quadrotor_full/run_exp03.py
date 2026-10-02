"""
run_exp03.py  —  Phase-4 benchmark: FULL quadrotor, classical vs NEF (rate & spiking).

Tracks Victor's combined trajectory (x,y slow sinusoid + z ramp/hold) over 50 s with
the full 12-state model and the cascaded controller, classical vs neuromorphic.

Outputs:
  results/summaries/exp03_quad_metrics.csv
  results/csv/exp03_quad_timeseries.csv   (downsampled to 5 ms)
  results/plots/exp03_quad_tracking.png, exp03_quad_path.png
"""
import sys, pathlib, time
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np, pandas as pd, nengo
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

from src.models.quadrotor import (quad_rk4, X0, x_ref, x_ref_dot, y_ref, y_ref_dot, z_ref)
from src.controllers_classical.quadrotor_pd import QuadGains, quad_control
from src.controllers_nengo.quadrotor_nef import build_network
from src.utils.metrics import tracking_metrics

DT, T_END, T0_METRIC, SEED = 0.001, 50.0, 3.0, 1
K = QuadGains()
RESULTS = ROOT / "results"
for s in ("csv", "summaries", "plots"):
    (RESULTS / s).mkdir(parents=True, exist_ok=True)


def run_classical():
    n = int(T_END / DT); X = X0.copy()
    t = np.arange(n) * DT
    S = np.zeros((n, 12)); U = np.zeros(n)
    for k in range(n):
        tk = t[k]
        refs = (x_ref(tk), x_ref_dot(tk), y_ref(tk), y_ref_dot(tk), z_ref(tk), 0.0)
        u, tp, tt, tph, _, _ = quad_control(X, refs, K)
        X = quad_rk4(X, u, tp, tt, tph, DT)
        S[k] = X; U[k] = u
    return t, S, U


def run_nef(neuron_type, label):
    t0 = time.time()
    net = build_network(DT, K, neuron_type=neuron_type, seed=SEED)
    with nengo.Simulator(net, dt=DT, progress_bar=False) as sim:
        sim.run(T_END)
    print(f"  NEF {label}: {time.time()-t0:.1f}s")
    return sim.trange(), sim.data[net.p_state], sim.data[net.p_u][:, 0]


print("=== Experiment 03: FULL quadrotor — classical vs NEF ===")
runs = {}
print("  classical ..."); t, S, U = run_classical(); runs["classical"] = (t, S, U)
runs["nef_rate"] = run_nef(nengo.RectifiedLinear(), "rate")
runs["nef_spiking"] = run_nef(nengo.LIF(), "LIF spiking")

# reference signals on the classical grid
tg = runs["classical"][0]
ref = dict(x=np.array([x_ref(tt) for tt in tg]),
           y=np.array([y_ref(tt) for tt in tg]),
           z=np.array([z_ref(tt) for tt in tg]))
idx = dict(x=0, y=2, z=4)

# ----- metrics -----
rows = {}
for name, (t, S, U) in runs.items():
    L = min(len(t), len(tg))
    m = {}
    for ax in ("x", "y", "z"):
        tk = tracking_metrics(t[:L], S[:L, idx[ax]], ref[ax][:L], t0=T0_METRIC)
        m[f"{ax}_rmse"] = tk["rmse"]; m[f"{ax}_iae"] = tk["iae"]; m[f"{ax}_maxerr"] = tk["max_abs_err"]
    mask = t[:L] >= T0_METRIC
    m["ctrl_energy_u"] = float(np.trapezoid(U[:L][mask] ** 2, t[:L][mask]))
    m["max_tilt_deg"] = float(np.degrees(np.max(np.abs(S[:L, [8, 10]]))))
    m["stable"] = bool(np.all(np.isfinite(S[-1])) and abs(S[-1, 4]) < 5)
    rows[name] = m

df = pd.DataFrame(rows).T
df.index.name = "controller"
pd.set_option("display.width", 170); pd.set_option("display.float_format", lambda v: f"{v:.4f}")
print("\n=== FULL-QUAD BENCHMARK (tracking, t>3s) ===")
print(df.to_string())
df.to_csv(RESULTS / "summaries" / "exp03_quad_metrics.csv")

# ----- timeseries csv (downsampled 5 ms) -----
step = 5
L = min(len(r[0]) for r in runs.values())
ts = pd.DataFrame({"time_s": tg[:L:step]})
for ax in ("x", "y", "z"):
    ts[f"{ax}_ref"] = ref[ax][:L:step]
for name, (t, S, U) in runs.items():
    for ax in ("x", "y", "z"):
        ts[f"{ax}_{name}"] = S[:L:step, idx[ax]]
    ts[f"u_{name}"] = U[:L:step]
ts.to_csv(RESULTS / "csv" / "exp03_quad_timeseries.csv", index=False)

# ----- plots -----
col = {"classical": "k", "nef_rate": "tab:blue", "nef_spiking": "tab:red"}
lab = {"classical": "classical", "nef_rate": "NEF rate", "nef_spiking": "NEF spiking"}
fig, ax = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
for i, axn in enumerate(("x", "y", "z")):
    ax[i].plot(tg, ref[axn], "g--", lw=1.2, label="reference")
    for name, (t, S, U) in runs.items():
        ax[i].plot(t, S[:, idx[axn]], col[name], lw=1.0, alpha=.85, label=lab[name])
    ax[i].set_ylabel(f"{axn} [m]"); ax[i].grid(alpha=.3)
ax[0].legend(loc="upper right", ncol=4, fontsize=8); ax[2].set_xlabel("time [s]")
ax[0].set_title("Exp03 — full quadrotor trajectory tracking: classical vs NEF")
plt.tight_layout(); plt.savefig(RESULTS / "plots" / "exp03_quad_tracking.png", dpi=120)

fig2, ax2 = plt.subplots(1, 2, figsize=(12, 5))
for name, (t, S, U) in runs.items():
    ax2[0].plot(S[:, 0], S[:, 2], col[name], lw=1.0, alpha=.85, label=lab[name])
    ax2[1].plot(t, U, col[name], lw=.9, alpha=.85, label=lab[name])
ax2[0].plot(ref["x"], ref["y"], "g--", lw=1.2, label="reference")
ax2[0].set_xlabel("x [m]"); ax2[0].set_ylabel("y [m]"); ax2[0].set_title("horizontal path"); ax2[0].grid(alpha=.3); ax2[0].legend(fontsize=8); ax2[0].axis("equal")
ax2[1].axhline(0.9 * 9.81, ls=":", c="g", lw=.8, label="hover")
ax2[1].set_xlabel("time [s]"); ax2[1].set_ylabel("thrust u [N]"); ax2[1].set_title("thrust"); ax2[1].grid(alpha=.3); ax2[1].legend(fontsize=8)
plt.tight_layout(); plt.savefig(RESULTS / "plots" / "exp03_quad_path.png", dpi=120)

print("\nstability:", {k: rows[k]["stable"] for k in rows})
print("saved: exp03_quad_metrics.csv, exp03_quad_timeseries.csv, exp03_quad_tracking.png, exp03_quad_path.png")
