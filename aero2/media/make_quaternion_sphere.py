"""Aero2 attitude as a trajectory on the orientation sphere (quaternion / SLERP view).

The body pointing direction d(theta,psi) = (cos th cos ps, cos th sin ps, sin th)
lives on the unit 2-sphere S^2 (the physically drawable projection of the unit
quaternion on S^3). Mapping:
    yaw  psi -> LONGITUDE  (continuous, slip-ring -> wraps all the way around)
    pitch th -> LATITUDE   (z = sin th; mechanically bounded to +/-60 deg band)
Shortest-path (quaternion / SLERP) control follows great-circle geodesics, which
is why the yaw error is naturally wrap-aware.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Line3DCollection

d2r = np.pi/180
PITCH_LIMIT = 60.0            # deg, mechanical band (|latitude| <= 60)

def dir_vec(th, ps):          # body pointing direction on S^2
    return np.array([np.cos(th)*np.cos(ps), np.cos(th)*np.sin(ps), np.sin(th)])

fig = plt.figure(figsize=(9.2, 8.4))
ax = fig.add_subplot(111, projection="3d")

# --- translucent sphere -----------------------------------------------------
u = np.linspace(0, 2*np.pi, 80); v = np.linspace(0, np.pi, 60)
xs = np.outer(np.cos(u), np.sin(v)); ys = np.outer(np.sin(u), np.sin(v)); zs = np.outer(np.ones_like(u), np.cos(v))
ax.plot_surface(xs, ys, zs, color="#bcd3e6", alpha=0.12, linewidth=0, zorder=0)

# graticule (meridians every 30 deg long, parallels every 30 deg lat)
for lon in range(0, 360, 30):
    th = np.linspace(-np.pi/2, np.pi/2, 60); ps = np.full_like(th, lon*d2r)
    P = dir_vec(th, ps); ax.plot(*P, color="0.7", lw=0.4, zorder=1)
for lat in range(-60, 61, 30):
    ps = np.linspace(0, 2*np.pi, 90); th = np.full_like(ps, lat*d2r)
    P = dir_vec(th, ps); ax.plot(*P, color="0.7", lw=0.4, zorder=1)

# --- forbidden pitch caps ( |lat| > 60 deg ) --------------------------------
for sgn in (+1, -1):
    vv = np.linspace(0, (90-PITCH_LIMIT)*d2r, 20)      # polar angle from the pole
    uu = np.linspace(0, 2*np.pi, 80)
    cx = np.outer(np.cos(uu), np.sin(vv)); cy = np.outer(np.sin(uu), np.sin(vv))
    cz = sgn*np.outer(np.ones_like(uu), np.cos(vv))
    ax.plot_surface(1.003*cx, 1.003*cy, 1.003*cz, color="#d62728", alpha=0.20, linewidth=0, zorder=2)
# boundary circles of the forbidden band
for sgn in (+1,-1):
    ps=np.linspace(0,2*np.pi,120); th=np.full_like(ps, sgn*PITCH_LIMIT*d2r)
    ax.plot(*dir_vec(th,ps), color="#d62728", lw=1.4, ls="--", zorder=3)

# --- equator = yaw circle (continuous) --------------------------------------
ps=np.linspace(0,2*np.pi,160); ax.plot(*dir_vec(np.zeros_like(ps),ps), color="#1a1a1a", lw=2.0, zorder=3)

# --- trajectory: yaw sweeps a full turn, pitch oscillates within the band ----
t = np.linspace(0, 1, 700)
psi = (-200 + 400*t)*d2r                    # -200 deg -> +200 deg (wraps past +/-180)
theta = (42*np.sin(2*np.pi*2.0*t))*d2r      # +/-42 deg pitch oscillation
P = dir_vec(theta, psi)                      # 3 x N
pts = P.T.reshape(-1,1,3); segs = np.concatenate([pts[:-1], pts[1:]], axis=1)
lc = Line3DCollection(segs, cmap="viridis", array=t[:-1], linewidth=3.2, zorder=5)
ax.add_collection3d(lc)
ax.scatter(*P[:,0], color="k", s=40, zorder=6); ax.text(*(1.12*P[:,0]), "start", fontsize=8)
ax.scatter(*P[:,-1], color="k", s=40, marker="s", zorder=6); ax.text(*(1.12*P[:,-1]), "end", fontsize=8)
# body-axis arrows at a few instants
for k in np.linspace(0, len(t)-1, 6).astype(int):
    ax.quiver(0,0,0, *P[:,k], color="0.35", lw=1.0, arrow_length_ratio=0.06, zorder=4)

# --- shortest-path (quaternion SLERP) vs naive long-way, near the +/-180 seam -
a = dir_vec(15*d2r, 168*d2r); b = dir_vec(15*d2r, -168*d2r)
def great_circle(a, b, phis):
    a=a/np.linalg.norm(a); n=b-np.dot(a,b)*a; n=n/np.linalg.norm(n)
    return np.array([np.cos(p)*a+np.sin(p)*n for p in phis]).T
Om = np.arccos(np.clip(np.dot(a,b),-1,1))
short = great_circle(a,b, np.linspace(0,Om,40)); long = great_circle(a,b, np.linspace(0,-(2*np.pi-Om),160))
ax.plot(*(1.01*long), color="0.55", lw=1.6, ls=":", zorder=6)
ax.plot(*(1.02*short), color="#2ca02c", lw=3.4, zorder=7)
ax.scatter(*a, color="#2ca02c", s=55, marker="*", zorder=8); ax.text(*(1.15*a), "$q_{ref}$", fontsize=9)
ax.scatter(*b, color="#2ca02c", s=55, marker="*", zorder=8); ax.text(*(1.15*b), "$q$", fontsize=9)

# --- labels / cosmetics (2D corners, no overlap with the sphere) ------------
ax.text2D(0.015, 0.95, "pitch $\\theta$ = latitude  ($\\pm$%d$^\\circ$ mechanical band, red caps)"%PITCH_LIMIT,
          transform=ax.transAxes, fontsize=9.5, color="#d62728")
ax.text2D(0.015, 0.05, "yaw $\\psi$ = longitude  (continuous, slip-ring $\\Rightarrow$ wraps around)",
          transform=ax.transAxes, fontsize=9.5, color="#1a1a1a")
ax.text2D(0.60, 0.95, "— shortest path (quaternion / SLERP)", transform=ax.transAxes, fontsize=9, color="#2ca02c")
ax.text2D(0.60, 0.915, "$\\cdots$ naïve yaw error (long way)", transform=ax.transAxes, fontsize=9, color="0.5")

ax.set_box_aspect([1,1,1]); lim=0.98
ax.set_xlim(-lim,lim); ax.set_ylim(-lim,lim); ax.set_zlim(-lim,lim)
ax.set_axis_off(); ax.view_init(elev=22, azim=48)
fig.suptitle("Aero2 attitude on the orientation sphere — pitch$\\times$yaw as a quaternion trajectory",
             y=0.93, fontsize=12)
# colorbar for time
cb = fig.colorbar(lc, ax=ax, shrink=0.5, pad=0.02); cb.set_label("normalized time")
fig.tight_layout()
out = r"C:\Research\aero2\results_paper\figures\fig_quaternion_sphere.png"
fig.savefig(out, dpi=210, bbox_inches="tight"); print("SAVED", out)
