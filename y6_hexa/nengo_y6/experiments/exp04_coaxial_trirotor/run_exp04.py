"""
run_exp04.py  —  Phase-5 benchmark: coaxial Y6 trirotor, classical vs NEF (rate & spiking).

The paper's headline airframe.  Scenario (01_Code default): hover at 1.5 m, then at t=2 s
step to waypoint (1, -0.5, 2.0) m with 20 deg yaw.  The NEF controller adds the new piece —
a **neural control allocator** (4-D command ensemble -> 6 rotor thrusts via the 6x4 mixer).

Outputs:
  results/summaries/exp04_trirotor_metrics.csv
  results/csv/exp04_trirotor_timeseries.csv
  results/plots/exp04_trirotor_tracking.png, exp04_trirotor_rotors.png
"""
import sys, pathlib, time
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np, pandas as pd, nengo
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

from src.models.coaxial_trirotor import (TrirotorParams, rk4_step, IX, IY, IZ, IPHI, ITHE, IPSI)
from src.controllers_classical.trirotor_pd import TrirotorGains, baseline_control

DT, T_END, T_STEP, SEED = 0.001, 12.0, 2.0, 1
P, G = TrirotorParams(), TrirotorGains()
TARGET = dict(x=1.0, y=-0.5, z=2.0, yaw=np.radians(20.0))
RESULTS = ROOT / "results"
for s in ("csv", "summaries", "plots"):
    (RESULTS / s).mkdir(parents=True, exist_ok=True)


def ref_fn(t):
    return (0.0, 0.0, 1.5, 0.0) if t < T_STEP else (TARGET["x"], TARGET["y"], TARGET["z"], TARGET["yaw"])


def run_classical():
    n = int(T_END / DT); s = np.zeros(12)
    t = np.arange(n) * DT; S = np.zeros((n, 12)); OM = np.zeros((n, 6))
    for k in range(n):
        omega, _ = baseline_control(s, ref_fn(t[k]), P, G)
        s = rk4_step(s, omega, np.ones(6), DT, P)
        S[k] = s; OM[k] = omega
    return t, S, OM


N_CMD = 3000   # allocation-ensemble neurons: 3000 cuts steady offset ~6x vs 800 (Phase 5a)


def run_nef(neuron_type, label):
    from src.controllers_nengo.trirotor_nef import build_network
    t0 = time.time()
    net = build_network(DT, G, ref_fn, neuron_type=neuron_type, seed=SEED, n_cmd=N_CMD)
    with nengo.Simulator(net, dt=DT, progress_bar=False) as sim:
        sim.run(T_END)
    print(f"  NEF {label}: {time.time()-t0:.1f}s")
    return sim.trange(), sim.data[net.p_state], sim.data[net.p_omega]


def axis_metrics(t, y, target, t_step, band):
    """Steady RMSE (last 3 s), final error, and settling time (|y-target|<band after step)."""
    steady = t >= (t_end_steady := t[-1] - 3.0)
    rmse = float(np.sqrt(np.mean((y[steady] - target) ** 2)))
    final = float(abs(y[-1] - target))
    post = t >= t_step
    outside = np.abs(y[post] - target) > band
    if not np.any(outside):
        settle = 0.0
    else:
        last = np.where(outside)[0][-1]
        tp = t[post]
        settle = float(tp[last + 1] - t_step) if last + 1 < len(tp) else float("nan")
    return rmse, final, settle


print("=== Experiment 04: coaxial Y6 trirotor — classical vs NEF ===")
runs = {}
print("  classical ..."); runs["classical"] = run_classical()
runs["nef_rate"] = run_nef(nengo.RectifiedLinear(), "rate")
runs["nef_spiking"] = run_nef(nengo.LIF(), "LIF spiking")

axinfo = dict(x=(IX, 0.03), y=(IY, 0.03), z=(IZ, 0.03), yaw=(IPSI, np.radians(1.0)))
rows = {}
for name, (t, S, OM) in runs.items():
    m = {}
    for ax, (idx, band) in axinfo.items():
        tgt = TARGET[ax] if ax != "yaw" else TARGET["yaw"]
        rmse, final, settle = axis_metrics(t, S[:, idx], tgt, T_STEP, band)
        unit = 1.0 if ax != "yaw" else 1.0
        m[f"{ax}_rmse"] = rmse; m[f"{ax}_finalerr"] = final
        if ax == "z":
            m["settle_z_s"] = settle
    # combined settling (||pos-target||<5cm); NaN if it never settles within 5 cm
    perr = np.sqrt((S[:, IX] - TARGET["x"]) ** 2 + (S[:, IY] - TARGET["y"]) ** 2 + (S[:, IZ] - TARGET["z"]) ** 2)
    post = t >= T_STEP; tp = t[post]; outside = perr[post] > 0.05
    if not np.any(outside):
        m["settle_pos_s"] = 0.0
    else:
        last = int(np.where(outside)[0][-1])
        m["settle_pos_s"] = float(tp[last + 1] - T_STEP) if last + 1 < len(tp) else float("nan")
    m["ctrl_energy"] = float(np.trapezoid(np.sum(OM ** 2, axis=1), t))
    m["max_tilt_deg"] = float(np.degrees(np.max(np.abs(S[:, [IPHI, ITHE]]))))
    m["stable"] = bool(np.all(np.isfinite(S[-1])) and abs(S[-1, IZ] - TARGET["z"]) < 0.2)
    rows[name] = m

