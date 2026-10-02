"""make_figures.py -- figures + summary.json from results/*.npz (all numbers traceable)."""
import json, pathlib
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent
R, OUT = HERE / "results", HERE / "media" / "figs"
OUT.mkdir(parents=True, exist_ok=True)
C_CLS, C_NEF, C_REF = "#2a78d6", "#eb6834", "#8a8a86"
plt.rcParams.update({"font.family": "Tahoma", "font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.color": "#e6e6e3",
                     "grid.linewidth": 0.8, "axes.edgecolor": "#8a8a86", "lines.linewidth": 2})


def load(tag):
    return dict(np.load(R / f"{tag}.npz"))


def metrics(D):
    t, S, ref, yaw = D["t"], D["state"], D["ref_pos"], D["ref_yaw"]
    fly = (t > 6.0) & (t < 56.0)
    e = S[:, :3] - ref
    return dict(
        rmse_cm=[round(float(v)*100, 2) for v in np.sqrt(np.mean(e[fly]**2, axis=0))],
        max_err_cm=round(float(np.max(np.linalg.norm(e[fly], axis=1)))*100, 2),
        yaw_rmse_deg=round(float(np.degrees(np.sqrt(np.mean((S[fly, 8]-yaw[fly])**2)))), 3),
        max_tilt_deg=round(float(np.degrees(np.max(np.hypot(S[:, 6], S[:, 7])))), 2),
        omega_min=round(float(D["omega"][t > 3].min()), 1),
        omega_max=round(float(D["omega"][t > 3].max()), 1),
        wall_s=round(float(D["wall"]), 1) if "wall" in D else None,
        sim_s=round(float(t[-1]), 1))


tags = ["classical", "nef_lif", "classical_wind4", "nef_lif_wind4",
        "classical_wind4_int", "nef_lif_wind4_int"]
runs = {k: load(k) for k in tags if (R / f"{k}.npz").exists()}
summary = {k: metrics(v) for k, v in runs.items()}
V = dict(np.load(R / "validate_mj_vs_rk4.npz"))
dpos = V["S_mj"][:, :3] - V["S_rk"][:, :3]
summary["validation_mujoco_vs_rk4"] = dict(
    max_dpos_mm=round(float(np.abs(dpos).max())*1000, 3),
    rms_dpos_mm=round(float(np.sqrt(np.mean(dpos**2)))*1000, 4),
    max_dyaw_deg=round(float(np.degrees(np.abs(V["S_mj"][:, 8]-V["S_rk"][:, 8]).max())), 5))
