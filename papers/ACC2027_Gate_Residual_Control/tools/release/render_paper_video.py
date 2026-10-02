"""Real-time mission video for the GitHub release: X2 (left) and CF2 (right), five 45-s missions back to back.

Input: reproduce/recordings/<platform>_<mission>_<arm>/ from reproduce/record_mission.py (sealed runner, every run
MATCHes the published number). Per frame (1280x720, 30 fps, simulated time = video time):
  * top: MuJoCo render of each vehicle; solid axes = body, translucent axes = reference attitude
  * bottom: attitude error PD+ff (grey) vs PD+ff + gated CMG-PES (blue), the six CMG activities a_j, and the realized
    residual per axis as a fraction of its bound beta*l (the gate's blocks shaded)
Title and end cards carry the citation. Also writes a short GIF excerpt for the README.

Run with an environment that has mujoco + imageio + matplotlib (rendering only, no simulation):
    python tools/release/render_paper_video.py <out_dir>
"""
from __future__ import annotations

import sys
from pathlib import Path

import imageio.v2 as imageio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import mujoco  # noqa: E402
import numpy as np  # noqa: E402
import csv  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from gra_control.math3d import quat_conj, reference_quat  # noqa: E402
from gra_control.platforms.drone import SPECS  # noqa: E402

REC = REPO / "reproduce" / "recordings"
FPS, W, H = 30, 1280, 720
RW, RH, PH, TH = 640, 300, 380, 40          # render, plot and title heights
FONT = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 18)
FONT_S = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 15)
FONT_B = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 22)
FONT_T = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 34)
MISSIONS = [
    ("roll", "Roll", "single-axis roll, 0.25 rad sinusoid at 0.7 rad/s"),
    ("full3", "Full3", "three axes, 0.5 rad sinusoids, 1 rad/s, 90 deg apart"),
    ("hard45", "Hard45", "aggressive three-axis multisine, up to about 45 deg"),
    ("hardstep", "Hardstep", "steps every 2 s, up to 52 deg (saturates the torque box)"),
    ("yaw360", "Yaw360", "one smooth 360 deg yaw turn over 45 s"),
]
PLAT = {"x2": dict(spec="x2", label="Skydio X2", beta=0.5, dist=1.15, span=0.40),
        "cf2": dict(spec="cf2-rotor", label="Crazyflie 2 (1.5x rotors)", beta=0.2, dist=0.30, span=0.10)}
AX_COL = ([0.9, 0.2, 0.2], [0.2, 0.75, 0.2], [0.25, 0.4, 1.0])
CITE = ("G. Contreras, S. Sandoval, L. R. Garcia Carrillo, \"Online PES Decoder Learning in Neuromorphic Residual "
        "UAV Attitude Control,\" submitted to ACC 2027.")
REPO_URL = "github.com/gandhico/Neuromorphic-Embodied-AI/tree/main/online-pes-neuromorphic-residual-control"


def load(platform, mission):
    d = REC / f"{platform}_{mission}_cmg"
    z = np.load(d / "neural_trace_full_rate.npz")
    pose = np.load(d / "pose.npz")
    with (REC / f"{platform}_{mission}_pdff" / "trace.csv").open() as fh:
        rows = [(float(r["t"]), float(r["qerr_true_rad"])) for r in csv.DictReader(fh)]
    bt, be = map(np.asarray, zip(*rows))
    lim = np.array(__import__("json").loads((d / "summary.json").read_text())["actuation"]["torque_limits_Nm"])
    sl = slice(None, None, 50)                                      # 40 Hz for the plots
    return dict(t=z["t"][sl], err=np.degrees(z["qerr_true_rad"][sl]), act=z["activity"][sl],
                res=z["realized_residual_torque"][sl] / (PLAT[platform]["beta"] * lim[None, :]),
                blocked=(z["output_gate_mask"][sl] == 0).any(1),
                bt=bt, berr=np.degrees(be),
                pt=pose["t"], qpos=pose["qpos"])


