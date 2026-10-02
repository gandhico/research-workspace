"""
make_media.py  --  composite video, figures and summary for the heterogeneous race.

  media/race_events_grid.mp4     2x2 grid of [FPV RGB | DVS events] for X2, Y6, CF2, Omnicopter
  media/race_overview.mp4        spectator view of the whole fleet (ghost race)
  media/figs/fig_track.png       top + side view: racing line, gates, flown paths
  media/figs/fig_tracking.png    tracking error vs time per vehicle, gate passes marked
  media/figs/fig_event_rate.png  DVS event rate per vehicle (10 ms bins), gate passes marked
  media/figs/fig_event_snapshots.png   RGB vs 10-ms event frame at a gate for each vehicle
  results/summary.json           race + event statistics (all numbers used in the deck)
"""
import json, pathlib
import numpy as np
import mujoco
import imageio.v2 as imageio
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

import build_scene, track
from event_camera import event_frame, EVENT_DTYPE

HERE = pathlib.Path(__file__).resolve().parent
R, MED, FIG = HERE / "results", HERE / "media", HERE / "media" / "figs"
FIG.mkdir(parents=True, exist_ok=True)
FLEET = ["x2", "y6", "cf2", "omni"]
NAMES = {"x2": "Skydio X2", "cf2": "Crazyflie 2", "omni": "Omnicopter", "y6": "Coaxial Y6"}
COL = {"x2": "#2a78d6", "y6": "#eb6834", "cf2": "#1baf7a", "omni": "#4a3aa7"}   # validated categorical order
plt.rcParams.update({"font.family": "Tahoma", "font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.color": "#e6e6e3",
                     "lines.linewidth": 2})


def grid_video():
    readers = [imageio.get_reader(MED / f"events_{p}.mp4") for p in FLEET]
    out = imageio.get_writer(MED / "race_events_grid.mp4", fps=30, codec="libx264", quality=7, macro_block_size=2)
    blank = None
    iters = [iter(r) for r in readers]
    n = 0
    while True:
        frames, alive = [], False
        for it in iters:
            try:
                f = next(it); alive = True
            except StopIteration:
                f = None
            frames.append(f)
        if not alive:
            break
        if blank is None:
            blank = np.zeros_like(next(f for f in frames if f is not None))
        frames = [f if f is not None else blank for f in frames]
        out.append_data(np.vstack([np.hstack(frames[:2]), np.hstack(frames[2:])]))
        n += 1
    out.close()
    return n


def overview_video(D, fps=30):
    spec, m = build_scene.build(out=HERE / "models" / "_render_overview.xml")
    d = mujoco.MjData(m)
    r = mujoco.Renderer(m, 720, 1280)
    cam = mujoco.MjvCamera(); cam.lookat[:] = [0, 0, 2.5]; cam.distance = 38; cam.azimuth = -60; cam.elevation = -32
    T, Q = D["t"], D["qpos"]
    out = imageio.get_writer(MED / "race_overview.mp4", fps=fps, codec="libx264", quality=7, macro_block_size=2)
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 22)
    for tt in np.arange(0, T[-1], 1/fps):
        k = np.searchsorted(T, tt)
        d.qpos[:] = Q[min(k, len(Q) - 1)]; mujoco.mj_forward(m, d)
        r.update_scene(d, camera=cam)
        im = Image.fromarray(r.render()); dr = ImageDraw.Draw(im)
        dr.text((20, 16), f"Heterogeneous ghost race  t = {tt:5.1f} s   X2 | Y6 | CF2 | Omnicopter", font=font,
                fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))
        out.append_data(np.asarray(im))
    out.close()
    # hero still at a moment when all four are airborne and spread out
    tt = 16.0
    d.qpos[:] = Q[np.searchsorted(T, tt)]; mujoco.mj_forward(m, d)
    cam.distance = 30; r.update_scene(d, camera=cam); Image.fromarray(r.render()).save(MED / "race_hero.png")