df = pd.DataFrame(rows).T; df.index.name = "controller"
pd.set_option("display.width", 200); pd.set_option("display.float_format", lambda v: f"{v:.4f}")
show = ["x_rmse", "y_rmse", "z_rmse", "yaw_rmse", "x_finalerr", "y_finalerr", "z_finalerr",
        "settle_pos_s", "ctrl_energy", "max_tilt_deg", "stable"]
print("\n=== TRIROTOR BENCHMARK (steady RMSE / final err / settling) ===")
print(df[show].to_string())
df.to_csv(RESULTS / "summaries" / "exp04_trirotor_metrics.csv")

# timeseries csv (downsample 5 ms)
step = 5; L = min(len(r[0]) for r in runs.values())
ts = pd.DataFrame({"time_s": runs["classical"][0][:L:step]})
for ax, (idx, _) in axinfo.items():
    ts[f"{ax}_target"] = [(TARGET[ax] if tt >= T_STEP else (0.0 if ax != "z" else 1.5))
                          for tt in runs["classical"][0][:L:step]]
for name, (t, S, OM) in runs.items():
    for ax, (idx, _) in axinfo.items():
        ts[f"{ax}_{name}"] = S[:L:step, idx]
ts.to_csv(RESULTS / "csv" / "exp04_trirotor_timeseries.csv", index=False)

# ---- plots ----
col = {"classical": "k", "nef_rate": "tab:blue", "nef_spiking": "tab:red"}
lab = {"classical": "classical", "nef_rate": "NEF rate", "nef_spiking": "NEF spiking"}
fig, ax = plt.subplots(2, 2, figsize=(12, 7))
panels = [("x", ax[0, 0], 1.0, "x [m]"), ("y", ax[0, 1], 1.0, "y [m]"),
          ("z", ax[1, 0], 1.0, "z [m]"), ("yaw", ax[1, 1], 180 / np.pi, "yaw [deg]")]
for axn, a, scl, ylab in panels:
    idx = axinfo[axn][0]
    tgt_line = [( (TARGET[axn] if tt >= T_STEP else (0.0 if axn != "z" else 1.5)) ) * scl
                for tt in runs["classical"][0]]
    a.plot(runs["classical"][0], tgt_line, "g--", lw=1.1, label="reference")
    for name, (t, S, OM) in runs.items():
        a.plot(t, S[:, idx] * scl, col[name], lw=1.0, alpha=.85, label=lab[name])
    a.set_ylabel(ylab); a.grid(alpha=.3); a.set_xlabel("t [s]")
ax[0, 0].legend(loc="lower right", fontsize=8)
fig.suptitle("Exp04 — coaxial Y6 trirotor: classical vs NEF (waypoint + yaw)")
plt.tight_layout(); plt.savefig(RESULTS / "plots" / "exp04_trirotor_tracking.png", dpi=120)

# rotor speeds (classical vs NEF spiking) — shows the 6 coaxial rotors
fig2, ax2 = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True)
for a, name in zip(ax2, ("classical", "nef_spiking")):
    t, S, OM = runs[name]
    for j in range(6):
        a.plot(t, OM[:, j], lw=.8, label=f"rotor {j+1}")
    a.axhline(P.omega_max, ls="--", c="r", lw=.6)
    a.set_title(f"rotor speeds — {lab[name]}"); a.set_xlabel("t [s]"); a.grid(alpha=.3)
ax2[0].set_ylabel(r"$\omega$ [rad/s]"); ax2[0].legend(ncol=3, fontsize=7, loc="upper right")
fig2.suptitle("Exp04 — 6 coaxial rotor speeds (3 top + 3 bottom)")
plt.tight_layout(); plt.savefig(RESULTS / "plots" / "exp04_trirotor_rotors.png", dpi=120)

print("\nstability:", {k: rows[k]["stable"] for k in rows})
print("saved: exp04_trirotor_metrics.csv, exp04_trirotor_timeseries.csv, "
      "exp04_trirotor_tracking.png, exp04_trirotor_rotors.png")