class Panel:
    """Matplotlib panel (error, activity, residual) redrawn by set_data."""

    def __init__(self, title):
        self.fig, self.ax = plt.subplots(3, 1, figsize=(RW / 100, PH / 100), dpi=100, sharex=True)
        self.fig.subplots_adjust(left=0.11, right=0.985, top=0.93, bottom=0.09, hspace=0.18)
        self.fig.suptitle(title, fontsize=9, y=0.995)
        a0, a1, a2 = self.ax
        self.lb, = a0.semilogy([], [], color="0.55", lw=1.0, label="PD+ff alone")
        self.lc, = a0.semilogy([], [], color="tab:blue", lw=1.2, label="+ CMG-PES")
        a0.set_ylabel("error (deg)", fontsize=7); a0.legend(fontsize=6, loc="lower right", ncol=2)
        self.la = [a1.plot([], [], color=AX_COL[j % 3], ls="-" if j < 3 else "--", lw=1.0)[0] for j in range(6)]
        a1.set_ylim(-0.05, 1.08); a1.set_ylabel("CMG a_j", fontsize=7)
        a1.text(0.55, 1.02, "solid: +x +y +z   dashed: -x -y -z", transform=a1.transAxes, fontsize=6)
        self.lr = [a2.plot([], [], color=AX_COL[i], lw=1.0)[0] for i in range(3)]
        a2.set_ylim(-1.05, 1.05); a2.set_ylabel("residual / bound", fontsize=7); a2.set_xlabel("time (s)", fontsize=7)
        for a in self.ax:
            a.set_xlim(0, 45); a.tick_params(labelsize=6); a.grid(alpha=0.25)
        self.cur = [a.axvline(0, color="k", lw=0.6, alpha=0.5) for a in self.ax]
        self.shade = None

    def mission(self, D, ylim):
        """Draw the complete mission once; frames then reveal it up to the current time (fast, identical pixels)."""
        self.D = D
        self.ax[0].set_ylim(*ylim)
        if self.shade is not None:
            self.shade.remove()
            self.shade = None
        self.lb.set_data(D["bt"][::4], np.maximum(D["berr"][::4], 1e-4))
        self.lc.set_data(D["t"], np.maximum(D["err"], 1e-4))
        for j, l in enumerate(self.la):
            l.set_data(D["t"], D["act"][:, j])
        for i, l in enumerate(self.lr):
            l.set_data(D["t"], D["res"][:, i])
        if D["blocked"].any():
            self.shade = self.ax[2].fill_between(D["t"], -1.05, 1.05, where=D["blocked"], color="orange", alpha=0.25, lw=0)
        for c in self.cur:
            c.set_visible(False)
        self.fig.canvas.draw()
        self.base = np.asarray(self.fig.canvas.buffer_rgba())[..., :3].copy()
        h = self.base.shape[0]
        # pixel boxes of the three axes (rows top-down) and the data-to-pixel map of the shared time axis
        self.boxes = []
        for a in self.ax:
            (x0, y0), (x1, y1) = a.transAxes.transform([(0, 0), (1, 1)])
            self.boxes.append((int(round(h - y1)), int(round(h - y0)), int(round(x0)), int(round(x1))))
        (px0, _), (px45, _) = self.ax[0].transData.transform([(0, 1), (45, 1)])
        self.px = lambda t: px0 + (px45 - px0) * t / 45.0

    def draw(self, t):
        img = self.base.copy()
        xc = int(round(self.px(t)))
        for (r0, r1, c0, c1) in self.boxes:
            if xc + 1 < c1:
                region = img[r0 + 1:r1, max(xc + 1, c0 + 1):c1 - 1].astype(np.float32)
                img[r0 + 1:r1, max(xc + 1, c0 + 1):c1 - 1] = (0.12 * region + 0.88 * 255).astype(np.uint8)
            if c0 <= xc < c1:
                img[r0:r1, xc] = (60, 60, 60)
        return img


class View:
    def __init__(self, platform):
        p = PLAT[platform]
        self.m = mujoco.MjModel.from_xml_path(str(SPECS[p["spec"]].model))
        self.d = mujoco.MjData(self.m)
        self.r = mujoco.Renderer(self.m, RH, RW)
        self.cam = mujoco.MjvCamera(); self.cam.distance = p["dist"]; self.cam.azimuth = 135; self.cam.elevation = -18
        jid = next(j for j in range(self.m.njnt) if self.m.jnt_type[j] == mujoco.mjtJoint.mjJNT_FREE)
        self.body, self.qa = int(self.m.jnt_bodyid[jid]), int(self.m.jnt_qposadr[jid])
        self.span = p["span"]

    def render(self, qpos, t, mission):
        self.d.qpos[:] = qpos; mujoco.mj_forward(self.m, self.d)
        pos = self.d.xpos[self.body].copy()
        self.cam.lookat[:] = pos
        self.r.update_scene(self.d, camera=self.cam)
        scn = self.r.scene
        Rb = self.d.xmat[self.body].reshape(3, 3)
        Rd = np.zeros(9); mujoco.mju_quat2Mat(Rd, quat_conj(reference_quat(t, mission, 45.0))); Rd = Rd.reshape(3, 3)
        L = 1.0 * self.span
        for R, alpha, width in ((Rd, 0.35, 0.028), (Rb, 1.0, 0.014)):
            for k in range(3):
                if scn.ngeom >= scn.maxgeom:
                    break
                g = scn.geoms[scn.ngeom]
                mujoco.mjv_initGeom(g, mujoco.mjtGeom.mjGEOM_CAPSULE, np.zeros(3), np.zeros(3), np.zeros(9),
                                    np.array(AX_COL[k] + [alpha], dtype=np.float32))
                mujoco.mjv_connector(g, mujoco.mjtGeom.mjGEOM_CAPSULE, width * self.span, pos, pos + L * R[:, k])
                scn.ngeom += 1
        return self.r.render().copy()