(R / "summary.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))

C, N = runs["classical"], runs["nef_lif"]
t = C["t"]

# ---- 1. mission geometry: top + side view -------------------------------------------
fig, ax = plt.subplots(1, 2, figsize=(12, 4.6))
for a, (i, j, lab) in zip(ax, [(0, 1, "y [m]"), (0, 2, "z [m]")]):
    a.plot(C["ref_pos"][:, i], C["ref_pos"][:, j], "--", color=C_REF, lw=1.5, label="reference")
    a.plot(C["state"][:, i], C["state"][:, j], color=C_CLS, label="classical PD")
    a.plot(N["state"][:, i], N["state"][:, j], color=C_NEF, lw=1.5, label="spiking NEF (LIF)")
    a.set_xlabel("x [m]"); a.set_ylabel(lab); a.set_aspect("equal")
ax[0].plot([11.28, 11.28], [-3.7, 3.7], color="#333", lw=4, solid_capstyle="round")
ax[0].plot(12, 0, "s", color="#333", ms=9); ax[0].text(11.6, 4.0, "rotor disc", fontsize=10)
th = np.linspace(0, 2*np.pi, 100)
ax[1].plot([12, 12], [0, 8], color="#333", lw=4)
ax[1].plot(11.28 + 0*th, 8 + 3.7*np.sin(th), color="#333", lw=4)
ax[1].text(12.3, 1, "tower", fontsize=10)
ax[0].set_title("Top view", loc="left"); ax[1].set_title("Side view", loc="left")
ax[0].legend(loc="lower left", frameon=False, fontsize=10)
fig.tight_layout(); fig.savefig(OUT / "fig1_mission_geometry.png", dpi=160); plt.close(fig)

# ---- 2. tracking -------------------------------------------------------------------
fig, ax = plt.subplots(4, 1, figsize=(11, 8.4), sharex=True)
names = ["x [m]", "y [m]", "z [m]", "yaw [deg]"]
for k, a in enumerate(ax):
    if k < 3:
        r, c, n = C["ref_pos"][:, k], C["state"][:, k], N["state"][:, k]
    else:
        r, c, n = (np.degrees(C["ref_yaw"]), np.degrees(C["state"][:, 8]), np.degrees(N["state"][:, 8]))
    a.plot(t, r, "--", color=C_REF, lw=1.5, label="reference")
    a.plot(t, c, color=C_CLS, label="classical PD")
    a.plot(N["t"], n, color=C_NEF, lw=1.5, label="spiking NEF (LIF)")
    a.set_ylabel(names[k])
ax[0].legend(ncol=3, loc="upper left", frameon=False, fontsize=10)
ax[-1].set_xlabel("time [s]")
fig.suptitle("Inspection mission in MuJoCo - same controllers as the Nengo paper code", x=0.01, ha="left")
fig.tight_layout(); fig.savefig(OUT / "fig2_tracking.png", dpi=160); plt.close(fig)

# ---- 3. wind: PD vs PID, per controller (small multiples) --------------------------
fig, ax = plt.subplots(1, 2, figsize=(12, 3.8), sharey=True)
for a, base, title in zip(ax, ["classical", "nef_lif"], ["Classical cascade", "Spiking NEF (LIF)"]):
    for tag, col, lab in [(f"{base}_wind4", C_CLS, "PD (as in paper code)"),
                          (f"{base}_wind4_int", C_NEF, "PD + outer integral")]:
        D = runs[tag]
        a.plot(D["t"], np.linalg.norm(D["state"][:, :3]-D["ref_pos"], axis=1)*100, color=col, lw=1.5, label=lab)
    a.set_title(f"{title}  -  4 m/s wind + gusts", loc="left"); a.set_xlabel("time [s]")
ax[0].set_ylabel("|position error| [cm]"); ax[0].legend(frameon=False, fontsize=10)
fig.tight_layout(); fig.savefig(OUT / "fig3_wind.png", dpi=160); plt.close(fig)

# ---- 4. validation MuJoCo vs RK4 -----------------------------------------------------
fig, a = plt.subplots(figsize=(11, 3.2))
a.plot(V["t"], np.linalg.norm(dpos, axis=1)*1000, color=C_CLS, lw=1.5)
a.set_xlabel("time [s]"); a.set_ylabel("|p_MuJoCo - p_RK4| [mm]")
a.set_title("Plant cross-check: same classical controller, MuJoCo body vs Nengo-project RK4 model", loc="left")
fig.tight_layout(); fig.savefig(OUT / "fig4_validation.png", dpi=160); plt.close(fig)

# ---- 5. rotor speeds -----------------------------------------------------------------
fig, ax = plt.subplots(1, 2, figsize=(12, 3.6), sharey=True)
for a, D, title in zip(ax, [C, N], ["Classical PD", "Spiking NEF (LIF) + neural allocator"]):
    for i in range(6):
        a.plot(D["t"], D["omega"][:, i], lw=1, color=C_CLS if i % 2 == 0 else C_NEF,
               label=("top rotors 1,3,5" if i == 0 else "bottom rotors 2,4,6" if i == 1 else None))
    a.axhline(900, color="#333", lw=1, ls=":"); a.set_title(title, loc="left"); a.set_xlabel("time [s]")
ax[0].set_ylabel("rotor speed [rad/s]"); ax[0].legend(frameon=False, fontsize=10, loc="lower right")
ax[0].set_ylim(0, 950)
fig.tight_layout(); fig.savefig(OUT / "fig5_rotors.png", dpi=160); plt.close(fig)
print("figures ->", OUT)