def figures(D, S):
    line = track.RaceLine()
    s = np.linspace(0, line.length, 3000); P, _, _ = line.geom(s)
    fig, ax = plt.subplots(1, 2, figsize=(13, 5.2), gridspec_kw=dict(width_ratios=[1.1, 1]))
    ax[0].plot(P[:, 0], P[:, 1], "--", color="#8a8a86", lw=1.4, label="racing line")
    ax[1].plot(P[:, 0], P[:, 2], "--", color="#8a8a86", lw=1.4)
    for p in FLEET:
        X = D[f"{p}_p"]
        ax[0].plot(X[:, 0], X[:, 1], color=COL[p], lw=1.3, label=NAMES[p])
        ax[1].plot(X[:, 0], X[:, 2], color=COL[p], lw=1.1)
    h = track.GATE_INNER/2
    for i, (name, c, yaw) in enumerate(track.GATES):
        n = track.gate_normal(yaw); t = np.cross([0, 0, 1], n)
        a, b = np.array(c) - (h + 0.2)*t, np.array(c) + (h + 0.2)*t
        ax[0].plot([a[0], b[0]], [a[1], b[1]], color="#1f1f1f", lw=4, solid_capstyle="butt")
        ax[0].annotate(name.split()[0], (c[0], c[1]), xytext=(6, 6), textcoords="offset points", fontsize=9)
        ax[1].plot([c[0], c[0]], [c[2] - h - 0.2, c[2] + h + 0.2], color="#1f1f1f", lw=4)
    ax[0].set_aspect("equal"); ax[0].set_xlabel("x [m]"); ax[0].set_ylabel("y [m]")
    ax[1].set_xlabel("x [m]"); ax[1].set_ylabel("z [m]")
    ax[0].set_title("Top view", loc="left"); ax[1].set_title("Side view (Split-S = G4 over G5)", loc="left")
    ax[0].legend(loc="upper left", frameon=False, fontsize=9, ncol=2)
    fig.tight_layout(); fig.savefig(FIG / "fig_track.png", dpi=160); plt.close(fig)

    fig, axs = plt.subplots(4, 1, figsize=(12, 8.4), sharex=True)
    for a, p in zip(axs, FLEET):
        t, e = D[f"{p}_t"], np.linalg.norm(D[f"{p}_p"] - D[f"{p}_pref"], axis=1)*100
        a.plot(t, e, color=COL[p], lw=1.2)
        for ps in S[p]["passes"]:
            if ps["in_order"]:
                a.axvline(ps["t"], color="#8a8a86", lw=0.6)
        a.set_ylabel("|e| [cm]"); a.set_title(f"{NAMES[p]}  -  RMSE {S[p]['track_rmse_cm']} cm, "
                                               f"{S[p]['gates_passed_in_order']}/{S[p]['gates_expected']} gates", loc="left", fontsize=11)
        a.set_ylim(0, max(10, np.percentile(e[t > 5], 99.5)*1.2))
    axs[-1].set_xlabel("time [s]  (grey lines: gate passes)")
    fig.tight_layout(); fig.savefig(FIG / "fig_tracking.png", dpi=160); plt.close(fig)

    fig, axs = plt.subplots(4, 1, figsize=(12, 8.4), sharex=True)
    for a, p in zip(axs, FLEET):
        E = np.load(R / f"events_{p}.npz")
        a.plot(E["rate_t"], E["rate_ev_per_10ms"]/0.01/1e6, color=COL[p], lw=0.9)
        for ps in S[p]["passes"]:
            if ps["in_order"]:
                a.axvline(ps["t"], color="#8a8a86", lw=0.6)
        a.set_ylabel("Mev/s"); a.set_title(NAMES[p], loc="left", fontsize=11)
    axs[-1].set_xlabel("time [s]  (10 ms bins; grey lines: gate passes)")
    fig.tight_layout(); fig.savefig(FIG / "fig_event_rate.png", dpi=160); plt.close(fig)


def snapshots(D, S):
    """RGB vs 10-ms event frame when each vehicle is 3.0 m from G2 (first approach): same
    geometry for every airframe, independent of its speed."""
    spec, m = build_scene.build(out=HERE / "models" / "_render_snap.xml")
    d = mujoco.MjData(m); rr = mujoco.Renderer(m, 260, 346)
    T, Q = D["t"], D["qpos"]
    fig, axs = plt.subplots(2, 4, figsize=(15, 5.6))
    for j, p in enumerate(FLEET):
        g2 = [ps["t"] for ps in S[p]["passes"] if ps["gate"] == 2 and ps["in_order"]]
        tv, Pv = D[f"{p}_t"], D[f"{p}_p"]
        dist = np.linalg.norm(Pv - np.array(track.GATES[1][1]), axis=1)
        k = np.nonzero((tv < g2[0]) & (dist <= 3.0))[0][0]
        tt = float(tv[k])
        d.qpos[:] = Q[np.searchsorted(T, tt)]; mujoco.mj_forward(m, d)
        rr.update_scene(d, camera=f"{p}/dvs"); rgb = rr.render()
        allev = np.memmap(R / f"events_{p}.bin", dtype=EVENT_DTYPE, mode="r")    # time-ordered
        t_us = int(tt*1e6)
        i0, i1 = np.searchsorted(allev["t"], [t_us - 10_000, t_us])
        ev = np.array(allev[i0:i1])
        ef = event_frame(ev, 346, 260, t_us - 10_000, t_us)
        nwin = int(((ev["t"] >= t_us - 10_000) & (ev["t"] < t_us)).sum())
        axs[0, j].imshow(rgb); axs[1, j].imshow(ef)
        axs[0, j].set_title(f"{NAMES[p]}  t = {tt:.2f} s, 3 m to G2", loc="left", fontsize=11)
        axs[1, j].set_title(f"DVS, 10 ms window: {nwin:,} events", loc="left", fontsize=10)
        for a in axs[:, j]:
            a.set_xticks([]); a.set_yticks([]); a.grid(False)
    fig.tight_layout(); fig.savefig(FIG / "fig_event_snapshots.png", dpi=150); plt.close(fig)


if __name__ == "__main__":
    import sys
    D = dict(np.load(R / "race_fleet.npz"))
    if "--snap-only" in sys.argv:
        snapshots(D, json.loads((R / "race_fleet.json").read_text())); raise SystemExit
    S = json.loads((R / "race_fleet.json").read_text())
    ev_stats = {p: json.loads((R / f"events_{p}.json").read_text()) for p in FLEET}
    figures(D, S); snapshots(D, S)
    n = grid_video(); print("grid frames", n)
    overview_video(D)
    summary = dict(race={p: {k: v for k, v in S[p].items() if k != "passes"} for p in FLEET},
                   events=ev_stats, meta=S["_meta"])
    (R / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1)[:3000])