def hud(img, lines):
    im = Image.fromarray(img); dr = ImageDraw.Draw(im)
    for i, s in enumerate(lines):
        dr.text((8, 6 + 21 * i), s, font=FONT_S if i else FONT, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
    return np.asarray(im)


def card(lines, sizes):
    im = Image.new("RGB", (W, H), (14, 22, 38)); dr = ImageDraw.Draw(im)
    y = 120
    for s, f in zip(lines, sizes):
        font = {"t": FONT_T, "b": FONT_B, "n": FONT, "s": FONT_S}[f]
        w = dr.textlength(s, font=font)
        dr.text(((W - w) / 2, y), s, font=font, fill=(235, 240, 250)); y += {"t": 56, "b": 38, "n": 32, "s": 26}[f]
    return np.asarray(im)


def main(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    views = {p: View(p) for p in PLAT}
    panels = {p: Panel(PLAT[p]["label"]) for p in PLAT}
    writer = imageio.get_writer(out_dir / "missions_x2_cf2_realtime.mp4", fps=FPS, codec="libx264", quality=7,
                                macro_block_size=16)
    gif_frames = []
    title = card(["Online PES Decoder Learning in", "Neuromorphic Residual UAV Attitude Control", "",
                  "Gated CMG-PES residual on a PD + desired-rate feedforward attitude controller",
                  "MuJoCo, Skydio X2 and Crazyflie 2, five 45-s missions, real time", "",
                  "G. Contreras, S. Sandoval, L. R. Garcia Carrillo  -  submitted to ACC 2027", REPO_URL],
                 ["t", "t", "n", "b", "n", "n", "n", "s"])
    for _ in range(4 * FPS):
        writer.append_data(title)
    summary_rows = []
    for mi, (mission, name, desc) in enumerate(MISSIONS):
        D = {p: load(p, mission) for p in PLAT}
        for p in PLAT:
            e = np.concatenate([D[p]["err"], D[p]["berr"]])
            panels[p].mission(D[p], (max(np.percentile(e, 5) * 0.5, 1e-4), np.max(e) * 1.6))
            mean = lambda arm: np.degrees(__import__("json").loads((REC / f"{p}_{mission}_{arm}" / "summary.json")
                                                                   .read_text())["metrics"]["qerr_true_mean_rad"])
            summary_rows.append((name, p, mean("pdff"), mean("cmg")))      # exact published means
        n_frames = int((PREVIEW_S or 45.0) * FPS)
        for f in range(n_frames):
            t = f / FPS
            top, bottom = [], []
            for p in PLAT:
                k = min(np.searchsorted(D[p]["pt"], t), len(D[p]["pt"]) - 1)
                ke = min(np.searchsorted(D[p]["t"], t), len(D[p]["t"]) - 1)
                kb = min(np.searchsorted(D[p]["bt"], t), len(D[p]["bt"]) - 1)
                img = views[p].render(D[p]["qpos"][k], t, mission)
                top.append(hud(img, [f"{PLAT[p]['label']}   t = {t:4.1f} s",
                                     f"error now: PD+ff {D[p]['berr'][kb]:.3f} deg   + CMG-PES {D[p]['err'][ke]:.3f} deg",
                                     "solid axes: body     translucent axes: reference"]))
                bottom.append(panels[p].draw(t))
            band = Image.new("RGB", (W, TH), (14, 22, 38)); dr = ImageDraw.Draw(band)
            dr.text((12, 8), f"Mission {mi + 1}/5: {name}  -  {desc}", font=FONT_B, fill=(235, 240, 250))
            dr.text((W - 330, 12), "real time  |  orange = gate blocking", font=FONT_S, fill=(200, 210, 230))
            frame = np.vstack([np.asarray(band), np.hstack(top), np.hstack(bottom)])
            writer.append_data(frame)
            if PREVIEW_S and f == int(1.5 * FPS):
                Image.fromarray(frame).save(out_dir / f"preview_{mission}.png")
            if mission == "hard45" and 10.0 <= t < 22.0 and f % 3 == 0:
                gif_frames.append(Image.fromarray(frame).resize((W // 2, H // 2), Image.LANCZOS))
            if f % 300 == 0:
                print(f"  {name} {t:4.1f} s", flush=True)
    lines = ["Mean attitude error over 45 s (deg): PD+ff  ->  PD+ff + gated CMG-PES", ""]
    for name in [m[1] for m in MISSIONS]:
        x = [r for r in summary_rows if r[0] == name]
        lines.append(f"{name:9s}   X2: {x[0][2]:.3f} -> {x[0][3]:.3f}      CF2: {x[1][2]:.3f} -> {x[1][3]:.3f}")
    lines += ["", "Geometric-mean reduction over the five missions: 37.3 % (X2), 22.4 % (CF2)", "",
              "Please cite: " + CITE[:95], CITE[95:], REPO_URL]
    end = card(lines, ["b", "n"] + ["n"] * 5 + ["n", "b", "n", "s", "s", "s"])
    for _ in range(8 * FPS):
        writer.append_data(end)
    writer.close()
    Image.fromarray(end).save(out_dir / "end_card.png")
    if gif_frames:
        gif_frames[0].save(out_dir / "hard45_excerpt.gif", save_all=True, append_images=gif_frames[1:], duration=100,
                       loop=0, optimize=True)
    print("wrote", out_dir)


PREVIEW_S = None

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[2] == "--preview":          # 2 s of each mission, for layout checks
        PREVIEW_S = 2.0
    main(Path(sys.argv[1]))
